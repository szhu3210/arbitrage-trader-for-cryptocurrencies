"""
config_trader:
    Store all the config parameters used in trader
"""


trade_currency_pairs = ['ETH/BTC', 'ETC/BTC', 'LTC/BTC', 'BCC/BTC',
                        'BTC/USDT', 'ETH/USDT', 'ETC/USDT', 'LTC/USDT', 'BCC/USDT']  # base currency / quote currency
market_list = ['huobi_pro', 'poloniex']
profit_margin = '0.005'

huobi_pro_currency_pair_precision = {
    'BTC/USDT': '2',
    'BCC/USDT': '2',
    'ETH/USDT': '2',
    'LTC/USDT': '2',
    'DASH/USDT': '2',
    'ETC/USDT': '2',
    'BCC/BTC': '6',
    'ETH/BTC': '6',
    'LTC/BTC': '6',
    'DASH/BTC': '6',
    'ETC/BTC': '6',
    'BT1/BTC': '6',
    'BT2/BTC': '6',
    'KNC/BTC': '8',
    'ZRX/BTC': '8',
    'AST/BTC': '8',
    'RCN/BTC': '8',
    'RCN/ETH': '8',
}


def get_trade_size(currency):

    d = {
        'BTC': '0.1',
        'BCC': '0.6',
        'BCH': '0.6',
        'LTC': '10.0',
        'ETH': '2.0',
        'ETC': '40.0',
    }

    return d[currency]


def get_premium_threshold(currency_pair='', market_hi='', market_lo=''):

    transaction_fee = 0.0040  # transaction fee ratio
    transfer_fee = 0.0000  # default transfer fee ratio in poloniex

    base_currency, quote_currency = currency_pair.split('/')

    if (base_currency == 'BTC' and market_lo == 'huobi_pro') or (quote_currency == 'BTC' and market_hi == 'huobi_pro'):
        # buy BTC in huobi_pro, or sell other currencies with quote currency as BTC, will cause transfer from huobi_pro
        transfer_fee += 0.012  # transfer fee ratio, 0.004/0.35 BTC
        pass

    if quote_currency == 'USDT':
        if market_hi == 'huobi_pro':  # generate more USDT in huobi_pro, will cause transfer from huobi_pro
            transfer_fee += 0.002  # transfer fee ratio, 5/2500 USDT
        elif market_hi == 'poloniex':  # generate more USDT in poloniex, will cause transfer from poloniex
            transfer_fee += 0.001  # transfer fee ratio, 2/2000 USDT

    if market_hi:
        pass

    if market_lo:
        pass

    return '%.4f' % (float(profit_margin) + transaction_fee + transfer_fee)  # default threshold
