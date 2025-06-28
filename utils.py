import config as cfg
from telebot import types  # Импорт для работы с клавиатурами
from io import BytesIO  # Для работы с бинарными данными в памяти
from PIL import Image  # Для обработки изображений (библиотека Pillow)
def readFile(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as file:
        return file.read()


def validate_institute_name(message_text: str) -> tuple[bool, str]:
    """
    Проверяет корректность названия института/факультета.
    Возвращает (is_valid, error_message)
    """
    text = message_text.strip()

    # Проверка длины
    if len(text) > 50:
        return False, "❌ Название слишком длинное (максимум 50 символов)"

    # Проверка на цифры
    if any(char.isdigit() for char in text):
        return False, "❌ Название не должно содержать цифры"

    # Проверка на ссылки (простейшая проверка)
    if "http://" in text.lower() or "https://" in text.lower() or ".ru" in text.lower():
        return False, "❌ Название не должно содержать ссылки"

    # Проверка на специальные символы (кроме разрешённых)
    allowed_symbols = set(" -.,()")  # Допустимые символы
    if any(char for char in text if not (char.isalpha() or char in allowed_symbols)):
        return False, "❌ Использованы запрещённые символы (допустимы только буквы, пробел, -.,())"

    # Проверка на повторяющиеся пробелы/дефисы
    if "  " in text or "--" in text:
        return False, "❌ Уберите повторяющиеся пробелы или дефисы"

    return True, ""


def validate_course_number(message_text: str, max_course: int = 6) -> tuple[bool, str]:
    """
    Проверяет корректность номера курса.
    Возвращает (is_valid, error_message)

    Параметры:
        message_text - текст от пользователя
        max_course - максимально допустимый номер курса (по умолчанию 6)
    """
    text = message_text.strip()

    # Проверка на пустоту
    if not text:
        return False, "❌ Пожалуйста, введите номер курса"

    # Проверка что это число
    if not text.isdigit():
        return False, "❌ Номер курса должен быть целым числом"

    course = int(text)

    # Проверка диапазона
    if course < 1:
        return False, "❌ Номер курса не может быть меньше 1"

    if course > max_course:
        return False, f"❌ В нашем вузе максимальный курс - {max_course}"

    return True, ""


def downloadAndCompressPhoto(bot, fileId, maxSize=1024, quality=80):
    """Скачивает и сжимает фото с учетом ограничений API"""
    try:
        # 1. Получаем информацию о файле
        fileInfo = bot.get_file(fileId)

        # 2. Скачиваем файл (новый способ для актуальных версий)
        downloadedFile = bot.download_file(fileInfo.file_path)

        # 3. Сжимаем в оперативной памяти
        with Image.open(BytesIO(downloadedFile)) as img:
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # Масштабирование
            width, height = img.size
            if max(width, height) > maxSize:
                scale = maxSize / max(width, height)
                newSize = (int(width * scale), int(height * scale))
                img = img.resize(newSize, Image.LANCZOS)

            # Сохранение сжатого изображения
            output = BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            return output.getvalue()

    except Exception as e:
        return None

def createReplyKeyboard(options, one_time=True, columns=2):
    """
    Создает клавиатуру с кнопками.

    :param options: список вариантов ответа (например ["Мужской", "Женский"])
    :param one_time: скрывать клавиатуру после выбора (по умолчанию True)
    :param columns: количество кнопок в строке (по умолчанию 2)
    :return: объект ReplyKeyboardMarkup
    """
    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=one_time
    )

    row = []
    for option in options:
        row.append(types.KeyboardButton(option))
        if len(row) == columns:
            keyboard.add(*row)
            row = []
    if row:  # Добавляем оставшиеся кнопки
        keyboard.add(*row)
    return keyboard

def createInlineKeyboard(options, callback_prefix="opt_"):
    """
    Создает инлайн-клавиатуру с кнопками в чате

    :param options: список вариантов ответа (например ["Мужской", "Женский"])
    :param callback_prefix: префикс для callback_data (по умолчанию "opt_")
    :return: объект InlineKeyboardMarkup
    """
    keyboard = types.InlineKeyboardMarkup()

    # Добавляем кнопки в два столбца (аналогично ReplyKeyboard)
    row = []
    for option in options:
        # Формируем уникальный callback_data (например "opt_Мужской")
        callback_data = f"{callback_prefix}{option}"
        row.append(types.InlineKeyboardButton(option, callback_data=callback_data))

        if len(row) == 2:  # По 2 кнопки в строке
            keyboard.add(*row)
            row = []

    if row:  # Добавляем оставшиеся кнопки
        keyboard.add(*row)

    return keyboard

def isValidCityName(city: str) -> bool:
    city = city.strip()

    return (
        3 <= len(city) <= 40 and
        all(c.isalpha() or c in " -ёЁ" for c in city) and
        city[0].isupper() and
        city[0].isalpha()
    )

def has_three_comma_separated_words(text: str) -> bool:
    words = [word.strip() for word in text.split(',')]
    return len(words) == 3 and all(words)