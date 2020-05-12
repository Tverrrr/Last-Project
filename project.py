# -*- coding: utf-8 -*-
import telebot
from telebot import types, apihelper
import sqlite3
import requests
import time
import json
import random

bot = telebot.TeleBot('1258249708:AAHc9VMuhButatFD8c_Yg-4Pj17LS9Xgcmc')


@bot.message_handler(commands=['start'])
def start_message(message):
    connection = sqlite3.connect('database.sqlite')
    q = connection.cursor()
    userid = str(message.chat.id)
    q.execute("SELECT id FROM users WHERE id = {}".format(userid))
    row = q.fetchone()
    if row is None:
        q.execute("INSERT INTO users (id, rooms) VALUES ({}, 0)".format(userid))
        connection.commit()
    keyboard = types.ReplyKeyboardMarkup(True)
    keyboard.add(types.InlineKeyboardButton(text="Вступить в комнату", callback_data="join_room"))
    keyboard.add(types.InlineKeyboardButton(text="Создать комнату", callback_data="create_room"))
    keyboard.add(types.InlineKeyboardButton(text="Управление комнатами", callback_data="settings_room"))
    bot.send_message(message.chat.id, "Вы попали в главное меню", reply_markup=keyboard)


@bot.message_handler(content_types=['text'])
def send_text(message):
    if message.text.lower() == "Вступить в комнату".lower():
        msg = bot.send_message(message.chat.id, "Введите ID комнаты или дождитесь приглашения админа комнаты.")
        bot.register_next_step_handler(msg, join_room_id)

    if message.text.lower() == "Создать комнату".lower():
        connection = sqlite3.connect('database.sqlite')
        q = connection.cursor()
        q.execute("SELECT rooms_count FROM users WHERE id = {}".format(message.chat.id))
        count = q.fetchone()[0]
        if count + 1 < 6:
            msg = bot.send_message(message.chat.id, "Введите название комнаты.")
            bot.register_next_step_handler(msg, create_room_name)
        else:
            keyboard = types.ReplyKeyboardMarkup(True)
            keyboard.add(types.InlineKeyboardButton(text="Вступить в комнату", callback_data="join_room"))
            keyboard.add(types.InlineKeyboardButton(text="Создать комнату", callback_data="create_room"))
            keyboard.add(types.InlineKeyboardButton(text="Управление комнатами", callback_data="settings_room"))
            bot.send_message(message.chat.id, "Вы достигли лимита по комнатам (максимум 5 комнат).",
                             reply_markup=keyboard)

    if message.text.lower() == "Управление комнатами".lower():
        connection = sqlite3.connect('database.sqlite')
        q = connection.cursor()
        q.execute("SELECT room_name FROM rooms WHERE creator_id = {}".format(message.chat.id))
        rooms = q.fetchall()
        if rooms:
            keyboard = types.InlineKeyboardMarkup()
            for i in range(len(rooms)):
                s = "room_"
                s += str(i + 1)
                exec("keyboard.add(types.InlineKeyboardButton(text='{}', callback_data='{}'))".format(rooms[i][0], s))
            bot.send_message(message.chat.id, "Вы попали в меню управления комнатами.", reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, "У вас нет комнат.")


def create_room_name(message):
    room_name = message.text
    connection = sqlite3.connect('database.sqlite')
    q = connection.cursor()
    q.execute("SELECT room_id FROM rooms WHERE room_id != 0")
    ids = q.fetchall()[-1][0]
    ids += 1
    q.execute("INSERT INTO rooms (room_id, room_name, creator_id) VALUES ({}, '{}', {})".format(ids, room_name,
                                                                                                message.chat.id))
    connection.commit()
    msg = bot.send_message(message.chat.id, "Введите пароль для комнаты.")
    bot.register_next_step_handler(msg, create_room_password)


def create_room_password(message):
    room_password = message.text
    connection = sqlite3.connect('database.sqlite')
    q = connection.cursor()
    q.execute("SELECT room_id FROM rooms WHERE room_id != 0")
    ids = q.fetchall()[-1][0]
    q = connection.cursor()
    q.execute("update rooms set room_password = '{}' where room_id = {}".format(room_password, ids))
    connection.commit()
    keyboard = types.ReplyKeyboardMarkup(True)
    keyboard.add(types.InlineKeyboardButton(text="Вступить в комнату", callback_data="join_room"))
    keyboard.add(types.InlineKeyboardButton(text="Создать комнату", callback_data="create_room"))
    keyboard.add(types.InlineKeyboardButton(text="Управление комнатами", callback_data="settings_room"))
    bot.send_message(message.chat.id,
                     "Комната успешно создана, переходим в главное меню. Вступите в вашу комнату, её ID - {}".format(
                         ids), reply_markup=keyboard)


def join_room_id(message):
    room_id = message.text
    connection = sqlite3.connect('database.sqlite')
    q = connection.cursor()
    keyboard = types.ReplyKeyboardMarkup(True)
    keyboard.add(types.InlineKeyboardButton(text="Вступить в комнату", callback_data="join_room"))
    keyboard.add(types.InlineKeyboardButton(text="Создать комнату", callback_data="create_room"))
    keyboard.add(types.InlineKeyboardButton(text="Управление комнатами", callback_data="settings_room"))
    if room_id.isdigit():
        q.execute("SELECT room_id FROM rooms WHERE room_id = {}".format(room_id))
        check = q.fetchone()
        if not check:
            bot.send_message(message.chat.id, "Комнаты с таким ID нет, переходим в главное меню.",
                             reply_markup=keyboard)
        else:
            q.execute("SELECT rooms FROM users WHERE id = {}".format(message.chat.id))
            list_rooms = q.fetchone()[0]
            exec("list_rooms = {}".format(list_rooms))
            if room_id in list_rooms:
                bot.send_message(message.chat.id, "Вы уже вошли в эту комнату.", reply_markup=keyboard)
            else:
                msg = bot.send_message(message.chat.id, "Введите пароль от комнаты с указанным ID.")
                bot.register_next_step_handler(msg, join_room_pass, room_id)
    else:
        bot.send_message(message.chat.id, "Вы ввели ID комнаты в неправильном формате, переходим в главное меню.",
                         reply_markup=keyboard)


def join_room_pass(message, room_id):
    connection = sqlite3.connect('database.sqlite')
    q = connection.cursor()
    q.execute("SELECT room_password FROM rooms WHERE room_id = {}".format(room_id))
    check = q.fetchone()[0]
    password = message.text
    keyboard = types.ReplyKeyboardMarkup(True)
    keyboard.add(types.InlineKeyboardButton(text="Вступить в комнату", callback_data="join_room"))
    keyboard.add(types.InlineKeyboardButton(text="Создать комнату", callback_data="create_room"))
    keyboard.add(types.InlineKeyboardButton(text="Управление комнатами", callback_data="settings_room"))
    if password == check:
        bot.send_message(message.chat.id, "Вы успешно вошли в комнату, ожидайте начала викторины.",
                         reply_markup=keyboard)
        q.execute("SELECT rooms FROM users WHERE id = {}".format(message.chat.id))
        list_rooms = q.fetchone()[0]
        if str(list_rooms) == '0':
            n = [int(room_id)]
        else:
            n = []
            for i in list_rooms:
                if i.isdigit():
                    n.append(i)
            for i in range(len(n)):
                n[i] = int(n[i])
            n.append(int(room_id))
        q.execute("update users set rooms = '{}' where id = {}".format(str(n), message.chat.id))
        connection.commit()
        q.execute("select room_users from rooms where room_id = {}".format(room_id))
        list_users = q.fetchone()[0]
        if str(list_users) == '0':
            nn = [int(message.chat.id)]
            print(0)
        else:
            print(1)
            nn = []
            list_users = list_users.replace("[", '')
            list_users = list_users.replace("]", '')
            list_users = list_users.replace("'", '')
            list_users = list_users.split(',')
            print(list_users, 1)
            for i in list_users:
                if i.isdigit():
                    nn.append(int(i))
            for i in range(len(n)):
                nn[i] = int(nn[i])
            nn.append(int(message.chat.id))
            print(nn, 2)
        q.execute("update rooms set room_users = '{}' where room_id = {}".format(str(nn), room_id))
        connection.commit()
    else:
        bot.send_message(message.chat.id, "Вы ввели неправильный пароль, попробуйте снова.", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Начать викторину в комнате", callback_data="start_quiz"))
    keyboard.add(types.InlineKeyboardButton(text="Пригласить пользователя по ID", callback_data="invite_id"))
    keyboard.add(types.InlineKeyboardButton(text="Добавить вопрос в базу данных", callback_data="add_question_db"))
    keyboard.add(types.InlineKeyboardButton(text="Добавить вопрос в комнату по ID", callback_data="add_question"))
    keyboard.add(types.InlineKeyboardButton(text="Удалить вопрос", callback_data="delete_question"))
    keyboard.add(types.InlineKeyboardButton(text="Изменить пароль комнаты", callback_data="change_password"))
    connection = sqlite3.connect('database.sqlite')
    q = connection.cursor()
    q.execute("SELECT room_name, room_id, room_password FROM rooms WHERE creator_id = {}".format(call.message.chat.id))
    rooms = q.fetchall()

    if call.data[:6] == "room_1":
        bot.send_message(call.message.chat.id,
                         "Меню управления комнаты {}.\nID комнаты: {}\nПароль от комнаты: {}".format(rooms[0][0],
                                                                                                     rooms[0][1],
                                                                                                     rooms[0][2]),
                         reply_markup=keyboard)

    if call.data[:6] == "room_2":
        bot.send_message(call.message.chat.id,
                         "Меню управления комнаты {}.\nID комнаты: {}\nПароль от комнаты: {}".format(rooms[1][0],
                                                                                                     rooms[1][1],
                                                                                                     rooms[1][2]),
                         reply_markup=keyboard)

    if call.data[:6] == "room_3":
        bot.send_message(call.message.chat.id,
                         "Меню управления комнаты {}.\nID комнаты: {}\nПароль от комнаты: {}".format(rooms[2][0],
                                                                                                     rooms[2][1],
                                                                                                     rooms[2][2]),
                         reply_markup=keyboard)

    if call.data[:6] == "room_4":
        bot.send_message(call.message.chat.id,
                         "Меню управления комнаты {}.\nID комнаты: {}\nПароль от комнаты: {}".format(rooms[3][0],
                                                                                                     rooms[3][1],
                                                                                                     rooms[3][2]),
                         reply_markup=keyboard)

    if call.data[:6] == "room_5":
        bot.send_message(call.message.chat.id,
                         "Меню управления комнаты {}.\nID комнаты: {}\nПароль от комнаты: {}".format(rooms[4][0],
                                                                                                     rooms[4][1],
                                                                                                     rooms[4][2]),
                         reply_markup=keyboard)

    if call.data[:16] == "add_question_db":
        msg = bot.send_message(call.message.chat.id, "Сформулируйте сам вопрос и напишите его.")
        bot.register_next_step_handler(msg, add_question_db)

    if call.data[:13] == "add_question":
        msg = bot.send_message(call.message.chat.id, "Введите ID группы")
        bot.register_next_step_handler(msg, add_question)

    if call.data[:15] == "delete_question":
        msg = bot.send_message(call.message.chat.id, "Введите ID вопроса")
        bot.register_next_step_handler(msg, delete_question)

    if call.data[:16] == "change_password":
        msg = bot.send_message(call.message.chat.id, "Введите ID комнаты")
        bot.register_next_step_handler(msg, change_password)

    if call.data[:10] == "invite_id":
        msg = bot.send_message(call.message.chat.id, "Введите ID комнаты")
        bot.register_next_step_handler(msg, invite)

    if call.data[:11] == "start_quiz":
        msg = bot.send_message(call.message. chat. id, "Введите ID комнаты")
        bot.register_next_step_handler(msg, start_quiz)


def start_quiz(message):
    id_room = message.text
    connection = sqlite3.connect('database.sqlite')
    q = connection.cursor()
    if id_room.isdigit():
        q.execute("select room_id from rooms where room_id = {}".format(id_room))
        check = q.fetchone()
        if check:
            q.execute("select room_questions from rooms where room_id = {}".format(id_room))
            result = q.fetchone()
            if result != "0":
                n = []
                result = result[0]
                result = result.replace("[", "")
                result = result.replace("]", "")
                result = result.split(', ')
                for i in result:
                    if i.isdigit():
                        n.append(int(i))
                nn = len(n)
                print(n[0], 'n0')
                q.execute("select question, correct_answer, other_answers from questions where id = {}".format(n[0]))
                ans = q.fetchone()
                a = ans[1]
                b = ans[2]
                c = ans[0]
                q.execute("select room_users from rooms where room_id = {}".format(id_room))
                d = q.fetchone()
                if len(d) == 1:
                    exec("d = {}".format(d[0]))
                    if d[0]:
                        print(0)
                        quiz(0, a, b, d[0], nn, n, c)
                    else:
                        bot.send_message(message.chat.id, "У вас нет пользователей в комнате")
                else:
                    print(1)
                    d = d.replace("[", "")
                    d = d.replace("]", "")
                    d = d.split(', ') 
                    for i in d:
                        if i.isdigit():
                            e.append(int(i))
                    print(0, a, b, e, nn, n, c)
                    quiz(0, a, b, e, nn, n, c)
            else:
                bot.send_message(message.chat.id, "У вас нет вопросов в комнате.")
        else:
            bot.send_message(message.chat.id, "Нет комнаты с таким ID.")
    else:
        bot.send_message(message.chat.id, "Вы ввели ID комнаты в неправильном формате.")


def add_question_db(message):
    question = message.text
    connection = sqlite3.connect('database.sqlite')
    q = connection.cursor()
    q.execute("select id from questions where id != -1")
    ids = q.fetchall()[-1][0]
    ids += 1
    q.execute("INSERT INTO questions (id, question) VALUES ({}, '{}')".format(ids, question))
    connection.commit()
    msg = bot.send_message(message.chat.id, "Сейчас введи правильный ответ на ваш вопрос.")
    bot.register_next_step_handler(msg, add_correct_answer, ids)


def add_correct_answer(message, id):
    correct_answer = message.text
    connection = sqlite3.connect('database.sqlite')
    q = connection.cursor()
    q.execute("update questions set correct_answer = '{}' where id = {}".format(correct_answer, id))
    connection.commit()
    msg = bot.send_message(message.chat.id, "Введите 3 неправильных ответы на ваш вопрос, каждый на новой строчке.")
    bot.register_next_step_handler(msg, add_false_answers, id)


def add_false_answers(message, id):
    false_answers = message.text
    connection = sqlite3.connect('database.sqlite')
    q = connection.cursor()
    keyboard = types.ReplyKeyboardMarkup(True)
    keyboard.add(types.InlineKeyboardButton(text="Вступить в комнату", callback_data="join_room"))
    keyboard.add(types.InlineKeyboardButton(text="Создать комнату", callback_data="create_room"))
    keyboard.add(types.InlineKeyboardButton(text="Управление комнатами", callback_data="settings_room"))
    l = false_answers.split('\n')
    s = ', '.join(l)
    q.execute("update questions set other_answers = '{}' where id = {}".format(s, id))
    connection.commit()
    q.execute("update questions set users_id = {} where id = {}".format(message.chat.id, id))
    connection.commit()
    bot.send_message(message.chat.id, "Успешно добавили вопрос, возвращаемся в главное меню. ID вопроса - {}".format(id), reply_markup=keyboard)


def add_question(message):
    id = message.text
    if id.isdigit():
        msg = bot.send_message(message.chat.id, "Введите ID вопроса.")
        bot.register_next_step_handler(msg, add_question_id, id)
    else:
        bot.send_message(message.chat.id, "Вы ввели ID в неправильном формате.")


def add_question_id(message, id):
    connection = sqlite3.connect('database.sqlite')
    q = connection.cursor()
    id_ques = message.text
    if id_ques.isdigit():
        q.execute("select room_questions from rooms where room_id = {}".format(id))
        list_quest = q.fetchone()[0]
        q.execute("select id from questions where id = {}".format(id_ques))
        l = q.fetchone()
        if l:
            if str(list_quest) == '0':
                n = [int(id_ques)]
            else:
                list_quest = list_quest.replace("[", "")
                list_quest = list_quest.replace("]", "")
                list_quest = list_quest.split(', ')
                print(list_quest)
                n = []
                e = []
                for i in list_quest:
                    print(i)
                    if i.isdigit():
                        n.append(int(i))
                if int(id_ques) not in n:
                    n.append(int(id_ques))
                    print(n, 0)
            q.execute("update rooms set room_questions = '{}' where room_id = {}".format(str(n), id))
            connection.commit()
            bot.send_message(message.chat.id, "Готово.")
        else:
            bot.send_message(message.chat.id, "Такого вопроса нет в нашей базе данных.")
    else:
        bot.send_message(message.chat.id, "Вы ввели ID вопроса в неправильном формате.")


def delete_question(message):
    connection = sqlite3.connect('database.sqlite')
    q = connection.cursor()
    id_ques = message.text
    if id_ques.isdigit():
        msg = bot.send_message(message.chat.id, "Введите ID комнаты.")
        bot.register_next_step_handler(msg, delete_question_id, id_ques)
    else:
        bot.send_message(message.chat.id, "Вы ввели ID вопроса в неправильном формате.")


def delete_question_id(message, id_ques):
    connection = sqlite3.connect('database.sqlite')
    q = connection.cursor()
    id = message.text
    if id.isdigit():
        q.execute("select room_questions from rooms where room_id = {}".format(id))
        list_quest = q.fetchone()
        if str(list_quest) == '0':
            bot.send_message(message.chat.id, "Такого вопроса в вашей комнате нет.")
        else:
            list_quest = list_quest[0]
            list_quest = list_quest.replace("[", "")
            list_quest = list_quest.replace("]", "")
            list_quest = list_quest.split(', ')
            print(list_quest)
            n = []
            for i in list_quest:
                if i.isdigit():
                    n.append(int(i))
            if int(id_ques) in n:
                del n[n.index(int(id_ques))]
                if not n:
                    n = 0
                q.execute("update rooms set room_questions = '{}' where room_id = {}".format(str(n), id))
                connection.commit()
                msg = bot.send_message(message.chat.id, "Готово.")
            else:
                bot.send_message(message.chat.id, "Такого вопроса в вашей комнате нет.")
    else:
        bot.send_message(message.chat.id, "Вы ввели ID комнаты в неправильном формате.")


def change_password(message):
    id = message.text
    if id.isdigit():
        msg = bot.send_message(message.chat.id, "Введите пароль")
        bot.register_next_step_handler(msg, change_password_2, id)
    else:
        bot.send_message(message.chat.id, "Вы ввели ID комнаты в неправильном формате.")


def change_password_2(message, id):
    password = message.text
    connection = sqlite3.connect('database.sqlite')
    q = connection.cursor()
    q.execute("update rooms set room_password = {} where room_id = {}".format(password, id))
    connection.commit()
    bot.send_message(message.chat.id, "Готово. Вы установили пароль: {}".format(password))


def invite(message):
    id = message.text
    if id.isdigit():
        msg = bot.send_message(message.chat.id, "Введите ID пользователя.")
        bot.register_next_step_handler(msg, invite_id, id)
    else:
        bot.send_message(message.chat.id, "Вы ввели ID комнаты в неправильном формате.")


def invite_id(message, id):
    connection = sqlite3.connect('database.sqlite')
    q = connection.cursor()
    id_user = message.text
    q.execute("SELECT rooms FROM users WHERE id = {}".format(message.chat.id))
    list_rooms = q.fetchone()[0]
    if id_user.isdigit():
        if str(list_rooms) == '0':
            n = [int(id)]
        else:
            n = []
            for i in list_rooms:
                if i.isdigit():
                    n.append(i)
            for i in range(len(n)):
                n[i] = int(n[i])
            n.append(int(id))
        q.execute("update users set rooms = '{}' where id = {}".format(str(n), message.chat.id))
        connection.commit()
        q.execute("select id from users where id = {}".format(id_user))
        ids = q.fetchone()
        if ids:
            q.execute("select room_users from rooms where room_id = {}".format(id))
            list_users = q.fetchone()[0]
            if str(list_users) == '0':
                nn = [int(message.chat.id)]
                print(0)
            else:
                print(1)
                nn = []
                print(list_users, 0)
                list_users = list_users.replace("[", '')
                list_users = list_users.replace("]", '')
                list_users = list_users.replace("'", '')
                list_users = list_users.split(',')
                print(list_users, 1, len(list_users))
                for i in list_users:
                    if i.isdigit():
                        nn.append(int(i))
                        print(nn)
                for i in range(len(nn)):
                    nn[i] = int(nn[i])
                nn.append(int(message.chat.id))
                print(nn, 2)
                q.execute("update rooms set room_users = '{}' where room_id = {}".format(str(nn), id))
                connection.commit()
        else:
            bot.send_message(message.chat.id, "Такого пользователя нет у нас в базе.")
    else:
        bot.send_message(message.chat.id, "Вы ввели ID в неправильном формате.")


def quiz(id, correct_answer, other_answers, room_users, number, questions_id, question):
    other_answers += ', '
    other_answers += correct_answer
    other_answers = other_answers.split(', ')
    print(other_answers)
    print(id, correct_answer, other_answers, room_users, number, questions_id, question)
    random.shuffle(other_answers)
    print(type(room_users))
    if str(type(room_users)) != "<class 'list'>":
        room_users = room_users.replace("[", "")
        room_users = room_users.replace("]", "")
        room_users = room_users.split(', ')
    if id < number:
        for i in range(len(room_users)):
            print(i)
            x = requests.post(
                url='https://api.telegram.org/bot1258249708:AAHc9VMuhButatFD8c_Yg-4Pj17LS9Xgcmc/sendPoll?',
                data={'chat_id': room_users[i], 'question': question, 'options': json.dumps(other_answers), 'type': 'quiz', 'correct_option_id': other_answers.index(correct_answer)})
            print(x.content)
        if id + 1 < number:
            id += 1
            connection = sqlite3.connect('database.sqlite')
            q = connection.cursor()
            q.execute('select question, correct_answer, other_answers from questions where id = {}'.format(questions_id[id]))
            N = q.fetchall()[0]
            print(N)
            c = N[0]
            a = N[1]
            b = N[2]
            quiz(id, a, b, room_users, number, questions_id, c)
        else:
            for i in room_users:
                bot.send_message(i, 'Все вопросы отправлены, желаем успехов!')
    else:
        for i in room_users:
            bot.send_message(i, 'Все вопросы отправлены, желаем успехов!')


bot.polling(none_stop=True)
