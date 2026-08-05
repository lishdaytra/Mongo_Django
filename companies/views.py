import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from pymongo.errors import PyMongoError

from .models import CompanyAccess
from .services.mongo import (
    get_collection_name,
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