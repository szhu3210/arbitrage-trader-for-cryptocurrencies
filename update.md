01/18/2018: v3.7
1. Create account in Bitfinex.
2. Added funds to Bitfinex.

01/17/2018:
1. Implemented get_premium_async.

01/15/2018:
1. Debug the program.

01/14/2018:
1. Implemented async premiums_calculator, saving a lot of memory usage.
2. Fixed bugs.
3. Optimized the manager to make it faster.

01/13/2018:
1. Implemented new premium_calculator.
2. Implemented updated arbitrage manager to adapt to the new premium_calculator.

01/12/2018: v3.6
1. Backup codes in v3.6.
2. Implement market okex.
3. Fixed some bugs in pool.
4. Recycle redundant files to legacy.
5. Shorten configs.

01/11/2018:
1. Implemented unified_client. Above the client level, there is no market specific codes.

01/10/2018:
1. Updated even level and coin allocation.
2. Schedule new market, design interface.

01/09/2018:
1. Changed the pool to specify the number of threads, largely improve the speed of execution.

01/08/2018: v3.5
1. Implement seckill script using multithreading. Concurrency number is 16. To improve, use asyncio.

01/04/2018:
2. Adjusted the trade pair, added XTP/USDT, deleted all BTC based pairs.
3. Implement a fast trade script for the lottery/seckill game.

12/22/2017: v3.4
1. Implemented coin balancer (adaptive, soft).

12/19/2017:
1. Implement coin balancer (soft), adaptively balance the coins by trading.

12/18/2017:
4. Changed BCC to BCH in huobipro.

12/13/2017:
1. Fixed a few bugs.

12/12/2017:
1. Analysis of all premiums and decide the threshold.
2. Test the trader (sell DASH/USDT to get more USDT balance).
3. Now all the risk lies in the trader and the risk of the exchanges.

12/11/2017: v3.3
1. New subversion for backup.
2. Start to write new trade model that use reversed arbitrage to balance coins.

12/9/2017:
1. Record bug in Phase 1 of trader.

12/2/2017:
1. Increase buy margin of coins in poloniex client to ensure buy/sell success.

11/30/2017: v3.2
1. Add DASH.
2. Update delay list to per pair delay.

11/29/2017:
1. Add delay when there is error of premium that lead to negative profit.

11/26/2017:
1. Add DASH (?). No.

11/25/2017: v3.1
1. Tested margin 0.002 and 0.004.

11/11/2017:
1. Continue on the refactor of the code.
2. Re-organize the code using folders.

11/10/2017:
1. Continue on the refactor of the code.

11/9/2017:
1. Continue on the refactor of the code.

11/8/2017:
1. Write coin transfer_pro.
2. Write coin_balancer_pro.

11/7/2017:
1. Updated profit calculator to use USDT instead of CNY.
2. Updated results recorder to use USDT instead of CNY.

11/6/2017:
1. Delete all the fiat trader.
2. Use new Huobi API key.

9/25/2017:
1. Added the exception handler for coin transfer failure.
2. Adjusted the parameters in coin balancer.

9/24/2017: V2.8
1. Changed ETC trade amount. 
2. Adjust all fiat trade threshold to 0.013. Pro trade kept 0.012.

9/22/2017:
1. Update pro trader currency transfer (from main to pro) amount from 1.02 to 1.03.

9/21/2017:
1. Add timer for email client.
2. Add email exception handling for main trader.

9/19/2017:
1. Updated limit of coin transfer.
2. Added BCC transfer function.
3. Updated coin balancer.

9/12/2017:
1. Establish remote server.
2. Authorize remote server to the gmail server.
3. Added scripts for login, get logs, autorun, etc in remote server.

9/11/2017:
1. Add second verification to all traders.
2. Tested on server at Beijing.
3. Add timeout for BTC, LTC request functions.

9/9/2017:
1. Tested Linux system. Dependencies: Python3.6, Poloniex 0.4.3.
2. Added a time recorder to record the duration of a trade.
3. Reduce time of trading.
4. Disable balance check in all operators.
5. Disable bids print and asks print.
6. Disable print order details in all operators.

9/6/2017: V2.1
1. Fixed a few bugs.
2. Add description of market in email report.
3. Add timer to trader.
4. Add exception catcher to trader.
5. Checked LTC deposit problem and submitted a new detailed ticket.

8/13/2017: v2.0
1. Implemented all 4 pairs (BTC, ETH, LTC, ETC) and auto coin balancer in Huobi and Poloniex.
2. Implemented a logger in csv format recording each trade detail and assets.
3. Reduce the premium calculation time by 40%, typically 10 seconds.
4. Fixed a few bugs.
5. Use market quotes instead of ticker to calculate premiums.
6. Added a premium checker to avoid wrong market price data.

7/11/2017: v1.1
1. Implemented ETH/BTC auto arbitrage and ETH/LTC auto arbitrage.
2. Multiprocessing for premium calculator.
3. Domestic email client updated.
4. Coin balancer for BTC, LTC and ETH implemented.
5. Solved poloniex nonce problem.