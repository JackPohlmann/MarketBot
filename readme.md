# Market Bot

Discord bot that simulates large value trading.

## Usage

The `$` symbol is (aptly) used to communicate with the bot.

* `$ipo symbol` creates a new stock with symbol `symbol`
* `$buy symbol amount` purchase `amount` of `symbol`
* `$sell symbol amount` sell `amount` of `symbol`
* `$stimulate` vote to pass stimulus, depositing a flat amount of cash to all participants
* `$inflate` vote to pass inflation, reducing a percentage of cash from all participants
* `$portfolio` list the requesting user's portfolio
* `$market` list all stock symbols and their top holders, sorted alphabetically 
* `$leaderboard` list all stock symbols, sorted by price 
* `${stock}` get information on the stock with symbol `{stock}`

## IPOing

Users wishing to participate can designate a stock symbol.
New portfolios are initialized with 50% of the total shares of their own stock and an equivalent value of cash.
The remaining 50% of shares are given to the Market Maker and can be purchased by all users.

## Market Maker

In lieu of resolving orders between participants, a Market Maker entity exists to provide liquidity (much like reality).
The price of a stock is directly determined by the number of outstanding shares.

## Slippage

Models slippage using a simple exponential model.