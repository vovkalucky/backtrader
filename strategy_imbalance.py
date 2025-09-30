from os.path import abspath
from datetime import datetime
from backtrader import Cerebro, Strategy, sizers, analyzers, OrderBase
from backtrader.feeds import GenericCSVData

class ImbalanceStrategy(Strategy):
    """Стратегия торговли на медвежьем имбалансе"""
    params = {
        "imbalance": 0.7,
        "profit": 0.7,
        "stop_loss": 2.0,
        "take_profit": 1.5,
        "debug": True  # Режим отладки
    }

    def __init__(self):
        self.time = self.data.datetime
        self.open = self.data.open
        self.close = self.data.close
        self.high = self.data.high
        self.low = self.data.low
        self.volume = self.data.volume

        self.order = None
        self.entry_price = None
        self.win_trades = []
        self.lose_trades = []
        self.checks_counter = 0  # Счетчик проверок
        self.condition_stats = {
            'condition_0': 0,
            'condition_1': 0,
            'condition_2': 0,
            'all_conditions': 0
        }

    def find_bear_imbalance(self):
        """Поиск медвежьего имбаланса на последних 4 свечах"""
        if len(self) < 4:
            return False

        self.checks_counter += 1

        # Получаем данные
        third_imb_kline = self.low[-3]
        second_imb_kline = self.low[-2]
        first_imb_kline = self.high[-1]
        current_kline = self.close[0]

        # Вычисляем условия
        condition_0 = second_imb_kline < third_imb_kline
        condition_1 = (first_imb_kline - current_kline) / first_imb_kline > self.params.profit / 100
        condition_2 = (third_imb_kline - first_imb_kline) / third_imb_kline > self.params.imbalance / 100

        # Статистика условий
        if condition_0:
            self.condition_stats['condition_0'] += 1
        if condition_1:
            self.condition_stats['condition_1'] += 1
        if condition_2:
            self.condition_stats['condition_2'] += 1

        # Отладочный вывод каждые 100 свечей
        if self.params.debug and self.checks_counter % 100 == 0:
            imbalance_gap = ((third_imb_kline - first_imb_kline) / third_imb_kline * 100) if third_imb_kline > 0 else 0
            profit_gap = ((first_imb_kline - current_kline) / first_imb_kline * 100) if first_imb_kline > 0 else 0

            print(f"\n📊 Check #{self.checks_counter} | Date: {self.time.datetime(0)}")
            print(f"   Third Low[-3]: {third_imb_kline:.2f}")
            print(f"   Second Low[-2]: {second_imb_kline:.2f}")
            print(f"   First High[-1]: {first_imb_kline:.2f}")
            print(f"   Current Close[0]: {current_kline:.2f}")
            print(f"   Condition 0 (second < third): {condition_0} | {second_imb_kline:.2f} < {third_imb_kline:.2f}")
            print(f"   Condition 1 (profit > {self.params.profit}%): {condition_1} | Gap: {profit_gap:.2f}%")
            print(f"   Condition 2 (imbalance > {self.params.imbalance}%): {condition_2} | Gap: {imbalance_gap:.2f}%")

        if all([condition_0, condition_1, condition_2]):
            self.condition_stats['all_conditions'] += 1
            imbalance_gap = ((third_imb_kline - first_imb_kline) / third_imb_kline * 100)
            profit_gap = ((first_imb_kline - current_kline) / first_imb_kline * 100)

            print(f"\n✅✅✅ Bear Imbalance found! Date: {self.time.datetime(0)}")
            print(f"   Third Low[-3]: {third_imb_kline:.2f}")
            print(f"   Second Low[-2]: {second_imb_kline:.2f}")
            print(f"   First High[-1]: {first_imb_kline:.2f}")
            print(f"   Current Close[0]: {current_kline:.2f}")
            print(f"   Imbalance Gap: {imbalance_gap:.2f}%")
            print(f"   Profit Gap: {profit_gap:.2f}%")
            return True

        return False

    def notify_order(self, order: OrderBase):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.issell():
                self.entry_price = order.executed.price
                print(f"\n🔴 SHORT opened at {order.executed.price:.2f}")
                print(f"   Commission: {order.executed.comm:.2f}")
                print(f"   Stop Loss: {self.entry_price * (1 + self.params.stop_loss / 100):.2f}")
                print(f"   Take Profit: {self.entry_price * (1 - self.params.take_profit / 100):.2f}")
            elif order.isbuy():
                print(f"🟢 SHORT closed at {order.executed.price:.2f}")
                print(f"   Commission: {order.executed.comm:.2f}")

        elif order.status in [order.Cancelled, order.Margin, order.Rejected]:
            print(f"⚠️ Order cancelled/rejected: {order.status}")

        self.order = None

    def notify_trade(self, trade):
        if trade.isclosed:
            pnl_percent = (trade.pnlcomm / self.entry_price) * 100 if self.entry_price else 0

            if trade.pnlcomm > 0:
                self.win_trades.append(trade.pnlcomm)
                print(f"💰 Profit: {trade.pnlcomm:.2f} ({pnl_percent:.2f}%)")
            else:
                self.lose_trades.append(trade.pnlcomm)
                print(f"📉 Loss: {trade.pnlcomm:.2f} ({pnl_percent:.2f}%)")
            print()

    def next(self):
        if self.order:
            return

        if not self.position:
            if self.find_bear_imbalance():
                print(f"📊 Opening SHORT position")
                self.order = self.sell()
        else:
            current_price = self.close[0]

            if current_price >= self.entry_price * (1 + self.params.stop_loss / 100):
                print(f"🛑 Stop Loss triggered at {current_price:.2f}")
                self.order = self.buy()
            elif current_price <= self.entry_price * (1 - self.params.take_profit / 100):
                print(f"🎯 Take Profit triggered at {current_price:.2f}")
                self.order = self.buy()

    def stop(self):
        print("\n" + "=" * 60)
        print("📊 РЕЗУЛЬТАТЫ БЭКТЕСТА")
        print("=" * 60)
        print(f"Конечный капитал: ${self.broker.getvalue():.2f}")
        print(f"Прибыльных сделок: {len(self.win_trades)}")
        print(f"Убыточных сделок: {len(self.lose_trades)}")
        # Статистика проверок условий
        print("\n📈 СТАТИСТИКА УСЛОВИЙ:")
        print(f"Всего проверок: {self.checks_counter}")
        print(
            f"Condition 0 (second < third) выполнено: {self.condition_stats['condition_0']} раз ({self.condition_stats['condition_0'] / self.checks_counter * 100:.2f}%)")
        print(
            f"Condition 1 (profit > {self.params.profit}%) выполнено: {self.condition_stats['condition_1']} раз ({self.condition_stats['condition_1'] / self.checks_counter * 100:.2f}%)")
        print(
            f"Condition 2 (imbalance > {self.params.imbalance}%) выполнено: {self.condition_stats['condition_2']} раз ({self.condition_stats['condition_2'] / self.checks_counter * 100:.2f}%)")
        print(
            f"Все условия одновременно: {self.condition_stats['all_conditions']} раз ({self.condition_stats['all_conditions'] / self.checks_counter * 100:.2f}%)")

        all_trade_len = len(self.win_trades) + len(self.lose_trades)

        if all_trade_len > 0:
            win_rate = (len(self.win_trades) / all_trade_len) * 100
            total_profit = sum(self.win_trades)
            total_loss = sum(self.lose_trades)
            net_profit = total_profit + total_loss

            print(f"\n💼 ТОРГОВАЯ СТАТИСТИКА:")
            print(f"Всего сделок: {all_trade_len}")
            print(f"Коэффициент побед: {win_rate:.2f}%")

            if self.win_trades:
                max_win = max(self.win_trades)
            try:
                avg_win = total_profit / len(self.win_trades)
            except:
                avg_win = 0
            print(f"Максимальная прибыль: ${max_win:.2f}")
            print(f"Средняя прибыль: ${avg_win:.2f}")

            if self.lose_trades:
                max_lose = min(self.lose_trades)
                try:
                    avg_lose = total_loss / len(self.lose_trades)
                except ZeroDivisionError:
                    avg_lose = 0
            else:
                max_lose = 0
                avg_lose = 0

            print(f"Максимальный убыток: ${max_lose:.2f}")
            print(f"Средний убыток: ${avg_lose:.2f}")

            print(f"\n💰 ФИНАНСОВЫЕ ПОКАЗАТЕЛИ:")
            print(f"Общая прибыль: ${total_profit:.2f}")

            print(f"Общий убыток: ${total_loss:.2f}")
            print(f"Чистая прибыль: ${net_profit:.2f}")

            if self.win_trades and self.lose_trades:
                profit_factor = abs(total_profit / total_loss)
                print(f"Profit Factor: {profit_factor:.2f}")
        else:
            print("\n⚠️ Сделок не было")
            print("\n💡 РЕКОМЕНДАЦИИ:")
            print("   1. Уменьшите параметры imbalance и profit")
            print("   2. Проверьте данные в CSV файле")
            print("   3. Измените временной период")

            print("=" * 60)

class MyCSVData(GenericCSVData):
    """Класс для загрузки CSV файла"""
    params = {
        "dtformat": "%Y-%m-%d %H:%M:%S",
        "datetime": 0,
        "open": 1,
        "high": 2,
        "low": 3,
        "close": 4,
        "volume": 5,
        "openinterest": -1,
    }

if __name__ == "__main__":
    # Путь к CSV файлу
    csv_file_path = abspath("./data/BTCUSDT_15.csv")

    # Загрузка данных
    data = MyCSVData(
        dataname=csv_file_path,
        fromdate=datetime(2022, 1, 1),
        todate=datetime(2025, 10, 1),
        reverse=False
    )

    # Создание и настройка Cerebro
    cerebro = Cerebro()
    cerebro.adddata(data)

    # Параметры стратегии (попробуйте уменьшить для
    cerebro.addstrategy(ImbalanceStrategy,
                        imbalance=0.5,  # Уменьшен с 0.7 до 0.5
                        profit=0.5,  # Уменьшен с 0.7 до 0.5
                        stop_loss=2.0,
                        take_profit=1.5,
                        debug=True)  # Включена отладка

    cerebro.broker.setcash(10000)  # Стартовый баланс
    cerebro.addsizer(sizers.FixedSize, stake=0.1)  # Размер позиции
    cerebro.broker.setcommission(commission=0.0018)  # Комиссия

    # Добавление аналитики
    cerebro.addanalyzer(analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(analyzers.TradeAnalyzer, _name='trades')

    print(f"\n🚀 Начальный капитал: ${cerebro.broker.getvalue():.2f}")
    print(f"📅 Период: 2022-01-24 до 2025-08-02")
    print(f"⚙️ Параметры:")
    print(f"   - Imbalance: 0.5%")
    print(f"   - Profit: 0.5%")
    print(f"   - Stop Loss: 2.0%")
    print(f"   - Take Profit: 1.5%")

    # Запуск бэктеста
    results = cerebro.run()

    # Дополнительная аналитика
    strat = results[0]

    print("\n📊 ДОПОЛНИТЕЛЬНАЯ АНАЛИТИКА:")

    if hasattr(strat.analyzers, 'sharpe'):
        sharpe = strat.analyzers.sharpe.get_analysis().get('sharperatio', None)
        print(f"Sharpe Ratio: {sharpe if sharpe else 'N/A'}")

    if hasattr(strat.analyzers, 'drawdown'):
        dd = strat.analyzers.drawdown.get_analysis()
        max_dd = dd.get('max', {}).get('drawdown', 0)
        print(f"Max Drawdown: {max_dd:.2f}%")

    if hasattr(strat.analyzers, 'trades'):
        trades = strat.analyzers.trades.get_analysis()
        print(f"Total Trades: {trades.get('total', {}).get('total', 0)}")
        print(f"Won Trades: {trades.get('won', {}).get('total', 0)}")
        print(f"Lost Trades: {trades.get('lost', {}).get('total', 0)}")

    # Построение графика
    try:
        cerebro.plot(style="candle")
    except Exception as e:
        print(f"\n⚠️ Ошибка при построении графика: {e}")

        # cerebro.addstrategy(ImbalanceStrategy,
        #                     imbalance=0.3,  # Еще меньше
        #                     profit=0.3,  # Еще меньше
        #                     stop_loss=3.0,
        #                     take_profit=2.0,
        #                     debug=True)