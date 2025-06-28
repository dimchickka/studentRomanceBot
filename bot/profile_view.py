from utils import *
from functools import partial
class ProfileView:
    def __init__(self, bot, dataBase, parent):
        self.bot = bot
        self.db = dataBase
        self.parent = parent  # Ссылка на TelegramBot
        self.tempDataMyCity = {}
        self.tempDataMyUniversity = {}
        self.tempDataCity = {}
    def handleViewProfiles(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        # Если пол мужской (1), значит искать девушек, иначе парней
        target_label = "Девушки" if self.db.getSexById(message.chat.id) == 1 else "Парни"

        options = [
            f"{target_label} из моего ВУЗа",
            f"{target_label} из моего города",
            f"{target_label} из другого города",
            "В главное меню ⬅️",
        ]
        markup = createReplyKeyboard(options, columns=1)

        self.bot.send_message(message.chat.id, "Кого будем искать?", reply_markup=markup)
        self.bot.register_next_step_handler(message, self.handleWhoWillWeFind)

    def handleWhoWillWeFind(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        # Если пол мужской (1), значит искать девушек, иначе парней
        user_sex = self.db.getSexById(message.chat.id)
        target_label = "Девушки" if user_sex == 1 else "Парни"
        options = [
            f"{target_label} из моего ВУЗа",
            f"{target_label} из моего города",
            f"{target_label} из другого города",
            "В главное меню ⬅️",
        ]

        if message.text not in options:
            self.bot.send_message(
                message.chat.id,
                "Я тебя не понимаю, пожалуйста, выбери вариант с помощью кнопок"
            )
            self.bot.register_next_step_handler(message, self.handleWhoWillWeFind)
            return

        if(self.comeBackToTheMainMenu(message)): return

        else:
            if message.text == f"{target_label} из моего ВУЗа":
                if message.chat.id in self.tempDataMyUniversity:
                    self.showNextProfile(message, self.tempDataMyUniversity)
                    return

                users = self.db.getMatchingUsers(
                    viewer_id=message.chat.id,
                    sex= not user_sex,
                    university=self.db.getFieldById(message.chat.id, "university")
                )
                if (not self.isListOfUsersFull(message, users, university=1)):
                    return
                self.tempDataMyUniversity[message.chat.id] = {}  # Создаем новую запись
                self.tempDataMyUniversity[message.chat.id]['view_queue'] = users
                self.tempDataMyUniversity[message.chat.id]['view_index'] = 0
                self.showNextProfile(message, self.tempDataMyUniversity)

            elif message.text == f"{target_label} из моего города":
                city = self.db.getFieldById(message.chat.id, "city")
                if message.chat.id in self.tempDataMyCity:
                    self.showNextProfile(message, self.tempDataMyCity, city)
                    return
                users = self.db.getMatchingUsers(
                    viewer_id=message.chat.id,
                    sex= not user_sex,
                    city=city
                )
                if (not self.isListOfUsersFull(message, users, city=1)):
                    return
                self.tempDataMyCity[message.chat.id] = {}  # Создаем новую запись
                self.tempDataMyCity[message.chat.id]['view_queue'] = users
                self.tempDataMyCity[message.chat.id]['view_index'] = 0
                self.showNextProfile(message, self.tempDataMyCity, cityName= city)

            elif message.text == f"{target_label} из другого города":
                self.bot.send_message(message.chat.id,
                                      "🗺️ Введи город, в котором хочешь искать студентов.\n\nПример: Липецк, Нижний Новгород  (вводи с большой буквы)")
                self.bot.register_next_step_handler(message, self.handleCitySelection)
                return


    def handleCitySelection(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        self.tempDataCity[message.chat.id] = {}  # Создаем новую запись
        city = message.text.strip()

        if not isValidCityName(city):
            self.bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, введите корректное название города"
            )
            self.bot.register_next_step_handler(message, self.handleCitySelection)
            return

        user_sex = self.db.getSexById(message.chat.id)
        users = self.db.getMatchingUsers(
            viewer_id=message.chat.id,
            sex=not user_sex,
            city=city
        )
        if(not self.isListOfUsersFull(message, users, city = 1)):
            return
        self.tempDataCity[message.chat.id]['view_queue'] = users
        self.tempDataCity[message.chat.id]['view_index'] = 0
        self.showNextProfile(message, self.tempDataCity, cityName= city)

    def showNextProfile(self, message, tempData, cityName = None):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        user_id = message.chat.id

        # Получаем очередь и индекс текущего пользователя
        view_data = tempData.get(user_id, {})
        users = view_data.get('view_queue', [])
        index = view_data.get('view_index', 0)

        if index >= len(users):
            self.bot.send_message(user_id, "❌На данный момент пока всё😢\nВыбери другой фильтр для поиска пары. Или посмотри анкеты ещё раз")
            user_sex = self.db.getSexById(message.chat.id)
            if(cityName):
                users = self.db.getMatchingUsers(
                    viewer_id=message.chat.id,
                    sex=not user_sex,
                    city=cityName
                )
                if (not self.isListOfUsersFull(message, users,isFinishedButWas = True, city=1)):
                    return
            else:
                users = self.db.getMatchingUsers(
                    viewer_id=message.chat.id,
                    sex=not user_sex,
                    university=self.db.getFieldById(message.chat.id, "university")
                )
                if (not self.isListOfUsersFull(message, users)):
                    return

            tempData[message.chat.id]['view_queue'] = users
            tempData[message.chat.id]['view_index'] = 0
            self.showNextProfile(message, tempData, cityName)
            return
        profile_id = users[index]
        self.sendProfileCard(message, profile_id)
        # Ожидаем ответ
        self.bot.register_next_step_handler(message, lambda msg: self.handleProfileResponse(msg, tempData, cityName))

    def sendProfileCard(self, message, profile_id):
        user_id = message.chat.id
        profile = self.db.getUserById(profile_id)

        # Распаковка профиля
        user_id_, name, sex, city, university, course, age, description, photo = profile

        text = (
            f"Имя: {name}\n"
            f"🏙️Город: {city}\n"
            f"🎓 Университет:\n{university}, "
            f"📚 Курс: {course}\n"
            f"Возраст: {age}\n"
            f"📝 О себе: {description}\n"
        )
        # Кнопки
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("❤️ Лайк", "💔 Дизлайк")
        markup.add("В главное меню ⬅️")
        # Отправка анкеты (фото + текст)
        self.bot.send_photo(user_id, photo, caption=text, reply_markup=markup)

    def handleProfileResponse(self, message, tempData, cityName):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        user_id = message.chat.id
        action = message.text
        if action not in ["❤️ Лайк", "💔 Дизлайк", "В главное меню ⬅️"]:
            self.bot.send_message(user_id, "Пожалуйста, выбери действие кнопкой 👇")
            self.bot.register_next_step_handler(message, self.handleProfileResponse)
            return

        if self.comeBackToTheMainMenu(message): return

        # Обработка лайка
        if action == "❤️ Лайк":
            liked_profile = tempData[user_id]['view_queue'][tempData[user_id]['view_index']]
            self.parent.likeManager.handleLikes(liked_profile, message.chat.id)

        # Увеличиваем индекс и продолжаем просмотр
        tempData[user_id]['view_index'] += 1
        self.showNextProfile(message, tempData, cityName)


    def comeBackToTheMainMenu(self, message):
        if message.text == "В главное меню ⬅️":
            self.parent.showMainMenu(message)
            return True

    def isListOfUsersFull(self, message, users, isFinishedButWas = False, city=None, university=None):
        if users:
            return True  # Всё нормально — список непустой

        # Выводим корректное сообщение в зависимости от фильтра
        if city:
            filter_info = "городе"
        elif university:
            filter_info = "ВУЗе"

        if(isFinishedButWas):
            text = f"❌На данный момент пока всё😢, выбери другой фильтр для поиска пары"
        else:
            text = f"❌ В этом {filter_info} пока нет подходящих анкет 😢"
        self.bot.send_message(
            message.chat.id,
            text
        )
        self.handleViewProfiles(message)
        return False
