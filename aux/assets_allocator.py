import logging
from aux import assets_monitor
from config import config_coin, config_trader
from client import unified_client
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=logging.WARNING)


def calculate_allocation():

    mon = assets_monitor.AssetsMonitor()
    balance = mon.get_assets()
    # logging.warning(balance)
    balance = mon.cal_usdt_equivalent(balance)
    logging.warning(balance)

    total_portion = sum(map(lambda x: float(x), config_coin.currency_ratio.values()))
    # logging.warning(total_portion)

    amount_per_portion = float(balance['usdt_equ']) / total_portion
    # logging.warning(amount_per_portion)

    prices = unified_client.UnifiedClient(config_trader.market_fetch_ticker).get_tickers()
    # logging.warning(prices)

    allocation = {}
    for currency in config_coin.currency_list['standard']:
        if currency != 'USDT':
            pair = currency.upper() + '/USDT'
            allocation[currency] = float(amount_per_portion * float(config_coin.currency_ratio[currency])) \
                / float(prices[pair])
        else:
            allocation[currency] = float(amount_per_portion * float(config_coin.currency_ratio[currency]))
        allocation[currency] = '%.8f' % allocation[currency]
    # logging.warning(allocation)

    return allocation


def calculate_even_level():

    allocation = calculate_allocation()
    res = {}

    for currency in allocation:
        res[currency] = '%.8f' % (float(allocation[currency]) / len(config_trader.market_list))

    logging.warning(res)
    return res


def calculate_amount_to_allocation(ratio=False):

    mon = assets_monitor.AssetsMonitor()
    balance = mon.get_assets()
    allocation = calculate_allocation()

    res = {}

    for currency in config_coin.currency_list['standard']:
        res[currency] = '%.8f' % (float(allocation[currency]) - float(balance[currency])) if not ratio else \
            '%.8f' % (float(balance[currency]) / float(allocation[currency]))

    logging.warning(res)
    return res


if __name__ == '__main__':
    pass

    logging.warning('Allocation:')
    calculate_even_level()
    logging.warning('Amount to allocation:')
    calculate_amount_to_allocation()
    logging.warning('Ratio to allocation:')
    calculate_amount_to_allocation(ratio=True)
    logging.warning('Balances:')

    a = assets_monitor.AssetsMonitor()
    a.print_assets(a.get_balances_async())
    print(a.cal_usdt_equivalent(a.get_balance('huobipro')))
    print(a.cal_usdt_equivalent(a.get_balance('poloniex')))
    print(a.cal_usdt_equivalent(a.get_balance('okex')))
