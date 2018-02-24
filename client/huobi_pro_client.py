import base64
import hashlib
import hmac
import json
import logging
from datetime import datetime
from urllib import parse
from urllib import request

from config import config_coin, api_keys

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=logging.WARNING)


# timeout in 60 seconds:
TIMEOUT = 60

API_HOST = 'api.huobi.pro'

SCHEME = 'https'

# language setting: 'zh-CN', 'en':
LANG = 'zh-CN'

DEFAULT_GET_HEADERS = {
    'Accept': 'application/json',
    'Accept-Language': LANG,
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)\
        Chrome/39.0.2171.71 Safari/537.36'
}

DEFAULT_POST_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Accept-Language': LANG,
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)\
        Chrome/39.0.2171.71 Safari/537.36'
}


class Dict(dict):

    def __init__(self, **kw):
        super().__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value


def _to_dict(d):
    return Dict(**d)


class ApiError(BaseException):
    pass


class ApiNetworkError(BaseException):
    pass


class ApiClient(object):

    def __init__(self, app_key, app_secret, asset_password=None, host=API_HOST):

        # Init api client object, by passing appKey and appSecret.

        self._accessKeyId = app_key
        self._accessKeySecret = app_secret.encode('utf-8')  # change to bytes
        self._assetPassword = asset_password
        self._host = host

    def get(self, path, auth=True, **params):

        # Send a http get request and return json object.
        if auth:
            qs = self._sign('GET', path, self._utc(), params)
        else:
            qs = params['qs']
        return self._call('GET', '%s?%s' % (path, qs), auth=auth)

    def post(self, path, obj=None):

        # Send a http post request and return json object.

        qs = self._sign('POST', path, self._utc())
        data = None
        if obj is not None:
            data = json.dumps(obj).encode('utf-8')
        return self._call('POST', '%s?%s' % (path, qs), data)

    def _call(self, method, uri, data=None, auth=True):

        url = '%s://%s%s' % (SCHEME, self._host, uri)
        # print(url)

        headers = DEFAULT_GET_HEADERS if method == 'GET' else DEFAULT_POST_HEADERS
        if self._assetPassword and auth:
            headers['AuthData'] = self._auth_data()
        req = request.Request(url, data=data, headers=headers, method=method)
        with request.urlopen(req, timeout=TIMEOUT) as resp:
            if resp.getcode() != 200:
                raise ApiNetworkError('Bad response code: %s %s' % (resp.getcode(), resp.reason))
            if auth:
                return self._parse(resp.read())
            else:
                return json.loads(resp.read())

    @staticmethod
    def _parse(text):

        result = json.loads(text.decode(), object_hook=_to_dict)
        if result.status == 'ok':
            return result.data
        raise ApiError('%s: %s' % (result['err-code'], result['err-msg']))

    def _sign(self, method, path, ts, params=None):

        self._method = method
        # create signature:
        if params is None:
            params = {}
        params['SignatureMethod'] = 'HmacSHA256'
        params['SignatureVersion'] = '2'
        params['AccessKeyId'] = self._accessKeyId
        params['Timestamp'] = ts
        # sort by key:
        keys = sorted(params.keys())
        # build query string like: a=1&b=%20&c=:
        qs = '&'.join(['%s=%s' % (key, self._encode(params[key])) for key in keys])
        # build payload:
        payload = '%s\n%s\n%s\n%s' % (method, self._host, path, qs)
        # print('payload:\n%s' % payload)
        dig = hmac.new(self._accessKeySecret, msg=payload.encode('utf-8'), digestmod=hashlib.sha256).digest()
        sig = self._encode(base64.b64encode(dig).decode())
        # print('sign: ' + sig)
        qs = qs + '&Signature=' + sig
        return qs

    def _auth_data(self):
        md5 = hashlib.md5()
        md5.update(self._assetPassword.encode('utf-8'))
        md5.update('hello, moto'.encode('utf-8'))
        s = json.dumps({"assetPwd": md5.hexdigest()})
        return self._encode(s)

    @staticmethod
    def _utc():
        return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')

    @staticmethod
    def _encode(s):
        return parse.quote(s, safe='')


class HuobiProClient(ApiClient):

    def __init__(self, base_currency='', quote_currency=''):
        api_key = api_keys.HUOBI_ACCESS_KEY
        api_secret = api_keys.HUOBI_SECRET_KEY
        trade_pw = api_keys.HUOBI_TRADE_PW
        super().__init__(app_key=api_key, app_secret=api_secret, asset_password=trade_pw)
        # self.client = ApiClient(api_key, api_secret, asset_password=trade_pw)
        self.account_id = self._get_account_id()
        self.base_currency = base_currency
        self.quote_currency = quote_currency
        self.base_currency_lower = self.base_currency.lower()
        self.quote_currency_lower = self.quote_currency.lower()
        self.currency_pair = self.base_currency_lower + self.quote_currency_lower

    def get_market(self):
        logging.info('Getting market data:')
        return self.get('/market/depth', auth=False, qs='symbol=' + self.currency_pair + '&type=step0')

    def get_bids(self):
        logging.info('Getting bids:')
        return self.get_market()['tick']['bids']

    def print_bids(self):
        data = self.get_bids()
        self._print_market_order(data, title='BIDS(BUY)')

    def get_asks(self):
        logging.info('Getting asks:')
        return self.get_market()['tick']['asks']

    def get_lowest_ask_price(self):
        return self.get_asks()[0][0]

    def print_asks(self):
        data = self.get_asks()[::-1]
        self._print_market_order(data, title='ASKS(SELL)')

    def _print_market_order(self, data, title=''):
        logging.info('Printing Market Order of %s' % title)
        self._br()
        logging.warning('  ' + '~'*10 + ''.join(title) + '~'*10 + '\n')
        logging.warning('    Price       Volume')
        for line in data:
            logging.warning('%10.8f\t%10.4f' % (line[0], line[1]))
        self._br()

    def get_average_bids_given_size(self, size):
        size = float(size)
        logging.info('Calculating average bid price based on the size of %.8f' % size)
        bids = self.get_bids()
        total = 0
        rest = size
        price_range = []
        for bid in bids:
            price, volume = bid
            if volume > rest:
                total += price * rest
                price_range.append([price, rest])
                rest = 0
                break
            total += price*volume
            rest -= volume
            price_range.append(bid)
        status = (rest <= 0)
        return status, '%.8f' % (total/size), price_range

    def get_average_asks_given_size(self, size):
        size = float(size)
        logging.info('Calculating average ask price based on the size of %.8f' % size)
        asks = self.get_asks()
        # print(asks)
        # precision = len(asks[0][0].split('.')[1])
        # print(precision)
        total = 0
        rest = size
        price_range = []
        for ask in asks:
            price, volume = ask
            if volume > rest:
                total += price * rest
                price_range.append([price, rest])
                rest = 0
                break
            total += price*volume
            rest -= volume
            price_range.append(ask)
        status = (rest <= 0)
        return status, '%.8f' % (total/size), price_range

    def get_symbols(self):
        logging.warning('Getting symbols for client:')
        return self.get('/v1/common/symbols')

    def get_user_info(self):
        logging.warning('Getting user info for client:')
        return self.get('/v1/users/user')

    def get_all_accounts(self):
        logging.info('Getting accounts for client:')
        return self.get('/v1/account/accounts')

    def get_base_currency_balance(self):
        balance_list = self.get('/v1/account/accounts/%s/balance' % self.account_id).list
        for line in balance_list:
            if line.currency == self.base_currency_lower and line.type == 'trade':
                return line.balance
        raise BaseException('%s balance not found in account! Check %s account!' %
                            (self.base_currency, self.base_currency))

    def get_quote_currency_balance(self):
        balance_list = self.get('/v1/account/accounts/%s/balance' % self.account_id).list
        for line in balance_list:
            if line.currency == self.quote_currency_lower and line.type == 'trade':
                return line.balance
        raise BaseException('%s balance not found in account! Check %s account!' %
                            (self.quote_currency, self.quote_currency))

    def get_specific_currency_balance(self, currency):
        balance_list = self.get('/v1/account/accounts/%s/balance' % self.account_id).list
        for line in balance_list:
            if line.currency == currency.lower() and line.type == 'trade':
                return line.balance
        raise BaseException('%s balance not found in account! Check %s account!' % (currency, currency))

    def print_balance_raw(self):
        accounts = self.get_all_accounts()
        logging.warning('All Accounts: ')
        logging.warning(accounts)
        logging.warning('Getting balance for client:')
        for acc in accounts:
            logging.warning('Getting sub account: %s' % acc)
            sub_accounts = self.get('/v1/account/accounts/%s/balance' % acc.id)
            logging.warning(sub_accounts)

    def get_balance(self):
        res = []
        accounts = self.get_all_accounts()
        # logging.warning('All Accounts: ')
        # logging.warning(accounts)
        # logging.warning('Getting balance for client:')
        for acc in accounts:
            # logging.warning('Getting sub account: %s' % acc)
            sub_accounts = self.get('/v1/account/accounts/%s/balance' % acc.id)
            res.append(sub_accounts)
        return res

    def print_balance(self):
        accounts = self.get_all_accounts()
        logging.warning('All Accounts: ')
        logging.warning(accounts)
        logging.warning('Getting balance for client:')
        account_id = accounts[0].id
        for acc in accounts:
            logging.warning('Getting sub account: %s' % acc)
            sub_accounts = self.get('/v1/account/accounts/%s/balance' % acc.id)
            self._br()
            logging.warning('Account ID: %s' % account_id)
            logging.warning('#\tCurrency\tType\t\tBalance')
            for i, currency in enumerate(sub_accounts.list):
                logging.warning('%d\t%s\t\t%s\t\t%s' % (i+1, currency.currency, currency.type, currency.balance))
            self._br()

    def _get_account_id(self):
        return self.get_all_accounts()[0].id

    @staticmethod
    def _br():
        logging.warning('\n' + '-'*50 + '\n')

    def _get_orders(self, types='pre-submitted,submitted,partial-filled,partial-canceled,filled,canceled'):
        return self.get('/v1/order/orders', symbol=self.currency_pair, states=types)

    def get_submitted_orders(self):
        return self._get_orders('submitted')

    def print_submitted_orders(self):
        logging.warning('Getting submitted orders:')
        order_info = self.get_submitted_orders()
        self._print_orders(order_info, title='ALL SUBMITTED ORDERS')

    def get_current_orders(self):
        return self._get_orders('submitted,partial-filled,partial-canceled')

    def print_current_orders(self):
        logging.warning('Getting current orders:')
        order_info = self.get_current_orders()
        self._print_orders(order_info, title='CURRENT ORDERS')

    def get_all_valid_orders(self):
        return self._get_orders('submitted,partial-filled,partial-canceled,filled,canceled')

    def print_all_valid_orders(self):
        logging.warning('Getting all valid orders:')
        order_info = self.get_all_valid_orders()
        self._print_orders(order_info, title='ALL VALID ORDERS')

    def get_filled_orders(self):
        return self._get_orders('filled')

    def get_all_orders(self):
        return self._get_orders()

    def print_all_orders(self):
        logging.warning('Getting all orders:')
        order_info = self.get_all_orders()
        self._print_orders(order_info, title='ALL ORDERS')

    def _print_orders(self, order_info, title=''):
        self._br()
        logging.warning('  ' + '~'*10 + ''.join(title) + '~'*10 + '\n')
        logging.warning('  #   Order\t       Amount\t          Price\t           Create Time\
                 Type        Field-Amount      Field-Cash      Field-Fees       Finished Time\
                      Source   State       Cancelled at')
        for i, line in enumerate(order_info):
            # logging.warning(line)
            logging.warning('%3d  %d\t%s\t%15s\t  %s  \t%10s\t%15s\t%15s\t%15s\t   %s\t  %s  \t%s\t%s' % (
                i+1,
                line.id,
                line.amount,
                line.price,
                datetime.fromtimestamp(line['created-at']/1000).strftime('%Y-%m-%d %H:%M:%S'),
                line.type,
                line['field-amount'],
                line['field-cash-amount'],
                line['field-fees'],
                datetime.fromtimestamp(line['finished-at']/1000).strftime('%Y-%m-%d %H:%M:%S'),
                line.source,
                line.state,
                '' if 0 == line['canceled-at'] else datetime.fromtimestamp(line['canceled-at']/1000).
                strftime('%Y-%m-%d %H:%M:%S')
            ))
        self._br()

    def create_order(self, amount, price, direction):
        order_id = self.post('/v1/order/orders', {
            'account-id': self.account_id,
            'amount': amount,
            'price': price,
            'symbol': self.currency_pair,
            'type': direction,
            'source': 'api'
        })
        logging.warning('Printing order_id:')
        logging.warning(order_id)
        return order_id

    def place_order(self, order_id):
        return self.post('/v1/order/orders/%s/place' % order_id)

    def print_order_details(self, order_id):
        order_info = self.get('/v1/order/orders/%s' % order_id)
        self._print_orders([order_info], title='ORDER DETAIL of ORDER # %s' % order_id)

    def get_order_status(self, order_id):
        return self.get('/v1/order/orders/%s' % order_id).state

    def get_order_detail(self, order_id):
        return self.get('/v1/order/orders/%s' % order_id)

    def is_order_success(self, order_id):
        order_status = self.get_order_status(order_id)
        return order_status == 'filled'

    def is_order_cancelled(self, order_id):
        order_status = self.get_order_status(order_id)
        return order_status == 'canceled'

    def cancel_order(self, order_id):
        return self.post('/v1/order/orders/%s/submitcancel' % order_id)

    def cancel_all_orders(self):
        logging.warning('Cancelling all current orders:')
        self.print_current_orders()
        orders = self.get_current_orders()
        for order in orders:
            order_id = order.id
            logging.warning('Cancelling order # %d' % order_id)
            self.cancel_order(order_id)
        logging.warning('All orders cancelled!')

    def get_financial_history(self):
        return self.get('/v1/query/finances')

    def print_financial_history(self):
        history = self.get_financial_history()
        for transaction in history:
            logging.warning(transaction)

    def withdraw_create(self, destination='', amount='', currency='', fee=''):

        """
        This function withdraws coin to other market
        :param destination: string of market name in ['poloniex']
        :param amount: string
        :param currency: string upper case
        :param fee: optional, string
        :return:
        """

        if destination == 'poloniex' and currency == 'BCC':
            deposit_address = config_coin.coin_deposit_address[destination]['BCH']
        else:
            deposit_address = config_coin.coin_deposit_address[destination][currency]

        qs = {
            'address': deposit_address,
            'amount': amount,
            'currency': currency.lower()
        }
        if fee:
            qs['fee'] = fee
        withdraw_id = self.post('/v1/dw/withdraw/api/create', qs)
        logging.info('Printing withdraw_id:')
        logging.info(withdraw_id)
        return withdraw_id

    def withdraw_cancel(self, withdraw_id):
        status = self.post('/v1/dw/withdraw-virtual/%s/cancel' % withdraw_id)
        logging.warning('Withdraw cancel request placed.')
        logging.info('Printing cancel status:')
        logging.info(status)
        return status

    def get_deposit_address(self, currency=''):
        addresses = self.get('/v1/dw/deposit-virtual/addresses', currency=currency.lower())
        logging.info('Printing addresses:')
        logging.info(addresses)
        return addresses


def test_withdraw():

    """
    This is to test withdraw of coins
    :return: status
    """
    test_amount = '0.1'
    currency = 'LTC'
    fee = ''
    client = HuobiProClient(currency)
    withdraw_id = client.withdraw_create(destination='poloniex', amount=test_amount, currency=currency, fee=fee)
    print(withdraw_id)
    print(client.withdraw_cancel(withdraw_id=withdraw_id))

if __name__ == '__main__':
    # test_withdraw()
    pass
    # print(HuobiProClient('ETH', 'BTC').get_average_asks_given_size('2.0'))
    # print(HuobiProClient().get_symbols())
    # print(HuobiProClient().get_user_info())
    # print(HuobiProClient().get_all_accounts())
    # print(HuobiProClient().print_balance_raw())
    # print(HuobiProClient('ETH','BTC').print_all_orders())
    # print(HuobiProClient().print_financial_history())
    # Huobi_Pro_Client('BCC').transfer('in', 'all', 'ETC')
    # Huobi_Pro_Client('BCC').transfer('out', 'all', 'ETC')
    # Huobi_Pro_Client('BCC').transfer('in', 'all', 'LTC')
    # print(Huobi_Pro_Client('BCC').transfer('out', 'all', 'BTC'))
