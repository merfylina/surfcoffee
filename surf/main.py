import time
import traceback
import telebot
from telebot import types  # Добавляем импорт для работы с клавиатурой
from telebot.types import LabeledPrice, ShippingOption
from collections import defaultdict
from sber_payments import Client

from object import *
from config import *

bot = telebot.TeleBot(Api_bot_tg)
provider_token = Token_Sber

# Глобальные пермеменные ==================================================================================
str_done_order = "Сделать заказ  🌊"
selected_product = [] #список выбранных товаров
global products

prev_select_product = '' #предыдущие выбранные товары
price_all = 0 #цена
# ==========================================================================================================

# Админка и старт Старт ====================================================================================

# A function that processes the /start command
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    # Сохранение информации о пользователе в базе данных
    manager = UserManager(conn)  # Передаем объект session
    manager.register_user(user_id=user_id, username=username, first_name=first_name, role_user="user_role")  # Включаем user_id

    # Создаем клавиатуру с кнопкой "Сделать заказ"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_order = types.KeyboardButton(str_done_order)
    markup.add(button_order)

    # Отправляем сообщение с клавиатурой
    bot.send_message(message.chat.id, 'Ты зарегистрирован. Скорее заказывай кофе\nВ случае чего пиши сразу /help!', reply_markup=markup)

@bot.message_handler(commands=["admin"])
def admin_login(message):
    manager = UserManager(conn)  # Передаем объект sessio
    
    if manager.check_admin_role(message.from_user.id):

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button_create_pdf = types.KeyboardButton("Создать PDF файл")
        button_another_option = types.KeyboardButton("Создать JSON")
        button_exit = types.KeyboardButton("Выход")

        markup.add(button_create_pdf, button_another_option, button_exit)
        # Отправляем сообщение с клавиатурой
        bot.send_message(message.chat.id, 'Что делаем?', reply_markup=markup)
    else:
        bot.send_message(message.chat.id,'Ты НЕ админ')

@bot.message_handler(commands=["help"])
def help(message):
    message_user = '/start - Регистрация(Проходится один раз)\n/help - Вызов справки\n/list - Весь кофе\n'
    bot.send_message(message.chat.id, message_user, reply_markup=types.ReplyKeyboardRemove())
    # Удаляем клавиатуру после отправки сообщения
    
@bot.message_handler(commands=["list"])
def list_func(message):
    global products
    markup = types.InlineKeyboardMarkup(row_width=1)

    message_user = 'Список кофе ☕️:\n'
    
    managerProduct = ProductManager(conn)
    products = managerProduct.get_list()

    for product in products:
        button = types.InlineKeyboardButton(text=f'{product.id_product}: {product.price}₽\nОстаток: {product.count} уп.',
                                            callback_data=f'product_{product.id_product}')
        markup.add(button)
    button = types.InlineKeyboardButton(text=f'Закончить заказ ✅',callback_data=f'finish')
    markup.add(button)
    message_user += '\n(Цена указанна за одну упаковку)'
    
    bot.send_message(message.chat.id, message_user, reply_markup=markup)
    


# Админка и старт Конец ====================================================================================
@bot.message_handler(func=lambda message: message.text == str_done_order)
def make_order(message):

    global selected_product, products

    managerProduct = ProductManager(conn)
    products = managerProduct.get_list()

    markup = types.InlineKeyboardMarkup(row_width=1)

    message_user = 'Список кофе ☕️:\n'

    for product in products:
        button = types.InlineKeyboardButton(text=f'{product.id_product}: {product.price}₽\nОстаток: {product.count} уп.',
                                            callback_data=f'product_{product.id_product}')
        markup.add(button)
    
    button = types.InlineKeyboardButton(text=f'Закончить заказ ✅',callback_data=f'finish')

    markup.add(button)
    message_user += '\n(Цена указанна за одну упаковку)'
    
    bot.send_message(message.chat.id, message_user, reply_markup=markup)

def create_str_output_user(selected_products_func):
    formatted_strings = []

    for product in selected_products_func:
        formatted_string = f"{product['data']}: {product['count']} уп."
        formatted_strings.append(formatted_string)

    selected_product_cleaned = '\n'.join(formatted_strings)
    return selected_product_cleaned

@bot.callback_query_handler(func=lambda call: call.data == 'finish') #обрабатывает завершение заказа
def finish_order(call):
        global selected_product, price_all
        selected_product_cleaned = create_str_output_user(selected_product)
        if (price_all > 0):
            bot.send_message(call.message.chat.id, "Ваш заказ:\n" + selected_product_cleaned + "\nОбщая сумма: " + str(price_all) + "₽")

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button_yes = types.KeyboardButton("Оплатить 💳")
            #button_another_option = types.KeyboardButton("Изменить заказ 🤷")
            button_exit = types.KeyboardButton("Отменить заказ ❌")

            markup.add(button_yes, button_exit)
            bot.send_message(call.message.chat.id, "Все верно?", reply_markup=markup)
        else:
            bot.send_message(call.message.chat.id, "Вы ничего не выбрали 😔")

# эта нижняя часть кода отвечает за обработку выбора продукта через callback и запрос у пользователя ввода количества товара.
@bot.callback_query_handler(func=lambda call: call.data.startswith('product_'))
def handle_product_selection(call):
    global selected_product, prev_select_product

    # Извлекаем идентификатор продукта из callback_data
    product_id = call.data.replace('product_', '')
    prev_select_product = product_id

    # Вызываем функцию для ввода количества товара
    bot.send_message(call.message.chat.id, 'Введите количество товара', reply_markup=types.ReplyKeyboardRemove())

def group_objects(selected_product_func):
    # Используем defaultdict для группировки данных
    grouped_products = defaultdict(lambda: {'data': '', 'count': 0, 'price': 0.0})

    for product in selected_product_func:
        key = product['data']
        grouped_products[key]['data'] = product['data']
        grouped_products[key]['count'] += product['count']
        grouped_products[key]['price'] += product['price']

    # Преобразуем результат в список словарей
    grouped_product_list = list(grouped_products.values())

    result_list = []

    for product in grouped_product_list:
        result_list.append({"data": product['data'], "count": product['count'], "price": product['price']})

    return result_list

# Удалить повторяющиеся строки
@bot.message_handler(func=lambda message: message.text.isdigit())
def handle_quantity_selection(message):
    global selected_product, prev_select_product, price_all, products
     # Инициализация менеджера продуктов
    managerProduct = ProductManager(conn)
      # Получение списка продуктов
    products = managerProduct.get_list()
# Получение введенного пользователем количества товара
    quantity_str = message.text.strip()

     # Проверка, что строка не пуста
    if quantity_str:
        try: # Преобразование введенного количества в целое число
            quantity = int(quantity_str)
            # Меняем остаток
            for product in products:
                if product.id_product == prev_select_product:
                    old_count_data = product.count 
                    product.count -= quantity
                    if (product.count < 0):
                        #products = managerProduct.get_list()
                        product.count = old_count_data # Восстановление остатка при отрицательном количестве
                         # Получение обновленного списка продуктов
                        products = managerProduct.get_list()
                        bot.send_message(message.chat.id, f'Нет такого кол-во зерна ({quantity}) имеется: {old_count_data}.\nВыберите другой товар или введите число под остаток')
                        return make_order(message)
# Получение цены выбранного продукта
            price = managerProduct.get_price(prev_select_product)

            # Обновление общей стоимости заказа
            price_all += quantity * price

            # Добавление выбранного продукта к строке заказа
            selected_product.append({"data": prev_select_product, "count": quantity, "price": quantity * price})

            # Дополнительная обработка выбранного продукта (при необходимости)
            grouped_selected_product = group_objects(selected_product)
            # # Отправка подтверждающего сообщения
            bot.send_message(message.chat.id, f'Вы выбрали {quantity} уп. {prev_select_product}.\nЕще что-то🤔')

            # Обновление переменной selected_product
            selected_product = grouped_selected_product
              # Переход к созданию заказа
            make_order(message)
        except ValueError:
            # Обработка случая, когда преобразование в int не удалось
            bot.send_message(message.chat.id, 'Введите корректное количество товара')
    else: # Отправка сообщения об ошибке, если строка пуста
        bot.send_message(message.chat.id, 'Введите корректное количество товара')

# Обработчик сообщений для отмены заказа
@bot.message_handler(func=lambda message: message.text == "Отменить заказ ❌")
def order_exit(message):
    global selected_product, price_all, products
    # Возвращаем количество товара обратно на склад
    for selected_item in selected_product:
        product_id = selected_item['data']
        quantity = selected_item['count']
        for product in products:
            if product.id_product == product_id:
                product.count += quantity
                break
    
    # Обнуляем выбранные продукты и сумму
    selected_product = []
    price_all = 0
    # Инициализация менеджера продуктов
    managerProduct = ProductManager(conn)
      # Получение обновленного списка продуктов
    products = managerProduct.get_list()
    # Создаем клавиатуру с кнопкой "Сделать заказ"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_order = types.KeyboardButton(str_done_order)
    markup.add(button_order)
    
    bot.send_message(message.chat.id, 'А как же кофии? 🥺\n', reply_markup=markup)

# Обработчик сообщений для выхода из режима заказа
@bot.message_handler(func=lambda message: message.text == "Выход 🚪")
def exit(message):
    bot.send_message(message.chat.id,'Не забывай про наш сайт!\nhttps://www.surfcoffee.ru/')
    # Создаем клавиатуру с кнопкой "Сделать заказ"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_order = types.KeyboardButton(str_done_order)
    markup.add(button_order)
    # Отправляем сообщение с клавиатурой
    bot.send_message(message.chat.id, 'Ты снова с нами! Рады тебя видеть', reply_markup=markup)

# Обработчик сообщений для оплаты заказа
@bot.message_handler(func=lambda message: message.text == "Оплатить 💳")
def pay_order(message):
    global selected_product
    # Формирование списка цен для инвойса (здесь указана фиксированная цена за кофейные зерна и доставку)
    prices = [LabeledPrice(label='Кофейные зерна', amount=int(100 * price_all)), LabeledPrice('Доставка', 10000)]
    # Отправка инвойса с указанными параметрами
    bot.send_invoice(
                        message.chat.id,  #chat_id
                        'Кофейные зерна', #title
                        'Загляните в мир ароматного кофе с Surf Coffee! Наше приложение предлагает широкий ассортимент высококачественных кофейных зерен со всего мира. ', #invoice_payload
                         'HAPPY FRIDAYS COUPON', #invoice_payload
                        provider_token, #provider_token
                        'rub', #currency
                        prices, #prices
                        photo_url='https://34.img.avito.st/image/1/27TeIba_d12ohIVb5D6cpEuCcVdgQnOvbIJ1W2aEdV1qxA',
                        photo_height=512,  # !=0/None or picture won't be shown
                        photo_width=512,
                        photo_size=512,
                        is_flexible=False,  # True If you need to set up Shipping Fee
                        start_parameter='time-machine-example')  
    # Инициализация менеджера продуктов  
    managerProduct = ProductManager(conn)
     # Обновление остатков продуктов после оплаты
    for product in products:
        managerProduct.update_product_count(product.id_product, product.count)

        # Создаем клавиатуру с кнопкой "Сделать заказ"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_order = types.KeyboardButton(str_done_order)
    markup.add(button_order)

    bot.send_message(message.chat.id, 'Оплата прошла успешно, заказа едет к вам!',reply_markup=markup)

# Код на случай если реализовать дейсвтивительную оплату без тест api
# @bot.pre_checkout_query_handler(func=lambda query: True)
# def checkout(pre_checkout_query):
#     bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
#                                   error_message="Aliens tried to steal your card's CVV, but we successfully protected your credentials,"
#                                                 " try to pay again in a few minutes, we need a small rest.")


# @bot.message_handler(content_types=['successful_payment'])
# def got_payment(message):
#     bot.send_message(message.chat.id,
#                      'Hoooooray! Thanks for payment! We will proceed your order for `{} {}` as fast as possible! '
#                      'Stay in touch.\n\nUse /buy again to get a Time Machine for your friend!'.format(
#                          message.successful_payment.total_amount / 100, message.successful_payment.currency),
#                      parse_mode='Markdown')

#После выполнения этой команды, бот начнет постоянно опрашивать серверы Telegram 
#на предмет новых событий, таких как входящие сообщения или обновления, 
#и будет обрабатывать их согласно заданным обработчикам 
bot.infinity_polling(skip_pending = True) 

# Функция для запуска бота
def start_bot():
    try: # Вывод сообщения о старте бота
        print("Bot started")
        bot.polling(none_stop=True, interval=0) # Запуск опроса серверов Telegram 
    except Exception as e: # Обработка исключения при возникновении ошибки
        traceback_error_string = traceback.format_exc()
        with open("Error.Log", "a") as myfile: # Запись информации об ошибке в файл "Error.Log"
            myfile.write("\r\n\r\n" + time.strftime("%c") + "\r\n<<ERROR polling>>\r\n" + str(e) + "\r\n" + traceback_error_string + "\r\n<<ERROR polling>>")
        bot.stop_polling() # Остановка опроса серверов Telegram
        time.sleep(15) # Пауза на 15 секунд
        start_bot() # Рекурсивный вызов функции для повторного запуска бота после паузы


# Start Bot
if __name__ == "__main__":
    start_bot()
