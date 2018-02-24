"""
Arbitrage trader:
    1. Execute order, including balance check and execution-level error handling.
"""

import logging
import time
from aux import assets_monitor, timeout, time_usage, premium_calculator, trade_report, trade_operator
from config import config_trader, config_coin
from multiprocessing import Pool


class ArbitrageTrader:

    def __init__(self, currency_pair, market_hi, market_lo, premium_report=''):
        self.currency_pair = currency_pair
        self.base_currency, self.quote_currency = self.currency_pair.split('/')
        self.market_hi = market_hi
        self.market_lo = market_lo
        self.premium_report = premium_report
        self.premium_threshold = config_trader.get_premium_threshold(currency_pair, market_hi, market_lo)

    @time_usage.time_usage
    @timeout.timeout(600, 'Timeout: arbitrage function has been running for more than 10 minutes.')
    def arbitrage(self, base_currency_trade_amount='', amount_margin=''):

        if not amount_margin:
            amount_margin = '0.03'  # set margin to make sure enough balance

        if not base_currency_trade_amount:
            base_currency_trade_amount = config_trader.get_trade_size(self.base_currency)

        # record balance, check balance, execute arbitrage, calculate profit, report, record.

        logging.warning('=' * 50 + ' S T A R T ' + '=' * 50)
        logging.warning('Executing positive premium arbitrage:')

        # Phase 1: record balances
        logging.warning('Phase 1: Record balances:')
        balances_old = assets_monitor.AssetsMonitor().get_balances_mp()
        logging.warning('Current balances (before arbitrage): %s' % balances_old)

        # Phase 2: check balances and verify premium
        logging.warning('Phase 2: Get balances and verify trade amount:')

        logging.warning('%s trade amount: %s' % (self.currency_pair, base_currency_trade_amount))

        logging.warning('Current %s balance in %s: %s' %
                        (self.base_currency, self.market_hi, balances_old[self.market_hi][self.base_currency]))

        logging.warning('Current %s balance in %s: %s' %
                        (self.quote_currency, self.market_lo, balances_old[self.market_lo][self.quote_currency]))

        base_currency_affordable_amount = '%.8f' % \
                                          (float(balances_old[self.market_lo][self.quote_currency]) /
                                           float(premium_calculator.get_price_in_size(
                                                 market=self.market_lo, currency_pair=self.currency_pair)['ask'])
                                           )
        logging.warning('Affordable %s amount in %s: %s' %
                        (self.base_currency, self.market_lo, base_currency_affordable_amount))

        base_currency_max_amount = min(float(balances_old[self.market_hi][self.base_currency]),
                                       float(base_currency_affordable_amount))

        logging.warning('Maximum %s trade amount: %.4f ' % (self.base_currency, base_currency_max_amount))

        if float(base_currency_trade_amount) < base_currency_max_amount * (1 - float(amount_margin)):
            logging.warning('Balance verification: PASS!')
        else:
            logging.warning('Not enough balance to trade!')
            raise BaseException('Execution status: Insufficient Fund!')

        # Verify premium, if not over threshold, halt execution.
        logging.warning('Verifying premium.')
        try:
            premium = premium_calculator.get_premium_mp(currency_pair=self.currency_pair)['premium']
        except BaseException as err:
            logging.warning('Getting premium failed. Error: %s' % err)
            return ''

        threshold = self.premium_threshold

        if float(premium) < float(threshold):
            logging.warning('Premium (%s) below threshold (%s). Halt execution.' % (premium, threshold))
            raise BaseException('Premium (%s) below threshold (%s). Execution halted.' % (premium, threshold))

        # Phase 3: Sell in market_hi and buy in market_lo

        logging.warning('Phase 3: Sell %s in %s and buy %s in %s' %
                        (self.base_currency, self.market_hi, self.base_currency, self.market_lo))

        pool = Pool()

        logging.warning('Selling %s in %s: amount = %s' %
                        (self.base_currency, self.market_hi, base_currency_trade_amount))
        pool.apply_async(trade_operator.trade_operator,
                         args=(self.market_hi, self.currency_pair, 'sell', base_currency_trade_amount))
        # trade_operator.trade_operator(self.market_hi, self.currency_pair, 'sell', base_currency_trade_amount)

        logging.warning('Buying %s in %s: amount = %s' %
                        (self.base_currency, self.market_lo, base_currency_trade_amount))
        pool.apply_async(trade_operator.trade_operator,
                         args=(self.market_lo, self.currency_pair, 'buy', base_currency_trade_amount))
        # trade_operator.trade_operator(self.market_lo, self.currency_pair, 'buy', base_currency_trade_amount)

        pool.close()
        pool.join()

        logging.warning('Arbitrage successfully proceeded! %s amount = %s' %
                        (self.base_currency, base_currency_trade_amount))

        # Phase 4: Report

        logging.warning('Phase 4: Report')
        logging.warning('Getting balances:')
        balances_new = assets_monitor.AssetsMonitor().get_balances_mp()
        logging.warning('Current balances (after arbitrage): %s' % balances_new)

        # profit report
        trade_report.profit_report(balances_old, balances_new, self.premium_report, self.premium_threshold,
                                   self.market_hi+'/'+self.market_lo, self.currency_pair, base_currency_trade_amount)

        logging.warning('=' * 50 + ' E N D ' + '=' * 50)

        return 'Arbitrage trader finished execution.'


if __name__ == '__main__':
    pass
    # ArbitrageTrader('ETC/BTC', 'huobi_pro', 'poloniex', premium_report='0.010').\
    #     arbitrage(base_currency_trade_amount='1.0')
