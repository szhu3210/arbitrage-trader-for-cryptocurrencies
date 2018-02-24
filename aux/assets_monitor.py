import logging
from client import poloniex_client
from client import huobi_pro_client
from config import config_coin, config_trader
from multiprocessing import Pool
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=logging.WARNING)


class AssetsMonitor:

    @staticmethod
    def cal_assets(balances):

        res = {}

        for market in balances:
            for currency in balances[market]:
                res[currency] = \
                    balances[market][currency] if currency not in res else \
                    '%.8f' % (float(res[currency]) + float(balances[market][currency]))

        return res

    def get_assets(self):
        return self.cal_assets(self.get_balances_mp())

    @staticmethod
    def cal_profits(assets_old=None, assets_new=None):

        res = {}

        for currency in assets_new:
            res[currency] = '%.8f' % (float(assets_new[currency]) - float(assets_old[currency]))

        prices = poloniex_client.PoloniexClient().returnTicker()
        usdt_equ = 0
        for currency in res:
            if currency != 'USDT':
                pair = 'USDT_' + config_coin.currency_name_standard_to_poloniex(currency.upper())
                usdt_equ += float(res[currency]) * float(prices[pair]['last'])
            else:
                usdt_equ += float(res[currency])
        res['usdt_equ'] = '%.2f' % usdt_equ

        return res

    @staticmethod
    def get_balance(market='', include_frozen=True):

        """
        Get balance of a market and format it into dict
        :param market: market_name, in market_list in config_trader
        :param include_frozen: boolean
        :return: dict, {currency: string, standard}
        """

        res = {}

        if market == 'poloniex':
            balances = poloniex_client.PoloniexClient().get_balances()
            for currency in config_coin.currency_list[market]:
                currency_standard = config_coin.to_standard(market, currency)
                res[currency_standard] = balances[currency]
            return res

        if market == 'huobi_pro':
            balances = huobi_pro_client.HuobiProClient().get_balance()[0]['list']
            for balance in balances:
                # print(balance)
                currency = balance['currency'].upper()
                amount = '%.8f' % float(balance['balance'])
                if currency in config_coin.currency_list[market]:
                    if include_frozen:
                        res[currency] = amount if currency not in res else \
                            '%.8f' % (float(res[currency]) + float(amount))
                    else:
                        if balance['type'] == 'trade':
                            res[currency] = amount
            return res

    def get_balances_mp(self, include_frozen=True):

        """
        Get balances of all markets and currencies, only have those shown in the config_coin.
        :param include_frozen: boolean, default=True, if include frozen balance
        :return: dict[market_name][currency]
        """

        balances = dict()

        pool = Pool()

        for market in config_trader.market_list:
            balances[market] = pool.apply_async(self.get_balance,
                                                kwds={'market': market, 'include_frozen': include_frozen})

        pool.close()
        pool.join()

        for market in balances:
            balances[market] = balances[market].get()

        return balances


if __name__ == '__main__':
    pass
    # c = {}
    # for currency in config_coin.currency_list['standard']:
    #     c[currency] = '0.0'
    a = AssetsMonitor()
    b = a.get_assets()
    print(b)
    # c = a.cal_profits(b, b)
    # print(c)
