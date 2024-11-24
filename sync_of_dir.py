import os
import requests
import json
from requests.exceptions import HTTPError
import shutil


# Настройки
home_dir = os.environ.get('HOME')
with open('data/config.json', 'r') as f:
    settings = json.load(f)    
YANDEX_DISK_API_URL = settings['url']
TOKEN = settings['token']
LOCAL_DIRECTORY = home_dir + "/" + settings['directory']
yandex_folders = [] # глобальная переменная что бы получить итоговый список из рекурсивной функции

# Функция для получения информации о директории
def get_folder_info(folder_id='/'):
    url = YANDEX_DISK_API_URL
    params = {
        'path': folder_id,
        'fields': '_embedded.items.name,_embedded.items.type',
        'limit': 10000
    }
    headers = {'Authorization': f'OAuth {TOKEN}'}
    response = requests.get(url, params=params, headers=headers)
    try:
        response.raise_for_status()  # Проверка на ошибки
    except HTTPError:
        print("Ошибка авторизации. Пробуем ещё раз...")
        response = requests.get(url, params=params, headers=headers)
    return response.json()

# Рекурсивная функция для подсчета глубины вложенности
def max_depth(path='/', depth=0): 
    yandex_folders.append(path)
    info = get_folder_info(path)
    folders = [item['name'] for item in info['_embedded']['items'] if item['type'] == 'dir']
    if not folders:
        return depth
    if path == '/':
        return max(max_depth(f'{path}{folder}', depth + 1) for folder in folders)    
    else:
        return max(max_depth(f'{path}/{folder}', depth + 1) for folder in folders)

# Создание папок в локальном каталоге
def create_local_folders(yandex_folders, parent_folder=LOCAL_DIRECTORY):
    for folder in yandex_folders:
        if folder[0] != '/':
            local_path = os.path.join(parent_folder, folder)
        else:
            local_path = parent_folder + folder
        if not os.path.exists(local_path):
            os.makedirs(local_path)
            print(f'Создана папка: {local_path}')
        else:
            print(f'Папка уже существует: {local_path}')

# Удаление папок в локальном каталоге
def delete_local_folders(missing_folders, parent_folder=LOCAL_DIRECTORY):
    for folder in missing_folders:
        if folder[0] != '/':
            local_path = os.path.join(parent_folder, folder)
        else:
            local_path = parent_folder + folder
        if os.path.exists(local_path):
            shutil.rmtree(local_path) # удаляет рекурсивно вместе с начинкой
            print(f'Удалена папка: {local_path}')
        else:
            print(f'Папки не существует: {local_path}')

# Получение списка локальных директорий
def get_local_folders(directory):
    all_folders = []
    try:
        # Используем os.walk для рекурсивного обхода директории
        for root, dirs, files in os.walk(directory):
            for dir_name in dirs:
                # Формируем полный путь к папке и добавляем в список
                all_folders.append(os.path.join(root, dir_name))
    except Exception as e:
        print(f'Ошибка при получении папок: {e}')
    return all_folders

# Определяем папки, которые были удалены с яндекс диска. 
def compare_folders(local_folders, yandex_folders):
    for i in range(len(local_folders)):
        if LOCAL_DIRECTORY in local_folders[i]:
            local_folders[i] = local_folders[i].replace(LOCAL_DIRECTORY, '')
    missing_folders = [folder for folder in local_folders if folder not in yandex_folders]
    return missing_folders

def main():
    all_local_folders = get_local_folders(LOCAL_DIRECTORY)
    max_nesting_level = max_depth()
    try:
        yandex_folders.remove('/')
    except:
        print("Список корректен. Продолжаем...")
    print(f'Максимальная глубина вложенности папок: {max_nesting_level}')
    missing_folders = compare_folders(all_local_folders, yandex_folders)
    delete_local_folders(missing_folders)
    create_local_folders(yandex_folders)

if __name__ == '__main__':
    main()
