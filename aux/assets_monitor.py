import logging
import asyncio
from client import unified_client
from config import config_coin, config_trader
from multiprocessing import Pool
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=logging.WARNING)


class AssetsMonitor:

    def __init__(self):
        pass

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
        # return self.cal_assets(self.get_balances())
        return self.cal_assets(self.get_balances_async())

    @staticmethod
    def cal_usdt_equivalent(balance, limited=True):

        res = {}

        for currency in balance:
            if not limited or currency in config_coin.currency_list['standard']:
                res[currency] = '%.8f' % float(balance[currency])

        prices = unified_client.UnifiedClient(config_trader.market_fetch_ticker).get_tickers()
        usdt_equ = 0
        for currency in res:
            if float(res[currency]) > 0:
                if currency != 'USDT':
                    pair = currency.upper() + '/USDT'
                    usdt_equ += float(res[currency]) * float(prices[pair])
                else:
                    usdt_equ += float(res[currency])
        res['usdt_equ'] = '%.2f' % usdt_equ

        return res

    @staticmethod
    def cal_profits(assets_old=None, assets_new=None, limited=True):

        res = {}

        for currency in assets_new:
            if not limited or currency in config_coin.currency_list['standard']:
                res[currency] = '%.8f' % (float(assets_new[currency]) - float(assets_old[currency]))

        prices = unified_client.UnifiedClient(config_trader.market_fetch_ticker).get_tickers()
        usdt_equ = 0
        for currency in res:
            if currency != 'USDT':
                pair = currency.upper() + '/USDT'
                usdt_equ += float(res[currency]) * float(prices[pair])
            else:
                usdt_equ += float(res[currency])
        res['usdt_equ'] = '%.2f' % usdt_equ

        return res

    @staticmethod
    def get_balance(market='', include_frozen=True):

        res = unified_client.UnifiedClient(market).get_balances(all_currency=include_frozen)
        res['market'] = market
        return res

    @staticmethod
    async def get_balance_async(market='', include_frozen=True):

        res = await unified_client.UnifiedClient(market, True).get_balances_async(all_currency=include_frozen)
        res['market'] = market
        return res

    def get_balances_mp(self, include_frozen=True):

        """
        Get balances of all markets and currencies, only have those shown in the config_coin.
        :param include_frozen: boolean, default=True, if include frozen balance
        :return: dict[market_name][currency]
        """

        balances = dict()

        pool = Pool(len(config_trader.market_list))

        for market in config_trader.market_list:
            balances[market] = pool.apply_async(self.get_balance,
                                                kwds={'market': market, 'include_frozen': include_frozen})

        pool.close()
        pool.join()

        for market in balances:
            balances[market] = balances[market].get()

        pool.terminate()

        return balances

    def get_balances_async(self, include_frozen=True):

        res = {}

        tasks = []

        for market in config_trader.market_list:
            task = asyncio.ensure_future(self.get_balance_async(market, include_frozen))
            tasks.append(task)

        loop = asyncio.get_event_loop()
        done, pending = loop.run_until_complete(asyncio.wait(tasks))
        results = [future.result() for future in done]
        # print(results)
        # print(res)

        subres = {}
        failed = []

        for result in results:
            if isinstance(result, dict):
                res[result['market']] = result
                del res[result['market']]['market']

        # print(res)

        # print(res)
        for market in res:
            if not isinstance(res[market], dict):
                failed.append(market)
            else:
                subres[market] = res[market]

        # logging.warning(res)
        logging.info(subres)
        logging.info('Getting balances: %d/%d success. Failed ones: %s' % (len(subres), len(res), failed))

        # loop.close()

        return subres

    def get_balances(self, include_frozen=True):

        res = {}

        for market in config_trader.market_list:
            res[market] = self.get_balance(market, include_frozen)

        return res

    @staticmethod
    def print_assets(balances):
        for market in balances:
            print(market + ': \t' + ''.join(
                [(currency + ': ' + balances[market][currency] + '\t') for currency in
                 config_coin.currency_list['standard']]))


if __name__ == '__main__':
    pass
    # c = {}
    # for currency in config_coin.currency_list['standard']:
    #     c[currency] = '0.0'
    a = AssetsMonitor()
    # print(a.get_balance('huobipro'))
    print(a.get_balances())
    print(a.get_balances_async())
    # print(a.get_balances())
    # print(a.get_balances())
    # print(a.get_assets())
    # a.print_assets(a.get_balances_async())
    # c = a.cal_profits(b, b)
    # print(c)
    # print(a.cal_usdt_equivalent(a.get_balance('huobipro')))
    # print(a.cal_usdt_equivalent(a.get_balance('poloniex')))
