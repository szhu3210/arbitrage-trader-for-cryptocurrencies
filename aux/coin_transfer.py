import logging
from client import poloniex_client
from client import huobi_pro_client
from config import config_coin
from aux import email_client

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=logging.WARNING)


class CoinTransfer:

    @staticmethod
    def transfer_from_huobi(destination='', currency='', amount='', fee=''):

        """
        Transfer coin to other market
        :param destination: string, e.g. "poloniex"
        :param currency: string, upper case, e.g. "BTC"
        :param amount: string
        :param fee: string
        :return: boolean, status.
        """

        client = huobi_pro_client.HuobiProClient(currency)
        deposit_address = config_coin.coin_deposit_address[destination][
            config_coin.currency_name_standard_to_poloniex(currency) if destination == 'poloniex' else currency]
        logging.warning('Start transferring %s %s from huobi to %s...' % (amount, currency, destination))

        config_coin.verify_address(market=destination, currency=currency,
                                   deposit_address_local=deposit_address)

        logging.warning('Transferring pro from huobi to %s:' % destination)
        withdraw_id = client.withdraw_create(destination='poloniex', amount=amount, currency=currency, fee=fee)
        logging.warning('Transfer SUCCESS! Amount: %s %s, Withdraw_ID: %s' % (amount, currency, withdraw_id))

        return True

    @staticmethod
    def transfer_from_poloniex(destination='', currency='', amount=''):

        """
        Transfer from poloniex to other markets
        :param destination: string, e.g. "huobi_pro"
        :param currency: string, e.g. "BTC"
        :param amount: string, e.g. "0.5"
        :return: boolean, transfer status, True: success.
        """

        deposit_address = config_coin.coin_deposit_address[destination][currency]

        logging.warning('Start Transferring %s %s from poloniex to %s.' % (amount, currency, destination))

        config_coin.verify_address(market=destination, currency=currency,
                                   deposit_address_local=deposit_address)

        logging.warning('Transferring:')
        currency_poloniex = config_coin.currency_name_standard_to_poloniex(currency)
        status = poloniex_client.PoloniexClient().withdraw(
            currency=currency_poloniex, amount=amount, address=deposit_address)
        logging.warning('Returned response: \"%s\"' % status['response'])
        expected_response = 'Withdrew %.8f %s.' % (float(amount), currency_poloniex)
        logging.warning('Expected response: \"%s\"' % expected_response)
        if status['response'] == expected_response:
            logging.warning('Transfer status: OK! Status: %s' % status)
        else:
            logging.warning('Transfer status: ERROR! Status: %s' % status)
            raise BaseException('Transfer error! Status: %s' % status)

        return True

    def transfer(self, from_market, to_market, currency, amount):

        """

        :param from_market:
        :param to_market:
        :param currency: string, standard currency name, refer to config_coin
        :param amount:
        :return:
        """

        if from_market == 'poloniex':
            res = self.transfer_from_poloniex(
                destination=to_market, currency=currency, amount=amount)
        elif from_market == 'huobi_pro':
            res = self.transfer_from_huobi(destination=to_market, currency=currency, amount=amount)
        else:
            raise ValueError('from_market parameter error: %s' % from_market)

        email_client.EmailClient().notify_me_by_email(title='Transferred %s %s from %s to %s. Status: %s.' %
                                                            (amount, currency, from_market, to_market,
                                                             'Success' if res else 'Fail'))
        return res

if __name__ == '__main__':
    pass
    # CoinTransfer().transfer(from_market='huobi_pro', to_market='poloniex', amount='25.0', currency='USDT')
