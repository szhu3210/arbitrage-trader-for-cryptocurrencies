"""
Arbitrage trade manager:
    1. Monitor market prices and send trade order to arbitrage_trader
    2. Send coin balance order after each trade
    3. Loop 1-2
    4. Handle exceptions
"""

import logging
import time

import arbitrage_trader
import coin_balancer
from aux import email_client, timeout, premium_calculator
from config import config_trader, config_coin

rootLogger = logging.getLogger()

logFormatter = logging.Formatter("%(asctime)s  %(message)s")
fileHandler = logging.FileHandler('logs/arbitrage_trader.log')
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

# logFormatter = logging.Formatter("%(message)s")
# consoleHandler = logging.StreamHandler()
# consoleHandler.setFormatter(logFormatter)
# rootLogger.addHandler(consoleHandler)


@timeout.timeout(300, 'Timeout: arbitrage trader has been running for more than 5 minutes.')
def trade(balancer_type='soft'):

    res = ''

    logging.warning('\n\n')
    logging.warning(' ' * 0 + '#####     Trader started.     #####')

    # monitor premiums
    logging.warning('=====     Premium monitor    =====')

    try:
        premiums = premium_calculator.get_premiums_async()
    except BaseException as err:
        logging.warning('Get Premium failed. %s' % str(err))
        return

    logging.warning('Current premiums (highest 3): ')
    count = 0
    for premium in premiums:
        if count >= 3:
            break
        premium_threshold = config_trader.premium_threshold
        logging.warning(str(premium) + ' (threshold: ' + premium_threshold + ')')
        count += 1

    # time.sleep(1.0)

    logging.warning('=====     Coin Balancer      =====')
    try:
        coin_balancer.CoinBalancer().balance_balances(premiums)
    except BaseException as err:
        logging.warning('Exception in coin balancer (soft): %s' % str(err))
        if '_handle_timeout' in err or \
           'Error in get_balances.' in err:
            pass
        else:
            email_client.EmailClient().notify_me_by_email(title='Error in coin balancer: %s' % str(err))

    logging.warning('=====      Trader      =====')

    # filter premium that is higher than threshold
    filtered_premiums = []  # each element is a dict containing currency_pair, premium, market_hi and market_lo.
    for premium in premiums:
        premium_threshold = config_trader.premium_threshold
        if float(premium['premium']) > float(premium_threshold):
            filtered_premiums.append(premium)

    # sort premium
    filtered_premiums.sort(key=lambda x: float(x['premium']), reverse=True)
    logging.warning('Qualified premiums: %s' % filtered_premiums)

    # execute premium from the highest one, if success then return, else continue on the next one
    for premium in filtered_premiums:

        currency_pair = premium['currency_pair']
        if currency_pair in delay_list and delay_list[currency_pair] > time.time():
            content = 'Currency pair %s in delay list. Release time: %.0f seconds.' % \
                      (currency_pair, delay_list[currency_pair] - time.time())
            logging.warning(content)
            # email_client.EmailClient().notify_me_by_email(title=content)
            continue

        logging.warning('Sending arbitrage order to trader: %s' % str(premium))
        try:
            status = arbitrage_trader.ArbitrageTrader(premium['currency_pair'], premium['market_hi'],
                                                      premium['market_lo'], premium['premium']).arbitrage()
            logging.warning('Arbitrage order finished. Status: %s' % status)

            if 'Negative profit' in status:
                logging.warning('Negative profit in currency pair %s! ' % currency_pair)
                email_client.EmailClient().notify_me_by_email(title='Abnormal profit in currency pair %s.' %
                                                                    currency_pair)
                res = currency_pair
            break

        except BaseException as err:
            # raise err
            if any([err_ignore_message in str(err) for err_ignore_message in config_trader.err_ignore_messages]):
                logging.warning('Execution error: %s' % str(err))
            elif any([err_wait_message in str(err) for err_wait_message in config_trader.err_wait_messages]):
                logging.warning('Error of exchange: %s' % str(err))
                logging.warning('Sleep for 30 seconds.')
                time.sleep(30)
            else:
                email_client.EmailClient().notify_me_by_email(title='Arbitrage Execution of %s Error: %s' %
                                                              (premium, str(err)), content='Please handle exception.')

    logging.warning(' ' * 0 + '#####     Trader ended.       #####')

    return res

if __name__ == '__main__':

    delay_list = dict()

    # coin_balancer_hard.CoinBalancer().execute_coin_balance(even=True)

    while 1:
        try:
            logging.warning('')
            logging.warning('Delay list: %s', str(delay_list))
            err_pair = trade()
            delay_list[err_pair] = time.time() + 60 * float(config_trader.delay)
        except BaseException as e:
            # raise e
            logging.warning('Error occurred in manager: %s' % e)
            email_client.EmailClient().notify_me_by_email(title='Error in arbitrage manager: %s' % e,
                                                          content='Please handle it manually.')

        # time.sleep(10)
