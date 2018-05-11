# TODO: test this function after the currency balancer is done.

import time
import logging
import arbitrage_trader
from aux import email_client, assets_monitor, premium_calculator
from aux.timeout import timeout
from config import config_coin, config_trader


class CoinBalancer:

    @staticmethod
    @timeout(120, 'Timeout: function has been running for more than 120 seconds.')
    def balance_balances(premiums):

        balances = assets_monitor.AssetsMonitor().get_balances(include_frozen=True)
        # balances = assets_monitor.AssetsMonitor().get_balances_async(include_frozen=True)
        logging.info('Current balances:')
        logging.info(balances)

        # for market in balances:
        #     balances[market] = assets_monitor.AssetsMonitor().cal_usdt_equivalent(balances[market])
        #     logging.warning(market + ': \t' + ''.join(
        #         [(currency + ': ' + balances[market][currency] + '\t')
        #          for currency in config_coin.currency_list['standard']]))

        imbalance_ratio = {}
        for market in balances:
            imbalance_ratio[market] = {}
            for currency in config_coin.currency_list['standard']:
                imbalance_ratio[market][currency] = '%.4f' % (float(balances[market][currency])
                                                              / float(config_coin.even_level[currency]) - 1.0)
        logging.info('Balance even ratio:')
        for market in imbalance_ratio:
            logging.info(imbalance_ratio[market])

        balance_list = []
        for market_hi, market_lo in config_trader.market_pairs:

            base_currencies = [currency for currency in config_coin.currency_list['standard']
                               if float(imbalance_ratio[market_hi][currency])
                               > float(config_coin.imbalance_threshold_hi)
                               and float(imbalance_ratio[market_lo][currency])
                               < -float(config_coin.imbalance_threshold_lo)]
            quote_currencies = [currency for currency in config_coin.currency_list['standard']
                                if float(imbalance_ratio[market_lo][currency])
                                > float(config_coin.imbalance_threshold_hi)]

            logging.info('Market pair: %s, %s' % (market_hi, market_lo))
            logging.info('Currency pair: %s, %s' % (str(base_currencies), str(quote_currencies)))

            for currency_pair in config_trader.trade_currency_pairs:
                base_currency, quote_currency = currency_pair.split('/')
                if base_currency in base_currencies and quote_currency in quote_currencies:
                    balance_list.append([currency_pair, market_hi, market_lo,
                                         config_coin.balance_premium_threshold])

        logging.warning('Balance list: %s' % str(balance_list))

        if balance_list:
            logging.warning('=====     Coin Balancer (adaptive & reversed arbitrage)      =====')
            balance_list.sort(key=lambda x: float(x[3]))
            premium_cache = premiums
            for i in range(len(balance_list)):
                currency_pair, market_hi, market_lo, threshold = balance_list[i]
                logging.info('Trying to balance %s.' % str(balance_list[i]))
                try:
                    the_premium = [premium for premium in premium_cache
                                   if (premium['currency_pair'] == currency_pair and
                                       premium['market_hi'] == market_hi and
                                       premium['market_lo'] == market_lo)]
                    # print(the_premium)
                    if not the_premium:
                        continue
                        # premium = premium_calculator.get_premium_mp(currency_pair=currency_pair, market_hi=market_hi,
                        #                                             market_lo=market_lo)
                    else:
                        premium = the_premium[0]
                    # print(premium)
                except BaseException as err:
                    logging.warning('Get premium failed. %s' % str(err))
                    continue
                if float(premium['premium']) > float(threshold):
                    logging.warning('Premium (%s, threshold: %s) is good for reversed arbitrage.' % (premium, threshold))
                    logging.warning('Sending arbitrage order to trader: %s' % str(premium))
                    try:
                        status = arbitrage_trader. \
                            ArbitrageTrader(currency_pair, premium['market_hi'],
                                            premium['market_lo'], premium['premium'], premium_threshold=threshold). \
                            arbitrage(is_reversed=True)
                        logging.warning('Arbitrage order (reversed) finished. Status: %s' % status)
                        break
                    except BaseException as err:
                        if any([err_ignore_message in str(err)
                                for err_ignore_message in config_trader.err_ignore_messages]):
                            logging.warning('Arbitrage (reversed) execution error: %s' % err)
                        elif any([err_wait_message in str(err)
                                  for err_wait_message in config_trader.err_wait_messages]):
                            logging.warning('Error of exchange: %s' % str(err))
                            logging.warning('Sleep for 30 seconds.')
                            time.sleep(30)
                        else:
                            email_client.EmailClient().notify_me_by_email(
                                title='Arbitrage (reversed) Execution of %s Error: %s' % (premium, err),
                                content='Please handle exception.')
                else:
                    logging.info('Premium (%s) is not high enough (%s) for reversed arbitrage.' %
                                 (premium['premium'], threshold))
        else:
            logging.warning('No need to balance coins.')


if __name__ == '__main__':
    pass
    CoinBalancer().balance_balances()
