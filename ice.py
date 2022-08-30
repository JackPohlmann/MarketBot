import json

import market as m

def save_market(market, fname):
    with open(fname, 'w') as ofile:
        json.dump(market_to_dict(market), ofile, indent=4)

def load_market(fname):
    with open(fname) as ifile:
        market_from_dict(json.load(ifile))

def save_fed(fed, fname):
    with open(fname, 'w') as ofile:
        json.dump(fed_to_dict(fed), ofile, indent=4)

def load_fed(fname):
    with open(fname) as ifile:
        m.FED = fed_from_dict(json.load(ifile))

def save_users(users, fname):
    with open(fname, 'w') as ofile:
        json.dump(users, ofile, indent=4)

def load_users(fname):
    with open(fname) as ifile:
        return json.load(ifile)



def fed_to_dict(fed):
    fdict = {}
    fdict['stimulus'] = fed.stimulus
    fdict['inflation'] = fed.inflation
    fdict['stimulus_ctr'] = fed.stimulus_ctr
    fdict['inflation_ctr'] = fed.inflation_ctr
    return fdict

def fed_from_dict(fdict):
    stimulus = fdict['stimulus']
    inflation = fdict['inflation']
    stimulus_ctr = fdict['stimulus_ctr']
    inflation_ctr = fdict['inflation_ctr']
    fed = m.Fed(stimulus, inflation)
    fed.stimulus_ctr = stimulus_ctr
    fed.inflation_ctr = inflation_ctr
    return fed

def market_to_dict(market):
    mdict = {}
    tickers = []
    portfolios = []
    for ticker in market.stocks.values():
        tickers.append(ticker_to_dict(ticker))
    for portfolio in market.portfolios.values():
        portfolios.append(portfolio_to_dict(portfolio))
    mdict['tickers'] = tickers
    mdict['portfolios'] = portfolios
    return mdict

def market_from_dict(mdict):
    market = m.MarketMaker()
    m.MARKET = market
    #tickers first
    stocks = {}
    for ticker in mdict['tickers']:
        stocks[ticker['symbol']] = ticker_from_dict(ticker)
    market.stocks = stocks
    #portfolios second
    portfolios = {}
    for port in mdict['portfolios']:
        portfolios[port['symbol']] = portfolio_from_dict(port)
    market.portfolios = portfolios
    return market

def portfolio_to_dict(portfolio):
    pdict = {}
    pdict['symbol'] = portfolio.symbol
    pdict['cash'] = portfolio.cash
    positions = []
    for pos in portfolio.positions.values():
        positions.append(position_to_dict(pos))
    pdict['positions'] = positions
    return pdict

def portfolio_from_dict(pdict):
    symbol = pdict['symbol']
    cash = pdict['cash']
    positions = {}
    for pos in pdict['positions']:
        positions[pos['symbol']] = position_from_dict(pos)
    portfolio = m.Portfolio(symbol, 0, cash)
    portfolio.positions = positions
    return portfolio

def position_to_dict(position):
    pdict = {}
    pdict['owner'] = position.owner
    pdict['symbol'] = position.symbol
    pdict['basis'] = position.basis
    return pdict

def position_from_dict(pdict):
    owner = pdict['owner']
    symbol = pdict['symbol']
    basis = pdict['basis']
    position = m.Position(owner, symbol, 0, 0)
    position.basis = basis
    return position

def ticker_to_dict(ticker):
    tdict = {}
    tdict["symbol"] = ticker.symbol
    tdict["shareholders"] = ticker.shareholders
    return tdict

def ticker_from_dict(tdict):
    symbol = tdict["symbol"]
    ticker = m.Ticker(symbol)
    shareholders = tdict["shareholders"]
    # set the outstanding value
    outstanding = ticker.total
    maj = symbol
    for sym in shareholders.keys():
        outstanding -= shareholders[sym]
        if shareholders[sym] > shareholders[maj]:
            maj = sym
    # set values
    ticker.outstanding = outstanding
    ticker.majority = maj
    ticker.shareholders = shareholders
    return ticker

