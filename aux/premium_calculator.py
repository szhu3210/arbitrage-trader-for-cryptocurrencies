import logging
from multiprocessing import Pool
from aux import timeout
from client import unified_client
from config import config_trader
import asyncio
import ccxt

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=logging.WARNING)


class PremiumValueException(Exception):
    pass


def get_price_in_size(market='', currency_pair='', size='', margin='0', async=False):

    if async:
        return get_price_in_size_async(market, currency_pair, size, margin)

    base_currency, quote_currency = currency_pair.split('/')

    if not size:
        size = config_trader.trade_size[base_currency]

    if margin != 0:
        size = '%.8f' % (float(size) * (1 + float(margin)))

    return unified_client.UnifiedClient(market).get_ticker_with_size(base_currency, quote_currency,
                                                                     base_currency_trade_size=size)


async def get_price_in_size_async(market='', currency_pair='', size='', margin='0'):

    base_currency, quote_currency = currency_pair.split('/')

    if not size:
        size = config_trader.trade_size[base_currency]

    if margin != 0:
        size = '%.8f' % (float(size) * (1 + float(margin)))

    client = unified_client.UnifiedClient(market, True)

    try:
        res = await client.get_ticker_with_size_async(base_currency, quote_currency,
                                                                     base_currency_trade_size=size)
    except BaseException as err:
        return err

    res['market'] = market
    res['currency_pair'] = currency_pair

    return res


def get_prices_mp(currency_pair_first=False):

    """
    Get all prices in all currency_pairs in all markets
    :return: dict[market_name][currency_pair]['bid'/'ask']
    """

    res = {}

    pool = Pool(len(config_trader.market_list)*len(config_trader.trade_currency_pairs))

    if not currency_pair_first:
        for market in config_trader.market_list:
            res[market] = {}
            for currency_pair in config_trader.trade_currency_pairs:
                res[market][currency_pair] = \
                    pool.apply_async(get_price_in_size,
                                     kwds={'market': market, 'currency_pair': currency_pair})
    else:
        for currency_pair in config_trader.trade_currency_pairs:
            res[currency_pair] = {}
            for market in config_trader.market_list:
                res[currency_pair][market] = \
                    pool.apply_async(get_price_in_size,
                                     kwds={'market': market, 'currency_pair': currency_pair})

    pool.close()
    pool.join()
    # time.sleep(5)

    for k1 in res:
        for k2 in res[k1]:
            try:
                res[k1][k2] = res[k1][k2].get(timeout=1)
            except BaseException as err:
                logging.warning('Error in getting prices. (%s, %s)' % (k1, k2))
                pass

    pool.terminate()

    subres = {}
    failed = []
    for k1 in res:
        all_ok = True
        for k2 in res[k1]:
            if not isinstance(res[k1][k2], dict):
                failed.append(k1)
                all_ok = False
                break
        if all_ok:
            subres[k1] = res[k1]

    logging.info(res)
    logging.info(subres)
    logging.warning('Getting prices: %d/%d success. Failed ones: %s' % (len(subres), len(res), failed))
    return subres


def get_prices_async(currency_pair_first=False):

    """
    Get all prices in all currency_pairs in all markets
    :return: dict[market_name][currency_pair]['bid'/'ask']
    """

    res = {}

    tasks = []

    i = 0

    if not currency_pair_first:
        for market in config_trader.market_list:
            res[market] = {}
            for currency_pair in config_trader.trade_currency_pairs:
                res[market][currency_pair] = i
                task = asyncio.ensure_future(get_price_in_size(market, currency_pair, async=True))
                tasks.append(task)
                i += 1
    else:
        for currency_pair in config_trader.trade_currency_pairs:
            res[currency_pair] = {}
            for market in config_trader.market_list:
                res[currency_pair][market] = i
                task = asyncio.ensure_future(get_price_in_size(market, currency_pair, async=True))
                tasks.append(task)
                i += 1

    loop = asyncio.get_event_loop()
    done, pending = loop.run_until_complete(asyncio.wait(tasks))
    results = [future.result() for future in done]
    # print(results)
    # print(res)

    subres = {}
    failed = []

    for result in results:
        if isinstance(result, dict):
            if currency_pair_first:
                res[result['currency_pair']][result['market']] = result
            else:
                res[result['currency_pair']][result['market']] = result

    # print(res)

    # print(res)
    for k1 in res:
        all_ok = True
        for k2 in res[k1]:
            if not isinstance(res[k1][k2], dict):
                failed.append(k1)
                all_ok = False
                break
        if all_ok:
            subres[k1] = {}
            for k2 in res[k1]:
                subres[k1][k2] = res[k1][k2]

    # logging.warning(res)
    # logging.warning(subres)
    logging.warning('Getting prices: %d/%d success. Failed ones: %s' % (len(subres), len(res), failed))

    # loop.close()

    return subres


@timeout.timeout(60, 'Timeout: get_premium_mp has been running for more than 60 seconds.')
def get_premium_mp(currency_pair='', size='', market_hi='', market_lo='', disable_mp=False):

    if disable_mp:
        result = dict()
        for market in [market_hi, market_lo]:
            result[market] = get_price_in_size(market=market, currency_pair=currency_pair, size=size)
        highest_bid = result[market_hi]['bid']
        lowest_ask = result[market_lo]['ask']
    else:
        result = dict()
        pool = Pool(2)
        for market in [market_hi, market_lo]:
            result[market] = pool.apply_async(get_price_in_size,
                                              kwds={'market': market, 'currency_pair': currency_pair, 'size': size})
        pool.close()
        pool.join()

        highest_bid = result[market_hi].get(timeout=1)['bid']
        lowest_ask = result[market_lo].get(timeout=1)['ask']

        pool.terminate()

    premium = float(highest_bid)/float(lowest_ask)-1

    if premium > float(config_trader.premium_invalid_threshold):
        raise PremiumValueException('Premium value possible error! Premium: %.4f, %s, %s' %
                                    (premium, market_hi, market_lo))

    res = dict()
    res['currency_pair'] = currency_pair
    res['premium'] = "%.4f" % premium
    res['market_hi'] = market_hi
    res['market_lo'] = market_lo
    return res


@timeout.timeout(60, 'Timeout: get_premium_async has been running for more than 60 seconds.')
def get_premium_async(currency_pair='', size='', market_hi='', market_lo=''):

    tasks = []

    task = asyncio.ensure_future(get_price_in_size_async(market_hi, currency_pair, size))
    tasks.append(task)
    task = asyncio.ensure_future(get_price_in_size_async(market_lo, currency_pair, size))
    tasks.append(task)

    loop = asyncio.get_event_loop()
    done, pending = loop.run_until_complete(asyncio.wait(tasks))
    results = [future.result() for future in done]
    # print(results)
    # print(res)

    res = {}
    failed = []

    for result in results:
        if isinstance(result, dict):
            res[result['market']] = result
        else:
            failed.append(result)
            raise BaseException('Error in get_premium_async: getting prices failed. (%s)' % str(failed))

    highest_bid = res[market_hi]['bid']
    lowest_ask = res[market_lo]['ask']

    premium = float(highest_bid) / float(lowest_ask) - 1

    if premium > float(config_trader.premium_invalid_threshold):
        raise PremiumValueException('Premium value possible error! Premium: %.4f, %s, %s' %
                                    (premium, market_hi, market_lo))

    res = dict()
    res['currency_pair'] = currency_pair
    res['premium'] = "%.4f" % premium
    res['market_hi'] = market_hi
    res['market_lo'] = market_lo
    return res


def cal_premium(prices, currency_pair):

    res = []

    for market_hi, market_lo in config_trader.market_pairs:
        highest_bid = prices[market_hi]['bid']
        lowest_ask = prices[market_lo]['ask']
        premium = float(highest_bid) / float(lowest_ask) - 1
        temp = dict()
        temp['currency_pair'] = currency_pair
        temp['premium'] = "%.4f" % premium
        temp['market_hi'] = market_hi
        temp['market_lo'] = market_lo
        if abs(premium) > float(config_trader.premium_invalid_threshold):
            logging.warning('Premium value possible error! Premium: %s' % temp)
        else:
            res.append(temp)

    return res


def cal_premiums(prices):

    res = []

    for currency_pair in prices:
        res.extend(cal_premium(prices[currency_pair], currency_pair))

    return res


@timeout.timeout(60, 'Timeout: get_premiums_mp has been running for more than 60 seconds.')
def get_premiums_mp():

    res = cal_premiums(get_prices_mp(currency_pair_first=True))

    res.sort(key=lambda x: float(x['premium']), reverse=True)

    return res


@timeout.timeout(60, 'Timeout: get_premiums_async has been running for more than 60 seconds.')
def get_premiums_async():

    res = cal_premiums(get_prices_async(currency_pair_first=True))

    res.sort(key=lambda x: float(x['premium']), reverse=True)

    return res


if __name__ == '__main__':
    pass
    # print(get_prices_async())
    # print(get_price_in_size('huobipro', currency_pair='BCH/BTC', size='100'))
    # premiums = get_premium_mp('BTC/USDT', config_trader.trade_size['BTC'], 'poloniex', 'huobipro', disable_mp=False)
    premiums = get_premium_async('XRP/USDT', config_trader.trade_size['XRP'], 'poloniex', 'huobipro')
    # print(premiums)
    # premiums = get_premiums_async()
    print(premiums)
