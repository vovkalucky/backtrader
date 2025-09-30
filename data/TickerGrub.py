from pybit.unified_trading import HTTP
from pprint import pprint
from datetime import datetime

intro = """
<<<---TickerGrub--->>>
Привет!
Я соберу исторические данные с Bybit
Затем упакую в CSV файл
Формат тикеров:
BTCUSDT, LTCUSDT, ETHUSDT
Интервалы:
1, 3, 5, 15, 30, 60, 120, 240, 360, 720, D, W, M
>>>---TickerGrub---<<<
"""

# Глобальные переменные
ticker_name = ""
interval = "D"

# Создаём объект HTTP для работы с Bybit
session = HTTP(testnet=False)


def start_grub():
    global ticker_name, interval

    all_candles = []
    # начнем "сдалека", например 2017-01-01
    start_time = int(datetime(2022, 1, 1).timestamp())

    while True:
        get_candles = session.get_kline(
            category="spot",
            symbol=ticker_name,
            interval=interval,
            start=start_time * 1000,  # API ждёт миллисекунды
            limit=1000
        )

        candles = get_candles["result"]["list"]
        if not candles:
            break  # данных больше нет → останавливаемся

        candles.reverse()  # хронологический порядок
        all_candles.extend(candles)

        # берём последнюю свечу и ставим время +1 секунда
        last_time = int(candles[-1][0]) // 1000
        start_time = last_time + 1

        # Если меньше 1000 пришло → значит дошли до "конца истории"
        if len(candles) < 1000:
            break

    # сохраняем в CSV
    csv_file_name = f"{ticker_name}_{interval}.csv"
    first_row = "datetime,open,high,low,close,volume"

    with open(csv_file_name, mode="w", encoding="utf-8") as file:
        file.write(first_row + "\n")

        for candle in all_candles:
            unix_time = int(candle[0]) // 1000
            date_time = datetime.fromtimestamp(unix_time)
            candle[0] = date_time.strftime("%Y-%m-%d %H:%M:%S")

            candle_maped = map(str, candle[:6])
            candle_join = ",".join(candle_maped)
            file.write(candle_join + "\n")

    print(f"✅ Данные сохранены в {csv_file_name}")
    print(f"📊 Всего собрано свечей: {len(all_candles)}")


def menu():
    global intro, ticker_name, interval
    print(intro)

    print("Введите 1 если хотите начать новый поиск: ")
    print("Введите 2 если хотите выйти: ")
    answer = input(">>> ")

    if answer == "1":
        ticker_name = input("Введи имя тикера (например BTCUSDT): ").upper()
        interval = input("Введи интервал (1, 5, 15, 60, D, W, M): ").upper()
        start_grub()
        menu()
    elif answer == "2":
        print("Пока!")
        exit()
    else:
        print("Попробуй ещё раз")
        menu()


# Запуск
if __name__ == "__main__":
    menu()
