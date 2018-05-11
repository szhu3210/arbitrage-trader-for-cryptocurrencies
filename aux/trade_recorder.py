import csv
import logging
import os.path
import time
from collections import OrderedDict
from client import unified_client
from config import config_trader, config_coin

FILENAME = 'logs/trade_record.csv'


def save_trading_result(pair='N/A', market='N/A', premium_report='N/A', premium_threshold='N/A',
                        trade_amount='N/A', profit='N/A', assets=None, profit_ratio_num=0.0, is_reversed=False):

    logging.warning('Save trading result...')
    currency_list = config_coin.currency_list['standard']

    if not assets:
        assets = {}

    result = OrderedDict()

    try:
        result['time (GMT)'] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        result['time (local)'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        result['time zone'] = time.strftime("%z", time.gmtime())
        result['reversed'] = str(is_reversed)
        result['pair'] = pair
        result['market'] = market
        result['premium'] = premium_report
        result['threshold'] = premium_threshold
        result['amount'] = trade_amount
        result['profit'] = profit
        result['profit_ratio'] = '%.4f' % profit_ratio_num
        for currency in currency_list:
            result[currency] = assets[currency] if currency in assets else 'N/A'

        try:

            prices = unified_client.UnifiedClient(config_trader.market_fetch_ticker).get_tickers()

            for currency in currency_list:
                result[currency + ' price in USDT'] = \
                    prices[currency + '/USDT'] \
                    if currency != 'USDT' else '1.00'

            if 'N/A' in [result[currency] for currency in currency_list]:

                result['total assets in USDT'] = 'N/A'
                result['total assets in BTC'] = 'N/A'

            else:

                result['total assets in USDT'] = '%.2f' % sum(
                    [
                        float(result[currency]) * float(result[currency + ' price in USDT'])
                        for currency in currency_list
                    ]
                )

                result['total assets in BTC'] = \
                    '%.4f' % (float(result['total assets in USDT']) / float(result['BTC price in USDT']))

        except BaseException as e:
            logging.warning('Fetching prices failed: %s' % e)

        file_exists = os.path.isfile(FILENAME)

        with open(FILENAME, 'a' if file_exists else 'w') as csvfile:

            fieldnames = result.keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(result)

        logging.warning('Trading result Saved.')

    except BaseException as e:
        logging.warning('Error occurred when saving trading result: %s' % e)

if __name__ == '__main__':
    pass
    from aux import assets_monitor

    FILENAME = '../logs/trade_record.csv'

    save_trading_result(pair='Test Pair', market='Test Market', premium_report='0.02', premium_threshold='0.12',
                        trade_amount='2.00', profit='21.39', assets=assets_monitor.AssetsMonitor().get_assets())
