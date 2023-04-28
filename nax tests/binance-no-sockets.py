# %%
# Tutorial: https://youtu.be/rc_Y6rdBqXM
###!pip install binance
#!pip install python-binance

#!pip install python-decouple

#!pip install sqlalchemy
#!pip install sqlalchemy_utils

# %%
# Binance, including sockets
from binance import BinanceSocketManager
from binance.client import Client
from binance import Client#, ThreadedWebsocketManager, ThreadedDepthCacheManager
import datetime as dt

from secretttfolder import keystestnet

# Standart libraries
import pandas as pd
import numpy as np

import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database

import logging
logging.basicConfig(filename='/home/ubuntu/bot-diver/divervenv/logs/logfile.log', level=logging.DEBUG, filemode='a')


# API keys:
api_key = keystestnet.api_key
api_secret = keystestnet.api_secret
client = Client(api_key, api_secret, testnet=True)
client.API_URL = 'https://testnet.binance.vision/api'

# Settings:
symb = "BTCUSDT"
interval = "5MINUTE"

# %%
candles = client.get_klines(symbol=symb, interval=Client.KLINE_INTERVAL_5MINUTE)
numpycandles = np.array(candles)

# reshape date to pandas
df = pd.DataFrame(numpycandles.reshape(-1, 12), dtype=float, columns=('Open Time','Open','High','Low','Close','Volume','Close time','Quote asset volume','Number of trades','Taker buy base asset volume','Taker buy quote asset volume','Ignore'))
df['Open Time'] = pd.to_datetime(df['Open Time'], unit='ms')

# convert_to_hdf5 = df.to_hdf('prices.h5', key='binance_prices', mode='a')

close_prices = df['Close']


# %%
# Define the RSI indicator
def rsi(price, period=14):
    delta = price.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# Calculate the RSI indicator
rsi_indicator = rsi(df['Close'])


# Define Divergence 
def divergence(price_set, rsi_window=14, fast_ma = 1, slow_ma = 50):

# Calculate the RSI indicator for using in calculation of divergence 
   rsi_indicator = rsi(price_set)

# Calculate the Divergence indicator. 
   bullish_divergence = ((price_set.diff()<0) & (rsi_indicator.diff() > 0))
   bearish_divergence = ((price_set.diff()<0) & (rsi_indicator.diff() < 0))

   fast_ma_df = df[f'ma{fast_ma}'] = df['Close'].rolling(window=fast_ma).mean()
   slow_ma_df = df[f'ma{slow_ma}'] = df['Close'].rolling(window=slow_ma).mean()
   trend_up = fast_ma_df > slow_ma_df
   trend_down = fast_ma_df < slow_ma_df
   
   # Combine all previous indicators into the one 
   # We need that if bullish_divergence (trend_up), True PLUS fast MA above slow MA, then set 1, everything else - 0. If bearish_divergence True, PLUS fast MA above slow MA (trend_down), then set -1
   indicator = np.where( ( ( (bullish_divergence) == True)  & (trend_up == True) ), 1, 0)
   indicator = np.where( ( ( (bearish_divergence) == True)  & (trend_down == True) ), -1, indicator)
   
   return indicator

diver = divergence(close_prices, rsi_window=14, fast_ma = 1, slow_ma = 50)
last_indicator_value = diver[-1]

# %%
last_indicator_value

# %%
#last_indicator_value = 1

# %%
#last_indicator_value

# %%
def trade(ticker, lotsize, open_position = False):
  bm = BinanceSocketManager(client)
  trade_socket = bm.trade_socket(ticker)
  print(dt.datetime.now())
  if last_indicator_value > 0 and last_indicator_value != 0 and not open_position:
    order = client.create_order(symbol=ticker,
                                side='BUY',
                                type='MARKET',
                                quantity=lotsize)
    print(order)
    buyprice = float(order['fills'][0]['price'])
    open_position = True
    return
  if open_position and last_indicator_value < 0 and last_indicator_value != 0:
      order = client.create_order(symbol=ticker,
                                side='SELL',
                                type='MARKET',
                                quantity=lotsize)
      print(order)
      return
  time.sleep(1)  # sleep 1 seconds
  
trade('BTCUSDT', 0.001)

# %%
# info = client.get_account()
# info

# %%
"""1. Check balance
2. Check if price of current candle is not differ by x% from price from other exchange
3. Check if Ta-Lib indicator value not differ more than y% from another exchange
4. Check open positions
5. Check id position already open
6. Open position characteristics: long/short, timeframe, symbol, indicators values. Are any other positions with same characteristics? If yes, than it's duplicate 
7. Before Closing: check position
8. After closing: position closed? Ok, go check if we have opposite signal. We have opposite signal? Ok, go open opposite Trade Position
9. Position open time
10. How many bars passed
11. Get order ID
"""




"""You can configure the logging module to handle both the Python prints and the technical debugging information in the same file by adding another handler to the logger.

Here's an example of how you can do this:

import logging
import sys

# Initialize the logger with the desired settings
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Create a handler for writing to a file
file_handler = logging.FileHandler('/path/to/your/logfile.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s'))

# Create a handler for writing to the console (i.e. the Python prints)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(message)s'))

# Add both handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)
"""


"""you can configure Loguru to log to a file and to the console (i.e. the Python prints) in the same format:

import sys
from loguru import logger

# Configure the logger
logger.remove()  # Remove the default sink
logger.add(sys.stdout, level='INFO', format='{message}')
logger.add("/path/to/your/logfile.log", level='DEBUG', format="{time} {level}: {message}")

# Use the logger to write log messages
logger.info("This is an info message that will be printed to the console and written to the log file")
logger.debug("This is a debug message that will only be written to the log file")
"""
"""
Here's an updated version of the code that sets the maximum possible log level to TRACE and includes additional details in the log format:

python


import sys
from loguru import logger

# Configure the logger
logger.remove()  # Remove the default sink
logger.add(sys.stdout, level='TRACE', format='<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level}</level> | <cyan>{name}:{function}:{line}</cyan> | <level>{message}</level>')
logger.add("/path/to/your/logfile.log", level='TRACE', format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {message}")

# Use the logger to write log messages
logger.info("This is an info message that will be printed to the console and written to the log file")
logger.debug("This is a debug message that will only be written to the log file")
logger.trace("This is a trace message that will be printed to the console and written to the log file, with additional details")
"""