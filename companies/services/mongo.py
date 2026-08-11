import re
from functools import lru_cache

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database


ALLOWED_COLLECTION_SUFFIXES = frozenset(
    {
        "Goods",
        "User",
        "CashDocuments",
    }
)


class CompanyCollectionNotFoundError(LookupError):
    """Основная коллекция компании не найдена."""


ALLOWED_MODES = frozenset(
    {
        "retail",
        "cash",
        "proxy",
    }
)

COMPANY_ID_PATTERN = re.compile(
    r"^[A-Za-z0-9_-]+$"
)


def clean_company_id(company_id: str) -> str:
    """
    Проверяет ID компании перед формированием
    имени базы и коллекции.
    """

    clean_value = str(company_id).strip()

    if not clean_value:
        raise ValueError(
            "Не указан ID компании."
        )

    if not COMPANY_ID_PATTERN.fullmatch(clean_value):
        raise ValueError(
            "ID компании может содержать только "
            "латинские буквы, цифры, дефис "
            "и подчёркивание."
        )

    return clean_value


def validate_mode(mode: str) -> str:
    clean_mode = str(mode).strip().lower()

    if clean_mode not in ALLOWED_MODES:
        raise ValueError(
            f"Неизвестный режим подключения: {mode}"
        )

    return clean_mode


def resolve_database_name(
    mode: str,
    company_id: str,
) -> str:
    """
    Определяет имя базы MongoDB.

    Для RetailServer:
    1... -> RetailServer1
    2... -> RetailServer2
    ...
    9... -> RetailServer9
    остальные -> RetailServer

    Для CashServer база всегда CashServer.
    """

    clean_mode = validate_mode(mode)
    clean_company_id_value = clean_company_id(
        company_id
    )

    if clean_mode == "cash":
        return settings.CASH_DB_NAME

    if clean_mode == "proxy":
        return settings.RETAIL_PROXY_DB_NAME

    first_character = clean_company_id_value[0]

    if first_character in "123456789":
        return (
            f"{settings.RETAIL_DB_PREFIX}"
            f"{first_character}"
        )

    return settings.RETAIL_DB_PREFIX


def get_connection_uri(mode: str) -> str:
    clean_mode = validate_mode(mode)

    if clean_mode == "cash":
        uri = settings.CASH_MONGO_URI
        variable_name = "CASH_MONGO_URI"

    elif clean_mode == "proxy":
        uri = settings.RETAIL_PROXY_MONGO_URI
        variable_name = "RETAIL_PROXY_MONGO_URI"

    else:
        uri = settings.RETAIL_MONGO_URI
        variable_name = "RETAIL_MONGO_URI"

    if not uri:
        raise ImproperlyConfigured(
            f"Переменная {variable_name} не задана."
        )

    return uri


@lru_cache(maxsize=4)
def get_mongo_client(uri: str) -> MongoClient:
    """
    Возвращает единый MongoClient для каждого URI.
    """

    return MongoClient(
        uri,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        appname="Titan Web",
    )


def get_titan_database(
    mode: str,
    company_id: str,
) -> Database:
    uri = get_connection_uri(mode)

    database_name = resolve_database_name(
        mode,
        company_id,
    )

    client = get_mongo_client(uri)

    return client[database_name]


def get_collection_name(
    company_id: str,
    suffix: str,
    mode: str = "retail",
) -> str:
    """
    Формирует имя коллекции.

    RetailServer:
        {company_id}Goods
        {company_id}User
        {company_id}CashDocuments

    CashServer:
        Goods
        User
        CashDocuments
    """

    if suffix not in ALLOWED_COLLECTION_SUFFIXES:
        raise ValueError(
            f"Недопустимый тип коллекции: {suffix}"
        )

    clean_mode = validate_mode(mode)

    if clean_mode in {"cash", "proxy"}:
        return suffix

    clean_value = clean_company_id(company_id)
    separator = settings.MONGO_COLLECTION_SEPARATOR

    return f"{clean_value}{separator}{suffix}"

def ensure_primary_collection_exists(
    mode: str,
    company_id: str,
) -> str:
    """
    Проверяет наличие основной коллекции товаров.

    RetailServer:
        {company_id}Goods

    CashServer:
        Goods

    Возвращает имя найденной коллекции.
    Если коллекции нет — вызывает исключение.
    """

    clean_mode = validate_mode(mode)
    clean_id = clean_company_id(company_id)

    database = get_titan_database(
        clean_mode,
        clean_id,
    )

    primary_collection_name = get_collection_name(
        clean_id,
        "Goods",
        mode=clean_mode,
    )

    existing_collections = set(
        database.list_collection_names()
    )

    if primary_collection_name not in existing_collections:
        raise CompanyCollectionNotFoundError(
            "Компания не найдена. "
            f"В базе «{database.name}» отсутствует "
            f"основная коллекция "
            f"«{primary_collection_name}»."
        )

    return primary_collection_name

def get_company_collection(
    mode: str,
    company_id: str,
    suffix: str,
) -> Collection:
    database = get_titan_database(
        mode,
        company_id,
    )

    collection_name = get_collection_name(
        company_id,
        suffix,
        mode=mode,
    )

    return database[collection_name]