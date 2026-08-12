import os
import sys
import threading
import time
import webbrowser

from pathlib import Path

from waitress import serve


def get_app_dir():
    if getattr(sys, "frozen", False):
        return Path(
            sys.executable
        ).resolve().parent

    return Path(
        __file__
    ).resolve().parent


APP_DIR = get_app_dir()

os.chdir(APP_DIR)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)


from config.wsgi import application


HOST = "127.0.0.1"
PORT = 4000

URL = f"http://{HOST}:{PORT}/"


def open_browser():
    time.sleep(1)

    webbrowser.open(
        URL
    )


if __name__ == "__main__":
    threading.Thread(
        target=open_browser,
        daemon=True,
    ).start()

    serve(
        application,
        host=HOST,
        port=PORT,
        threads=4,
    )