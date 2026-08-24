import os
import sys
import threading
import time
import webbrowser

from pathlib import Path

import pystray
from PIL import Image
from waitress.server import create_server


# ---------------------------------------------------------
# Пути
# ---------------------------------------------------------

BUNDLE_DIR = Path(__file__).resolve().parent

if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
else:
    APP_DIR = BUNDLE_DIR

os.chdir(APP_DIR)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)


# Django импортируем после установки переменной окружения
from config.wsgi import application


# ---------------------------------------------------------
# Titan Web
# ---------------------------------------------------------

HOST = "127.0.0.1"
PORT = 4000

URL = f"http://{HOST}:{PORT}/"


# ---------------------------------------------------------
# Waitress
# ---------------------------------------------------------

server = create_server(
    application,
    host=HOST,
    port=PORT,
    threads=4,
)


def run_server():
    server.run()


# ---------------------------------------------------------
# Браузер
# ---------------------------------------------------------

def open_titan_web(icon=None, item=None):
    webbrowser.open(URL)


def open_browser_after_start():
    time.sleep(1)
    open_titan_web()


# ---------------------------------------------------------
# Завершение приложения
# ---------------------------------------------------------

def exit_titan_web(icon, item):
    try:
        server.close()
    except Exception:
        pass

    try:
        server.task_dispatcher.shutdown(
            cancel_pending=True,
            timeout=2,
        )
    except Exception:
        pass

    icon.stop()


# ---------------------------------------------------------
# Tray
# ---------------------------------------------------------

tray_image = Image.open(
    BUNDLE_DIR
    / "assets"
    / "TW.png"
)


tray_menu = pystray.Menu(
    pystray.MenuItem(
        "Открыть Titan Web",
        open_titan_web,
        default=True,
    ),

    pystray.Menu.SEPARATOR,

    pystray.MenuItem(
        "Выход",
        exit_titan_web,
    ),
)


tray_icon = pystray.Icon(
    "TitanWeb",
    tray_image,
    "Titan Web — Сервисный помощник",
    tray_menu,
)


# ---------------------------------------------------------
# Запуск
# ---------------------------------------------------------

if __name__ == "__main__":

    server_thread = threading.Thread(
        target=run_server,
        daemon=True,
    )

    server_thread.start()

    threading.Thread(
        target=open_browser_after_start,
        daemon=True,
    ).start()

    tray_icon.run()