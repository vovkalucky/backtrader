from pybit.unified_trading import HTTP
from pprint import pprint
from datetime import datetime

intro = """
<<<---TickerGrub--->>>
Привет!
Я соберу исторические данные с Bybit
Затем упакую в CSV файл
Формат свечей: D1 (1000 свечей)
Формат тикеров:
BTCUSDT, LTCUSDT, ETHUSDT
>>>---TickerGrub---<<<
"""

# Глобальные переменные
ticker_name = ""
interval = "D"

# Создаём объект HTTP для работы с Bybit
session = HTTP(testnet=False)

def start_grub():
    global ticker_name, interval

    # Запрашиваем данные у Bybit
    get_candles = session.get_kline(
        category="linear",
        symbol=ticker_name,
        interval=interval,
        limit=2000
    )

    # Достаём список свечей
    candles = get_candles["result"]["list"]
    candles.reverse()  # Чтобы шли в хронологическом порядке

    # Имя CSV файла
    csv_file_name = ticker_name + "_" + interval + ".csv"
    first_row = "datetime,open,high,low,close,volume"

    with open(csv_file_name, mode="w", encoding="utf-8") as file:
        file.write(first_row + "\n")

        for candle in candles:
            # Преобразуем UNIX TIME → datetime
            unix_time = int(candle[0]) // 1000
            date_time = datetime.fromtimestamp(unix_time)

            # Формат для Backtrader (с часами, минутами, секундами)
            candle[0] = date_time.strftime("%Y-%m-%d %H:%M:%S")

            # Преобразуем список в строку
            candle_maped = map(str, candle[:6])  # Берём только datetime, O,H,L,C,V
            candle_join = ",".join(candle_maped)
            file.write(candle_join + "\n")
    print("✅ Данные сохранены в", csv_file_name)

def menu():
    global intro, ticker_name, interval
    print(intro)

    print("Введите 1 если хотите начать новый поиск: ")
    print("Введите 2 если хотите выйти: ")
    answer = input(">>> ")

    if answer == "1":
        ticker_name = input("Введи имя тикера: ")
        interval = input("Введи интервал (1, 5, 15, 60, D, W, M): ")
        start_grub()
        menu()
    elif answer == "2":
        print("Пока!")
        exit()
    else:
        print("Попробуй ещё раз")
        menu()

# Запуск
menu()
