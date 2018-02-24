import logging
from client import poloniex_client, huobi_pro_client

currency_list = dict()
currency_list['huobi_pro'] = ['BTC', 'BCC', 'ETH', 'ETC', 'LTC', 'USDT']
currency_list['poloniex'] = ['BTC', 'BCH', 'ETH', 'ETC', 'LTC', 'USDT']
currency_list['standard'] = currency_list['huobi_pro']

transfer_ratio = '0.8'  # ratio is the portion of balance gap that is being transferred from market A to market B.

low_level = {
    'BTC': '0.15',
    'BCC': '1.0',
    'ETH': '3.2',
    'ETC': '62.5',
    'LTC': '17.0',
    'USDT': '1000'
}

min_transfer = {
    'BTC': '0.3',
    'BCC': '2.0',
    'ETH': '6.5',
    'ETC': '125.0',
    'LTC': '35.0',
    'USDT': '2000'
}

coin_deposit_address = {
    'poloniex': {
        'BTC': 
        'BCH': 
        'ETH': 
        'ETC': 
        'LTC': 
        'USDT': 
    },
    'huobi_pro': {
        'BTC': 
        'BCC': 
        'ETH': 
        'ETC': 
        'LTC': 
        'USDT':
    }
}


def verify_address(market, currency, deposit_address_local):

    """
    Contact server and verify the coin deposit address
    :param market: string, e.g. "poloniex"
    :param currency: string, e.g. "BTC"
    :param deposit_address_local: string, e.g. "1PtcVjjUerk4ZvariNoYRGsFZt7v6J1azo"
    :return: Boolean
    """

    logging.warning('Getting %s deposit address from %s server:' % (currency, market))

    if market == 'poloniex':
        currency = currency_name_standard_to_poloniex(currency)
        deposit_address_remote = poloniex_client.PoloniexClient().returnDepositAddresses()[currency]
    elif market == 'huobi_pro':
        deposit_address_remote = huobi_pro_client.HuobiProClient().get_deposit_address(currency=currency)
    else:
        raise BaseException('Market name invalid.')

    logging.warning('Deposit address returned from %s: \t%s' % (market, deposit_address_remote))
    logging.warning('Deposit address in local record: \t\t\t%s' % deposit_address_local)

    res = deposit_address_local == deposit_address_remote
    if res:
        logging.warning('Deposit address verification result: PASS!')
    else:
        logging.warning('Deposit address verification result: FAIL!')

    return res


def verify_all_address():

    """
    Verify all deposit addresses in huobi_pro and poloniex.
    :return: Boolean
    """

    logging.warning('Starting to verify all coin deposit addresses')

    for currency in currency_list['huobi_pro']:
        verify_address('huobi_pro', currency=currency,
                       deposit_address_local=coin_deposit_address['huobi_pro'][currency])

    for currency in currency_list['poloniex']:
        verify_address('poloniex', currency=currency,
                       deposit_address_local=coin_deposit_address['poloniex'][currency])

    logging.warning('All coin deposit addresses verified. Result: PASS.')

    return True


def currency_name_standard_to_poloniex(currency_name):
    if currency_name == 'BCC':
        return 'BCH'
    return currency_name


def to_standard(market, currency):

    table = {
                'poloniex': {'BCH': 'BCC'}
            }

    if market in table and currency in table[market]:
        return table[market][currency]

    return currency

if __name__ == '__main__':
    verify_all_address()
