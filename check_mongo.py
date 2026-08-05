from getpass import getpass

from pymongo import MongoClient
from pymongo.errors import PyMongoError


def main() -> None:
    uri = getpass("Введите MongoDB URI — ввод будет скрыт: ")

    try:
        with MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        ) as client:
            ping_result = client.admin.command("ping")
            server_info = client.server_info()

            print("\nСоединение установлено.")
            print("Ping:", ping_result)
            print("Версия MongoDB:", server_info.get("version"))
            print("Максимальная wire-версия:", server_info.get("maxWireVersion"))

    except PyMongoError as error:
        print("\nСоединение не установлено.")
        print("Тип ошибки:", type(error).__name__)
        print("Описание:", error)


if __name__ == "__main__":
    main()