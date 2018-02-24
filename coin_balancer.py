import functools
import logging
import poloniex
from aux import email_client, assets_monitor, coin_transfer
from aux.timeout import timeout
from config import config_coin, config_trader


def insufficient_balance_error_handler(func):
    @functools.wraps(func)
    def wrapper(*args, **kw):
        try:
            res = func(*args, **kw)
            return res
        except BaseException as e:
            if '余额不足' in str(e):
                logging.warning('Insufficient balance error handler: Balance not available for transfer. Need to wait.')
                return 'Insufficient balance for transfer.'
    return wrapper


class CoinBalancer:

    @staticmethod
    @timeout(120, 'Timeout: function has been running for more than 120 seconds.')
    @insufficient_balance_error_handler
    def balance_balances():

        balances = assets_monitor.AssetsMonitor().get_balances_mp(include_frozen=False)
        logging.warning('Current balances:')

        for market in balances:
            logging.warning(market + ': \t' + ''.join(
                [(currency + ': ' + balances[market][currency] + '\t') for currency in config_coin.currency_list['standard']]))

        for currency in config_coin.currency_list['standard']:

            # logging.warning('Checking %s.' % currency)

            min_balance = None
            min_market = None
            max_balance = None
            max_market = None

            for market in config_trader.market_list:

                balance = balances[market][currency]
                if not min_balance or float(balance) < float(min_balance):
                    min_balance = balance
                    min_market = market
                if not max_balance or float(balance) > float(max_balance):
                    max_balance = balance
                    max_market = market

            if min_market == max_market:
                logging.warning('Caution: min_market == max_market.')
                break

            low_level = config_coin.low_level[currency]
            if float(min_balance) < float(low_level):
                logging.warning('%s balance (%s) in %s market is below low level (%s), needs transfer.' %
                                (currency, min_balance, min_market, low_level))
                amount = '%.2f' % ((float(max_balance) - float(low_level)) * float(config_coin.transfer_ratio))
                logging.warning('Transfer amount: %s' % amount)
                if float(amount) < float(config_coin.min_transfer[currency]):
                    logging.warning('Amount smaller than min amount (%s).' % config_coin.min_transfer[currency])
                else:
                    status = coin_transfer.CoinTransfer().transfer(
                        max_market, min_market, currency=currency, amount=amount)
                    logging.warning('Transferred %s %s from %s to %s, status: %s' %
                                    (amount, currency, max_market, min_market, status))
            else:
                logging.warning('No need to transfer %s.' % currency)

    def execute_coin_balance(self):

        try:
            self.balance_balances()

        except poloniex.PoloniexError as e:
            if 'Withdrawal would exceed your daily withdrawal limit.' in str(e):
                logging.warning('Withdrawal exceeds daily limit.')
                email_client.EmailClient().\
                    notify_me_by_email(title='Coin balancer error: Withdraw exceeds daily limit.',
                                       content='PoloniexError')
            else:
                logging.error('Other Poloniex error happened: %s' % e)

        except TimeoutError:
            logging.warning('Coin balancer time out!\n')

        except BaseException as e:
            logging.warning('Error occurred in coin balancer. Sending email notification: %s' % e)
            email_client.EmailClient().notify_me_by_email(title='Error occurred in coin balancer.',
                                                          content='Error (%s) occurred.\n Please check code.' % e)


if __name__ == '__main__':
    pass
    # CoinBalancer().balance_balances()
    CoinBalancer().execute_coin_balance()
