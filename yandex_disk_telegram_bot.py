import telebot
import requests
from pathlib import Path


def setup_method_telegram_token():
    file_path = Path('.').absolute().joinpath('token_telegram_bot.txt')
    with open(file_path, 'r') as file:
        return file.read().strip()


bot = telebot.TeleBot(setup_method_telegram_token())


def setup_method_yandex_headers():
    file_path = Path('.').absolute().joinpath('token_YandexDisk.txt')
    with open(file_path, 'r') as file:
        token = file.read().strip()
        headers = {
            'Authorization': f'OAuth {token}'
        }
        return headers


def create_folder_yandex_disk(message):
    path = message.text
    headers = setup_method_yandex_headers()
    response = requests.put(f'https://cloud-api.yandex.net/v1/disk/resources', 
                            headers=headers, 
                            params={'path': path})
    if response.status_code == 201:
        bot.send_message(message.chat.id, f'Папка {path} создана')
    elif response.status_code == 409:
        bot.send_message(message.chat.id, f'Папка {path} уже существует')
    else:
        bot.send_message(message.chat.id, f'Что-то пошло не так. Текст ошибки: {response.text}')


def delete_folder_yandex_disk(message):
    path = message.text
    headers = setup_method_yandex_headers()
    response = requests.delete(f'https://cloud-api.yandex.net/v1/disk/resources', 
                            headers=headers, 
                            params={'path': path,
                                    'permanently': 'true'})
    if response.status_code == 204:
        bot.send_message(message.chat.id, f'Папка {path} удалена')
    elif response.status_code == 404:
        bot.send_message(message.chat.id, f'Папка {path} не существует')
    else:
        bot.send_message(message.chat.id, f'Что-то пошло не так. Текст ошибки: {response.text}')


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 'Привет, я учебный бот!')
    bot.send_message(message.chat.id, 'Что будем делать?')


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, 'Я умею только отвечать на команды: /start, /help, /create_folder, /delete_folder')


@bot.message_handler(commands=['create_folder'])
def create_folder(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Введи название папки')
    bot.register_next_step_handler(message, create_folder_yandex_disk)


@bot.message_handler(commands=['delete_folder'])
def delete_folder(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Введи название папки')
    bot.register_next_step_handler(message, delete_folder_yandex_disk)



if __name__ == '__main__':
    print('Бот запущен')
    bot.polling()