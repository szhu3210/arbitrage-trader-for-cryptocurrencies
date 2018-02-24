import logging
from aux import email_client, trade_recorder, assets_monitor
from client import poloniex_client
from config import config_coin


def profit_report(balances_old, balances_new, premium_report, premium_threshold,
                  market, currency_pair, trade_amount):

    # profit report

    logging.warning('Premium Report: \n%s (threshold: %s)' % (premium_report, premium_threshold))

    assets_old = assets_monitor.AssetsMonitor().cal_assets(balances_old)
    assets_new = assets_monitor.AssetsMonitor().cal_assets(balances_new)

    logging.warning('Assets Report: \n%s' % assets_new)

    profit_report_data = assets_monitor.AssetsMonitor().cal_profits(assets_old=assets_old,
                                                                    assets_new=assets_new)
    profit_report_text = str(profit_report_data)
    profit_report_short = profit_report_data['usdt_equ']
    logging.warning('Profit Report: \n%s' % profit_report_text)

    base_currency, quote_currency = currency_pair.split('/')
    prices = poloniex_client.PoloniexClient().returnTicker()
    profit_usdt = float(profit_report_short)
    trade_amount_usdt = float(trade_amount) * \
        float(prices['USDT_' + config_coin.currency_name_standard_to_poloniex(base_currency)]['last'])
    profit_ratio_num = profit_usdt / trade_amount_usdt
    profit_ratio_report = '%.4f %%' % (profit_usdt / trade_amount_usdt * 100)

    logging.warning('Report by email...')

    email_client.EmailClient().notify_me_by_email(
        title='Arbitrage (%s, %s, %s, %s) successfully proceeded!' %
              (currency_pair, market, premium_report, profit_report_short),
        content='Trade amount: %s \nOld balances: \n%s \nNew balances: \n%s\n\n'
                'Premium Report: \n%s\n\nAssets Report:\n%s\n\n Profit Report: \n %s (%s)' % (
                    trade_amount, balances_old, balances_new, premium_report, assets_new,
                    profit_report_text, profit_ratio_report))

    # save to csv
    trade_recorder.save_trading_result(pair=currency_pair, market=market,
                                       premium_report=premium_report, premium_threshold=premium_threshold,
                                       trade_amount=trade_amount, profit=profit_report_short,
                                       assets=assets_new, profit_ratio_num=profit_ratio_num)

if __name__ == '__main__':
    pass
    # from aux import assets_monitor
    # a = assets_monitor.AssetsMonitor()
    # b = a.get_balances_mp()
    # profit_report(b, b, '0.022', 'huobi_pro/poloniex', 'ETH/BTC', '2.0')
