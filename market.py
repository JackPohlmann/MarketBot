'''
market

source for market bot


'''
import numpy as np
import scipy.stats

"""
TODO::Commands
- liquidate/sellall
- $buy/$sell max

TODO::2.0
- persistence (Pickle)
- 

TODO::3.0
- config.py for IPO_AMOUNT, etc.
- historical prices -> plots

TODO::4.0
- derivatives

"""
IPO_AMOUNT = 500_000
IPO_PRICE = 50

DEF_STIMULUS = 1e-4
DEF_INFLATION = .0015

class StockException(Exception):
  pass

class NoSuchSymbol(StockException):
  pass

class NotEnoughFunds(StockException):
  pass

class NotEnoughShares(StockException):
  pass

def log(s):
  #print(s)
  pass


class PriceModel:
  '''
  evaluates stock price based on outstanding shares
  cash value of a trade is determined by summing all prices for that amount of shares
  '''
    def __init__(self, ipo_price, total_shares):
        self.ipo_price = ipo_price
        self.total_shares = total_shares
        self.model = PriceModel.create_model(ipo_price, total_shares)

    @staticmethod
    def create_model(ipo_price, total_shares):
        pareto = np.array([scipy.stats.pareto.pdf(np.arange(total_shares) + 1, 1 / ipo_price, loc=0, scale=1)])[0].T
        os_array = (np.arange(total_shares) + 1).astype(float)
        norm = pareto[int(total_shares/2) - 1]
        scl = ((total_shares/2) - os_array) / (total_shares/2)
        exp = ipo_price ** (scl + 1)
        return exp * (pareto / norm)

    def price_at(self, remaining):
        return self.model[int(remaining) - 1]

    def block_price(self, remaining_low, remaining_high):
        idxl = int(remaining_low) - 1
        idxh = int(remaining_high)
        return np.trapz(self.model[idxl:idxh])


class MarketMaker:
  '''
  market maker entity
  holds all outstanding shares and an unlimited amount of cash
  '''
  def __init__(self):
    self.stocks = {}
    self.portfolios = {}
    self.price_model = PriceModel(IPO_PRICE, IPO_AMOUNT)

  def ipo(self, symbol):
    self.new_stock(symbol)
    log("New ipo: {:}".format(symbol))

  def buy(self, buyer, symbol, amount):
    self.check_sym(buyer)
    self.check_sym(symbol)
    ticker = self.get_ticker(symbol)

    if amount <= 0:
      raise StockException
    if amount >= ticker.outstanding:
      raise NotEnoughShares

    block_cost = self.price_model.block_price(ticker.outstanding - amount, ticker.outstanding)

    prev_majority = ticker.get_majority()
    self.get_portfolio(buyer).buy(symbol, block_cost, amount)
    post_majority = ticker.get_majority()
    
    suf = "New majority shareholder: {:}\n".format('$' + post_majority) if post_majority != prev_majority else ""
    return "{:} bought {:} shares in {:}\n".format('$' + buyer, amount, '$' + symbol) + suf + '\n' + Ticker.header() + '\n' + str(self.get_ticker(symbol))
    #

  def sell(self, seller, symbol, amount):
    self.check_sym(seller)
    self.check_sym(symbol)
    ticker = self.get_ticker(symbol)

    if amount <= 0:
      raise StockException
    if symbol not in self.portfolios[seller].positions.keys():
      raise NotEnoughShares
    
    block_sale = self.price_model.block_price(ticker.outstanding, ticker.outstanding + amount)

    prev_majority = ticker.get_majority()
    self.get_portfolio(seller).sell(symbol, block_sale, amount)
    post_majority = ticker.get_majority()

    suf = "New majority shareholder: {:}\n".format('$' + post_majority) if post_majority != prev_majority else ""
    return "{:} sold {:} shares in {:}\n".format('$' + seller, amount, '$' + symbol) + suf + '\n' + Ticker.header() + '\n' + str(self.get_ticker(symbol))

  
  def update(self, ticker, amount):
    pass

  def get_ticker(self, symbol):
    return self.stocks[symbol]

  def get_portfolio(self, symbol):
    self.check_sym(symbol)
    return self.portfolios[symbol]

  def new_stock(self, symbol):
    self.stocks[symbol] = Ticker(symbol)
    amt = int(IPO_AMOUNT/ 2)
    cash = self.price_model.block_price(IPO_AMOUNT - amt, IPO_AMOUNT)
    self.portfolios[symbol] = Portfolio(symbol, amt, cash)

  def check_sym(self, symbol):
    if symbol not in self.stocks.keys():
      raise NoSuchSymbol(symbol)

  # data methods
  def market_cap(self):
    mcap = 0
    for s in self.stocks.values():
      mcap += IPO_AMOUNT * s.get_price()
    for p in self.portfolios.values():
      mcap += p.cash
    return mcap

  # print methods
  def print_stock(self, symbol):
    if symbol not in self.stocks.keys():
      raise NoSuchSymbol
    stock = self.stocks[symbol]
    ticker = self.get_ticker(symbol)

    msg = Ticker.header() + "\n"
    msg += str(ticker) + "\n\n"

    #majority shareholder
    ms = ticker.get_majority()

    shs = list(ticker.shareholders.keys())
    shs.sort(key=lambda sh: ticker.shareholders[sh])
    shs.reverse()

    msg += "{:<6}{:<8}{:>12}\n".format("Pos.", "Founder", "Pct. Owned")
    counter = 0
    for sh in shs:
      counter += 1
      msg += "{:<6}{:<8}{:>11.2f}%\n".format(counter, "$" + sh, 100 * ticker.shareholders[sh] / IPO_AMOUNT)
    return msg

  def print_market(self):
    msg = Ticker.header() + "\n"
    tickers = list(self.stocks.values())
    tickers.sort(key=Ticker.get_price)
    tickers.reverse()
    for t in tickers:
      msg += str(t) + "\n"
    return msg

  def print_leaderboard(self):
    lb = [port for port in self.portfolios.values()]
    lb.sort(key=lambda p: p.total_value())
    lb.reverse()
    msg = '{:<6}{:<8}{:>16}\n'.format('Pos.', 'Founder', 'Total Value')
    count = 1
    for port in lb:
      msg += '{:<6}{:<8}{:>16.3e}\n'.format(count, "$" + port.symbol, port.total_value())
      count += 1
    return msg


# pickle
MARKET = MarketMaker()

class Fed:
  '''
  voting system that manipulates the cash positions of all participants
  '''
  def __init__(self, stimulus, inflation):
    self.stimulus = stimulus
    self.inflation = inflation
    self.stimulus_ctr = 0
    self.inflation_ctr = 0
  
  def stimulate(self):
    self.stimulus_ctr += 1
    stimmy = self.get_stimulus_value()
    for p in MARKET.portfolios.values():
      p.cash += stimmy
  
  def get_stimulus_value(self):
    inflation_factor = (1 + self.inflation) ** self.inflation_ctr
    base = MARKET.market_cap()
    return self.stimulus * inflation_factor * base
    
  def inflate(self):
    self.inflation_ctr += 1
    infl = self.get_inflation_pct()
    for p in MARKET.portfolios.values():
      p.cash *= infl

  def get_inflation_pct(self):
    stimulus_factor = self.stimulus_ctr
    base = self.inflation
    return (1 - base) ** stimulus_factor
    
FED = Fed(DEF_STIMULUS, DEF_INFLATION)

class Portfolio:
  '''
  a user's portfolio
  tracks the amount of each symbol that a user owns
  '''
  #TODO: track basis throughout. use basis to determine total market cap
  def __init__(self, symbol, shares, cash):
    self.symbol = symbol
    self.positions = {}
    self.cash = cash
    basis = MARKET.price_model.block_price(IPO_AMOUNT - shares, IPO_AMOUNT)
    self.new_position(symbol, basis, shares)

  def __str__(self):
    msg = Position.header()
    value = 0
    basis = 0
    positions = list(self.positions.values())
    positions.sort(key=Position.get_value)
    positions.reverse()
    for position in positions:
      msg += "\n" + str(position)
      value += position.get_value()
      basis += position.basis
    msg += "\n"
    msg += Position.COLF.format('Cash', 1.00, 1.00, int(self.cash), 0, 0, self.cash)
    value += self.cash
    basis += self.cash
    msg += "\n"
    msg += "\n{:>16}{:>16}{:>16}".format("Total", "Basis", "Total G/L")
    msg += "\n{:>16.3e}{:>16.3e}{:>16.3e}".format(value, basis, value - basis)
    return msg

  def get_position(self, symbol):
    if symbol not in self.positions.keys():
      raise NoSuchSymbol
    return self.positions[symbol]

  def chk_position(self, symbol):
    return symbol in self.positions.keys()

  def new_position(self, symbol, basis, amount):
    self.positions[symbol] = Position(self.symbol, symbol, basis, amount)

  def rm_position(self, symbol):
    del self.positions[symbol]

  def total_value(self):
    tv = 0
    for position in self.positions.values():
      tv += position.get_value()
    return tv + self.cash

  def buy(self, symbol, basis, amount):
    if basis > self.cash:
      raise NotEnoughFunds
    if not self.chk_position(symbol):
      self.new_position(symbol, basis, amount)
    else:
      self.get_position(symbol).buy(basis, amount)
    self.cash -= basis

  def sell(self, symbol, basis, amount):
    if not self.chk_position(symbol):
      raise NotEnoughShares
    self.get_position(symbol).sell(basis, amount)
    if self.get_position(symbol).get_amount() == 0:
      self.rm_position(symbol)
    self.cash += basis


class Position:
  '''
  a functional link that connects a position owner to a symbol
  '''
  COLS = ['Symbol', 'Price', 'Average', 'Amount', 'Basis', 'G/L', 'Value']
  COLH = '{:<12}{:>8}{:>12}{:>12}{:>16}{:>16}{:>16}'
  COLF = '{:<12}{:>8.3f}{:>12.3f}{:>12d}{:>16.3e}{:>16.3e}{:>16.3e}'

  @staticmethod
  def header():
    return Position.COLH.format(*Position.COLS)

  # data only
  def __init__(self, owner, symbol, basis, amount):
    self.owner = owner
    self.symbol = symbol
    self.basis = 0
    self.buy(basis, amount)

  def __str__(self):
    price = MARKET.get_ticker(self.symbol).get_price()
    amount = self.get_amount()
    ave = self.basis / amount if amount > 0 else 0.0
    return Position.COLF.format("$" + self.symbol, price, ave, int(amount), self.basis, self.get_value() - self.basis, self.get_value())
  
  def get_amount(self):
    return self.get_ticker().get_amount_owned(self.owner)

  def get_ticker(self):
    return MARKET.get_ticker(self.symbol)

  def get_value(self):
    return self.get_amount() * self.get_ticker().get_price()

  def buy(self, basis, amount):
    self.get_ticker().buy(self.owner, amount)
    self.basis += basis

  def sell(self, basis, amount):
    if amount > self.get_amount():
      raise NotEnoughShares
    self.get_ticker().sell(self.owner, amount)
    self.basis -= basis


class Ticker:
  '''
  a stock symbol
  maintains a list of all shareholders, the original owner, and current price
  '''
  COLS = ['Symbol', 'Price', 'Outstanding', 'Maj.Owner']
  COLH = '{:<12}{:>8}{:>12}{:>12}'
  COLF = '{:<12}{:>8.3f}{:>12d}{:>12}'
  # data only
  def __init__(self, symbol):
    self.symbol = symbol
    self.total = IPO_AMOUNT
    self.outstanding = int(IPO_AMOUNT)
    self.majority = symbol
    self.shareholders = {}
  
  def __str__(self):
    return Ticker.COLF.format('$' + self.symbol, self.get_price(), self.outstanding, "$" + self.majority)

  @staticmethod
  def header():
    return Ticker.COLH.format(*Ticker.COLS)

  def get_majority(self):
    majority = None
    for symbol in self.shareholders.keys():
      if majority == None:
        majority = symbol
        continue
      if self.shareholders[symbol] > self.shareholders[majority]:
        majority = symbol
    return majority

  def get_amount_owned(self, symbol):
    if symbol not in self.shareholders.keys():
      return 0
    else:
      return self.shareholders[symbol]

  def get_price(self):
    return MARKET.price_model.price_at(self.outstanding)

  def buy(self, symbol, amount):
    if amount > self.outstanding:
      raise NotEnoughShares
    if symbol not in self.shareholders.keys():  
      self.shareholders[symbol] = 0
    self.outstanding -= amount
    self.shareholders[symbol] += amount

  def sell(self, symbol, amount):
      if amount > self.shareholders[symbol]:
        raise NotEnoughShares
      self.outstanding += amount
      self.shareholders[symbol] -= amount
      if self.shareholders[symbol] == 0:
        del self.shareholders[symbol]
