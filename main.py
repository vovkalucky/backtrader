from os.path import abspath # Функция дпя работы с путями
from datetime import datetime # Объект дпя работы со временем
from backtrader import Cerebro, Strategy, sizers, analyzers, OrderBase  # Компоненты
from backtrader.feeds import GenericCSVData # Основной class дпя CSV
# import matplotlib
# matplotlib.use('TkAgg')


class CandlesOnly(Strategy): #Наследуемся c1асса Strategy
    params = {
        "ExitCandles": 5 # через сколько дней выйдем из позиции
    }

    def __init__(self):
        # Инициализация стратегии и временных рядов
        # В self.data хранится временной ряд первого источника данных
        # Сокращаем внешний вид переменных с данными о свечах
        self.time = self.data.datetime  # Время свечей
        self.open = self.data.open  # Цены открытия
        self.close = self.data.close  # Цены закрытия
        self.high = self.data.high  # Цены максимума
        self.low = self.data.low  # Цены минимума
        self.volume = self.data.volume  # Объёмы
        self.order = None  # Храним ордер
        self.bar_executed = None
        self.win_trades = []  # Суммы прибыльных трейдов
        self.lose_trades = []  # Суммы убыточных трейдов

    def notify_order(self, order: OrderBase):
        # Срабатывает, когда изменяется статус ордера
        print("Cтaтyc ордера изменился", order.status)
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                print("Произошла заявка на покупку",order.executed.price)
                print("Оплаченные комиссии",order.executed.comm)
                self.bar_executed = len(self)
                print("Номер свечи на которой исполнилась покупка", self.bar_executed)
            elif order.issell():
                print("Произошла заявка на продажу",order.executed.price)
                print("Оплаченные комиссии",order.executed.comm)
        elif order.status in [order.Cancelled, order.Margin, order.Rejected]:
            print("order.Cancelled, order.Margin, order.Rejected")
        self.order = None

    def notify_trade(self, trade):
        # Срабатывает, когда произошел трейд
        #print("Произошел трейд", trade.pnl)  # Финальная сумма с трейда
        if trade.isclosed:
            if trade.pnlcomm > 0:
                self.win_trades.append(trade.pnlcomm)
                print("Profit", trade.pnlcomm)
            else:
                self.lose_trades.append(trade.pnlcomm)
                print("Loses", trade.pnlcomm)
            print()

    def next(self):
        if self.order:
            return
        if not self.position:
            is_buy = self.close[0] < self.close[-1] and self.close[-2]
            #is_buy = self.close[0] < self.close[-1] and self.close[-1] < self.close[-2]
            if is_buy:
                print("Make BUY!")
                self.order = self.buy()
        else:
            is_sell = len(self) - self.bar_executed >= self.params.ExitCandles  # ExitCandles
            if is_sell:
                print("END deal")
                self.order = self.sell()

    def stop(self):
        # Срабатывает после завершения бэктеста
        print("Результат бэктеста")
        print("Конечный капитал: ", self.broker.getvalue())
        print("Количество прибыльных сделок: ", len(self.win_trades))
        print("Количество убыточных сделок: ", len(self.lose_trades))
        all_trade_len = len(self.win_trades) + len(self.lose_trades)
        try:
            win_rate = (len(self.win_trades) / all_trade_len) * 100
        except:
            win_rate = 0
        try:
            max_win_trades = max(self.win_trades)
            max_lose_trades = max(self.lose_trades)
        except:
            max_win_trades = 0
            max_lose_trades = 0
        print("Bceгo сделок: ", all_trade_len)
        print("Коэффициент побед: ", win_rate)
        print("Максимальная прибыль: ", max_win_trades)
        print("Максимальный убыток: ", max_lose_trades)

class MyCSVData(GenericCSVData):
    # Подготовка источника свечных данных
    # MyCSVData - основной класс для загрузки СSV - файла
    params = {
                 "dtformat": "%Y-%m-%d %H:%M:%S",  # Формат времени для парсинга
                 "datetime": 0,
                 "open": 1,
                 "high": 2,
                 "low": 3,
                 "close": 4,
                 "volume": 5,
                 "openinterest": -1,  # -1 - это последний столбец
    }


csv_file_path = abspath("./data/BTCUSDT_60.csv")  # Путь к источнику данных
data = MyCSVData(
    dataname = csv_file_path,
    fromdate = datetime(2022, 1, 24),
    todate = datetime(2025, 8, 2),
    reverse = False)
# Подключение источника данных, аналитика и запуск бэктеста
cerebro = Cerebro()  # Создаём объект Церебро. Мозг Бэктрейдера
cerebro.adddata(data)  # Добавляем поток данных. Хранится в self.data
cerebro.addstrategy(CandlesOnly)  # Добавляем стратегию CandlesOnly
cerebro.broker.setcash(10000)  # стартовый баланс
cerebro.addsizer(sizers.FixedSize, stake=0.1)  # Размер позиции
cerebro.broker.setcommission(commission=0.0018)  # Комиссия брокера
cerebro.run()  # Запускаем бэктест
cerebro.plot(style="candle")  # Рисуем свечной график
cerebro.plot()