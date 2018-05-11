import logging
import time
from config import config_trader, config_coin, api_keys
import ccxt
import ccxt.async
import asyncio

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=logging.WARNING)

# A unified client to link my program to ccxt
# Above this interface there should not be any market specific codes

market_order_detail_type_1 = ['huobipro', 'okex']


class UnifiedClient:

    def __init__(self, market_name, async=False):
        self.client = eval(('ccxt.' if not async else 'ccxt.async.') + market_name)({
            'apiKey': api_keys.keys[market_name]['access'],
            'secret': api_keys.keys[market_name]['secret'],
            'nonce': ccxt.Exchange.microseconds,
            # 'verbose': True,
        })

    def get_tickers(self, async=False):
        if async:
            return self.get_tickers_async()
        tickers = self.client.fetch_tickers()
        res = {}
        for symbol in tickers:
            res[symbol] = '%.8f' % tickers[symbol]['last']
        return res

    async def get_tickers_async(self):
        tickers = await self.client.fetch_tickers()
        res = {}
        for symbol in tickers:
            res[symbol] = '%.8f' % tickers[symbol]['last']
        return res

    def get_balances(self, all_currency=True, ignore_zero=False, limited=True):
        try_count = 0
        while try_count < 5:
            try:
                balances = self.client.fetch_total_balance() if all_currency else self.client.fetch_free_balance()
                res = {}
                for currency in balances:
                    if (not limited or currency in config_coin.currency_list['standard']) \
                            and (not ignore_zero or float(balances[currency]) > 0):
                        res[currency] = '%.8f' % balances[currency]
                return res
            except BaseException as err:
                logging.warning('Error occurred in get_balances: %s. Try again.' % err)
        raise BaseException('Error in get_balances. Have tried 5 times.')

    async def get_balances_async(self, all_currency=True, ignore_zero=False, limited=True):
        balances = (await self.client.fetch_total_balance()) \
            if all_currency else (await self.client.fetch_free_balance())
        res = {}
        for currency in balances:
            if (not limited or currency in config_coin.currency_list['standard']) \
                    and (not ignore_zero or float(balances[currency]) > 0):
                res[currency] = '%.8f' % balances[currency]
        return res

    def get_balance(self, currency):
        return self.get_balances()[currency]

    def get_available_balances(self):
        res = {}
        balances = self.get_balances()
        for c in balances:
            if float(balances[c]) != 0:
                res[c] = balances[c]
        return res

    def print_available_balances(self):
        balances = self.get_balances()
        for c in balances:
            if float(balances[c]) != 0:
                logging.warning('%5s  %10s' % (c, balances[c]))

    def cal_buy_price(self, currency_pair, size, async=False):
        if async:
            return self.cal_buy_price_async(currency_pair, size)
        size = float(size)
        asks = self.client.fetch_order_book(currency_pair)['asks']
        # logging.warning(asks)
        total = 0
        rest = size
        price_range = []
        for ask in asks:
            price_s, volume_s = ask
            price, volume = map(float, ask)
            if volume > rest:
                total += price*rest
                price_range.append([price_s, rest])
                rest = 0
                break
            total += price*volume
            rest -= volume
            price_range.append(ask)
        status = (rest <= 0)
        return status, '%.8f' % (total/size), price_range

    async def cal_buy_price_async(self, currency_pair, size):
        size = float(size)
        asks = await self.client.fetch_order_book(currency_pair)
        asks = asks['asks']
        # logging.warning(asks)
        total = 0
        rest = size
        price_range = []
        for ask in asks:
            price_s, volume_s = ask
            price, volume = map(float, ask)
            if volume > rest:
                total += price*rest
                price_range.append([price_s, rest])
                rest = 0
                break
            total += price*volume
            rest -= volume
            price_range.append(ask)
        status = (rest <= 0)
        return status, '%.8f' % (total/size), price_range

    def buy_coin(self, base_currency, quote_currency, amount):

        """
        Buy coin according to the market.
        :param base_currency: string, uppercase
        :param quote_currency: string, uppercase
        :param amount: string
        :return: None
        """

        currency_pair = base_currency + '/' + quote_currency

        balance_quote_currency = self.get_balance(quote_currency)

        # reserve enough market space
        market_available, avg_price, price_range = self.cal_buy_price(currency_pair, float(amount) * 2)

        # buy price, raise 5 % limit to ensure trade success
        price = '%.8f' % (float(price_range[-1][0]) * 1.08)

        # check balance of quote currency
        if float(balance_quote_currency) > float(price)*float(amount)*1.01:

            # check market status (if it is big enough for this order)
            if market_available:

                logging.warning('Buying %s: amount = %s, price = %s, total = %.6f' %
                                (base_currency, amount, price, float(price)*float(amount)))
                order_detail = self.client.create_order(currency_pair, 'limit', 'buy', float(amount), price=price)
                # print(order_detail)
                if self.client.id in market_order_detail_type_1:
                    time.sleep(1.0)
                    deal_amount = '0.0'
                    orders = self.client.fetch_orders(symbol=currency_pair, params={'status': 'closed'})
                    for record in orders:
                        if str(record['id']) == order_detail['id']:
                            deal_amount = str(record['filled'])
                            break
                else:  # poloniex, etc.
                    deal_amount = str(sum([float(trade['amount']) for trade in order_detail['trades']]))
                logging.warning(order_detail)
                logging.warning('Traded amount: %s / %s (%.0f%%)' %
                                (deal_amount, amount, 100*float(deal_amount)/float(amount)))
                if abs(float(deal_amount)-float(amount))/float(amount) < 0.01:  # more than 99% of orders completed
                    logging.warning('Order successfully traded!')
                else:
                    logging.warning('Order is good but trade failed! Please handle exceptions manually.')
                return order_detail
            else:
                logging.warning('Market not enough for buying %s of amount %s.' % (base_currency, amount))
        else:
            logging.warning('Not enough balance available to buy %s of amount %s.' % (base_currency, amount))
        logging.warning('Order failed. Please handle exceptions manually.')

    def cal_sell_price(self, currency_pair, size, async=False):
        if async:
            return self.cal_sell_price_async(currency_pair, size)
        size = float(size)
        bids = self.client.fetch_order_book(currency_pair)['bids']
        # logging.warning(bids)
        total = 0
        rest = size
        price_range = []
        for bid in bids:
            price_s, volume_s = bid
            price, volume = map(float, bid)
            if volume > rest:
                total += price*rest
                price_range.append([price_s, rest])
                rest = 0
                break
            total += price*volume
            rest -= volume
            price_range.append(bid)
        status = (rest <= 0)
        return status, '%.8f' % (total/size), price_range

    async def cal_sell_price_async(self, currency_pair, size):
        size = float(size)
        bids = await self.client.fetch_order_book(currency_pair)
        bids = bids['bids']
        # logging.warning(bids)
        total = 0
        rest = size
        price_range = []
        for bid in bids:
            price_s, volume_s = bid
            price, volume = map(float, bid)
            if volume > rest:
                total += price*rest
                price_range.append([price_s, rest])
                rest = 0
                break
            total += price*volume
            rest -= volume
            price_range.append(bid)
        status = (rest <= 0)
        return status, '%.8f' % (total/size), price_range

    def sell_coin(self, base_currency, quote_currency, amount):

        """
        Sell coin according to the market.
        :param base_currency: string, uppercase
        :param quote_currency: string, uppercase
        :param amount: string
        :return: None
        """

        currency_pair = base_currency + '/' + quote_currency
        balance_base_currency = self.get_balance(base_currency)

        # reserve enough market space
        market_available, avg_price, price_range = self.cal_sell_price(currency_pair, float(amount)*2)

        # sell price, lower 8 % limit to ensure trade success
        price = '%.8f' % (float(price_range[-1][0]) * 0.92)

        # check balance of base currency
        if float(balance_base_currency) > float(amount):

            # check market status (if it is big enough for this order)
            if market_available:
                logging.warning('Selling %s: amount = %s, price = %s' % (base_currency, amount, price))
                order_detail = self.client.create_order(currency_pair, 'limit', 'sell', float(amount), price=price)
                # print(order_detail)
                if self.client.id in market_order_detail_type_1:
                    time.sleep(1.0)
                    deal_amount = '0.0'
                    orders = self.client.fetch_orders(symbol=currency_pair, params={'status': 'closed'})
                    for record in orders:
                        if str(record['id']) == order_detail['id']:
                            deal_amount = str(record['filled'])
                            break
                else:  # poloniex, etc.
                    deal_amount = str(sum([float(trade['amount']) for trade in order_detail['trades']]))
                logging.warning(order_detail)
                logging.warning('Traded amount: %s / %s (%.0f%%)' %
                                (deal_amount, amount, 100*float(deal_amount)/float(amount)))
                if abs(float(deal_amount)-float(amount))/float(amount) < 0.01:  # more than 99% of orders completed
                    logging.warning('Order successfully traded!')
                else:
                    logging.warning('Order is good but trade failed! Please handle exceptions manually.')
                return order_detail
            else:
                logging.warning('Market not enough for selling %s of amount %s.' % (base_currency, amount))
        else:
            logging.warning('Not enough %s balance for selling (selling amount: %s).' % (base_currency, amount))
        logging.warning('Order failed. Please handle exceptions manually.')

    def get_ticker_with_size(self, base_currency, quote_currency, base_currency_trade_size=None, async=False):

        if async:
            return self.get_ticker_with_size_async(base_currency, quote_currency, base_currency_trade_size)

        if not base_currency_trade_size:
            base_currency_trade_size = config_trader.trade_size[base_currency]

        ticker = {}
        currency_pair = base_currency + '/' + quote_currency
        ticker['ask'] = self.cal_buy_price(currency_pair=currency_pair,
                                           size=base_currency_trade_size)[1]
        ticker['bid'] = self.cal_sell_price(currency_pair=currency_pair,
                                            size=base_currency_trade_size)[1]
        return ticker

    async def get_ticker_with_size_async(self, base_currency, quote_currency, base_currency_trade_size=None):

        if not base_currency_trade_size:
            base_currency_trade_size = config_trader.trade_size[base_currency]

        ticker = {}
        currency_pair = base_currency + '/' + quote_currency
        ticker['ask'] = (await self.cal_buy_price_async(currency_pair=currency_pair,
                         size=base_currency_trade_size))[1]
        ticker['bid'] = (await self.cal_sell_price_async(currency_pair=currency_pair,
                         size=base_currency_trade_size))[1]
        return ticker


if __name__ == '__main__':
    trader = UnifiedClient('okex')
    # print(trader.client.urls['api'])
    # print(trader.get_tickers())
    print(trader.get_balances())
    # print(trader.get_balance('LTC'))
    # print(trader.get_available_balances())
    # print(trader.print_available_balances())
    # print(trader.cal_buy_price('LTC/USDT', size='0.01'))
    # print(trader.client.fetch_orders(symbol='XRP/USDT', params={'status': 'closed'}))
    # print(trader.buy_coin('LTC', 'USDT', '0.01'))
    # print(trader.sell_coin('LTC', 'USDT', '0.01'))
    # print(trader.get_ticker_with_size('XRP', 'USDT'))
    # print(trader.get_balances())

    # trader = UnifiedClient('poloniex', async=True)
    # print(trader.client.urls['api'])
    # print(trader.get_balances())
    # print(trader.get_balance('LTC'))
    # print(trader.get_available_balances())
    # print(trader.print_available_balances())
    # print(trader.cal_buy_price('LTC/USDT', size='0.01'))
    # print(trader.client.fetch_orders(symbol='XRP/USDT', params={'status': 'closed'}))
    # print(trader.buy_coin('LTC', 'USDT', '0.01'))
    # print(trader.sell_coin('LTC', 'USDT', '0.01'))
    # print(trader.get_ticker_with_size('XRP', 'USDT'))
    # print(trader.get_balances())

    # trader = UnifiedClient('poloniex', async=True)
    # print(trader.client.urls['api'])
    # tasks = []
    # task = asyncio.ensure_future(trader.get_tickers(async=True))
    # tasks.append(task)
    # task = asyncio.ensure_future(trader.get_ticker_with_size('XRP', 'USDT', async=True))
    # tasks.append(task)
    # loop = asyncio.get_event_loop()
    # done, pending = loop.run_until_complete(asyncio.wait(tasks))
    # results = [future.result() for future in done]
    # print(results)
    # loop.close()
    pass
