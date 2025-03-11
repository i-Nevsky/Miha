import os
import sqlite3
from flask import Flask, request, abort
import telebot
from telebot import types

# Токен вашего бота
TOKEN = "5380087368:AAE_8MEs80Nb_BEpS3Ph2dpZMZbMfeix6DU"
bot = telebot.TeleBot(TOKEN)

# Создаем Flask-приложение
app = Flask(__name__)
WEBHOOK_URL_PATH = f"/{TOKEN}"

# Маршрут для webhook (Telegram будет отправлять обновления сюда)
@app.route(WEBHOOK_URL_PATH, methods=["POST"])
def webhook():
    if request.headers.get("Content-Type", "") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "", 200
    else:
        abort(403)

# Корневой маршрут (например, для пинга)
@app.route("/")
def index():
    return "Бот работает!", 200

# --- Начало вашего кода для работы с опросом и БД ---

# Список вопросов (ключ, текст)
questions = [
    ("name", "Ваше ФИО:"),
    ("age", "Возраст:"),
    ("height_weight", "Рост и вес:"),
    ("contact", "Контакт: выберите способ заполнения (Номер телефона или Мессенджер):"),
    ("training_goal", "Какова основная цель занятий?"),
    ("chronic_diseases", "Есть ли хронические заболевания или травмы? (Сердце, суставы, спина и т.д.)"),
    ("medications", "Принимаешь ли какие-либо лекарства на постоянной основе?"),
    ("surgeries", "Были ли операции за последние 2 года?"),
    ("physical_activity_level", "Какой у вас уровень физической активности?"),
    ("bad_habits", "Есть ли вредные привычки (курение, алкоголь)?"),
    ("preferred_training_time", "Предпочтительное время для занятий (утро, день, вечер)?")
]

# Для отображения данных с понятными названиями
labels = {
    "name": "ФИО",
    "age": "Возраст",
    "height_weight": "Рост / вес",
    "contact": "Контакт",
    "training_goal": "Цель занятий",
    "chronic_diseases": "Хронические заболевания/травмы",
    "medications": "Лекарства",
    "surgeries": "Операции",
    "physical_activity_level": "Физическая активность",
    "bad_habits": "Вредные привычки",
    "preferred_training_time": "Предпочтительное время для занятий"
}

# Опции для вопросов с выбором
question_key_options = {
    "training_goal": ["Набор мышечной массы", "Снижение веса", "Улучшение выносливости", "Общая физическая форма", "Коррекция фигуры", "Другое"],
    "chronic_diseases": ["Да", "Нет"],
    "medications": ["Да", "Нет"],
    "surgeries": ["Да", "Нет"],
    "physical_activity_level": ["Сидячий", "Умеренный", "Высокий"],
    "bad_habits": ["Да", "Нет"],
    "preferred_training_time": ["Утро", "День", "Вечер"]
}

# Опции для вопроса "contact"
contact_options = ["Номер телефона", "Мессенджер"]

def create_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        chat_id INTEGER PRIMARY KEY,
        name TEXT,
        age TEXT,
        height_weight TEXT,
        contact TEXT,
        training_goal TEXT,
        chronic_diseases TEXT,
        medications TEXT,
        surgeries TEXT,
        physical_activity_level TEXT,
        bad_habits TEXT,
        preferred_training_time TEXT
    )
    ''')
    conn.commit()
    conn.close()

def save_user(chat_id, answers):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR REPLACE INTO users (
        chat_id, name, age, height_weight, contact,
        training_goal, chronic_diseases, medications, surgeries,
        physical_activity_level, bad_habits, preferred_training_time
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        chat_id,
        answers.get("name", ""),
        answers.get("age", ""),
        answers.get("height_weight", ""),
        answers.get("contact", ""),
        answers.get("training_goal", ""),
        answers.get("chronic_diseases", ""),
        answers.get("medications", ""),
        answers.get("surgeries", ""),
        answers.get("physical_activity_level", ""),
        answers.get("bad_habits", ""),
        answers.get("preferred_training_time", "")
    ))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    conn.close()
    return users

# Хранение состояний пользователей: номер вопроса, ответы и вспомогательные флаги
user_states = {}

@bot.message_handler(commands=['start'])
def start_message(message):
    chat_id = message.chat.id
    user_states[chat_id] = {"index": 0, "answers": {}}
    bot.send_message(chat_id, "Здравствуйте! Давайте заполним анкету!\n\n" + questions[0][1])

@bot.message_handler(commands=['view_users'])
def view_users(message):
    chat_id = message.chat.id
    users = get_all_users()
    if not users:
        bot.send_message(chat_id, "Пока нет пользователей.")
        return
    response = "Список пользователей:\n\n"
    for user in users:
        response += (
            f"ID: {user[0]}\n"
            f"ФИО: {user[1]}\n"
            f"Возраст: {user[2]}\n"
            f"Рост и вес: {user[3]}\n"
            f"Контакт: {user[4]}\n"
            f"Цель занятий: {user[5]}\n"
            f"Хронические заболевания/травмы: {user[6]}\n"
            f"Лекарства: {user[7]}\n"
            f"Операции: {user[8]}\n"
            f"Физическая активность: {user[9]}\n"
            f"Вредные привычки: {user[10]}\n"
            f"Время занятий: {user[11]}\n\n"
        )
    bot.send_message(chat_id, response)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    if chat_id not in user_states:
        bot.send_message(chat_id, "Напишите /start чтобы начать заполнение анкеты.")
        return

    state = user_states[chat_id]
    index = state["index"]
    current_key, _ = questions[index]

    # Обработка вопроса "contact" (двухшаговый выбор)
    if current_key == "contact":
        if "contact_choice" not in state:
            if message.text not in contact_options:
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
                markup.add(*contact_options)
                bot.send_message(chat_id, "Пожалуйста, выберите один из вариантов:", reply_markup=markup)
                return
            else:
                state["contact_choice"] = message.text
                if message.text == "Номер телефона":
                    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
                    button = types.KeyboardButton("Отправить номер", request_contact=True)
                    markup.add(button)
                    bot.send_message(chat_id, "Пожалуйста, отправьте ваш номер телефона", reply_markup=markup)
                    return  # ждём обработки контакта через handler для 'contact'
                else:
                    bot.send_message(chat_id, "Пожалуйста, введите ваш мессенджер (например, @username)")
                    return
        else:
            state["answers"]["contact"] = message.text.strip()
            del state["contact_choice"]
            state["index"] += 1
    else:
        state["answers"][current_key] = message.text.strip()
        # Если текущий вопрос training_goal и выбран вариант "Снижение веса" – отправляем видео
        if current_key == "training_goal" and message.text.strip() == "Снижение веса":
            try:
                with open("weight_loss_video.mp4", "rb") as video:
                    bot.send_video(chat_id, video, caption="Видео для снижения веса")
            except Exception as e:
                print(f"[ERROR] Не удалось отправить видео: {e}")
        state["index"] += 1

    # Переходим к следующему вопросу, если он есть
    if state["index"] < len(questions):
        next_key, next_text = questions[state["index"]]
        if next_key in question_key_options:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add(*question_key_options[next_key])
            bot.send_message(chat_id, next_text, reply_markup=markup)
        elif next_key == "contact":
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add(*contact_options)
            bot.send_message(chat_id, next_text, reply_markup=markup)
        else:
            bot.send_message(chat_id, next_text)
    else:
        try:
            save_user(chat_id, state["answers"])
            response = "Спасибо! Ваши данные получены:\n\n"
            for key, label in labels.items():
                response += f"{label}: {state['answers'].get(key, '')}\n"
            bot.send_message(chat_id, response)
            print(f"[INFO] Анкета от {chat_id} успешно сохранена.")
        except Exception as e:
            print(f"[ERROR] Ошибка при сохранении данных для {chat_id}: {e}")
            bot.send_message(chat_id, "Произошла ошибка при сохранении данных. Попробуйте снова позже.")
        finally:
            del user_states[chat_id]

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    chat_id = message.chat.id
    if chat_id not in user_states:
        return
    state = user_states[chat_id]
    if questions[state["index"]][0] == "contact" and state.get("contact_choice") == "Номер телефона":
        phone = message.contact.phone_number
        state["answers"]["contact"] = phone
        del state["contact_choice"]
        state["index"] += 1
        if state["index"] < len(questions):
            next_key, next_text = questions[state["index"]]
            if next_key in question_key_options:
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
                markup.add(*question_key_options[next_key])
                bot.send_message(chat_id, next_text, reply_markup=markup)
            elif next_key == "contact":
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
                markup.add(*contact_options)
                bot.send_message(chat_id, next_text, reply_markup=markup)
            else:
                bot.send_message(chat_id, next_text)
        else:
            try:
                save_user(chat_id, state["answers"])
                response = "Спасибо! Ваши данные получены:\n\n"
                for key, label in labels.items():
                    response += f"{label}: {state['answers'].get(key, '')}\n"
                bot.send_message(chat_id, response)
                print(f"[INFO] Анкета от {chat_id} успешно сохранена.")
            except Exception as e:
                print(f"[ERROR] Ошибка при сохранении данных для {chat_id}: {e}")
                bot.send_message(chat_id, "Произошла ошибка при сохранении данных. Попробуйте снова позже.")
            finally:
                del user_states[chat_id]

# --- Конец основного кода ---

create_db()

if __name__ == "__main__":
    # Настраиваем webhook, используя PUBLIC_URL из переменных окружения
    PUBLIC_URL = os.environ.get("PUBLIC_URL")
    if PUBLIC_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{PUBLIC_URL}/{TOKEN}")
    else:
        print("PUBLIC_URL не установлен. Webhook не будет настроен.")
    
    # Запускаем Flask-сервер. Render передает PORT через переменную окружения.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
