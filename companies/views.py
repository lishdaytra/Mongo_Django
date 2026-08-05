import logging
import math
import re


from django.shortcuts import redirect, render
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import PyMongoError
from django.http import Http404
from datetime import datetime


from .services.mongo import (
    clean_company_id,
    get_collection_name,
    get_company_collection,
    get_titan_database,
    resolve_database_name,
)


logger = logging.getLogger(__name__)

MODE_LABELS = {
    "retail": "RetailServer",
    "cash": "CashServer",
}


def get_connection_context(
    mode: str,
    company_id: str,
) -> dict:
    """
    Проверяет параметры адреса и возвращает
    информацию о подключении для шаблонов.
    """

    try:
        clean_id = clean_company_id(company_id)
        database_name = resolve_database_name(
            mode,
            clean_id,
        )

    except ValueError as error:
        raise Http404(str(error)) from error

    return {
        "mode": mode,
        "mode_label": MODE_LABELS.get(
            mode,
            mode,
        ),
        "company_id": clean_id,

        # Оставляем это поле для совместимости
        # с уже созданными шаблонами.
        "company_name": clean_id,

        "database_name": database_name,
    }

DOCUMENT_TYPE_LABELS = {
    "Check": "Кассовый чек",
    "CashShift": "Z-отчёт",
    "MoneyOrder": "Кассовая операция",
    "IssuingCash": "Выдача денежных средств",
    "Cancellation": "Аннулирование",
}

PAYMENT_TYPE_LABELS = {
    1: "Наличные",
    2: "Безналичные",
    3: "Прочие",
}

TAX_LABELS = {
    0: "Без налогов",
    1: "0%",
    2: "10%",
    3: "20%",
    4: "25%",
}


def format_document_datetime(value):
    """
    Преобразует строку вида 2025-02-18T18:34:18.000
    в привычный формат 18.02.2025 18:34:18.
    """

    if not value:
        return "—"

    try:
        clean_value = str(value).replace("Z", "+00:00")
        parsed_value = datetime.fromisoformat(clean_value)

        return parsed_value.strftime("%d.%m.%Y %H:%M:%S")

    except (TypeError, ValueError):
        return str(value)


def get_document_type_label(document):
    document_type = document.get("Type")

    if document_type == "Check":
        if document.get("Refund") is True:
            return "Возврат"

        return "Продажа"

    if document_type == "MoneyOrder":
        if document.get("IsDeposit") is True:
            return "Внесение"

        return "Изъятие"

    return DOCUMENT_TYPE_LABELS.get(
        document_type,
        document_type or "Неизвестный тип",
    )


def summarize_payments(payments):
    result = {
        "cash": 0.0,
        "cashless": 0.0,
        "other": 0.0,
    }

    if not isinstance(payments, list):
        return result

    for payment in payments:
        if not isinstance(payment, dict):
            continue

        try:
            payment_sum = float(payment.get("Sum") or 0)
        except (TypeError, ValueError):
            payment_sum = 0.0

        payment_type = payment.get("TypeFlag")

        if payment_type == 1:
            result["cash"] += payment_sum
        elif payment_type == 2:
            result["cashless"] += payment_sum
        else:
            result["other"] += payment_sum

    return result


def dashboard(request):
    error = None

    selected_mode = request.POST.get(
        "mode",
        "retail",
    )

    company_id = request.POST.get(
        "company_id",
        "",
    ).strip()

    if request.method == "POST":
        try:
            clean_id = clean_company_id(company_id)

            resolve_database_name(
                selected_mode,
                clean_id,
            )

        except ValueError as validation_error:
            error = str(validation_error)

        else:
            return redirect(
                "companies:company_dashboard",
                mode=selected_mode,
                company_id=clean_id,
            )

    return render(
        request,
        "companies/dashboard.html",
        {
            "error": error,
            "selected_mode": selected_mode,
            "company_id": company_id,
        },
    )

def company_dashboard(
    request,
    mode,
    company_id,
):
    access = get_connection_context(
        mode,
        company_id,
    )

    mongo_available = False
    mongo_error = None
    collections = []

    try:
        database = get_titan_database(
            mode,
            company_id,
        )

        existing_collections = set(
            database.list_collection_names()
        )

        mongo_available = True

        collection_descriptions = (
            ("Goods", "Товары"),
            ("User", "Пользователи"),
            (
                "CashDocuments",
                "Кассовые документы",
            ),
        )

        for suffix, label in collection_descriptions:
            collection_name = get_collection_name(
                company_id,
                suffix,
                mode=mode,
            )

            collections.append(
                {
                    "label": label,
                    "name": collection_name,
                    "exists": (
                        collection_name
                        in existing_collections
                    ),
                }
            )

    except Exception as error:
        logger.exception(
            "Ошибка подключения к MongoDB."
        )

        mongo_error = (
            "Не удалось подключиться к базе "
            f"{access['database_name']}: "
            f"{type(error).__name__}"
        )

    return render(
        request,
        "companies/company_dashboard.html",
        {
            "access": access,
            "collections": collections,
            "mongo_available": mongo_available,
            "mongo_error": mongo_error,
        },
    )

def goods_list(request, mode, company_id):
    access = get_connection_context(
    mode,
    company_id,
    )

    search_query = request.GET.get("q", "").strip()
    show_deleted = (
    request.GET.get("show_deleted") == "1"
    )

    try:
        page_number = int(
            request.GET.get("page", "1")
        )
    except ValueError:
        page_number = 1

    page_number = max(page_number, 1)
    page_size = 50

    mongo_filter = {}
    if not show_deleted:
        mongo_filter["Deleted"] = False

    if search_query:
        safe_query = re.escape(search_query)

        mongo_filter["$or"] = [
            {
                "Name": {
                    "$regex": safe_query,
                    "$options": "i",
                },
            },
            {
                "Barcode": {
                    "$regex": safe_query,
                    "$options": "i",
                },
            },
            {
                "VendorCode": {
                    "$regex": safe_query,
                    "$options": "i",
                },
            },
        ]

    try:
        collection = get_company_collection(
            mode,
            company_id,
            "Goods",
        )

        total_count = collection.count_documents(
            mongo_filter
        )

        page_count = max(
            math.ceil(total_count / page_size),
            1,
        )

        page_number = min(
            page_number,
            page_count,
        )

        skip_count = (
            page_number - 1
        ) * page_size

        projection = {
            "_id": 0,
            "Id": 1,
            "Name": 1,
            "Barcode": 1,
            "VendorCode": 1,
            "Price": 1,
            "Measure": 1,
            "VATrate": 1,
            "Sale": 1,
            "Deleted": 1,
            "Manufacturer": 1,
        }

        goods = list(
            collection.find(
                mongo_filter,
                projection,
            )
            .sort("Name", ASCENDING)
            .skip(skip_count)
            .limit(page_size)
        )

        mongo_error = None

    except PyMongoError:
        logger.exception(
            "Ошибка чтения справочника товаров."
        )

        goods = []
        total_count = 0
        page_count = 1
        mongo_error = (
            "Не удалось получить справочник товаров."
        )

    context = {
        "access": access,
        "goods": goods,
        "query": search_query,
        "total_count": total_count,
        "page_number": page_number,
        "page_count": page_count,
        "has_previous": page_number > 1,
        "has_next": page_number < page_count,
        "previous_page": page_number - 1,
        "next_page": page_number + 1,
        "mongo_error": mongo_error,
        "show_deleted": show_deleted,
    }

    return render(
        request,
        "companies/goods_list.html",
        context,
    )


def cash_documents_list(request, mode, company_id):
    access = get_connection_context(
        mode,
        company_id,
    )

    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()
    number = request.GET.get("number", "").strip()
    cashier = request.GET.get("cashier", "").strip()
    serial_id = request.GET.get("serial_id", "").strip()
    document_type = request.GET.get("type", "").strip()
    operation = request.GET.get("operation", "").strip()
    show_deleted = (
        request.GET.get("show_deleted") == "1"
    )

    try:
        page_number = int(
            request.GET.get("page", "1")
        )
    except ValueError:
        page_number = 1

    page_number = max(page_number, 1)
    page_size = 50

    mongo_filter = {
        "StatusFlag": 2,
    }
    if not show_deleted:
        mongo_filter["Deleted"] = False

    position_filter = {}

    if date_from:
        position_filter["$gte"] = (
            f"{date_from}T00:00:00.000"
        )

    if date_to:
        position_filter["$lte"] = (
            f"{date_to}T23:59:59.999"
        )

    if position_filter:
        mongo_filter["Position"] = position_filter

    if number:
        mongo_filter["Number"] = {
            "$regex": re.escape(number),
            "$options": "i",
        }

    if cashier:
        mongo_filter["Author.Name"] = {
            "$regex": re.escape(cashier),
            "$options": "i",
        }

    if serial_id:
        mongo_filter["SerialId"] = {
            "$regex": re.escape(serial_id),
            "$options": "i",
        }

    if document_type:
        mongo_filter["Type"] = document_type

    if operation == "sale":
        mongo_filter["Type"] = "Check"
        mongo_filter["Refund"] = {
            "$ne": True,
        }

    elif operation == "refund":
        mongo_filter["Type"] = "Check"
        mongo_filter["Refund"] = True

    try:
        collection = get_company_collection(
            mode,
            company_id,
            "CashDocuments",
        )

        total_count = collection.count_documents(
            mongo_filter
        )

        page_count = max(
            math.ceil(total_count / page_size),
            1,
        )

        page_number = min(
            page_number,
            page_count,
        )

        skip_count = (
            page_number - 1
        ) * page_size

        projection = {
            "_id": 0,
            "Id": 1,
            "Author": 1,
            "CreatedAt": 1,
            "Position": 1,
            "Number": 1,
            "Payments": 1,
            "Refund": 1,
            "IsDeposit": 1,
            "SerialId": 1,
            "Signature": 1,
            "DiscountSum": 1,
            "TotalSum": 1,
            "Type": 1,
            "Deleted": 1,
        }

        cursor = (
            collection.find(
                mongo_filter,
                projection,
            )
            .sort("Position", DESCENDING)
            .skip(skip_count)
            .limit(page_size)
        )

        documents = []

        for document in cursor:
            author = document.get("Author")

            if not isinstance(author, dict):
                author = {}

            documents.append(
                {
                    "id": document.get("Id", ""),
                    "number": document.get(
                        "Number",
                        "—",
                    ),
                    "type_label": (
                        get_document_type_label(
                            document
                        )
                    ),
                    "type": document.get(
                        "Type",
                        "",
                    ),
                    "position": (
                        format_document_datetime(
                            document.get("Position")
                        )
                    ),
                    "created_at": (
                        format_document_datetime(
                            document.get("CreatedAt")
                        )
                    ),
                    "cashier": author.get(
                        "Name",
                        "—",
                    ),
                    "serial_id": document.get(
                        "SerialId",
                        "—",
                    ),
                    "discount_sum": float(
                        document.get(
                            "DiscountSum",
                            0,
                        )
                        or 0
                    ),
                    "total_sum": float(
                        document.get(
                            "TotalSum",
                            0,
                        )
                        or 0
                    ),
                    "payments": summarize_payments(
                        document.get(
                            "Payments",
                            [],
                        )
                    ),
                }
            )

        mongo_error = None

    except PyMongoError:
        logger.exception(
            "Ошибка чтения кассовых документов."
        )

        documents = []
        total_count = 0
        page_count = 1
        mongo_error = (
            "Не удалось получить кассовые документы."
        )

    pagination_params = request.GET.copy()
    pagination_params.pop("page", None)

    context = {
        "access": access,
        "documents": documents,
        "total_count": total_count,
        "page_number": page_number,
        "page_count": page_count,
        "has_previous": page_number > 1,
        "has_next": page_number < page_count,
        "previous_page": page_number - 1,
        "next_page": page_number + 1,
        "pagination_query": (
            pagination_params.urlencode()
        ),
        "mongo_error": mongo_error,

        "date_from": date_from,
        "date_to": date_to,
        "number": number,
        "cashier": cashier,
        "serial_id": serial_id,
        "selected_type": document_type,
        "selected_operation": operation,
        "show_deleted": show_deleted,
    }

    return render(
        request,
        "companies/cash_documents_list.html",
        context,
    )


def cash_document_detail(
    request,
    mode,
    company_id,
    document_id,
):
    access = get_connection_context(
        mode,
        company_id,
    )

    try:
        collection = get_company_collection(
            mode,
            company_id,
            "CashDocuments",
        )

        document = collection.find_one(
            {
                "Id": document_id,
            },
            {
                "_id": 0,
            },
        )

    except PyMongoError as error:
        logger.exception(
            "Ошибка чтения кассового документа."
        )

        raise Http404(
            "Не удалось получить документ."
        ) from error

    if document is None:
        raise Http404(
            "Кассовый документ не найден."
        )

    author = document.get("Author")

    if not isinstance(author, dict):
        author = {}

    prepared_lines = []

    for line in document.get("Lines", []):
        if not isinstance(line, dict):
            continue

        goods = line.get("Goods")

        if not isinstance(goods, dict):
            goods = {}

        tax_value = line.get("Tax")

        prepared_lines.append(
            {
                "name": goods.get(
                    "Name",
                    "Без названия",
                ),
                "barcode": goods.get(
                    "Barcode",
                    "—",
                ),
                "vendor_code": goods.get(
                    "VendorCode",
                    "—",
                ),
                "measure": goods.get(
                    "Measure",
                    "—",
                ),
                "quantity": float(
                    line.get("Quantity", 0) or 0
                ),
                "price": float(
                    line.get("Price", 0) or 0
                ),
                "discount_rate": float(
                    line.get("DiscountRate", 0) or 0
                ),
                "discount_sum": float(
                    line.get("DiscountSum", 0) or 0
                ),
                "discount_label": line.get(
                    "DiscountLabel",
                    "",
                ),
                "total_sum": float(
                    line.get("TotalSum", 0) or 0
                ),
                "tax": TAX_LABELS.get(
                    tax_value,
                    str(tax_value)
                    if tax_value is not None
                    else "—",
                ),
            }
        )

    prepared_payments = []

    for payment in document.get("Payments", []):
        if not isinstance(payment, dict):
            continue

        payment_type = payment.get("TypeFlag")

        prepared_payments.append(
            {
                "type": PAYMENT_TYPE_LABELS.get(
                    payment_type,
                    f"Тип {payment_type}",
                ),
                "sum": float(
                    payment.get("Sum", 0) or 0
                ),
            }
        )

    context = {
        "access": access,
        "document": {
            "id": document.get("Id", ""),
            "number": document.get(
                "Number",
                "—",
            ),
            "type_label": get_document_type_label(
                document
            ),
            "created_at": format_document_datetime(
                document.get("CreatedAt")
            ),
            "position": format_document_datetime(
                document.get("Position")
            ),
            "cashier": author.get(
                "Name",
                "—",
            ),
            "serial_id": document.get(
                "SerialId",
                "—",
            ),
            "signature": document.get(
                "Signature",
                "—",
            ),
            "currency": document.get(
                "Currency",
                "BYN",
            ),
            "discount_sum": float(
                document.get("DiscountSum", 0) or 0
            ),
            "total_sum": float(
                document.get("TotalSum", 0) or 0
            ),
            "deleted": document.get("Deleted") is True,
        },
        "lines": prepared_lines,
        "payments": prepared_payments,
    }

    return render(
        request,
        "companies/cash_document_detail.html",
        context,
    )