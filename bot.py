import telebot
import config
from api import get_users

bot = telebot.TeleBot(config.BOT_TOKEN)


@bot.message_handler(commands=['start'])
def start_message(message):
    photo = open('media/hello.png', 'rb')

    if message.from_user.id == config.ADMIN_ID:
        text = (f'Привет, {message.from_user.first_name}. '
                f'Ты админ, выбери нужную опцию!')
        markup = telebot.types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)

        btn1 = telebot.types.KeyboardButton('Узнать уровень')
        btn2 = telebot.types.KeyboardButton('Админка')
        markup.add(btn1, btn2)

        bot.send_message(message.chat.id, text, reply_markup=markup)
        bot.send_photo(message.chat.id, photo)

    else:
        text = f'Привет, {message.from_user.first_name}, узнай за 5 минут свой уровень английского!'
        markup = telebot.types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)

        btn1 = telebot.types.KeyboardButton('Узнать уровень')
        markup.add(btn1)

        bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(regexp='Админка')
def admin_panel(message):
    btn1 = telebot.types.KeyboardButton('Пользователи')
    markup = telebot.types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    markup.add(btn1)

    text = 'Выбери нужную опцию:'

    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(regexp='Пользователи')
def get_users(message):
    users = get_users()
    text = f'Пользователи: {users}'

    btn1 = telebot.types.KeyboardButton('Назад')
    markup = telebot.types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    markup.add(btn1)

    bot.send_message(message.chat.id, text, reply_markup=markup)



@bot.message_handler(regexp='Узнать уровень')
def check_level(message):
    pass


bot.infinity_polling()