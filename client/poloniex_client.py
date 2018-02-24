import logging
import poloniex
from config import config_trader, api_keys
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=logging.WARNING)


class PoloniexClient(poloniex.Poloniex):

    def __init__(self):
        public_key = api_keys.POLONIEX_ACCESS_KEY
        secret_key = api_keys.POLONIEX_SECRET_KEY
        super().__init__(public_key, secret_key)

    def get_balances(self):
        return self.returnBalances()

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

    def cal_buy_price(self, currency_pair, size):
        size = float(size)
        asks = self.returnOrderBook(currency_pair)['asks']
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

        currency_pair = quote_currency + '_' + base_currency

        balance_quote_currency = self.get_balance(quote_currency)

        # reserve enough market space
        market_available, avg_price, price_range = self.cal_buy_price(currency_pair, float(amount) * 2)

        # buy price, raise 1 % limit to ensure trade success
        price = '%.8f' % (float(price_range[-1][0]) * 1.01)

        # check balance of BTC
        if float(balance_quote_currency) > float(price)*float(amount)*1.01:

            # check market status (if it is big enough for this order)
            if market_available:

                logging.warning('Buying %s: amount = %s, price = %s, total = %.6f' %
                                (base_currency, amount, price, float(price)*float(amount)))
                order_detail = self.buy(currency_pair, amount=amount, rate=price)
                deal_amount = str(sum([float(trade['amount']) for trade in order_detail['resultingTrades']]))
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

    def cal_sell_price(self, currency_pair, size):
        size = float(size)
        bids = self.returnOrderBook(currency_pair)['bids']
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

        currency_pair = quote_currency + '_' + base_currency
        balance_base_currency = self.get_balance(base_currency)

        # reserve enough market space
        market_available, avg_price, price_range = self.cal_sell_price(currency_pair, float(amount)*2)

        # sell price, lower 1 % limit to ensure trade success
        price = '%.8f' % (float(price_range[-1][0]) * 0.99)

        # check balance of base currency
        if float(balance_base_currency) > float(amount):

            # check market status (if it is big enough for this order)
            if market_available:
                logging.warning('Selling %s: amount = %s, price = %s' % (base_currency, amount, price))
                order = self.sell(currency_pair, amount=amount, rate=price)
                deal_amount = str(sum([float(trade['amount']) for trade in order['resultingTrades']]))
                logging.warning(order)
                logging.warning('Traded amount: %s / %s (%.0f%%)' %
                                (deal_amount, amount, 100*float(deal_amount)/float(amount)))
                if abs(float(deal_amount)-float(amount))/float(amount) < 0.01:  # more than 99% of orders completed
                    logging.warning('Order successfully traded!')
                else:
                    logging.warning('Order is good but trade failed! Please handle exceptions manually.')
                return order
            else:
                logging.warning('Market not enough for selling %s of amount %s.' % (base_currency, amount))
        else:
            logging.warning('Not enough %s balance for selling (selling amount: %s).' % (base_currency, amount))
        logging.warning('Order failed. Please handle exceptions manually.')

    # def get_ticker_all(self):
    #
    #     ticker = {}
    #
    #     for currency_pair in ['BTC_ETH', 'BTC_ETC', 'BTC_LTC', 'ETH_ETC', 'BTC_BCH']:
    #         base_currency = currency_pair.split('_')[1]
    #         base_currency_trade_size = config_trader.get_trade_size(base_currency)
    #         ticker[currency_pair] = {}
    #         ticker[currency_pair]['ask'] = self.cal_buy_price(currency_pair=currency_pair,
    #                                                           size=base_currency_trade_size)[1]
    #         ticker[currency_pair]['bid'] = self.cal_sell_price(currency_pair=currency_pair,
    #                                                            size=base_currency_trade_size)[1]
    #
    #     return ticker

    def get_ticker_with_size(self, base_currency, quote_currency, base_currency_trade_size=None):

        if not base_currency_trade_size:
            base_currency_trade_size = config_trader.get_trade_size(base_currency)

        ticker = {}
        currency_pair = quote_currency + '_' + base_currency
        ticker['ask'] = self.cal_buy_price(currency_pair=currency_pair,
                                           size=base_currency_trade_size)[1]
        ticker['bid'] = self.cal_sell_price(currency_pair=currency_pair,
                                            size=base_currency_trade_size)[1]
        return ticker


if __name__ == '__main__':
    trader = PoloniexClient()
    # print(trader.get_ticker_with_size('ETH', 'BTC'))
    pass
