#В дипсик написано что делать, нужно чтобы ответ от GPT был без модуля think. А то он сейчас вместе с think в генерации анкеты ИИ делает
#Также в меню необходимо реализовать диактивацию анкеты
import telebot
from database import Database
from telebot import types  # Импорт для работы с клавиатурами
import config as cfg
from bot.profile_view import ProfileView
from bot.registration import Registration
from likeManager import LikeManager
from bot.AIDescriptionForUser import AIDescription
from bot.deleteProfile import DeleteProfile
from bot.adminPanel import AdminCatalog
#библиотеки для обработки описания
import threading
import time
import datetime
from utils import *
#соединяться с БД нужно непосредственно здесь, а не в том классе!
class TelegramBot:
    def __init__(self):
        self.bot = telebot.TeleBot(cfg.BOT_TOKEN)
        self.db = Database()
        self.adminCatalog = AdminCatalog(self.bot, self.db, parent=self)
        self.registration = Registration(self.bot, self.db, parent=self)
        self.isOpenBot = False
        self.codeForPassingEmailControl = 'aaaAAA56'
        self.profileDeleter = DeleteProfile(self.bot, self.db, parent=self)
        self.profileView = ProfileView(self.bot, self.db, parent=self)
        self.likeManager = LikeManager(self.bot, self.db, parent=self )
        self.aiDescription = AIDescription(self.bot, self.db, parent=self)
        self.tempDataIsUserInCallBack = {}
        self.tempDataHowManyTimesUserUsedDescriptionAIFunction = {}
        self.start_daily_operations()
        self._setup_handlers()  #Вызов метода
    def _setup_handlers(self):
        """Регистрация обработчиков команд."""
        self.registration.register_handlers()
        self.likeManager.register_handlers()


    def showMainMenu(self, message):
        if(self.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Смотреть анкеты")
        markup.add("Описание к твоей анкете от ИИ")
        markup.add("Моя анкета")
        markup.add("Удалить анкету")
        if(message.chat.id == cfg.admin):
            markup.add("Панель админа")
        self.bot.send_message(
            chat_id=message.chat.id,
            text="Выбери, что хочешь сделать дальше:",
            reply_markup=markup
        )
        self.bot.register_next_step_handler(message, self.handleMainMenu)

    def handleMainMenu(self, message):
        if (self.tempDataIsUserInCallBack.get(message.chat.id, False)): return
        if message.content_type != "text":
            self.bot.send_message(message.chat.id, "Пожалуйста, пришли текстовое сообщение")
            return self.bot.register_next_step_handler(message, self.handleMainMenu)
        if message.text == "Смотреть анкеты":
            self.profileView.handleViewProfiles(message)
        elif message.text == "Описание к твоей анкете от ИИ":
            self.aiDescription.handleAIProfileDescription(message)
        elif message.text == "Моя анкета":
            self.registration.checkMyProfile(message)
        elif message.text == "Удалить анкету":
            self.profileDeleter.handleDeleteProfile(message)
        elif (message.chat.id == cfg.admin and message.text == "Панель админа"):
            self.adminCatalog.adminMenu()
        else:
            self.bot.send_message(message.chat.id, "Выберите вариант из меню.")
            self.bot.register_next_step_handler(message, self.handleMainMenu)

    def reset_usage_counter_daily_thread(self):
        while True:
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.tempDataHowManyTimesUserUsedDescriptionAIFunction.clear()
            self.notification_worker_who_liked_whom()
            time.sleep(24 * 60 * 60)  # 1 день

    def start_daily_operations(self):
        # Поток для основной функции
        thread1 = threading.Thread(target=self.reset_usage_counter_daily_thread, daemon=True)
        thread1.start()

    def notification_worker_who_liked_whom(self):
        try:
            # Создаем копию словаря для безопасного обращения
            users_to_notify = list(self.likeManager.tempDataWhoLikedWhom.keys())

            for user_id in users_to_notify:
                try:
                    if user_id in self.likeManager.tempDataWhoLikedWhom:  # Проверяем, что пользователь еще в словаре
                        self.likeManager.sendLikeNotification(user_id)
                except Exception as e:
                    print(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")

        except Exception as e:
            print(f"Критическая ошибка в worker: {e}")

    def run(self):
        while True:
            try:
                print(f"🔁 Bot polling started at {datetime.datetime.now()}")
                self.bot.polling(non_stop=True, timeout=30)
                break
            except Exception as e:
                print(f"❌ Bot crashed at {datetime.datetime.now()}: {e}")
                time.sleep(1)

