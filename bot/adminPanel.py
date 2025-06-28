import telebot
import config as cfg
from utils import *
from telebot import types  # Импорт для работы с клавиатурами
import threading
import time
import random
import string
import re
class AdminCatalog:
    def __init__(self, bot, dataBase, parent):
        self.bot = bot
        self.db = dataBase
        self.parent = parent  # Ссылка на TelegramBot
        self.temp_notification_data = {}  # временное хранилище
        self.audienceTextForNotification = {}
        self.listOfUsersForNotification = []

    def adminMenu(self):
        if (self.parent.tempDataIsUserInCallBack.get(cfg.admin, False)): return
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Открыть бота")
        markup.add("Закрыть бота")
        markup.add("Выложить уведомление")
        markup.add("Сгенерировать код для прохождения e-mail контроля")
        markup.add("Удалить пользователя из БД")
        markup.add("Перезапустить регистрацию для пользователя")
        markup.add("Создать новый токен для io.net")
        markup.add("В главное меню ⬅️")
        self.bot.send_message(
            chat_id=cfg.admin,
            text="Выбери, что хочешь сделать дальше:",
            reply_markup=markup
        )
        self.bot.register_next_step_handler_by_chat_id(cfg.admin, self.adminActions)

    def adminActions(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(cfg.admin, False)): return
        if message.content_type != "text":
            self.bot.send_message(message.chat.id, "Пожалуйста, пришли текстовое сообщение")
            return self.bot.register_next_step_handler(message, self.adminActions)
        text = message.text.strip().lower()

        if text == "открыть бота":
            if(self.parent.isOpenBot):
                self.bot.send_message(cfg.admin, "Бот уже открыт")
                return self.adminMenu()
            self.bot.send_message(cfg.admin, "Бот открыт")
            self.parent.isOpenBot = True
            self.temp_notification_data = {
                'text': "🚀Мы рады сообщить что, бот начал свою работу!🎉\nНапиши мне что-нибудь для начала диалога",
                'photo': None
            }
            self.collectUsers()

        elif text == "закрыть бота":
            if(not self.parent.isOpenBot):
                self.bot.send_message(cfg.admin, "Бот уже закрыт")
                return self.adminMenu()
            self.bot.send_message(cfg.admin, "Бот закрыт")
            self.parent.isOpenBot = False
            self.adminMenu()

        elif text == "выложить уведомление":
            # Заглушка для будущего уведомления
            self.bot.send_message(cfg.admin, "Введите текст уведомления:")
            self.bot.register_next_step_handler(message, self.handleNotification)

        elif text == "сгенерировать код для прохождения e-mail контроля":
            self.generateNewCodeForPassingEmailControl()
            self.adminMenu()

        elif text == "перезапустить регистрацию для пользователя":
            self.bot.send_message(cfg.admin, "Введите id пользователя")
            self.bot.register_next_step_handler(message, self.handleIdOfUserToResetRegistration)
        elif text == "удалить пользователя из бд":
            # Заглушка для удаления пользователя
            self.bot.send_message(cfg.admin, "Введите ID пользователя для удаления:")
            self.bot.register_next_step_handler(message, self.handleDeleteUser)

        elif text == "создать новый токен для io.net":
            # Заглушка для удаления пользователя
            self.bot.send_message(cfg.admin, "Пришли новый токен")
            self.bot.send_message(cfg.admin, "Получить его можно здесь: https://ai.io.net/ai/api-keys")
            self.bot.register_next_step_handler(message, self.handleNewToken)

        elif message.text == "В главное меню ⬅️":
            if(self.parent.isOpenBot):
                self.parent.showMainMenu(message)
            else:
                self.bot.send_message(cfg.admin, "Бот закрыт. Доступно только меню админа")
                self.adminMenu()

        else:
            self.bot.send_message(cfg.admin, "Неверная команда. Пожалуйста, выберите из меню.")
            self.adminMenu()

    def handleIdOfUserToResetRegistration(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(cfg.admin, False)): return
        if message.content_type != "text":
            self.bot.send_message(message.chat.id, "Пожалуйста, пришли текстовое сообщение")
            return self.bot.register_next_step_handler(message, self.handleIdOfUserToResetRegistration)
        if not message.text or not isinstance(message.text, str):
            self.bot.send_message(message.chat.id, "Пожалуйста, введи корректный Id.")
            return self.bot.register_next_step_handler(message, self.handleAge)

        text = message.text.strip()
        if not re.fullmatch(r'\d+', text):
            self.bot.send_message(message.chat.id, "Возраст должен быть числом.")
            return self.bot.register_next_step_handler(message, self.handleAge)

        if(self.parent.registration.resetUserById(int(text))):
            self.bot.send_message(message.chat.id, "Данные успешно очищены")
        else:
            self.bot.send_message(message.chat.id, "Пользователь не найден в tempData")
        self.adminMenu()

    def handleNewToken(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(cfg.admin, False)): return
        if message.content_type != "text":
            self.bot.send_message(message.chat.id, "Пожалуйста, пришли текстовое сообщение")
            return self.bot.register_next_step_handler(message, self.handleNewToken)
        new_token = message.text.strip()
        cfg.update_openrouter_key(new_token)
        self.bot.send_message(message.chat.id, "✅ Новый токен сохранён и будет использоваться.")
        self.adminMenu()

    def generateNewCodeForPassingEmailControl(self):
        if (self.parent.tempDataIsUserInCallBack.get(cfg.admin, False)): return
        self.bot.send_message(cfg.admin, "Генерация кода...")

        chars = string.ascii_letters + string.digits
        self.parent.codeForPassingEmailControl = ''.join(random.choice(chars) for _ in range(10))
        self.bot.send_message(cfg.admin, self.parent.codeForPassingEmailControl)
    def handleDeleteUser(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(cfg.admin, False)): return
        if message.content_type != "text":
            self.bot.send_message(message.chat.id, "Пожалуйста, пришли текстовое сообщение")
            return self.bot.register_next_step_handler(message, self.handleDeleteUser)
        if message.text.isdigit():
            if self.db.deleteUserById(int(message.text)):
                self.parent.tempDataIsUserInCallBack.pop(message.chat.id, None)
                self.bot.send_message(cfg.admin, f"Пользователь {message.text} удалён из БД")
            else:
                self.bot.send_message(cfg.admin, f"Ошибка удаления пользователя {message.text}")
            if(self.db.deleteUserById(cfg.admin)):
                self.adminMenu()
        else:
            self.bot.send_message(cfg.admin, f"Сообщение должно содержать только цифры. Возврат в меню")
            self.adminMenu()

    def handleNotification(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(cfg.admin, False)): return
        # Сохраняем текст и фото (если есть)

        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id  # самое большое изображение
            self.temp_notification_data['photo'] = file_id
            self.temp_notification_data['text'] = message.caption or ""
        elif message.content_type == 'text':
            self.temp_notification_data['text'] = message.text
            self.temp_notification_data['photo'] = None
        else:
            self.bot.send_message(cfg.admin, "Пожалуйста, отправьте текст или фото с подписью.")
            return self.bot.register_next_step_handler(message, self.handleNotification)

        # Запрашиваем аудиторию
        self.bot.send_message(
            cfg.admin,
            "Для какой аудитории отправить уведомление?\nФормат: Город:Липецк, ВУЗ:None"
        )
        self.bot.register_next_step_handler(message, self.handleNotificationAudience)

    def handleNotificationAudience(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(cfg.admin, False)): return
        if message.content_type != "text":
            self.bot.send_message(message.chat.id, "Пожалуйста, пришли текстовое сообщение")
            return self.bot.register_next_step_handler(message, self.handleNotificationAudience)
        audience_text = message.text.strip()

        # Преобразуем строку в словарь
        try:
            for item in audience_text.split(","):
                key, value = item.split(":")
                self.audienceTextForNotification[key.strip()] = value.strip() if value.strip().lower() != "none" else None
        except ValueError:
            self.bot.send_message(cfg.admin, "Неверный формат. Пример: Город:Липецк, ВУЗ:None")
            self.bot.register_next_step_handler(message, self.handleNotificationAudience)
            return

        else:
            if self.temp_notification_data.get('photo'):
                self.bot.send_photo(
                    cfg.admin,
                    self.temp_notification_data['photo'],
                    caption=self.temp_notification_data['text'],
                    reply_markup=createReplyKeyboard(["Да, всё верно", "В главное меню ⬅️"])
                )
            else:
                self.bot.send_message(
                    cfg.admin,
                    f"Уведомление будет отправлено аудитории:\n{self.audienceTextForNotification}\nТекст: {self.temp_notification_data['text']}",
                    reply_markup=createReplyKeyboard(["Да, всё верно", "В главное меню ⬅️"])
                )

            self.bot.register_next_step_handler(message, self.checkIsAudienceForNotificationCorrect)

    def checkIsAudienceForNotificationCorrect(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(cfg.admin, False)): return
        if message.content_type != "text":
            self.bot.send_message(message.chat.id, "Пожалуйста, пришли текстовое сообщение")
            return self.bot.register_next_step_handler(message, self.checkIsAudienceForNotificationCorrect)
        options = [
            "Да, всё верно",
            "В главное меню ⬅️",
        ]

        if message.text not in options:
            self.bot.send_message(
                cfg.admin
                ,
                "Я тебя не понимаю, пожалуйста, выбери вариант с помощью кнопок"
            )
            self.bot.register_next_step_handler(message, self.checkIsAudienceForNotificationCorrect)
            return

        if (self.parent.profileView.comeBackToTheMainMenu(message)):return

        else:
            self.collectUsers()
    def collectUsers(self):
        # все значения None
        if all(v is None for v in self.audienceTextForNotification.values()):
            self.listOfUsersForNotification = self.db.getAllUserIds()
        # ВУЗ не указан
        elif not (self.audienceTextForNotification.get('Город') is None):
            self.listOfUsersForNotification = self.db.getMatchingUsers(city=self.audienceTextForNotification.get('Город'))
        # Город не указан
        else:
            self.listOfUsersForNotification = self.db.getMatchingUsers(city=self.audienceTextForNotification.get('ВУЗ'))
        self.sendNotificationThread()

        self.bot.send_message(
            cfg.admin,
            "✅Рассылка началась!"
        )

    def sendNotificationThread(self):
        if (self.parent.tempDataIsUserInCallBack.get(cfg.admin, False)): return
        def worker():
            for user_id in self.listOfUsersForNotification[:]:  # копия списка для безопасного удаления
                try:
                    if self.temp_notification_data.get('photo'):
                        self.bot.send_photo(
                            chat_id=user_id,
                            photo=self.temp_notification_data['photo'],
                            caption=self.temp_notification_data.get('text', '')
                        )
                    else:
                        self.bot.send_message(
                            chat_id=user_id,
                            text=self.temp_notification_data.get('text', '')
                        )
                except Exception:
                    self.db.deleteUserById(user_id)  # удаляем пользователя из БД
                time.sleep(0.5)
            self.finishedNotifyUsers()

        threading.Thread(target=worker).start()

    def finishedNotifyUsers(self):
        if (self.parent.tempDataIsUserInCallBack.get(cfg.admin, False)): return
        self.bot.send_message(
            cfg.admin,
            "✅Рассылка успешно завершена!"
        )
        self.audienceTextForNotification.clear()
        self.adminMenu()