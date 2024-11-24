import sys
from enum import Enum
import json
import threading
import time

import sqlite3

import telebot
from telebot import apihelper, types

class Rights(int, Enum):
    unknown = 0
    read = 1
    write = 2
    owner = 4

# Подключение к БД
with sqlite3.connect('kinobot_database.db') as connection:
    cursor = connection.cursor()

# Создаем экземпляр бота
bot = telebot.TeleBot(token = sys.argv[1], threaded=False, num_threads=1)

handlers = {}

class Dialog:
    def __init__(self, user_id):
        print(user_id)
        self.user_id = user_id
        self.response_handler = None
        self.previosly_message = None
        self.add_user()
        self.list_lists()
        
    def delete_prev_message(self):
        if self.previosly_message:
            bot.delete_message(self.user_id, self.previosly_message)
            self.previosly_message = None
        
    def add_user(self):
        print("add_user")
        with connection:
            cursor.execute('INSERT OR IGNORE INTO User (user_id) VALUES (?)', (self.user_id,))

    def list_lists(self):
        print("list_lists")
        # Получить список доступных списков из БД
        with connection:
            cursor.execute('SELECT List.list_id, List.name FROM List JOIN UsersLists ON UsersLists.list_id=List.list_id JOIN User ON User.user_id=? AND UsersLists.user_id=User.user_id', (self.user_id,))
            lists = cursor.fetchall()

        # Добавляем кнопки со списками
        markup = types.InlineKeyboardMarkup()
        for movie_list in lists:
            button = types.InlineKeyboardButton(movie_list[1], callback_data=json.dumps(('o', movie_list[0])))
            markup.add(button)

        markup.row(types.InlineKeyboardButton("Создать", callback_data=json.dumps('c')), types.InlineKeyboardButton("Добавить", callback_data=json.dumps('i')))

        self.response_handler = self.list_lists_handler
        if lists:
            message_text = "Выбери список"
        else:
            message_text = "Доступных списков нет"
        self.previosly_message = bot.send_message(self.user_id, message_text, reply_markup=markup).message_id

    def list_lists_handler(self, data):
        print("list_lists_handler")
        result = False
        if type(data) is str:
            # создание нового списка
            if data == 'c':
                result = True
                self.new_list()
            # импорт чужого списка
            elif data == 'i':
                result = True
                self.import_list()
        # открытие списка
        elif type(data) is tuple and len(data) == 2 and data[0] == 'o':
            result = True
            self.open_list_menu(data[1])

        if not result:
            self.list_lists()
   
    def new_list(self):
        print("new_list")
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("Назад", callback_data=json.dumps('e')))
        self.response_handler = self.new_list_handler
        self.previosly_message = bot.send_message(self.user_id, "Введи имя списка", reply_markup=markup).message_id
        
    def new_list_handler(self, data):
        print("new_list_handler")
        result = False
        if type(data) is str:
            # назад
            if data == 'e':
                result = True
            # введено имя нового списка
            elif len(data) > 0:
                with connection:
                    cursor.execute('INSERT INTO List VALUES (NULL,?,?) RETURNING list_id', (data,self.user_id))
                    list_id = cursor.fetchone()
                    cursor.execute('INSERT INTO UsersLists VALUES (?,?,?)', (self.user_id,list_id[0],Rights.owner))
                    result = True

        if not result:
            self.new_list()
        else:
            self.list_lists()        

    def import_list(self):
        print("import_list")
                
    # работа со списками
    def open_list_menu(self, list_id):
        print("list_menu")

    def list_movies(self, list_id):
        print("list_movies")

    def list_all_movies(self, list_id):
        print("list_movies")
    
    def add_movie_to_list(self, list_id):
        print("add_movie_to_list")
        
    def share_list(self):
        # TODO добавить шифрование при передаче списков
        print("share_list")
        
    # работа с фильмами
    def remove_movie_from_list(self):
        print("remove_movie_from_list")
        
    def change_movie_status(self):
        print("change_movie_status")    
        

# Функция, обрабатывающая команду /start
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id   
    handlers[user_id] = Dialog(user_id)

# Получение сообщений от юзера
@bot.message_handler(content_types=["text"])
def handle_text(message):
    user_id = message.from_user.id
    handle_all(user_id, message.text)
    # удалить сообщение пользователя
    bot.delete_message(user_id, message.id)     

# Обработка нажатий кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_button(call):
    user_id = call.from_user.id
    handle_all(user_id, json.loads(call.data))

# Обработчик всех действий пользователя       
def handle_all(user_id, data):
    if not(user_id in handlers):
        handlers[user_id] = Dialog(user_id)
    else:
        handlers[user_id].delete_prev_message()
        handlers[user_id].response_handler(data)

# Запускаем бота
apihelper.RETRY_ON_ERROR = True        
while True:
        try:
            bot.polling(none_stop=True, interval=0)
        except Exception as e:
            time.sleep(3)
            print("Exception: ")
            print(e)
            
connection.close()