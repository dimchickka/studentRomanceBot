from utils import *

class DeleteProfile:
    def __init__(self, bot, dataBase, parent):
        self.bot = bot
        self.db = dataBase
        self.parent = parent  # Ссылка на TelegramBot

    def handleDeleteProfile(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        options = [
            f"Да",
            "В главное меню ⬅️",
        ]
        markup = createReplyKeyboard(options, columns=1)
        sex = "уверен" if self.db.getSexById(message.chat.id) == 1 else "уверена"
        self.bot.send_message(message.chat.id, f"Ты {sex}, что хочешь удалить свою анкету🥺\nМы будем очень скучать🥺🥺🥺", reply_markup=markup)
        self.bot.register_next_step_handler(message, self.handleDoYouReallyWantToDeleteYourProfile)

    def handleDoYouReallyWantToDeleteYourProfile(self, message):
        if (self.parent.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        if message.content_type != "text":
            self.bot.send_message(message.chat.id, "Пожалуйста, пришли текстовое сообщение")
            return self.bot.register_next_step_handler(message, self.handleDoYouReallyWantToDeleteYourProfile)
        options = [
            "Да",
            "В главное меню ⬅️",
        ]

        if message.text not in options:
            self.bot.send_message(
                message.chat.id,
                "Я тебя не понимаю, пожалуйста, выбери вариант с помощью кнопок"
            )
            self.bot.register_next_step_handler(message, self.handleDoYouReallyWantToDeleteYourProfile)
            return

        if (self.parent.profileView.comeBackToTheMainMenu(message)):
            return

        else:
            sex = "нашёл" if self.db.getSexById(message.chat.id) == 1 else "нашла"
            self.bot.send_message(message.chat.id, f"Ладно, надеюсь ты {sex} кого-то благодаря мне🤗\nЕсли захочешь ещё кого-то найти, обращайся")
            self.db.deleteUserById(message.chat.id)
            self.parent.tempDataIsUserInCallBack.pop(message.chat.id, None)
            self.bot.send_message(message.chat.id, "📜Анкета успешно удалена")
