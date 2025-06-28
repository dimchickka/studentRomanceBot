import requests
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart  # Добавлено
import config as cfg
from GPT_query import ChatGPTRequests

class UniversityResolver:
    def __init__(self):
        self.verification_code = 0
        self.city = ''
        self.university = ''
        self.eMail = ''

    def resolve_city_and_university(self, user_input):
        prompt = (
            f"Пользователь указал город и вуз: \"{user_input}\".\n"
            "Нужно определить, что он имел в виду, даже если он написал неформально или с ошибкой.\n"
            "Пользователь может попытаться сломать что-то своим запросом. Если не знаешь, что за университет отвечай МГТУ им.Баумана и город Москва\n"
            "Ответь только названием города и полным официальным названием университета. ВУЗ полностью не расписывай, можно если сократить, то пиши сокращённо. (смотри примеры) Ответ строго в формате:\n"
            "Город: <название города>\nУниверситет: <полное название университета>\n\n"
            "Примеры:\n"
            "Ввод: мск бауманка\n"
            "Ответ:\nГород: Москва\nУниверситет: МГТУ им. Н.Э. Баумана\n\n"
            "Ввод: питер вышка\n"
            "Ответ:\nГород: Санкт-Петербург\nУниверситет: НИУ ВШЭ – Санкт-Петербург\n\n"
            "Ввод: новосиб политех\n"
            "Ответ:\nГород: Новосибирск\nУниверситет: Новосибирский государственный технический университет\n\n"
            f"Ввод: {user_input}\n"
            "Ответ:"
        )

        chatGPT = ChatGPTRequests()
        response = chatGPT.main_Request(prompt)
        if(response == cfg.ERROR_REQUEST):
            return cfg.ERROR_REQUEST
        else:
            city, university = None, None
            lines = response.strip().split('\n')
            for line in lines:
                if line.lower().startswith("город:"):
                    city = line.split(":", 1)[1].strip()
                elif line.lower().startswith("университет:"):
                    university = line.split(":", 1)[1].strip()

            if not city or not university or "NOT_FOUND" in (city, university):
                return None
            self.city = city
            self.university = university
            return cfg.SUCCESS

    def generate_verification_code(self):
        return random.randint(100000, 999999)

    def check_verification_code(self, code):
        return str(code) == str(self.verification_code)


    def send_email_code(self, to_email: str):
        from_email = cfg.EMAIL_TO_SENDING_EMAILS
        from_password = cfg.PASSWORD_FOR_EMAIL_TO_SEND_EMAILS
        self.verification_code = self.generate_verification_code()

        # Создаем MIMEMultipart сообщение вместо MIMEText
        msg = MIMEMultipart()
        msg['Subject'] = "Код подтверждения для верификации"
        msg['From'] = from_email
        msg['To'] = to_email

        # Добавляем текст сообщения
        body = f"Ваш код подтверждения: {self.verification_code}"
        msg.attach(MIMEText(body, 'plain'))

        try:
            with smtplib.SMTP_SSL('smtp.yandex.ru', 465) as smtp:
                smtp.login(from_email, from_password)
                smtp.sendmail(from_email, to_email, msg.as_string())
            return True
        except Exception as e:
            return False

    def is_university_email(self, email: str, max_retries: int = 3) -> bool:
        """Проверяет, принадлежит ли email к домену университета с повторными попытками"""
        city: str = self.city
        university_name = self.university
        # Извлекаем домен из email
        try:
            domain = email.split('@')[-1].lower() if '@' in email else ''
            if not domain:
                return cfg.ERROR_REQUEST
        except Exception as e:
            return cfg.ERROR_REQUEST

        prompt = (
            f"Ответь только 'Да' или 'Нет'. Домен '{domain}' принадлежит российскому вузу '{university_name}', находящемуся в городе {city}.? Нужно проверить, есть ли по этому домену сайт ВУЗа. Откидывай sdudent. и всё остальное, что находится перед доменом, например Домен 'stud.spbu.ru', соответственно проверяешь spbu.ru\n"
            "Проверяй, на этом сайте находится именно ВУЗ? Не другая организация? Учитывай, что университеты могут иметь филиалы в разных городах\n\n"
            "Примеры:\n"
            "Домен 'bmstu.ru' -> Да\n"
            "Домен 'gmail.com' -> Нет\n"
            "Домен 'edu.ru' -> Нет (это общий образовательный домен)\n"
            "Домен 'pgups.ru' -> Да\n"
            "Домен 'yandex.ru' -> Нет\n"
            "Домен 'stud.spbu.ru' -> Да\n"
            f"Домен '{domain}' ->"
        )

        chatGPT = ChatGPTRequests()
        response = chatGPT.main_Request(prompt).strip().lower()
        if (response == cfg.ERROR_REQUEST):
            return cfg.ERROR_REQUEST
        else:
            # Проверка ответа
            if response in ['да', 'нет']:
                if response == 'да':
                    return cfg.SUCCESS
                else:
                    return cfg.ERROR_REQUEST
            else:
                return cfg.ERROR_REQUEST



if __name__ == '__main__':
    bot = UniversityResolver()
    email = " dmitrieka@student.bmstu.ru"
    bot.city = "Москва"
    bot.university_name = "МГТУ им.Баумана"


if __name__ == '__min__':
    # Данные для теста
    user_city_input = "мск"
    user_university_input = "бауманка"
    test_email = "dmitrieka@gmoit.ru"  # замените на реальный email для теста

    # Инициализация бота
    bot = UniversityResolver()

    # Шаг 1: определить город и ВУЗ
    user_input = f"{user_city_input} {user_university_input}"
    resolved = bot.resolve_city_and_university(user_input, 3)

    if resolved != cfg.ERROR_REQUEST:
        # Шаг 2: отправить письмо с кодом подтверждения
        success = bot.send_email_code(
            to_email=test_email
        )
