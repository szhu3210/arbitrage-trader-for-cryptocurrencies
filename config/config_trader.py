market_list = ['huobipro', 'poloniex', 'okex']
# market_list = ['huobipro', 'poloniex']

# trade_currency_pairs = ['BTC/USDT', 'ETH/USDT', 'ETC/USDT', 'LTC/USDT', 'BCH/USDT', 'DASH/USDT', 'XRP/USDT']

trade_currency_pairs = ['XRP/BTC', 'ETH/BTC', 'ETC/BTC', 'BCH/BTC', 'LTC/BTC', 'DASH/BTC',
                        'BTC/USDT', 'ETH/USDT', 'ETC/USDT', 'LTC/USDT', 'BCH/USDT', 'DASH/USDT', 'XRP/USDT']

# premium_threshold = '0.005'
premium_threshold = '0.010'

premium_invalid_threshold = '0.2'

market_fetch_ticker = 'poloniex'  # default market for usdt_equ calculation

delay = '5'  # in minutes

trade_size = {
    'BTC': '0.01',
    'BCH': '0.06',
    'LTC': '1.5',
    'ETH': '0.1',
    'ETC': '4.0',
    'DASH': '0.15',
    'XRP': '80',  # XRP amount needs to be integer
}

err_ignore_messages = [
    'Execution status: Insufficient Fund!',
    'Execution Halted',
    'Premium',
    'urlopen',
    'HTTP Error 504',
    'Remote end closed connection without response',
    'request timeout',
    'EOF occurred in violation of protocol',
]

err_wait_messages = [
    'Max retries exceeded with url',
    '429',
]


def cal_market_pairs():

    res = []

    for market_hi in market_list:
        for market_lo in market_list:
            if market_hi != market_lo:
                res.append((market_hi, market_lo))

    return res

market_pairs = cal_market_pairs()

# exchange_currency_pairs = {
#     'poloniex': ['XRP/BTC', 'ETH/BTC', 'ETC/BTC', 'BCH/BTC', 'LTC/BTC', 'DASH/BTC',
#                  'BTC/USDT', 'ETH/USDT', 'ETC/USDT', 'LTC/USDT', 'BCH/USDT', 'DASH/USDT', 'XRP/USDT'],
#     'huobipro': ['XRP/BTC', 'ETH/BTC', 'ETC/BTC', 'BCH/BTC', 'LTC/BTC', 'DASH/BTC',
#                  'BTC/USDT', 'ETH/USDT', 'ETC/USDT', 'LTC/USDT', 'BCH/USDT', 'DASH/USDT', 'XRP/USDT'],
#     'okex': ['XRP/BTC', 'ETH/BTC', 'ETC/BTC', 'BCH/BTC', 'LTC/BTC', 'DASH/BTC',
#              'BTC/USDT', 'ETH/USDT', 'ETC/USDT', 'LTC/USDT', 'BCH/USDT', 'DASH/USDT', 'XRP/USDT'],
#     'gdax': [],
#     'kraken': [],
#     'bittrex': [],
#     'bitfinex': [],
# }