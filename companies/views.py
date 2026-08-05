import logging
import math
import re

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import PyMongoError
from django.http import Http404

from .models import CompanyAccess
from .services.mongo import (
    get_collection_name,
    get_company_collection,
    get_titan_database,
)


logger = logging.getLogger(__name__)


@login_required
def dashboard(request):
    accesses = CompanyAccess.objects.filter(
        user=request.user,
        is_active=True,
    )

    companies = []
    mongo_available = False
    mongo_error = None

    try:
        database = get_titan_database()

        # Получаем имена коллекций один раз,
        # а не отдельным запросом для каждой компании.
        existing_collections = set(
            database.list_collection_names()
        )

        mongo_available = True

        for access in accesses:
            goods_collection = get_collection_name(
                access.company_id,
                "Goods",
            )
            users_collection = get_collection_name(
                access.company_id,
                "User",
            )
            cash_documents_collection = get_collection_name(
                access.company_id,
                "CashDocuments",
            )

            companies.append(
                {
                    "access": access,
                    "collections": [
                        {
                            "label": "Товары",
                            "name": goods_collection,
                            "exists": (
                                goods_collection
                                in existing_collections
                            ),
                        },
                        {
                            "label": "Пользователи",
                            "name": users_collection,
                            "exists": (
                                users_collection
                                in existing_collections
                            ),
                        },
                        {
                            "label": "Кассовые документы",
                            "name": cash_documents_collection,
                            "exists": (
                                cash_documents_collection
                                in existing_collections
                            ),
                        },
                    ],
                },
            )

    except PyMongoError:
        logger.exception(
            "Не удалось подключиться к MongoDB TitanRetail."
        )
        mongo_error = (
            "Не удалось получить данные из TitanRetail. "
            "Проверьте подключение и журнал сервера."
        )

    context = {
        "companies": companies,
        "mongo_available": mongo_available,
        "mongo_error": mongo_error,
    }

    return render(
        request,
        "companies/dashboard.html",
        context,
    )

@login_required
def goods_list(request, company_id):
    access = get_object_or_404(
        CompanyAccess,
        user=request.user,
        company_id=company_id,
        is_active=True,
    )

    search_query = request.GET.get("q", "").strip()

    try:
        page_number = int(
            request.GET.get("page", "1")
        )
    except ValueError:
        page_number = 1

    page_number = max(page_number, 1)
    page_size = 50

    mongo_filter = {
        "Deleted": {"$ne": True},
    }

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
    }

    return render(
        request,
        "companies/goods_list.html",
        context,
    )