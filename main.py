import telebot
from pathlib import Path
from telebot import types
from random import shuffle, choice
from telebot.handler_backends import State, StatesGroup
from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from time import sleep

from sqlalchemy import create_engine, Column, Integer, String, Text, Date, ForeignKey, func
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from models import Base, create_tables, drop_tables, fill_words, Users, Words, UserWords


DSN = 'postgresql://postgres:20145@localhost:5432/learning_English'
engine = create_engine(DSN)

Base = declarative_base()

Session = sessionmaker(bind = engine)
session = Session()



print('Телеграмм бот запускается...')

# Создает объект StateMemoryStorage для хранения состояний
state_storage = StateMemoryStorage()

def setup_method_telegram_token():
    file_path = Path('.').absolute().joinpath('token_telegram_bot.txt')
    with open(file_path, 'r') as file:
        return file.read().strip()


bot = telebot.TeleBot(setup_method_telegram_token(), state_storage=state_storage)


class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово 🔙'
    NEXT = 'Дальше ⏭'
    START = '/start'
    DEFAULT_BUTTONS = [types.KeyboardButton(item) for item in [ADD_WORD, DELETE_WORD, NEXT]]


class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()

def getting_other_words(message, data, markup):

    # Получение целевого слова из данных
    target_word = data['target_word']
    word = session.query(Words).filter(Words.target_word == target_word).first()


    # Получение других слов для вариантов ответа
    other_user_words = session.query(UserWords).filter(UserWords.user_id == message.from_user.id, word.id != UserWords.word_id).all()
    
    if len(other_user_words) < 3:
        markup.add(*Command.DEFAULT_BUTTONS)
        bot.send_message(message.chat.id, "В базе данных недостаточно слов для тренировки. Минимальное количество: 4.", reply_markup=markup)
        return
    
    other_words = [session.query(Words).filter(user_word.word_id == Words.id).first() for user_word in other_user_words[:3]]
    # print([f"{words_other.target_word} : {words_other.russian_word}" for words_other in other_words])


    # Заполнение списка вариантов ответа
    answers = [word.target_word] + [words_other.target_word for words_other in other_words]
    shuffle(answers)

    # Создание клавиатуры с вариантами ответа
    buttons = [types.KeyboardButton(answer) for answer in answers]
    buttons.extend(Command.DEFAULT_BUTTONS)
    markup.add(*buttons)

    bot.send_message(message.chat.id, f"Переведи слово: *{word.russian_word}*", 
                     reply_markup=markup, parse_mode='Markdown')
    # print(message.from_user)
    # print(f"{message.from_user.first_name} (Переведи слово: {word.russian_word}")
    
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = word.target_word
        data['translate_word'] = word.russian_word
        data['other_words'] = [other_word.target_word for other_word in other_words]


def get_random_word(message):
    
    # Создаем объект клавиатуры с изменяемым размером и 2 кнопками в ряд
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    global buttons
    buttons = []

    # Получаем слова для текущего пользователя
    user_words = session.query(UserWords).filter(UserWords.user_id == message.from_user.id).all()
    
    if not user_words:
        bot.send_message(message.chat.id, "В базе данных нет слов для тренировки.")
        return
    
    # Получаем рандомное слово для пользователя из таблицы UserWords
    random_user_word = choice(user_words)

    # Фильтруем и достаем слово из таблицы Words по id
    word = session.query(Words).filter(Words.id == random_user_word.word_id).first()
    print('word:', word)
    if not word:
        bot.send_message(message.chat.id, "В базе данных нет слов для тренировки.")
        return
    
    # Получение других слов для вариантов ответа
    getting_other_words(message, {"target_word": word.target_word, "translate_word": word.russian_word}, markup)



@bot.message_handler(commands=['cards', 'start'])
def start_bot(message):

    # Получаем пользователя из базы данных или создаем нового
    user = session.query(Users).filter(Users.id == message.from_user.id).first()
    # print(user, message.from_user.id)
    print(message)    
    if user is None:
        user = Users(
            id = message.from_user.id,
            username = message.from_user.username,
            first_name = message.from_user.first_name,
            last_name = message.from_user.last_name,
            chat_id = message.chat.id
        )
        session.add(user)
        session.commit()
        print(f"Пользователь {user.username}({user.id}) добавлен в базу данных")

        fill_words(session, user.id)

    # print('Сообщение', user.id, user.chat_id)
    
    bot.send_message(message.chat.id, f"Приветствую, {message.from_user.first_name} 🥳 \n\nПредлагаю сыграть в угадай слово 🤘 🤩")

    get_random_word(message)


@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    # Добавляем слово в базу данных
    bot.send_message(message.chat.id, f"Введите слово для добавления на английском:")
    bot.register_next_step_handler(message, process_add_word_step1)

def process_add_word_step1(message):
    # Получаем введенное слово на английском
    english_word = message.text.strip()
  
    # Запрашиваем следующий шаг - слово на русском
    bot.send_message(message.chat.id, f"Введите перевод слова '{english_word}' на русском:")
    bot.register_next_step_handler(message, process_add_word_step2, english_word)


def process_add_word_step2(message, english_word):
    # Получаем введенное слово на русском
    russian_word = message.text.strip()

    # Проверяем есть ли это слово в базе для текущего пользователя

    existing_word = session.query(UserWords).join(Words).filter(
        UserWords.user_id == message.from_user.id,
        Words.target_word == english_word
    ).first()


    if existing_word:
        bot.send_message(message.chat.id, f"Слово '{english_word}' уже есть в базе данных.")
    else:
        # Добавляем слово в базу данных
        new_word = Words(target_word=english_word, russian_word=russian_word)
        session.add(new_word)
        session.commit()
        
        # Связываем с текущим пользователем
        new_user_word = UserWords(user_id=message.from_user.id, word_id=new_word.id)
        session.add(new_user_word)
        session.commit()

        bot.send_message(message.chat.id, f"Слово '{english_word}' с переводом '{russian_word}' успешно добавлено в базу данных.")


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def handle_delete_word(message):
    # Получаем все слова пользователя
    user_words = session.query(UserWords).filter(UserWords.user_id == message.from_user.id).all()

    if not user_words:
        bot.send_message(message.chat.id, "В вашем списке слов нет слов для удаления.")
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        buttons = [types.KeyboardButton(word.word.target_word) for word in user_words]
        markup.add(*buttons)
        bot.send_message(message.chat.id, "Выберите слово для удаления:", reply_markup=markup)
        bot.register_next_step_handler(message, process_delete_word)


def process_delete_word(message):

    word_to_delete = message.text.strip()
    word = session.query(Words).join(UserWords).filter(
        UserWords.user_id == message.from_user.id,
        Words.target_word == word_to_delete
    ).first()

    user_word = session.query(UserWords).join(Words).filter(
        UserWords.user_id == message.from_user.id,
        Words.target_word == word_to_delete
    ).first()

    if word:
        session.delete(word)
        session.delete(user_word)
        session.commit()
        bot.send_message(message.chat.id, f"Слово '{word_to_delete}' успешно удалено из вашего списка слов.")
    else:
        bot.send_message(message.chat.id, f"Слово '{word_to_delete}' не найдено в вашем списке слов.")

    get_random_word(message)


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def handle_next_word(message):
    get_random_word(message)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    try:
        print(message.from_user.id, message.chat.id)

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            print('data:', data)
            print('message.text:', message.text, 'target_word:', data['target_word'])
            if message.text == data['target_word']:
                bot.send_message(message.chat.id, f'Правильно! 🎉')
                triger = 0
            elif message.text in data['other_words']:
                triger = 1
                bot.send_message(message.chat.id, f'Неправильно 😔 Попробуйте снова.')
                markup=types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                
        if triger == 0:
            get_random_word(message)
        elif triger == 1:
            getting_other_words(message, data, markup)

    except Exception as e:
        print(e)


session.close()


if __name__ == '__main__':
    bot.polling()

    