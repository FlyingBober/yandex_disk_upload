
import time
import os
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import upload_to_yadisk
import sync_of_dir

# Настройки
home_dir = os.environ.get('HOME')
with open('data/config.json', 'r') as f:
    settings = json.load(f)    
TOKEN = settings['token']
LOCAL_DIRECTORY = home_dir + "/" + settings['directory']

# Обработчик событий
class NewFileHandler(FileSystemEventHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processed_files = set()  # Хранит уже обработанные файлы
  
    def on_created(self, event):
        print("event: ",event)
        if not event.is_directory:  # Проверяем, что это не директория
            file_path = event.src_path
            if file_path not in self.processed_files:
                self.processed_files.add(file_path)
                # Запускаем обработку файла в отдельном потоке               
                print("self.processed_files: ",self.processed_files)
                folder_in_ydisk = file_path.replace(LOCAL_DIRECTORY, '')
                folder_in_ydisk = folder_in_ydisk.replace(os.path.basename(folder_in_ydisk), '')
                if folder_in_ydisk.endswith('/'):
                    folder_in_ydisk = folder_in_ydisk[:-1]
                print("folder_in_ydisk: ",folder_in_ydisk)
                threading.Thread(target=upload_to_yadisk.upload, args=(file_path, folder_in_ydisk)).start()

def main(directory_to_watch = LOCAL_DIRECTORY):
    event_handler = NewFileHandler()
    observer = Observer()
    observer.schedule(event_handler, directory_to_watch, recursive=True)
    observer.start()
    print(f'Начато отслеживание каталога: {directory_to_watch}')

    try:
        while True:
            print("Синхронизация каталогов...")
            sync_of_dir.main()
            print("Синхронизация каталогов завершена.")
            time.sleep(60)  # Основной поток просто ждет
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == '__main__':
    main()