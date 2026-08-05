from typing import Any

from django.core.management.base import BaseCommand, CommandError
from pymongo.errors import PyMongoError

from companies.services.mongo import (
    get_collection_name,
    get_titan_database,
)


COLLECTION_SUFFIXES = (
    "Goods",
    "User",
    "CashDocuments",
)


def describe_value(value: Any) -> str:
    """Возвращает тип значения без вывода самого значения."""

    if isinstance(value, dict):
        nested_keys = list(value.keys())[:15]
        keys_text = ", ".join(str(key) for key in nested_keys)

        if len(value) > 15:
            keys_text += ", ..."

        return f"object; поля: {keys_text}"

    if isinstance(value, list):
        if not value:
            return "array; пустой"

        item_types = sorted(
            {
                type(item).__name__
                for item in value[:20]
            }
        )

        return (
            "array; типы элементов: "
            + ", ".join(item_types)
        )

    return type(value).__name__


class Command(BaseCommand):
    help = (
        "Показывает количество документов и структуру "
        "коллекций компании TitanRetail."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "company_id",
            type=str,
            help="Префикс компании, например vial",
        )

    def handle(self, *args, **options):
        company_id = options["company_id"].strip()

        if not company_id:
            raise CommandError(
                "Не указан идентификатор компании."
            )

        try:
            database = get_titan_database()
            existing_collections = set(
                database.list_collection_names()
            )

            for suffix in COLLECTION_SUFFIXES:
                collection_name = get_collection_name(
                    company_id,
                    suffix,
                )

                self.stdout.write("")
                self.stdout.write(
                    self.style.MIGRATE_HEADING(
                        f"Коллекция: {collection_name}"
                    )
                )

                if collection_name not in existing_collections:
                    self.stdout.write(
                        self.style.ERROR(
                            "Коллекция не найдена."
                        )
                    )
                    continue

                collection = database[collection_name]

                document_count = (
                    collection.estimated_document_count()
                )

                self.stdout.write(
                    f"Примерное количество документов: "
                    f"{document_count}"
                )

                sample = collection.find_one()

                if sample is None:
                    self.stdout.write(
                        self.style.WARNING(
                            "Коллекция существует, "
                            "но документов в ней нет."
                        )
                    )
                    continue

                self.stdout.write(
                    "Поля первого документа:"
                )

                for field_name, field_value in sample.items():
                    description = describe_value(
                        field_value
                    )

                    self.stdout.write(
                        f"  {field_name}: {description}"
                    )

        except PyMongoError as error:
            raise CommandError(
                "Ошибка при обращении к MongoDB: "
                f"{type(error).__name__}: {error}"
            ) from error