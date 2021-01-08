#!/usr/bin/env python
# coding: utf-8

# # Opening Range Breakout
# Every trading strategy has two important elements that a lot of us overlook.
# * Stock Selection.
# * Risk control.
# 
# The objective in this program is to achieve two things.
# 1. Build a stock scanner to identify candidate stocks to trade the **Opening Range Breakout (ORB)** strategy.
# 2. Calculate the appropriate **Position size** for these stocks based on our max Risk per trade.

# In[1]:


import numpy as np
import pandas as pd
import sys
import os
import datetime
import configparser #added on 13-10-2020 to ensure defaults/constants are read from config file instead of hardcoding. Easier to customize


# ## How to define Risk?
# One approach to define risk is as follows.
# * Our maximum risk per trade should not be more than **1%** (or 2%) of our **trading capital**.
# > For example: If ₹ 10,000 is our trading capital, then the maximum loss we should take per trade is ₹100
# * In Range breakout trading strategies, the intial stoploss is usually the opposite side of the range.
# * For Opening Range High Breakout, the intial stoploss is if price cross below the Range Low.
# * For Opening Range Low Breakout, the intial stoploss is if price cross above the Range High.
# * Our Position size should consider this range size and our maximum risk.
# * Position Size = RISK / Range.
# > For example: if our **Opening Range(OR) High** price is ₹120 and the **OR** **Low** price is ₹110. Then our Range is High - Low. So 120 - 110 = 10. Hence, if our risk is ₹100 , then our position size will be 100/10=10. We will either buy/sell 10 stocks to ensure our intial stoploss doesn't go beyond ₹100

"""Adding logic to load values from a configuration file - 13-10-2020
Will use a file name config.ini located in same directory/folder as python script file"""
config = configparser.ConfigParser()
config.read('config.ini')
ORBConfig = config['ORBScanner']

# In[2]:


RISK = ORBConfig.getint('risk') #defining max risk per trade. If running as script, allow a commandline input/config file to set this
NUM_BUY_STOCKS = ORBConfig.getint('numoflongstocks') #DEFAULT MAX STOCKS TO BUY
NUM_SELL_STOCKS = ORBConfig.getint('numofshortstocks') #DEFAULT MAX STOCKS TO SHORT


# ## Stock Selection
# 
# The stocks that I want to trade for ORB High are:
# * Stocks that have opened **gapped-up** from Previous day High.
# * Today's high is **preferably** at least 1% higher than Previous Day Close.
# * Maximum **5 candidate stocks** to trade per day.
# * If there are more than 5 stocks, then preferance is to be given for 5 stocks with **higher price change** between **Range High** and **Previous Day Close**.
# 
# The stocks that I want to trade for ORB Low are:
# * Stocks that have opened **gapped-down** from Previous day High.
# * Today's Low is **preferably** at least 1% lower than Previous Day Close.
# * Maximum **5 candidate stocks** to trade per day.
# * If there are more than 5 stocks, then preferance is to be given for 5 stocks with **higher price change** between **Range Low** and **Previous Day Close**.

# ## Where to find the data to scan and calculate position size?
# 
# There are many sources and data feeds for realtime data. Almost all of them are paid and premium services. But, a free source of real-time data **(almost!)** is the **live market watch** page on the **National Stock Exchange of India (NSE) website**. There is a **time lag** of some seconds before we hit the refresh button to get latest OHLC and volume values here. The best part is that we can download data of any of the segment as a **CSV** file. I usually trade stocks in NSE's '**Securities which are part of Futures and Options**' Segment as they are very liquid.
# 
# The CSV File can be got from [NSE website](https://www.nseindia.com/market-data/live-equity-market)
# * Download it and put it in a folder called data.
# * File name is usually **MW-'SEGMENT-NAME'-'dd-mmm-yyyy'.csv** format
# * *Example: I trade in stocks which are part of F&O Segment. SO on 18th September,2020, the filename is* **MW-SECURITIES-IN-F&O-18-Sep-2020.csv**

# In[3]:

"""New code added for commandline optimization to run as a script : 28-09-2020
to accept 1.filename , 2.number of stocks to buy , 3.number of stocks to sell , 4.risk
"""
#Setting Default creation of csv file name
FOLDER_NAME =  ORBConfig['foldername'] #'data/'
PREFIX_CSV =  ORBConfig['csvfileprefix'] #'MW-SECURITIES-IN-F&O-'
today = datetime.date.today().strftime('%d-%b-%Y')
FILE_NAME = FOLDER_NAME + PREFIX_CSV + today + '.csv' #csv filename. This should ideally be commandline input for script

# print('# debug sys.argv',sys.argv)
 
if len(sys.argv) > 1: # filename provided as CLI argument
	if sys.argv[1].upper() != 'D': #if D then take default filename but include additional arguments as CLI.
		FILE_NAME = FOLDER_NAME + sys.argv[1] #24-10-202 bug fix of error code: PREFIX_CSV + sys.argv[1]
if len(sys.argv) > 2: #number of stocks to buy and sell respectively given as single argument
	NUM_BUY_STOCKS = int(sys.argv[2])
	NUM_SELL_STOCKS = int(sys.argv[2])
if len(sys.argv) > 3: #number of stocks to sell given as separate value from number of stocks to buy
	NUM_SELL_STOCKS = int(sys.argv[3])
if len(sys.argv) > 4:
	RISK = int(sys.argv[4])

#Sanity Check for CSV File name
while True:
	if not os.path.exists(FILE_NAME):
		print('Warning: File {} does not exists'.format(FILE_NAME))
		inp = input('Enter CSV file complete path:')
		if len(inp) < 1:
			sys.exit()
		FILE_NAME = inp
	else:
		break


# In[4]:


#We need to use thousands=',' parameter as CSV columns have number with comma. Else pandas will treat float numbers as object
df = pd.read_csv(FILE_NAME,thousands=',')


# In[5]:


#Rename columns to keep it cleaning. Column names from NSE website has \n and other characters. keeping it simple
df.columns = ['SYMBOL','OPEN', 'HIGH', 'LOW', 'PREV CLOSE', 'LTP', 'CHNG',
       '%CHNG', 'VOLUME', 'VALUE', '52W H', '52W L',
       '365 D', '30 D']


# In[6]:


#unwanted columns to drop. We don't need these to for either scanning candidate stocks or calculating position size
cols_to_drop = ['CHNG',
       'VOLUME', 'VALUE', '52W H', '52W L',
       '365 D', '30 D','LTP','%CHNG']


# In[7]:


df.head()


# In[8]:


df.drop(columns=cols_to_drop,inplace=True)


# In[9]:


df.head()


# In[10]:


df.set_index('SYMBOL',inplace=True) #set stock symbol as index


# In[11]:


df.head()


# In[12]:


#drop stocks with open price < 30 or > 3000. These stocks have liquidity/slippage issues
df_todrop = df[(df['OPEN'] > 3000) | (df['OPEN'] < 30)]


# In[13]:


print('Dropping {} stocks with OPEN price > 3000 or < 30 '.format(len(df_todrop)))
# print(df_todrop['OPEN'])


# In[14]:


df.drop(df_todrop.index,inplace = True)

#SANITY CHECK. To drop any stocks where high == Low to avoid infinity position size.
#Bug fix done on 12-10-2020
if len(df[df['HIGH']==df['LOW']]) > 0:
    bad_df = df[ df['HIGH'] == df['LOW'] ]
    print ('ALERT: {} stock/stocks with HIGH = LOW'.format(len(bad_df)))
    print( bad_df )
    for stock in bad_df.index:
        print('Dropping {} from today\'s list'.format(stock))
    df.drop(bad_df.index, inplace = True)



# In[15]:


#calculate gap up/down open percentage and set a new column to store these values
df['%GAP'] = round((df['OPEN'] - df['PREV CLOSE']) / df['PREV CLOSE'] * 100,2)


# In[16]:


df.head()


# In[17]:


print('Number of stocks Gapped Up Open for the day: {}'.format(len(df[df['%GAP'] >0])))
print('Number of stocks Gapped Down Open for the day: {}'.format(len(df[df['%GAP'] <0])))


# For stocks that have **gapped-up**, calculate the price difference between our timeframe's **Range High** and **Previous Day Close** price as percentage change with respect to Previous Day Close price.

# In[18]:


#Finding range high price difference (in percentage) from previous day close price for gap-up stocks only
df.loc[df['%GAP'] > 0,'%RANGE HIGH GP'] = round(( df['HIGH'] - df['PREV CLOSE'] ) / df['PREV CLOSE'] * 100,2)


# In[19]:


df.head()


# For stocks that have **gapped-down**, calculate the price difference between our timeframe's **Range Low** and **Previous Day Close** price as percentage change with respect to Previous Day Close price.

# In[20]:


#Finding range low price difference (in percentage) from previous day close price for gap-down stocks only
df.loc[df['%GAP'] < 0,'%RANGE LOW GD'] = round(( df['PREV CLOSE'] - df['LOW'] ) / df['PREV CLOSE'] * 100,2)


# In[21]:


df.head()


# In[22]:


df[ (df['%GAP'] > 0) & (df['%RANGE HIGH GP'] > 1) ] #gapup stocks with range high > 1% from prev close


# In[23]:


df[ ( df['%GAP'] < 0 ) & (df['%RANGE LOW GD'] > 1 ) ] #gapdown stocks with prev close > 1% from range low


# In[24]:


df.loc[df['%GAP'] < 0,'%GAP'] = abs(df['%GAP']) #Coverting GAP down to abslute value for sorting and selecting top 5 stocks


# ### Position Size Calculation
# * Get the top 5 gap up stocks with respect today's range High.
# * Get the top 5 gap down stocks with respect today's range Low.
# * Calculate the Position size for these 10 stocks.
# * **Position size = Max Risk amount in a trade / Range**
# > RISK set by us individually. Range is **High - LOW**

# In[25]:


#find top 5(default) gapup stocks with respect to range high - prev close price change and calculate position size
df.loc[df.nlargest(NUM_BUY_STOCKS,['%RANGE HIGH GP','%GAP']).index ,'PSIZE']= round((RISK / (df['HIGH'] - df['LOW'])))


# In[26]:


#find top 5(default) gapdown stocks with respect to prev close - range low price change and calculate position size
df.loc[df.nlargest(NUM_SELL_STOCKS,['%RANGE LOW GD','%GAP']).index,'PSIZE'] = round((RISK / (df['HIGH'] - df['LOW'])))


# Drop all the other stocks except for these 10 stocks.

# In[27]:


df.dropna(thresh=7,inplace= True) #drop other stocks except for these 10 stocks to trade for the day


# * Position size is calculated by default as **Float** number.
# * Convert the column for Position size into **Integer**

# In[28]:


df['PSIZE']=df['PSIZE'].astype(int) #convert position size from float to int


# In[29]:


df['PSIZE']

def displayStockPositionSize(s):
	print('{0:<10}{1:>5}'.format('STOCKS','QTY'))
	print('-'*15)
	#print('debug: type(s)',type(s))
	for stock in s.index:
		name = stock
		#print('debug:', s[stock])
		qty = s[stock]
		print('{0:<10}{1:>5}'.format(stock,qty))
	return


# In[30]:

if len(df.loc[(df['PSIZE'] > 0) & df['%RANGE HIGH GP'].notna(), 'PSIZE']) > 0:
	print('------BUY------')
	series_buy = df.loc[(df['PSIZE'] > 0) & df['%RANGE HIGH GP'].notna(), 'PSIZE']
	displayStockPositionSize(series_buy)
	#print(df.loc[(df['PSIZE'] > 0) & df['%RANGE HIGH GP'].notna(), 'PSIZE'].to_frame())
else:
	print('No Stocks for ORB Long')

# In[31]:

if len(df.loc[(df['PSIZE'] > 0) & df['%RANGE LOW GD'].notna(), 'PSIZE']) == 0:
	print('No Stocks for ORB SHORT Sell')
else:
	print('-----SELL------')
	series_sell = df.loc[(df['PSIZE'] > 0) & df['%RANGE LOW GD'].notna(), 'PSIZE']
	displayStockPositionSize(series_sell)
	#print(df.loc[(df['PSIZE'] > 0) & df['%RANGE LOW GD'].notna(), 'PSIZE'].to_frame())
# print(df.loc[(df['PSIZE'] > 0) & df['%RANGE LOW GD'].notna(),['%GAP','%RANGE LOW GD','PSIZE']])


# In[ ]: