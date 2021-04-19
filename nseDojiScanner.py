#!/usr/bin/env python
# coding: utf-8
'''
The objective of this program is to scan for Hammer (dragonfly & gravestone doji) candlestick formation
from OHLC values from a data source. 

Our first data source will be CSV file downloaded from NSE website's live market/EOD for any given
segment of stocks. This would be used anytime during a trading and immediately after close of trading
session to do any trades for post market session.

Here, the Last traded Price (LTP) column for a stock will be considered as the Close price to calculate if
a hammer is formed or not. 

The second data source would be the bhavcopy CSV file from NSE website with settlement/close price. The
bhavcopy is available for download only after 6:00pm and can be used for analysis to place AMO (After
Market Orders) for next day's trading session.


'''
import numpy as np
import pandas as pd
import configparser
import sys
import os
# import datetime
from datetime import timedelta, datetime

def fileValidityCheck(FILE_NAME, IGNORE=False):
    '''Checks to see if a file exists. If not, asks user input for a valid name if IGNORE=True.
        returns a valid filename or None'''
    while True:
        if not os.path.exists(FILE_NAME):
            print('Warning! The file {} does not exist.'.format(FILE_NAME))
            if IGNORE:
                return None
            FILE_NAME = input('Enter fullpath to the CSV file: ')
            if len(FILE_NAME) == 0:
                return None
        else:
            return FILE_NAME

def getBhavCopyData(index, BHAV):
    '''Extracts data from Bhav for securities/stocks present in the symbol index given
       Returns a filtered DataFrame with stocks having Series 'EQ' only'''
    bhavDF = pd.read_csv(BHAV)
    bhavDF.set_index('SYMBOL', inplace = True)
    bhavDF.dropna(axis=1,inplace=True,thresh=1)
    bhavDF = bhavDF.loc[index]
    return bhavDF[ bhavDF['SERIES'] == 'EQ' ]

def isTradingHoliday(theDay,holidayList):
    '''Checks if the theday date is in HolidayList or if it is a weekend and
        returns True if it is a trading holiday. Else returns False'''
    if theDay.weekday() > 4: #is it a weekend (>4)
        print('{} is a weekend'.format(theDay.strftime('%A, %d %b %Y,')))
        return True
    theKeyDay = theDay.strftime('%d-%b-%Y')
    if theKeyDay in holidayList:
        print(theKeyDay,'is a trading holiday')
        return True
    else:
        return False

#Load config file. The file config.ini must be in the same folder/directory as this python program
config = configparser.ConfigParser()
config.read('config.ini')
dojiScanner = config['DojiScanner']
holidayList = dojiScanner['holidays'].strip().split(',') #List of NSE trading holidays that are on weekday

#offset value for calculating date. Default is 0 days
backDate = 0

#Checking for CLI arguments for offset date, if any.
if len(sys.argv) > 1:
    if sys.argv[1].upper() == '-D':
        if len(sys.argv) > 2:
            if sys.argv[2].isdigit():
                backDate = int(sys.argv[2])
            else:
                backDate = 1
        else:
            backDate = 1

delta = timedelta(days = backDate)

#Setting the default CSV filename
FOLDER_NAME = dojiScanner['foldername'] #Example: data/scanner/
PREFIX_CSV = dojiScanner['csvfileprefix'] #Example: 'MW-SECURITIES-IN-F&O-'
theDay = datetime.today() - delta

#sanity check to see if the given date is a trading holiday/weekend
if isTradingHoliday(theDay,holidayList):
    print('The given date\'{}\' is a trading holiday/weekend. Select another date'.format(theDay.strftime('%d-%b-%Y')))
    sys.exit()

today = theDay.strftime('%d-%b-%Y') #format: 24-Mar-2021. dd-mmm-yyyy
FILE_NAME = FOLDER_NAME + PREFIX_CSV + today + '.csv'

#Setting the latest bhavcopy CSV filename
BHAV_PREFIX = dojiScanner['bhavPrefix']
BHAV_SUFFIX = dojiScanner['bhavSuffix']
today = today.replace('-','').upper() #bhavcopy file has the date in filename format ddmmyyy. Stripping '-'
BHAV = FOLDER_NAME + BHAV_PREFIX + today + BHAV_SUFFIX + '.csv'
# print('Debug: BHAV :', BHAV)

#Sanity check to see of live market segment CSV file exists
print('\nVerifying the live market data CSV file')
FILE_NAME = fileValidityCheck(FILE_NAME)
if not FILE_NAME:
    print('#User input None. Exiting the program..')
    sys.exit()
print('Live market data CSV file present: ',FILE_NAME)

#Read CSV file into a dataframe.
df = pd.read_csv(FILE_NAME,thousands=',') 
# We need to use thousands=',' parameter as CSV columns have number with comma.
# Else pandas will treat the price (float) values as object

#Rename columns to keep it clean. Column names from NSE website has \n and other characters.
df.columns = ['SYMBOL','OPEN', 'HIGH', 'LOW', 'PREV CLOSE', 'CLOSE', 'CHNG',
       '%CHNG', 'VOLUME', 'VALUE', '52W H', '52W L',
       '365 D', '30 D'] #LTP or last traded price column is set as CLOSE

df.set_index('SYMBOL',inplace=True)

#Sanity check to see if latest Bhavcopy exists. 
#Will use bhavcopy for analysis if available. Else use the live trade csvfile
print('\nVerifying the Bhavcopy CSV file for the day')
BHAV = fileValidityCheck(BHAV,True)
if BHAV:
    print('Bhavcopy : {} found! Proceeding with Bhavcopy file for data analysis\n'.format(BHAV))
    df = getBhavCopyData(df.index,BHAV)
else:
    print('No Bhavcopy found! Proceeding with live market data CSV file for data analysis\n')

#First filteration: Eliminate stocks whose prices are lower or upper than the set price band
LOW_LIMIT = dojiScanner.getint('lowerpricelimit')
UP_LIMIT = dojiScanner.getint('upperPriceLimit')
dfToDrop = df[(df['CLOSE'] < LOW_LIMIT) | (df['CLOSE'] > UP_LIMIT)]
print('Dropping {0} stocks with CLOSE price > {1} or < {2}'.format(len(dfToDrop),UP_LIMIT,LOW_LIMIT))
df.drop(dfToDrop.index,inplace=True)

#SANITY CHECK. To drop any stocks where high == Low to avoid infinity position size.
if len(df[df['HIGH']==df['LOW']]) > 0:
    bad_df = df[ df['HIGH'] == df['LOW'] ]
    print ('ALERT: {} stock/stocks with HIGH = LOW'.format(len(bad_df)))
    print( bad_df )
    for stock in bad_df.index:
        print('Dropping {} from today\'s list'.format(stock))
    df.drop(bad_df.index, inplace = True)
    
MULTIPLIER = dojiScanner.getfloat('tailtobodyratio')
print('\nMinimum Tail/Body Ratio = \'{} : 1\''.format(MULTIPLIER))
#Both Green (Close>=Open) and Red (OPEN>CLOSE) Dragonfly dojis or hammer candlestick formations
dragonFlyDf = df[ (
                    (df['CLOSE'] >= df['OPEN']) 
                & ( (df['OPEN'] - df['LOW'] ) > ((df['CLOSE'] - df['OPEN']) * MULTIPLIER) )
                & ( (df['HIGH'] - df['CLOSE']) < (df['CLOSE'] - df['OPEN']) )
                ) |
                (
                    (df['OPEN'] > df['CLOSE']) 
                & ( (df['CLOSE'] - df['LOW'] ) > ((df['OPEN'] - df['CLOSE']) * MULTIPLIER) )
                & ( (df['HIGH'] - df['OPEN']) < (df['OPEN'] - df['CLOSE']) )
                )
]

if len(dragonFlyDf) > 0:
    print('\n{} stocks show Hammer Candlestick pattern'.format(len(dragonFlyDf)))
    for stock in dragonFlyDf.index:
        print(stock)
else:
    print('\nNo stocks with Hammer pattern')