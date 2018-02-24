"""
Arbitrage trade manager:
    1. Monitor market prices and send trade order to arbitrage_trader
    2. Send coin balance order after each trade
    3. Loop 1-2
    4. Handle exceptions
"""


import arbitrage_trader
import coin_balancer
# import time
from aux import email_client, timeout, premium_calculator
from config import config_trader

import logging

rootLogger = logging.getLogger()

logFormatter = logging.Formatter("%(asctime)s  %(message)s")
fileHandler = logging.FileHandler('logs/arbitrage_trader.log')
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

# logFormatter = logging.Formatter("%(message)s")
# consoleHandler = logging.StreamHandler()
# consoleHandler.setFormatter(logFormatter)
# rootLogger.addHandler(consoleHandler)


@timeout.timeout(900, 'Timeout: arbitrage trader has been running for more than 5 minutes.')
def trade():

    logging.warning('\n\n')
    logging.warning(' ' * 0 + '#####     Trader started.     #####')

    logging.warning('=====     Coin Balancer      =====')
    coin_balancer.CoinBalancer().execute_coin_balance()

    logging.warning('=====     Premium monitor    =====')

    try:
        premiums = premium_calculator.get_premiums_mp()
    except BaseException as err:
        logging.warning('Get Premium failed. %s' % str(err))
        return

    logging.warning('Current premiums: ')
    for currency_pair in premiums:
        premium = premiums[currency_pair]
        premium_threshold = config_trader.get_premium_threshold(
            currency_pair, premium['market_hi'], premium['market_lo'])
        logging.warning(currency_pair + ': ' + str(premiums[currency_pair]) + ' (threshold: ' + premium_threshold + ')')

    # filter premium that is higher than threshold
    filtered_premiums = []  # each element is a dict containing currency_pair, premium, market_hi and market_lo.
    for currency_pair in premiums:
        premium = premiums[currency_pair]
        premium['currency_pair'] = currency_pair
        premium_threshold = config_trader.get_premium_threshold(
                currency_pair, premium['market_hi'], premium['market_lo'])
        if float(premium['premium']) > float(premium_threshold):
            filtered_premiums.append(premium)

    # sort premium
    filtered_premiums.sort(key=lambda x: float(x['premium']), reverse=True)
    logging.warning('Qualified premiums: %s' % filtered_premiums)

    # execute premium from the highest one, if success then return, else continue on the next one
    for premium in filtered_premiums:
        logging.warning('Sending arbitrage order to trader: %s' % str(premium))
        try:
            status = arbitrage_trader.ArbitrageTrader(premium['currency_pair'], premium['market_hi'],
                                                      premium['market_lo'], premium['premium']).arbitrage()
            logging.warning('Arbitrage order finished. Status: %s' % status)
            break
        except BaseException as err:
            if str(err) == 'Execution status: Insufficient Fund!' \
                    or 'Execution halted' in str(err)\
                    or 'Premium' in str(err):
                pass
            else:
                email_client.EmailClient().notify_me_by_email(title='Arbitrage Execution of %s Error: %s' %
                                                              (premium, err), content='Please handle exception.')

    logging.warning(' ' * 0 + '#####     Trader ended.       #####')

if __name__ == '__main__':

    while 1:
        try:
            trade()
        except BaseException as e:
            logging.warning('Error occurred in trader: %s' % e)
            try:
                email_client.EmailClient().notify_me_by_email(title='Error in arbitrage manager: %s' % e,
                                                              content='Please handle it manually.')
            except BaseException as e:
                logging.warning('Sending email error! ' % e)

        # time.sleep(10)
