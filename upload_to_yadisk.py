#!/usr/bin/python3

"""
Скрипт загрузки файла на яндекс.диск

Использовать: <script_name> -s <Путь к файлу> --d <в какую папку на диске положить>
параметр --d не обязателен.
!!! Добавьте токен авторизации в переменную окружения YANDEX_AUTH_TOKEN перед использованием.
Для работы через http/https прокси добавьте переменную окружения YA_HTTP_PROXY и укажите в ней адрес прокси с протоколом

!!! Папки на Яндекс.Диске нужно создавать вручную.
!!! Скрипт заливает только 1 файл за вызов.
"""

import threading
import os
import json
import sys
from pathlib import Path, PurePosixPath
from argparse import ArgumentParser
import requests

# Настройки
home_dir = os.environ.get('HOME')
with open('data/config.json', 'r') as f:
    settings = json.load(f)    
YANDEX_DISK_API_URL = settings['url'] + "/disk/resources/upload"
TOKEN = settings['token']
LOCAL_DIRECTORY = home_dir + "/" + settings['directory']

def upload(path_to_file, upload_to, overwrite: bool = True):
   
    print("Размер:", round(os.path.getsize(path_to_file) / (1024**3), 2), "GB")
    
    file_name = os.path.basename(path_to_file)

    session = requests.Session()
    if os.environ.get("YA_HTTP_PROXY", False):
        session.proxies = {"HTTP": os.environ["YA_HTTP_PROXY"], "HTTPS": os.environ["YA_HTTP_PROXY"]}

    session.headers = {'Authorization': f'OAuth {TOKEN}'}
    upload_url_request = f"{YANDEX_DISK_API_URL}?path={upload_to}/{file_name}&overwrite={str(overwrite).lower()}"
    
    upload_url = session.get(upload_url_request).json()

    print("upload_url: ",upload_url)
    assert upload_url.get("href", False), f"Ну удалось получить url для загрузки файла. Ответ Api: {upload_url}"

    try:
        print("Uploading...")
        with open(path_to_file, 'rb') as data:
            upload_request = session.put(upload_url["href"], data=data)
            print ("upload_request: ", upload_request)
        if upload_request.status_code == 201:
            print("Файл успешно загружен.")
            if  os.path.exists(path_to_file):
                os.remove(path_to_file)

        elif upload_request.status_code == 202:
            print("Файл принят сервером, но еще не был перенесен непосредственно в Яндекс.Диск")

        elif upload_request.status_code == 413:
            print("Слишком большой файл, лимит на размер файла равен 50GB.")
            exit_result.append(1)

        elif upload_request.status_code in [500, 503]:
            print("HTTP 500/503, Яше плохо. Попробуйте позже.")
            exit_result.append(1)

        elif upload_request.status_code == 507:
            print("На Яндекс.Диске закончилось место.")
            exit_result.append(1)

    except FileNotFoundError:
        print("Файл", file, "не найден. Проверьте правильность пути.")

    except requests.exceptions.ConnectTimeout:
        print("Недоступен сервер Яндекс.Диск или проблемы с сетью.")


if __name__ == "__main__":
    # arg_parser = ArgumentParser()
    # arg_parser.add_argument("-s", type=str, help="Локальный путь к загружаемомму файлу")
    # arg_parser.add_argument("--d", type=str, default='', help="Папка, в которую следует поместить файл на Яндекс.Диске")
    # args = arg_parser.parse_args()
    upload(f'{LOCAL_DIRECTORY}/Приложения/test2.zip', "/Приложения")
    print("it`s OK!")
    exit(0)
    upload(Path(args.s), upload_to=PurePosixPath(args.d))
