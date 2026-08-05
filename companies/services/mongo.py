from functools import lru_cache

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from pymongo import MongoClient
from pymongo.database import Database


ALLOWED_COLLECTION_SUFFIXES = frozenset(
    {
        "Goods",
        "User",
        "CashDocuments",
    }
)


@lru_cache(maxsize=1)
def get_mongo_client() -> MongoClient:
    """Возвращает единый MongoClient для приложения."""

    if not settings.MONGO_URI:
        raise ImproperlyConfigured(
            "Переменная MONGO_URI не задана."
        )

    return MongoClient(
        settings.MONGO_URI,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
    )


def get_titan_database() -> Database:
    """Возвращает базу TitanRetail."""

    if not settings.MONGO_DB_NAME:
        raise ImproperlyConfigured(
            "Переменная MONGO_DB_NAME не задана."
        )

    client = get_mongo_client()
    return client[settings.MONGO_DB_NAME]


def get_collection_name(
    company_id: str,
    suffix: str,
) -> str:
    """Формирует безопасное имя коллекции компании."""

    if suffix not in ALLOWED_COLLECTION_SUFFIXES:
        raise ValueError(
            f"Недопустимый тип коллекции: {suffix}"
        )

    clean_company_id = company_id.strip()

    if not clean_company_id:
        raise ValueError("Не указан идентификатор компании.")

    separator = settings.MONGO_COLLECTION_SEPARATOR

    return f"{clean_company_id}{separator}{suffix}"