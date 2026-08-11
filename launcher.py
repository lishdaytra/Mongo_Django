import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

from dotenv import load_dotenv
from waitress import serve


def get_application_directory() -> Path:
    """
    В собранном приложении возвращает папку,
    в которой находится TitanWeb.exe.

    При обычном запуске возвращает папку проекта.
    """

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent


APP_DIR = get_application_directory()

# Все относительные пути будут считаться
# от папки рядом с TitanWeb.exe.
os.chdir(APP_DIR)

ENV_FILE = APP_DIR / ".env"

if not ENV_FILE.is_file():
    raise RuntimeError(
        "Не найден файл настроек .env.\n"
        f"Ожидаемый путь: {ENV_FILE}"
    )

load_dotenv(
    dotenv_path=ENV_FILE,
    override=False,
)

required_variables = [
    "DJANGO_SECRET_KEY",
]

missing_variables = [
    variable
    for variable in required_variables
    if not os.getenv(variable)
]

if missing_variables:
    raise RuntimeError(
        "В файле .env отсутствуют обязательные "
        "переменные: "
        + ", ".join(missing_variables)
    )

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

# Импорт Django должен выполняться только после
# загрузки переменных из .env.
from config.wsgi import application


HOST = "127.0.0.1"
PORT = 8765
URL = f"http://{HOST}:{PORT}/"


def open_browser() -> None:
    time.sleep(1.5)
    webbrowser.open(URL)


def main() -> None:
    threading.Thread(
        target=open_browser,
        daemon=True,
    ).start()

    print("Titan Web запущен.")
    print(f"Адрес: {URL}")
    print("Для завершения закройте это окно.")

    serve(
        application,
        host=HOST,
        port=PORT,
        threads=4,
    )


if __name__ == "__main__":
    main()