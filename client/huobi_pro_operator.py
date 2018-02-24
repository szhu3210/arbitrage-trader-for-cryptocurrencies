import logging
import time

from config import config_trader
from client import huobi_pro_client

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=logging.WARNING)


class HuobiProOperator:

    @staticmethod
    def sell_pro(base_currency, quote_currency, amount):

        huobi_pro_client_instance = huobi_pro_client.HuobiProClient(
            base_currency=base_currency, quote_currency=quote_currency)

        # Amount to sell
        logging.warning('Amount to sell: %s' % amount)

        market_available, avg_price, sell_prices = huobi_pro_client_instance.get_average_bids_given_size(float(amount) * 2)
        logging.warning(str(market_available) + ' ' + str(avg_price) + ' ' + str(sell_prices))

        logging.warning('Average Sold Price (estimated): %s' % avg_price)

        sell_price = ('%.' + config_trader.huobi_pro_currency_pair_precision[base_currency + '/' + quote_currency]
                      + 'f') % (sell_prices[-1][0] * 0.99)  # lower sell_price by 1 % to ensure trade success
        logging.warning('Set Sell Price: %s ' % sell_price)

        # Sell Pro
        if market_available:

            # Create order and place order
            price = sell_price
            direction = 'sell-limit'
            order_id = huobi_pro_client_instance.create_order(amount, price, direction)
            huobi_pro_client_instance.place_order(order_id)

            # Check order status, if success report
            count = 0
            while count <= 6:
                if huobi_pro_client_instance.is_order_success(order_id):
                    logging.warning('Order Successfully Filled!')
                    break
                time.sleep(1)
                count += 1
            if count > 6:  # order not placed within 30 seconds
                logging.warning('Order Failed! The following is detailed info.')
                huobi_pro_client_instance.print_order_details(order_id)
                logging.warning('Cancelling order...')
                huobi_pro_client_instance.cancel_order(order_id)
                time.sleep(1)
                if huobi_pro_client_instance.is_order_cancelled(order_id):
                    logging.warning('Order cancelled successfully!')
                else:
                    logging.warning('Please check if the order is cancelled. Manually handle exceptions.')
                    # raise 'Exception: order not canceled successfully!'
                huobi_pro_client_instance.print_order_details(order_id)
            return huobi_pro_client_instance.get_order_detail(order_id)
        else:
            logging.warning('No enough market for selling %s of amount %s' % (base_currency, amount))

    @staticmethod
    def buy_pro(base_currency, quote_currency, amount):

        huobi_pro_client_instance = huobi_pro_client.HuobiProClient(
            base_currency, quote_currency=quote_currency)

        # Amount to buy
        logging.warning('Amount to buy: %s' % amount)

        market_available, avg_price, buy_prices = huobi_pro_client_instance.get_average_asks_given_size(float(amount) * 2)
        logging.warning(str(market_available) + ' ' + str(avg_price) + ' ' + str(buy_prices))

        logging.warning('Average Bought Price (estimated): %s' % avg_price)

        buy_price = ('%.' + config_trader.huobi_pro_currency_pair_precision[base_currency + '/' + quote_currency]
                     + 'f') % (buy_prices[-1][0] * 1.01)  # raise buy_price by 1 % to ensure trade success
        logging.warning('Set Buy Price: %s ' % buy_price)

        # Buy Pro
        if market_available:

            # Create order and place order
            price = buy_price
            direction = 'buy-limit'
            order_id = huobi_pro_client_instance.create_order(amount, price, direction)
            huobi_pro_client_instance.place_order(order_id)

            # Check order status, if success report
            count = 0
            while count <= 6:
                if huobi_pro_client_instance.is_order_success(order_id):
                    logging.warning('Order Successfully Filled!')
                    # huobi_pro_client_instance.printOrderDetails(order_id)
                    break
                time.sleep(1)
                count += 1

            if count > 6:  # order not placed within 30 seconds
                logging.warning('Order Failed! The following is detailed info.')
                huobi_pro_client_instance.print_order_details(order_id)
                logging.warning('Cancelling order...')
                huobi_pro_client_instance.cancel_order(order_id)
                time.sleep(1)
                if huobi_pro_client_instance.is_order_cancelled(order_id):
                    logging.warning('Order cancelled successfully!')
                else:
                    logging.warning('Please check if the order is cancelled. Manually handle exceptions.')
                    # raise 'Exception: order not canceled successfully!'
                huobi_pro_client_instance.print_order_details(order_id)

            return huobi_pro_client_instance.get_order_detail(order_id)

        else:
            logging.warning('No enough market for buying %s of amount %s' % (base_currency, amount))

if __name__ == '__main__':
    pass
