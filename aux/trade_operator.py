"""
trade_operator:
    standard trade function to trade in multiple markets
"""

from client import poloniex_client, huobi_pro_operator
from config import config_coin


def trade_operator(market, currency_pair, direction, amount):

    """
    Call buy or sell in clients
    :param market: string
    :param currency_pair: string, standard pair name, refer to config_coin
    :param direction: 'buy' or 'sell'
    :param amount: string
    :return: boolean, success if True.
    """

    table = {
        'poloniex': {
            'buy': poloniex_client.PoloniexClient().buy_coin,
            'sell': poloniex_client.PoloniexClient().sell_coin
        },
        'huobi_pro': {
            'buy': huobi_pro_operator.HuobiProOperator.buy_pro,
            'sell': huobi_pro_operator.HuobiProOperator.sell_pro
        }
    }

    base_currency, quote_currency = currency_pair.split('/')

    if market == 'poloniex':
        base_currency = config_coin.currency_name_standard_to_poloniex(base_currency)
        quote_currency = config_coin.currency_name_standard_to_poloniex(quote_currency)

    table[market][direction](base_currency, quote_currency, amount)

    return True


if __name__ == '__main__':
    pass
    # trade_operator('huobi_pro', 'ZRX/BTC', 'buy', '1')
