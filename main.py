import discord

import os
import time
import threading

import market
import ice



client = discord.Client()

@client.event
async def on_ready():
  print('logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
  params = message.content.split(" ")
  if message.author == client.user:
    return

  if message.content.startswith("$info"):
    hmsg = ""
    hmsg += "market.IPOs are {:shares} at {:price}.\n".format(shares=market.IPO_AMOUNT, price=market.IPO_PRICE)
    hmsg += "Owners are entitled to half of their shares ({:shares}),\n".format(shares=market.IPO_AMOUNT/2)
    hmsg += "and that same value in cash ({:value}).\n".format(value=market.IPO_AMOUNT*market.IPO_PRICE/2)
    hmsg += "\n"
    hmsg += "Commands:"
    hmsg += "$ipo, $buy, $sell, $portfolio, $market"
    await send(message.channel, hmsg)
    return

  if message.content.startswith("$ipo"):
    await ipo(message)
    return

  if message.content.startswith("$buy"):
    await buy(message)
    return

  if message.content.startswith("$sell"):
    await sell(message)
    return

  if message.content.startswith("$stimulate"):
    await stimulate(message)
    return

  if message.content.startswith("$inflate"):
    await inflate(message)
    return

  if message.content.startswith("$portfolio"):
    await portfolio(message)
    return
  
  if message.content.startswith("$market"):
    await market_p(message)
    return

  if message.content.startswith("$leaderboard"):
    await leaderboard(message)
    return

  if message.content.startswith("$stock"):
    await stock(message)
    return

  if message.content.startswith("$"):
    await stock(message)
    return


USER_SYMBOLS = {}

#helper functions

async def send(channel, msg):
  await channel.send("```" + msg + "```")


#commands
async def ipo(message):
  # create new stock
  params = message.content.split(" ")
  if len(params) < 2:
    await send(message.channel, "Invalid symbol.")
    return
  if message.author.display_name in USER_SYMBOLS.keys():
    await send(message.channel, "User already has a stock: ${:}".format(USER_SYMBOLS[message.author.display_name]))
    return
  symbol = params[1].upper()

  USER_SYMBOLS[message.author.display_name] = symbol
  _ = market.MARKET.ipo(symbol)
  user = message.author.display_name
  await send(message.channel, "Congrats on the ${:} IPO, {:}!  to the moon!".format(symbol, message.author.display_name))

async def buy(message):
  # purchase stock
  params = message.content.split(" ")
  if len(params) > 3:
    await send(message.channel, "Unknown order syntax.")
    return
  if message.author.display_name not in USER_SYMBOLS.keys():
    await send(message.channel, "That symbol doesn't exist...")
  buyer = USER_SYMBOLS[message.author.display_name]
  symbol = params[1].upper()
  amount = params[2] if len(params) > 2 else 1
  try:
    amount = int(amount.lower().replace('k', '000'))
  except:
    await send(message.channel, "Try switching the symbol and the amount.")
    return
  try:
    msg = market.MARKET.buy(buyer, symbol, amount)
  except Exception as e:
    msg = "Error: {:}".format(type(e).__name__)
  await send(message.channel, msg)
  return

async def sell(message):
  # sell stock
  params = message.content.split(" ")
  if len(params) > 3:
    await send(message.channel, "Unknown order syntax.")
    return
  if message.author.display_name not in USER_SYMBOLS.keys():
    await send(message.channel, "That symbol doesn't exist...")
    return
  seller = USER_SYMBOLS[message.author.display_name]
  symbol = params[1].upper()
  amount = params[2] if len(params) > 2 else 1
  try:
    amount = int(amount.lower().replace('k', '000'))
  except:
    await send(message.channel, "Try switching the symbol and the amount.")
    return
  try:
    msg = market.MARKET.sell(seller, symbol, amount)
  except Exception as e:
    msg = "Error: {:}".format(type(e).__name__)
  await send(message.channel, msg)
  return

async def portfolio(message):
  # display portfolio
  user = message.author.display_name
  if user not in USER_SYMBOLS.keys():
    await send(message.channel, "You must have a stock to participate, try '$ipo'.")
    return
  symbol = USER_SYMBOLS[user]
  await send(message.channel, str(market.MARKET.get_portfolio(symbol)))
  return

async def stock(message):
  # get info on stock
  params = message.content.split(" ")
  symbol = params[0][1:].upper()
  if symbol == "STOCK": symbol = params[1].upper()
  try:
    msg = market.MARKET.print_stock(symbol)
  except Exception as e:
    msg = "Error: {:}".format(type(e).__name__)
  await send(message.channel, msg)
  return


STIMULUS_VOTERS = []
async def stimulate(message):
  # vote to pass a stimulus bill, increases available cash for all participants
  user = message.author.display_name
  if user not in USER_SYMBOLS.keys():
    await send(message.channel, "You need a portfolio in order to vote to stimulate, try '$ipo'")
    return
  symbol = USER_SYMBOLS[user]
  if symbol not in STIMULUS_VOTERS: STIMULUS_VOTERS.append(symbol)
  if len(set(STIMULUS_VOTERS)) > 0.5 * len(USER_SYMBOLS):
    msg = "Stimulus vote passed, {:.3e} was added to all portfolios.".format(market.FED.get_stimulus_value())
    market.FED.stimulate()
    STIMULUS_VOTERS.clear()
  else:
    msg = "{:d} / {:d} votes to stimulate, need >50%.".format(int(len(STIMULUS_VOTERS)), int(len(USER_SYMBOLS)))
  await send(message.channel, msg)
  return

INFLATION_VOTERS = []
async def inflate(message):
  # vote for inflation, reduces available cash for all participants
  user = message.author.display_name
  if user not in USER_SYMBOLS.keys():
    await send(message.channel, "You need a portfolio in order to vote to inflate, try '$ipo'")
    return
  symbol = USER_SYMBOLS[user]
  if symbol not in INFLATION_VOTERS: INFLATION_VOTERS.append(symbol)
  if len(set(INFLATION_VOTERS)) > 0.5 * len(USER_SYMBOLS):
    msg = "Inflation vote passed, {:2.2f}% of cash was deducted from all portfolios.".format(100 * (1 - market.FED.get_inflation_pct()))
    market.FED.inflate()
    INFLATION_VOTERS.clear()
  else:
    msg = "{:d} / {:d} votes to inflate, need >50%.".format(int(len(INFLATION_VOTERS)), int(len(USER_SYMBOLS)))
  await send(message.channel, msg)
  return
  
async def market_p(message):
  await send(message.channel, market.MARKET.print_market())
  return

async def leaderboard(message):
  await send(message.channel, market.MARKET.print_leaderboard())
  return

tfile = open('token.txt', 'r')
token = tfile.readline()

#def run_client(client, token):
#  client.run(token)
#client_thread = threading.Thread(target=run_client, args=(client, token))

MARKET_JSON = 'market.json'
FED_JSON = 'fed.json'
USERS_JSON = 'users.json'
def save_state():
  ice.save_market(market.MARKET, MARKET_JSON)
  ice.save_fed(market.FED, FED_JSON)
  ice.save_users(market.USER_SYMBOLS, USERS_JSON)

def load_state():
  ice.load_market(MARKET_JSON)
  ice.load_fed(FED_JSON)
  global USER_SYMBOLS
  USER_SYMBOLS = ice.load_users(USERS_JSON)

def run_console():
  import code
  code.interact(local=globals())
console_thread = threading.Thread(target=run_console)

console_thread.start()

client.run(token)