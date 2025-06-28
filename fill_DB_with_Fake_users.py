import os
import random
from faker import Faker
from database import Database  # Импортируй свою реализацию

import base64
from PIL import Image
from io import BytesIO


def compressPhotoToBase64(image_path: str, max_size: tuple = (512, 512), quality: int = 70) -> str:
    """
    Сжимает изображение и возвращает его в виде строки base64.

    :param image_path: путь к изображению
    :param max_size: максимальный размер (ширина, высота)
    :param quality: качество JPEG (1-95)
    :return: строка base64
    """
    # Открытие и сжатие
    img = Image.open(image_path)
    img.thumbnail(max_size)  # изменяет размер "по месту"

    buffer = BytesIO()
    img.convert("RGB").save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)

    # Кодирование в base64
    img_bytes = buffer.read()
    base64_str = base64.b64encode(img_bytes).decode("utf-8")

    return base64_str



fake = Faker("ru_RU")

# ✅ Список городов
cities = ["Самара", "Нижний Новгород", "Ростов-на-Дону", "Уфа", "Липецк"
]

# ✅ Список университетов
universities = [
    "МГТУ им. Н.Э. Баумана",
    "НИУ ВШЭ – Санкт-Петербург",
    "Новосибирский государственный технический университет",
    "СПбГЭТУ 'ЛЭТИ'",
    "Томский политехнический университет",
    "КФУ",
    "Липецкий государственный технический университет"
]

# ✅ Папка с фотографиями
photo_folder = "sample_photos"
photo_files = [f for f in os.listdir(photo_folder) if f.endswith(('.jpg', '.jpeg', '.png'))]

# ✅ Инициализация базы
db = Database()

for i in range(28

               ):
    user_id = 10_000_000 + i
    username = fake.first_name()
    sex = random.choice([0, 1])
    city = random.choice(cities)
    university = random.choice(universities)
    course = str(random.randint(1, 6))
    age = random.randint(18, 25)
    description = fake.sentence(nb_words=12)

    # ✅ Случайное фото
    photo_path = os.path.join(photo_folder, random.choice(photo_files))
    with open(photo_path, "rb") as f:
        photo_data = f.read()

    # ✅ Добавление пользователя в БД
    db.addUser(
        userId=user_id,
        username=username,
        sex=bool(sex),
        city=city,
        university=university,
        course=course,
        age=age,
        description=description,
        photo=photo_data
    )
