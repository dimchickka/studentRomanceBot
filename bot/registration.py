#Нужно разделить всю логику на отдельные файлы: файл регистрация, просмотр анкет и другие манипуляции из меню
from utils import *
from telebot import types  # Импорт для работы с клавиатурами
import config as cfg

from validation import UniversityResolver
#библиотеки для обработки описания
from better_profanity import profanity
import re
#соединяться с БД нужно непосредственно здесь, а не в том классе!

class Registration:
    def __init__(self, bot, dataBase, parent):
        self.bot = bot
        self.db = dataBase
        self.tempData = {}  # Хранит данные вида {chatId: { name: str, sex: bool, age: int, description: str}}
        self.parent = parent  # Ссылка на TelegramBot

    def register_handlers(self):
        """Регистрация обработчиков команд."""  #далее bot.polling сам опрашивает чат на наличие сообщений. Мы только регистрируем здесь
        # Регистрируем обработчик с привязкой self
        self.bot.callback_query_handler(
            func=lambda call: call.data.startswith("course_")
        )(lambda call: self.handle_inline_buttons_for_course(call))


        @self.bot.message_handler(func=lambda message: True)  # Ловит все сообщения
        def handle_all_messages(message):
            if (message.chat.id in self.parent.tempDataIsUserInCallBack):
                return
            # Проверяем наличие пользователя в словаре
            elif message.chat.id not in self.parent.tempDataIsUserInCallBack:
                # Если пользователя нет - добавляем с флагом False
                self.parent.tempDataIsUserInCallBack[message.chat.id] = False

            if self.db.getUserById(message.chat.id):
                if (self.parent.isOpenBot):
                    self.parent.showMainMenu(message)
                elif (message.chat.id == cfg.admin):
                    self.parent.adminCatalog.adminMenu()
                elif (not self.parent.isOpenBot):
                    self.bot.send_message(
                        message.chat.id,
                        "До 10 июля функционал ограничен",
                        reply_markup=createReplyKeyboard(["Смотреть мою анкету", "Заполнить анкету заново"])
                    )
                    self.bot.register_next_step_handler(message, self.handleMenuUntilStart)
            else:
                self._handleStart(message)

    def _handleStart(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        self.tempData[message.chat.id] = {}  # Создаем новую запись
        """Обработка первого сообщения от пользователя."""
        welcomeText = readFile(cfg.WELCOME_TEXT_PATH)
        self.bot.send_message(message.chat.id, welcomeText)
        self.bot.register_next_step_handler(message, self.handleName)


    def handleName(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        if message.content_type != "text":
            self.bot.send_message(message.chat.id, "Пожалуйста, пришли текстовое сообщение")
            return self.bot.register_next_step_handler(message, self.handleName)
        if (message.chat.id not in self.tempData): return self._handleStart(message)
        """Обработка имени"""

        if not message.text or not isinstance(message.text, str):
            self.bot.send_message(message.chat.id, "Имя не может быть пустым. Попробуйте ещё раз)")
            return self.bot.register_next_step_handler(message, self.handleName)

        name = message.text.strip()

        # Проверка: имя только из букв (русские и латинские)
        if not re.match(r'^[A-Za-zА-Яа-яЁё]+$', name):
            self.bot.send_message(message.chat.id, "Имя должно содержать только буквы, без смайликов и символов. Попробуйте ещё раз)")
            return self.bot.register_next_step_handler(message, self.handleName)

        self.tempData[message.chat.id]['name'] = name
        self.askSex(message)

    def askSex(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        if (message.chat.id not in self.tempData): return self._handleStart(message)
        """запрос пола"""
        self.bot.send_message(
            message.chat.id,
            "Выбери свой пол:",
            reply_markup=createReplyKeyboard(["Мужской", "Женский"])
        )
        self.bot.register_next_step_handler(message, self.handleSex)


    def handleSex(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        if (message.chat.id not in self.tempData): return self._handleStart(message)
        if message.content_type != "text":
            self.bot.send_message(message.chat.id, "Пожалуйста, пришли текстовое сообщение")
            return self.bot.register_next_step_handler(message, self.handleSex)
        """Обработка пола"""
        if message.text not in ["Мужской", "Женский"]:
            self.bot.send_message(message.chat.id, "Пожалуйста, выбери пол с помощью кнопок!")
            return self.askSex(message)
        self.tempData[message.chat.id]['gender'] = cfg.MALE if message.text == "Мужской" else cfg.FEMALE
        # Удаляем клавиатуру
        self.bot.send_message(
            chat_id=message.chat.id,
            text="Сколько тебе лет?",
            reply_markup=types.ReplyKeyboardRemove()  # Полное удаление
        )
        self.askAge(message)


    def askAge(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        if (message.chat.id not in self.tempData): return self._handleStart(message)
        """запрос возраста"""
        self.bot.register_next_step_handler(message, self.handleAge)


    def handleAge(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        if (message.chat.id not in self.tempData): return self._handleStart(message)
        if message.content_type != "text":
            self.bot.send_message(message.chat.id, "Пожалуйста, пришли текстовое сообщение")
            return self.bot.register_next_step_handler(message, self.handleAge)
        if not message.text or not isinstance(message.text, str):
            self.bot.send_message(message.chat.id, "Пожалуйста, введи корректный возраст (целое число).")
            return self.bot.register_next_step_handler(message, self.handleAge)

        text = message.text.strip()
        if not re.fullmatch(r'\d+', text):
            self.bot.send_message(message.chat.id, "Возраст должен быть числом.")
            return self.bot.register_next_step_handler(message, self.handleAge)

        age = int(text)

        if age < 15:
            self.bot.send_message(
                message.chat.id,
                "Похоже, ты ещё слишком молод(а) для этого бота 😊\n"
                "Минимальный возраст регистрации — 16 лет.\nЕсли ты случайно ошибся(лась), то напиши корректный возраст. Если нет, то придётся подождать)"
            )
            self.bot.register_next_step_handler(message, self.handleAge)
            return cfg.SUCCESS

        elif age > 40:
            self.bot.send_message(
                message.chat.id,
                "Вы — живое доказательство, что учиться никогда не поздно! Так держать! 😄\n"
                "Надеюсь, ты не против, что средний возраст в этом боте 21 год?",
                reply_markup=createReplyKeyboard(["Продолжить"])
            )
            self.tempData[message.chat.id]['age'] = int(age)

            # Ждём подтверждения от пользователя
            def confirmContinue(m):
                if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
                if (message.chat.id not in self.tempData): return self._handleStart(message)
                # Удаляем клавиатуру
                self.bot.send_message(
                    chat_id=message.chat.id,
                    text="Хорошо, продолжаем дальше 👇 Придумай описание для своей анкеты😊",
                    reply_markup=types.ReplyKeyboardRemove()  # Полное удаление
                )
                self.bot.register_next_step_handler(message, self.handleDescription)

            confirmContinue(message)
        else:
            # Возраст в норме — сохраняем и продолжаем
            self.tempData[message.chat.id]['age'] = int(message.text)
            self.bot.send_message(
                message.chat.id,
                "Придумай описание для своей анкеты😊\n"
            )
            self.bot.register_next_step_handler(message, self.handleDescription)


    def handleDescription(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        if (message.chat.id not in self.tempData): return self._handleStart(message)
        if message.content_type != "text":
            self.bot.send_message(message.chat.id, "Пожалуйста, пришли текстовое сообщение")
            return self.bot.register_next_step_handler(message, self.handleDescription)
        if not message.text or not isinstance(message.text, str):
            self.bot.send_message(message.chat.id, "Пожалуйста, введите корректное описание")
            return self.bot.register_next_step_handler(message, self.handleDescription)

        description = message.text.strip()

        if not description:
            self.bot.send_message(message.chat.id, "Описание не может быть пустым.")
            return self.bot.register_next_step_handler(message, self.handleDescription)

        if len(description) < 10:
            self.bot.send_message(message.chat.id, "Описание слишком короткое. Расскажи чуть больше.")
            return self.bot.register_next_step_handler(message, self.handleDescription)

        if len(description) > 300:
            self.bot.send_message(message.chat.id, "Слишком длинное описание. Уложись в 300 символов.")
            return self.bot.register_next_step_handler(message, self.handleDescription)

        if re.search(r'https?://|www\.', description, re.IGNORECASE):
            self.bot.send_message(message.chat.id, "В описании нельзя указывать ссылки.")
            return self.bot.register_next_step_handler(message, self.handleDescription)

        if profanity.contains_profanity(message.text):
            self.bot.send_message(message.chat.id, "Пожалуйста, не используй ненормативную лексику.")
            return self.bot.register_next_step_handler(message, self.handleDescription)

        # Сохраняем описание
        self.tempData[message.chat.id]['description'] = description
        # запрос города обучения и университета
        self.askCityAndUniversity(message)


    def askCityAndUniversity(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        if (message.chat.id not in self.tempData): return self._handleStart(message)
        """Запрос города обучения с обработкой неформальных названий"""
        self.bot.send_message(
            message.chat.id,
            "В каком ВУЗе ты учишься? Напиши город и универ в формате: Москва, МГТУ им. Баумана"
        )
        self.bot.register_next_step_handler(message, self.validationCityAndUniversity)


    def validationCityAndUniversity(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        if (message.chat.id not in self.tempData): return self._handleStart(message)
        if message.content_type != "text":
            self.bot.send_message(message.chat.id, "Пожалуйста, пришли текстовое сообщение")
            return self.bot.register_next_step_handler(message, self.validationCityAndUniversity)
        if not message.text or not isinstance(message.text, str):
            self.bot.send_message(
                message.chat.id,
                "Не удалось распознать город. Пожалуйста, попробуй ещё раз в формате: Москва, МГТУ им.Баумана:"
            )
            self.bot.register_next_step_handler(message, self.validationCityAndUniversity)
        """Валидация города с использованием UniversityResolver"""
        self.tempData[message.chat.id]['resolver'] = UniversityResolver()

        result = self.tempData[message.chat.id]['resolver'].resolve_city_and_university(message.text)

        if result == cfg.ERROR_REQUEST:
            self.bot.send_message(
                message.chat.id,
                "Не удалось распознать город. Пожалуйста, попробуй ещё раз в формате: Москва, МГТУ им.Баумана:"
            )
            self.bot.register_next_step_handler(message, self.validationCityAndUniversity)
        else:

            """запрос подтверждения"""
            confirmation_text = (
                f"Я правильно понял?\n"
                f"🏙 Город: {self.tempData[message.chat.id]['resolver'].city}\n"
                f"🎓 Университет: {self.tempData[message.chat.id]['resolver'].university}\n\n"
                f"Если всё верно - нажми 'Да', если нет - 'Нет'"
            )

            self.bot.send_message(
                message.chat.id,
                confirmation_text,
                reply_markup=createReplyKeyboard(["Да", "Нет"])
            )
            self.bot.register_next_step_handler(message, self.handleUniversity)


    def handleUniversity(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        if (message.chat.id not in self.tempData): return self._handleStart(message)
        if message.content_type != "text":
            self.bot.send_message(message.chat.id, "Пожалуйста, пришли текстовое сообщение")
            return self.bot.register_next_step_handler(message, self.handleUniversity)
        """Обработка универа"""
        if message.text not in ["Да", "Нет"]:
            self.bot.send_message(message.chat.id, "Пожалуйста, введите ответ с помощью кнопок!")
            self.bot.register_next_step_handler(message, self.handleUniversity)
            return cfg.SUCCESS
        else:
            if message.text == "Да":
                self.tempData[message.chat.id]['city'] = self.tempData[message.chat.id]['resolver'].city
                self.tempData[message.chat.id]['university'] = self.tempData[message.chat.id]['resolver'].university
                # Создаем клавиатуру
                course_keyboard = createInlineKeyboard(["1", "2", "3", "4", "5", "6", "Магистратура", "Аспирантура"],
                                                       "course_")

                # Отправляем сообщение с клавиатурой
                self.bot.send_message(
                    chat_id=message.chat.id,
                    text="На каком ты курсе?",
                    reply_markup=course_keyboard
                )
                return cfg.SUCCESS
            else:
                self.bot.send_message(
                    message.chat.id,
                    "Хм... Странно. Пожалуйста, попробуй ещё раз в формате: Москва, МГТУ. им Баумана:"
                )
                self.bot.register_next_step_handler(message, self.validationCityAndUniversity)
                return cfg.SUCCESS

    def confirmEMAILExicting(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        if (message.chat.id not in self.tempData): return self._handleStart(message)
        if message.content_type != "text":
            self.bot.send_message(message.chat.id, "Пожалуйста, пришли текстовое сообщение")
            return self.bot.register_next_step_handler(message, self.confirmEMAILExicting)
        """Обработка ответа на вопрос: Действительно ли существует почта?"""
        if message.text == self.parent.codeForPassingEmailControl:
            self.bot.send_message(message.chat.id, "Принято, разрешаю тебе не вводить почту!")
            if(message.chat.id != cfg.admin): self.parent.adminCatalog.generateNewCodeForPassingEmailControl()
            self.askPhoto(message)
            return cfg.SUCCESS
        if message.text not in ["Да", "Нет"]:
            self.bot.send_message(message.chat.id, "Пожалуйста, введите ответ с помощью кнопок!")
            self.bot.register_next_step_handler(message, self.confirmEMAILExicting)
            return cfg.SUCCESS
        else:
            if message.text == "Да":
                # Удаляем клавиатуру
                self.bot.send_message(
                    chat_id=message.chat.id,
                    text="Вводи её сюда. На неё придёт подтверждающий код",
                    reply_markup=types.ReplyKeyboardRemove()  # Полное удаление
                )
                self.bot.register_next_step_handler(message, self.validationEmail)
                return cfg.SUCCESS
            else:
                self.bot.send_message(
                    message.chat.id,
                    f"Нам очень жаль, но на данный момент отсутсвует иное подтверждение того, что ты являешься студентом. Если ты очень хочешь зарегистрироваться здесь напиши {cfg.SUPPORT}, мы тебе поможем"
                )

                self.bot.send_message(
                    message.chat.id,
                    f"Если ты ошибся, и случайно нажал нет, то вводи почту:"
                )
                self.bot.register_next_step_handler(message, self.validationEmail)
                return cfg.SUCCESS
    def validationEmail(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        if (message.chat.id not in self.tempData): return self._handleStart(message)
        if message.content_type != "text":
            self.bot.send_message(message.chat.id, "Пожалуйста, пришли текстовое сообщение")
            return self.bot.register_next_step_handler(message, self.validationEmail)
        resolver = self.tempData[message.chat.id]['resolver']
        result = resolver.is_university_email(message.text)

        if result != cfg.ERROR_REQUEST:
            resolver.send_email_code(message.text)
            self.bot.send_message(message.chat.id, "На данную почту мы отправили код подтверждения. Вводи его сюда")
            self.bot.register_next_step_handler(message, self.check_validation_code)

        else:
            self.bot.send_message(message.chat.id,
                                  f"Извини, но нужно отправить обязательно корпоративную почту. Например: ya_sudent@student.bmstu.ru\nДавай попробуем ещё раз\nP.S. Если вдруг всё правильно, то напиши об этом {cfg.SUPPORT} мы исправим проблему")
            self.bot.register_next_step_handler(message, self.validationEmail)


    def check_validation_code(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        if (message.chat.id not in self.tempData): return self._handleStart(message)
        if message.content_type != "text":
            self.bot.send_message(message.chat.id, "Пожалуйста, пришли текстовое сообщение")
            return self.bot.register_next_step_handler(message, self.check_validation_code)
        """Проверка кода подтверждения"""
        result = self.tempData[message.chat.id]['resolver'].check_verification_code(message.text)
        if (result):
            self.askPhoto(message)
        else:
            if 'quantity_code_email' not in self.tempData[message.chat.id]:
                self.bot.send_message(
                    message.chat.id,
                    "Код подтверждения неверный\nПопробуй ввести ещё раз"
                )
                self.tempData[message.chat.id]['quantity_code_email'] = 1
                self.bot.register_next_step_handler(message, self.check_validation_code)
            elif (self.tempData[message.chat.id].get('quantity_code_email', 0) > 4):
                self.bot.send_message(
                    message.chat.id,
                    f"Код подтверждения неверный\nТы либо балуешься, либо действительно какие-то проблемы\nЕсли второе, то напиши в поддержку: {cfg.SUPPORT}"
                )
            else:
                self.bot.send_message(
                    message.chat.id,
                    "Код подтверждения неверный\nДавай я отправлю код ещё раз",
                    reply_markup=createReplyKeyboard(["Да, давай", "Ввести заново почту"])
                )
                self.tempData[message.chat.id]['quantity_code_email'] += 1
                self.bot.register_next_step_handler(message, self.checkAnswerToSendCodeOneMoreTime)


    def checkAnswerToSendCodeOneMoreTime(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        if (message.chat.id not in self.tempData): return self._handleStart(message)
        if message.content_type != "text":
            self.bot.send_message(message.chat.id, "Пожалуйста, пришли текстовое сообщение")
            return self.bot.register_next_step_handler(message, self.checkAnswerToSendCodeOneMoreTime)
        if (message.text == "Да, давай"):
            self.bot.send_message(message.chat.id, "Код подтверждения отправлен, вводи его сюда! В этот раз не ошибайся)")
            self.bot.register_next_step_handler(message, self.check_validation_code)
        elif (message.text == "Ввести заново почту"):
            self.bot.send_message(message.chat.id, "Введи сюда свою корпоративную почту. В этот раз не ошибайся)")
            self.bot.register_next_step_handler(message, self.validationEmail)
        else:
            self.bot.send_message(message.chat.id,
                                  "Извини, я тебя не понимаю. Скажи: \"Да, давай\" и я пришлю тебе код повторно!")
            self.bot.register_next_step_handler(message, self.checkAnswerToSendCodeOneMoreTime)


    def askPhoto(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        if (message.chat.id not in self.tempData): return self._handleStart(message)
        """запрос фото"""
        self.bot.send_message(message.chat.id, "Пришли свое фото для анкеты:")
        self.bot.register_next_step_handler(message, self.handlePhoto)  # Изменили на handlePhoto


    def handlePhoto(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        if (message.chat.id not in self.tempData): return self._handleStart(message)
        if message.content_type != "photo":
            self.bot.send_message(message.chat.id, "Пожалуйста, пришли фото")
            return self.bot.register_next_step_handler(message, self.handlePhoto)
        """Обработка полученного фото"""
        if message.content_type != 'photo':
            self.bot.send_message(message.chat.id, "Пожалуйста, пришлите фото!")
            return self.bot.register_next_step_handler(message, self.handlePhoto)

        try:
            photo = message.photo[-2]  # Среднее качество
            compressedPhoto = downloadAndCompressPhoto(self.bot, photo.file_id)

            if not compressedPhoto:
                raise ValueError("Не удалось обработать фото")

            self.tempData[message.chat.id]['photo'] = compressedPhoto

            self.finishRegistration(message)

        except Exception as e:
            self.bot.send_message(message.chat.id, "❌ Ошибка обработки фото. Попробуй прислать другое) ")
            self.bot.register_next_step_handler(message, self.handlePhoto)


    def finishRegistration(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        if (message.chat.id not in self.tempData): return self._handleStart(message)
        """Завершение регистрации с подтверждением данных"""
        user_data = self.tempData.get(message.chat.id, {})
        course = user_data.get('course')
        # Формируем сообщение с данными пользователя
        confirmation_message = (
            "📋 Проверьте ваши данные:\n\n"
            f"Имя: {user_data.get('name', 'не указано')}\n"
            f"Пол: {'мужской' if user_data.get('gender') == 1 else 'женский' if user_data.get('gender') == 0 else 'не указан'}\n"
            f"Город: {user_data.get('city', 'не указано')}\n"
            f"ВУЗ: {user_data.get('university')}, "
            f"{f'{course} курс' if course not in ['Аспирантура', 'Магистратура'] else course}\n"
            f"Возраст: {user_data.get('age', 'не указан')}\n"
            f"Описание: {user_data.get('description')}\n"
            "Всё верно? Отправьте 'Да' для подтверждения или 'Заполнить анкету заново' для изменения данных."
        )

        # Отправляем фото с текстом (caption)
        self.bot.send_photo(
            chat_id=message.chat.id,
            photo=user_data.get('photo'),  # Бинарные данные фото
            caption=confirmation_message,  # Текст описания
            reply_markup=createReplyKeyboard(['Да', 'Заполнить анкету заново'])
        )
        self.bot.register_next_step_handler(message, self.checkCorrectionData)


    def checkCorrectionData(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        if (message.chat.id not in self.tempData): return self._handleStart(message)
        if message.content_type != "text":
            self.bot.send_message(message.chat.id, "Пожалуйста, пришли текстовое сообщение")
            return self.bot.register_next_step_handler(message, self.checkCorrectionData)
        if message.text not in ["Да", "Заполнить анкету заново"]:
            self.bot.send_message(message.chat.id, "Я вас не понимаю. Пожалуйста, введите ответ с помощью кнопок!")
            self.bot.register_next_step_handler(message, self.checkCorrectionData)

        elif message.text == "Да":
            if(not self.db.getUserById(message.chat.id)):
                user_data = self.tempData.get(message.chat.id, {})
                self.db.addUser(
                    userId=message.chat.id,
                    username=user_data.get('name'),
                    sex=user_data.get('gender'),
                    city=user_data.get('city'),
                    university=user_data.get('university'),
                    course=user_data.get('course'),
                    age=user_data.get('age'),
                    description=user_data.get('description'),
                    photo=user_data.get('photo')  # Передаем бинарные данные
                )
            # Удаляем клавиатуру
            self.bot.send_message(
                chat_id=message.chat.id,
                text="✅ Регистрация завершена!",
                reply_markup=types.ReplyKeyboardRemove()  # Полное удаление
            )
            if(self.parent.isOpenBot):
                self.parent.showMainMenu(message)
            else:
                if (message.chat.id == cfg.admin):
                    self.parent.adminCatalog.adminMenu()
                else:
                    self.bot.send_message(message.chat.id,"Бот начнёт функционировать с 10 июля, мы тебя обязательно уведомим", reply_markup = createReplyKeyboard(["Смотреть мою анкету", "Заполнить анкету заново"]))

                    with open(cfg.RAFFLE_TEXT_PATH, "r", encoding="utf-8") as f:
                        raffle_text = f.read()

                    # Открываем и отправляем фото
                    with open(cfg.RAFFLE_PHOTO_PATH, "rb") as photo:
                        self.bot.send_photo(message.chat.id, photo, caption=raffle_text)
                    self.bot.register_next_step_handler(message, self.handleMenuUntilStart)

        else:
            if (self.db.getUserById(message.chat.id)):
                self.db.deleteUserById(message.chat.id)
            self.bot.send_message(message.chat.id, "С хорошим человеком можно и 2 раза познакомиться! Как тебя зовут?")
            self.bot.register_next_step_handler(message, self.handleName)
        self.tempData.pop(message.chat.id, None)

    def handle_inline_buttons_for_course(self, call):
        if (self.parent.tempDataIsUserInCallBack.get(call.message.chat.id, False)): return
        if (call.message.chat.id not in self.tempData): return self._handleStart(call.message)
        if(self.tempData.get(call.message.chat.id, {})):
            # Проверяем, делал ли пользователь уже выбор
            if 'course' in self.tempData.get(call.message.chat.id, {}):
                return
            selected_option = call.data.replace("course_", "")  # Извлекаем текст кнопки
            chat_id = call.message.chat.id

            # Сохраняем выбор
            self.tempData[chat_id]['course'] = selected_option

            self.bot.send_message(
                chat_id,
                "Есть ли у тебя в ВУЗе корпоративная почта студента?",
                reply_markup=createReplyKeyboard(["Да", "Нет"])
            )
            self.bot.register_next_step_handler(call.message, self.confirmEMAILExicting)
        else:
            return

    def handleMenuUntilStart(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        if message.content_type != "text":
            self.bot.send_message(message.chat.id, "Пожалуйста, пришли текстовое сообщение")
            return self.bot.register_next_step_handler(message, self.handleMenuUntilStart)
        if(not self.parent.isOpenBot):
            if (message.text == "Смотреть мою анкету"):
                self.checkMyProfile(message)
            elif(message.text == "Заполнить анкету заново"):
                self.bot.send_message(message.chat.id, "С хорошим человеком можно и 2 раза познакомиться! Как тебя зовут?")
                self.db.deleteUserById(message.chat.id)
                self.tempData[message.chat.id] = {}  # Создаем новую запись
                self.bot.register_next_step_handler(message, self.handleName)
            else:
                self.bot.send_message(message.chat.id, "Я вас не понимаю. Пожалуйста, введите ответ с помощью кнопок!")
                self.bot.send_message(
                    message.chat.id,
                    "Бот начнёт функционировать с 10 июля. Пока ты можешь только изменить данные своей анкеты",
                    reply_markup=createReplyKeyboard(["Смотреть мою анкету", "Заполнить анкету заново"])
                )
                self.bot.register_next_step_handler(message, self.handleMenuUntilStart)
        else:
            self.parent.showMainMenu(message)

    def checkMyProfile(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        profile = self.db.getUserById(message.chat.id)

        # Распаковка профиля
        user_id_, name, sex, city, university, course, age, description, photo = profile
        sex_text = "Мужской" if self.db.getSexById(message.chat.id) == 1 else "Женский"
        text = (
            f"Имя: {name}\n"
            f"Пол: {sex_text}\n"
            f"🏙️Город: {city}\n"
            f"🎓 Университет:\n{university}, "
            f"📚 Курс: {course}\n"
            f"Возраст: {age}\n"
            f"📝 О себе: {description}\n"
        )
        if(self.parent.isOpenBot):
            self.bot.send_photo(message.chat.id, photo, caption=text)
            self.parent.showMainMenu(message)
        else:
            self.bot.send_photo(message.chat.id, photo, caption=text, reply_markup=createReplyKeyboard(["Смотреть мою анкету", "Заполнить анкету заново"]))
            self.bot.register_next_step_handler(message, self.handleMenuUntilStart)

    def resetUserById(self, user_id):
        if(self.parent.tempDataIsUserInCallBack.get(cfg.admin, False)): return
        if user_id not in self.tempData:
            return False
        self.tempData.pop(user_id, None)
        return True

