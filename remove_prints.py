import os
import re

EXCLUDED_DIRS = {'.venv', 'venv', '__pycache__'}  # можно добавить свои

def remove_prints_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    with open(file_path, 'w', encoding='utf-8') as file:
        for line in lines:
            # Удаляем строки, где только print(...)
            if not re.match(r'^\s*print\(.*?\)\s*$', line):
                file.write(line)

def process_directory(path):
    for root, dirs, files in os.walk(path):
        # Удаляем из обхода все папки, которые нужно исключить
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        for file_name in files:
            if file_name.endswith('.py'):
                full_path = os.path.join(root, file_name)
                remove_prints_from_file(full_path)

# === ЗАПУСК ===
process_directory(".")
