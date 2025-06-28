from utils import *
import telebot
class LikeManager:
    def __init__(self, bot, dataBase, parent):
        self.bot = bot
        self.db = dataBase
        self.parent = parent  # Ссылка на TelegramBot
        self.tempDataWhoLikedWhom = {}  #Структура кого лайкнули: [...] - список тех, кто лайкнул

    def register_handlers(self):
        """Регистрация обработчиков команд."""  #далее bot.polling сам опрашивает чат на наличие сообщений. Мы только регистрируем здесь
        # Регистрируем обработчик с привязкой self
        self.bot.callback_query_handler(
            func=lambda call: call.data.startswith("view_likes")
        )(lambda call: self.handleViewLikesCallback(call))


    def handleLikes(self, whoHasBeenLiked, whoLiked):
        """
        whoHasBeenLiked — пользователь, которого лайкнули
        whoLiked — пользователь, который лайкнул
        """

        # Проверка: если пользователя ещё нет в словаре — создаём для него запись
        if whoHasBeenLiked not in self.tempDataWhoLikedWhom:
            self.tempDataWhoLikedWhom[whoHasBeenLiked] = [whoLiked]
            self.sendLikeNotification(whoHasBeenLiked)
        else:
            # Если уже есть — добавляем, если ещё не добавлен
            if whoLiked not in self.tempDataWhoLikedWhom[whoHasBeenLiked]:
                self.tempDataWhoLikedWhom[whoHasBeenLiked].append(whoLiked)

    def handleViewLikesCallback(self, call):
        user_id = call.from_user.id
        if (self.parent.tempDataIsUserInCallBack.get(user_id)):return
        if(not self.db.getUserById(user_id)):return
        self.parent.tempDataIsUserInCallBack[user_id] = True

        self.bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="✅ Запрос принят! Сейчас покажем, кто вас лайкнул 👇",
            reply_markup=None
        )

        self.sendNextLikerProfile(call)

    def sendNextLikerProfile(self, call):
        message = call.message
        self.sendNextLikerProfileProcessing(message)


    def sendNextLikerProfileProcessing(self, message):
        data = self.tempDataWhoLikedWhom.get(message.chat.id, {})
        if not data:
            self.bot.send_message(message.chat.id,
                                  "Похоже что этот пользователь уже кого-то нашёл себе😕\nНе расстраивайся, мы тебе тоже кого-нибудь найдём 😄")
            self.tempDataWhoLikedWhom.pop(message.chat.id, None)
            self.parent.tempDataIsUserInCallBack[message.chat.id] = False
            self.parent.showMainMenu(message)
            return

        liker_id = data[0]
        liker_data = self.db.getUserById(liker_id)

        if not liker_data:
            # Если данные лайкнувшего не найдены — удаляем его, показываем следующего
            data.pop(0)
            self.sendNextLikerProfile(message.chat.id)
            return
        # Показываем карточку профиля
        self.parent.profileView.sendProfileCard(message, liker_id)
        # Ожидаем ответ
        self.bot.register_next_step_handler_by_chat_id(message.chat.id, self.handleProfileResponse)
        # self.bot.register_next_step_handler(user_id, self.handleProfileResponse)

    def handleProfileResponse(self, message):
        if message.content_type != "text":
            self.bot.send_message(message.chat.id, "Пожалуйста, пришли текстовое сообщение")
            return self.bot.register_next_step_handler(message, self.handleProfileResponse)
        user_id = message.chat.id
        action = message.text
        data = self.tempDataWhoLikedWhom.get(user_id, {})
        liker_id = data[0]

        if action not in ["❤️ Лайк", "💔 Дизлайк", "В главное меню ⬅️"]:
            self.bot.send_message(user_id, "Пожалуйста, выбери действие кнопкой 👇")
            self.bot.register_next_step_handler(message, self.handleProfileResponse)
            return

        if self.parent.profileView.comeBackToTheMainMenu(message): return

        # Обработка лайка
        if action == "❤️ Лайк":
            username = self.getUsername(liker_id)
            if username:
                sex = "Её" if self.db.getSexById(message.chat.id) == 1 else "Его"
                shortName = f"@{username}"
                self.bot.send_message(user_id, f"Взаимная симпатия! Пиши 👉 {shortName}\nP.S. Только ты можешь это сделать. Только у тебя есть {sex} контакт")
            else:
                self.db.deleteUserById(liker_id)
                self.bot.send_message(user_id, "Похоже что этот пользователь уже кого-то нашёл себе😕\n Не расстраивайся, мы тебе тоже кого нибудь найдём 😄")
        data.pop(0)
        self.handleOneMoreUserWhoLiked(message)
    def handleOneMoreUserWhoLiked(self, message):
        data = self.tempDataWhoLikedWhom.get(message.chat.id, {})
        if(data):
            markup = createReplyKeyboard(["Посмотреть", "В главное меню ⬅️"])
            self.bot.send_message(message.chat.id, "В списке, кому вы понравились, есть ещё пользователь", reply_markup=markup)
            self.bot.register_next_step_handler(message, self.handleContinueViewOnProfilesOfUsersWhoLikedYou)
        else:
            self.parent.tempDataIsUserInCallBack[message.chat.id] = False
            self.tempDataWhoLikedWhom.pop(message.chat.id, None)
            self.parent.showMainMenu(message)
    def handleContinueViewOnProfilesOfUsersWhoLikedYou(self, message):
        if message.content_type != "text":
            self.bot.send_message(message.chat.id, "Пожалуйста, пришли текстовое сообщение")
            return self.bot.register_next_step_handler(message, self.handleContinueViewOnProfilesOfUsersWhoLikedYou)
        user_id = message.chat.id
        action = message.text
        if action not in ["Посмотреть", "В главное меню ⬅️"]:
            self.bot.send_message(user_id, "Пожалуйста, выбери действие кнопкой 👇")
            self.bot.register_next_step_handler(message, self.handleContinueViewOnProfilesOfUsersWhoLikedYou)
            return
        if message.text == "В главное меню ⬅️":
            self.parent.tempDataIsUserInCallBack[message.chat.id] = False
            self.sendLikeNotification(message.chat.id)
            self.parent.showMainMenu(message)
            return
        self.sendNextLikerProfileProcessing(message)

    def getUsername(self, user_id):
        try:
            chat = self.bot.get_chat(user_id)
            return chat.username or None
        except Exception as e:
            self.db.deleteUserById(user_id)  # Твоя функция удаления из БД
            return None

    def sendLikeNotification(self, user_id):
        try:
            markup = createInlineKeyboard(["Посмотреть кто"], callback_prefix="view_likes")
            self.bot.send_message(user_id, "❤️ Кто-то проявил к вам интерес!", reply_markup=markup)

        except telebot.apihelper.ApiTelegramException as e:
            error_text = str(e).lower()

            if any(keyword in error_text for keyword in [
                "chat not found",
                "bot was blocked",
                "user is deactivated",
                "user not found",
                "can't initiate conversation",
                "user is not a member"
            ]):
                self.db.deleteUserById(user_id)  # Метод удаления из базы
            else:
                return cfg.ERROR_REQUEST