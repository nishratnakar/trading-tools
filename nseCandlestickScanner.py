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
from datetime import timedelta, datetime, date
import getMarketData
import urllib3
import argparse
urllib3.disable_warnings()

VERBOSE = False

def fileValidityCheck(FILE_NAME, IGNORE=False):
    '''Checks to see if a file exists. If not, asks user input for a valid name if IGNORE=True.
        returns a valid filename or None'''
    while True:
        if not os.path.exists(FILE_NAME):
            if IGNORE:
                return None
            print('Warning! The file {} does not exist.'.format(FILE_NAME))
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
        if VERBOSE: print('{} is a weekend'.format(theDay.strftime('%A, %d %b %Y,')))
        return True
    theKeyDay = theDay.strftime('%d-%b-%Y')
    if theKeyDay in holidayList:
        if VERBOSE: print(theKeyDay,'is a trading holiday')
        return True
    else:
        return False

def getPrevTradingDay(yesterday,holidayList):
    '''Checks if yesterday is a trading day or not. 
    Returns the valid previous trading day as a string of format ddMMMyyyy'''
    while(isTradingHoliday(yesterday,holidayList)):
        yesterday = yesterday - timedelta(days=1)
    yesterdayStr = yesterday.strftime('%d%b%Y').upper()
    if VERBOSE: print('Previous trading day:', yesterdayStr)
    return yesterdayStr

def getBullishHammer(df, MULTIPLIER=3):
    '''Gets stocks that are forming Bullish Hammer pattern. Returns a DataFrame
    containing stocks which form a bullish Hammer pattern with Multiplier as the 'tail : body' ratio'''
    print('\nBULLISH HAMMER CANDLESTICK SCAN')
    print('-------------------------------')
    if VERBOSE: print('Minimum Tail/Body Ratio = \'{} : 1\''.format(MULTIPLIER))
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
        if VERBOSE: print('{} stocks show Hammer Candlestick pattern'.format(len(dragonFlyDf)))
        for stock in dragonFlyDf.index:
            print(stock)
    else:
        print('No stocks with Hammer pattern')
    

def getBullishMarubozu(bhavcopyDF, SHADOW_RATIO = 0.07):
    '''Gets stocks that are forming Bullish Marubozu pattern'''
    print('\nBULLISH MARUBOZU CANDLESTICK SCAN')
    print('---------------------------------')
    if VERBOSE: print('Marubozu Shadow to body ratio :',SHADOW_RATIO)
    marubozuDF = bhavcopyDF.loc[
     ( bhavcopyDF['CLOSE'] > bhavcopyDF['OPEN'] ) &
     ((( bhavcopyDF['HIGH'] - bhavcopyDF['CLOSE'] ) / ( bhavcopyDF['CLOSE'] - bhavcopyDF['OPEN'] )) < SHADOW_RATIO ) &
     ((( bhavcopyDF['OPEN'] - bhavcopyDF['LOW'] ) / ( bhavcopyDF['CLOSE'] - bhavcopyDF['OPEN'] )) < SHADOW_RATIO )
    ]
    if len(marubozuDF) > 0:
        if VERBOSE: print('{} stocks show Bullish Marubozu Candlestick pattern'.format(len(marubozuDF)))
        for stock in marubozuDF.index:
            print(stock)
    else:
        print('No stocks with Bullish Marubozu pattern')

def getBullishEngulfing(bhavcopyDF,prevBhavFound):
    '''Gets stocks that are forming Bullish Engulfing pattern'''
    print('\nBULLISH ENGULFING CANDLESTICK SCAN')
    print('----------------------------------')
    if not prevBhavFound:
        print('Previous trading session data file not found. Cannot scan for Bullish Engulfing pattern')
        return
    engulfingDF = bhavcopyDF.loc[
            ( ( bhavcopyDF['PREVOPEN'] > bhavcopyDF['PREVCLOSE'] ) & ( bhavcopyDF['CLOSE'] > bhavcopyDF['OPEN'] ) ) &
            ( ( bhavcopyDF['OPEN'] < bhavcopyDF['PREVCLOSE'] ) & ( bhavcopyDF['CLOSE'] > bhavcopyDF['PREVOPEN'] ) ),
            ['OPEN','PREVCLOSE','CLOSE','PREVOPEN']
        ]
    if len(engulfingDF) > 0:
        if VERBOSE: print('{} stocks show Bullish Engulfing Candlestick pattern'.format(len(engulfingDF)))
        for stock in engulfingDF.index:
            print(stock)
    else:
        print('No stocks with Bullish Engulfing pattern')

def getBullishHarami(bhavcopyDF, prevBhavFound):
    '''Gets stocks that are forming Bullish Harami pattern'''
    print('\nBULLISH HARAMI CANDLESTICK SCAN')
    print('-------------------------------')
    if not prevBhavFound:
        print('Previous trading session data file not found. Cannot scan for Bullish Harami pattern')
        return
    haramiDF = bhavcopyDF.loc[
        ( ( bhavcopyDF['PREVOPEN'] > bhavcopyDF['PREVCLOSE'] ) & ( bhavcopyDF['CLOSE'] > bhavcopyDF['OPEN'] ) ) &
        ( ( bhavcopyDF['OPEN'] > bhavcopyDF['PREVCLOSE'] ) & ( bhavcopyDF['CLOSE'] < bhavcopyDF['PREVOPEN'] ) ),
        ['OPEN','PREVCLOSE','CLOSE','PREVOPEN']
    ]
    if not haramiDF.empty:
            if VERBOSE: print('{} stocks show Bullish Harami Candlestick pattern'.format(len(haramiDF)))
            for stock in haramiDF.index:
                print(stock)
    else:
        print('No stocks with Bullish Harami pattern')

def getBullishOutsideBar(bhavcopyDF, prevBhavFound):
    '''Gets stocks that are forming Bullish Outside bar reversal pattern'''
    print('\nBULLISH OUTSIDE BAR CANDLESTICK SCAN')
    print('----------------------------------')
    if not prevBhavFound:
        print('Previous trading session data file not found. Cannot scan for Bullish Outside Bar pattern')
        return
    outsideDF = bhavcopyDF.loc[
            ( ( bhavcopyDF['PREVOPEN'] > bhavcopyDF['PREVCLOSE'] ) & ( bhavcopyDF['CLOSE'] > bhavcopyDF['OPEN'] ) ) &
            ( ( bhavcopyDF['LOW'] < bhavcopyDF['PREVLOW'] ) & ( bhavcopyDF['CLOSE'] > bhavcopyDF['PREVHIGH'] ) ),
            ['OPEN','PREVCLOSE','CLOSE','PREVOPEN']
        ]
    if len(outsideDF) > 0:
        if VERBOSE: print('{} stocks show Bullish Outside Bar Candlestick pattern'.format(len(outsideDF)))
        for stock in outsideDF.index:
            print(stock)
    else:
        print('No stocks with Bullish Outside Bar pattern')


def scanAllPatterns(args):
    '''Returns False if at least one pattern is specified as a commandline option.
    Else returns True'''
    if args.hammer: return False
    if args.marubozu: return False
    if args.engulfing: return False
    if args.harami: return False
    if args.outside: return False
    else: return True

def main():
    #Load config file. The file config.ini must be in the same folder/directory as this python program
    config = configparser.ConfigParser()
    config.read('config.ini')
    candlestickScanner = config['CandlestickScanner']

    parser = argparse.ArgumentParser(description='NSE Candlestick Pattern Scanner')
    parser.add_argument('-v','--verbose', action='store_true', default=False, help='Add verbosity')
    parser.add_argument('-d', '--delta', type=int, default=0, help='Offset to scan using backdate. Default is %(default)s days')
    parser.add_argument('-H','--hammer', action='store_true',default=False, help='Hammer pattern scan')
    parser.add_argument('-M','--marubozu', action='store_true', default=False, help='Marubozu pattern scan')
    parser.add_argument('-E','--engulfing', action='store_true', default=False, help='Engulfing pattern scan')
    parser.add_argument('-A','--harami', action='store_true', default=False, help='Harami pattern scan')
    parser.add_argument('-O','--outside', action='store_true', default=False, help='Outside Bar pattern scan')
    args = parser.parse_args()

    holidayList = candlestickScanner['holidays'].strip().split(',') #List of NSE trading holidays that are on weekday
    
    #setting Verbosity globally
    global VERBOSE
    VERBOSE = args.verbose
    
    SCAN_ALL = scanAllPatterns(args)

    #offset value for calculating date. Default is 0 days
    backDate = args.delta
    if VERBOSE:
        print('Offset for backdate:',backDate)
    delta = timedelta(days = backDate)

    #Setting the default CSV filename
    FOLDER_NAME = candlestickScanner['foldername'] #Example: data/scanner/
    PREFIX_CSV = candlestickScanner['csvfileprefix'] #Example: 'MW-SECURITIES-IN-F&O-'
    theDay = datetime.today() - delta

    #sanity check to see if the given date is a trading holiday/weekend
    if isTradingHoliday(theDay,holidayList):
        print('The given date\'{}\' is a trading holiday/weekend. Select another date'.format(theDay.strftime('%d-%b-%Y')))
        sys.exit()

    theDayStr = theDay.strftime('%d-%b-%Y') #format: 24-Mar-2021. dd-mmm-yyyy
    FILE_NAME = FOLDER_NAME + PREFIX_CSV + theDayStr + '.csv'

    #Setting the latest bhavcopy CSV filename
    BHAV_PREFIX = candlestickScanner['bhavPrefix']
    BHAV_SUFFIX = candlestickScanner['bhavSuffix']
    theDayStr = theDayStr.replace('-','').upper() #bhavcopy file has the date in filename format ddmmyyy. Stripping '-'
    BHAV = FOLDER_NAME + BHAV_PREFIX + theDayStr + BHAV_SUFFIX + '.csv'
    # print('Debug: BHAV :', BHAV)

    #Sanity check to see of live market segment CSV file exists
    if VERBOSE:
        print('Verifying the live market data CSV file')
    FILE_NAME = fileValidityCheck(FILE_NAME)
    if not FILE_NAME:
        if VERBOSE: print('User input None. Exiting the program..')
        sys.exit()
    if VERBOSE:
        print('Live market data CSV file present: ',FILE_NAME)

    #Read CSV file into a dataframe.
    df = pd.read_csv(FILE_NAME,thousands=',') 

    #Rename columns to keep it clean. Column names from NSE website has \n and other characters.
    df.columns = ['SYMBOL','OPEN', 'HIGH', 'LOW', 'PREVCLOSE', 'CLOSE', 'CHNG',
        '%CHNG', 'VOLUME', 'VALUE', '52W H', '52W L',
        '365 D', '30 D'] #LTP or last traded price column is set as CLOSE

    df.set_index('SYMBOL',inplace=True)

    now = datetime.now()
    today = date(year=now.year,month=now.month,day=now.day)
    theDay = date(theDay.year, theDay.month, theDay.day)
    
    # if the day to fetch data is current day and time is greater than or equal to 6:00pm,
    # or if the day to fetch data is prior to current trading day , only then bhavcopy is available
    found = False
    if ((today == theDay) and ( now.hour >= 18 )) or today > theDay:
        found = getMarketData.fetchBhavcopy(theDayStr, FOLDER_NAME, BHAV, VERBOSE)

    if found:#Will use bhavcopy for analysis if available.
        if VERBOSE: print('Bhavcopy fetched successfully for date:',theDayStr)
        else: print('Date:',theDayStr)
        df = getBhavCopyData(df.index,BHAV)
    else:#Else use the live trade csvfile
        if VERBOSE: print('No Bhavcopy found! Proceeding with live market data CSV file for data analysis\n')
        else: print('Date:',theDayStr)

    #First filteration: Eliminate stocks whose prices are lower or upper than the set price band
    LOW_LIMIT = candlestickScanner.getint('lowerpricelimit')
    UP_LIMIT = candlestickScanner.getint('upperPriceLimit')
    dfToDrop = df[(df['CLOSE'] < LOW_LIMIT) | (df['CLOSE'] > UP_LIMIT)]
    if VERBOSE: print('Dropping {0} stocks with CLOSE price > {1} or < {2}'.format(len(dfToDrop),UP_LIMIT,LOW_LIMIT))
    df.drop(dfToDrop.index,inplace=True)

    #SANITY CHECK. To drop any stocks where high == Low to avoid infinity position size.
    if len(df[df['HIGH']==df['LOW']]) > 0:
        bad_df = df[ df['HIGH'] == df['LOW'] ]
        if VERBOSE: print ('ALERT: {} stock/stocks with HIGH = LOW'.format(len(bad_df)))
        print( bad_df )
        for stock in bad_df.index:
            if VERBOSE: print('Dropping {} from today\'s list'.format(stock))
        df.drop(bad_df.index, inplace = True)

    #Get Previous session bhavcopy
    prevDay = getPrevTradingDay(theDay - timedelta(days=1),holidayList)
    # print('\nPrevious Trading day is', prevDay)
    prevBhavFile = FOLDER_NAME + BHAV_PREFIX + prevDay + BHAV_SUFFIX + '.csv'
    found = getMarketData.fetchBhavcopy(prevDay,FOLDER_NAME, prevBhavFile, VERBOSE)
    if found:
        prevDayBhavDF = getBhavCopyData(df.index, prevBhavFile)
        df['PREVOPEN'] = prevDayBhavDF['OPEN']
        df['PREVLOW'] = prevDayBhavDF['LOW']
        df['PREVHIGH'] = prevDayBhavDF['HIGH']

    #SCAN FOR THE CANDLESTICK PRICE ACTION PATTERNS AND DISPLAY THE RESULTS
    #Bullish Hammer Pattern
    if SCAN_ALL or args.hammer:
        MULTIPLIER = candlestickScanner.getfloat('tailtobodyratio')
        getBullishHammer(df,MULTIPLIER)
    
    #Bullish Marubozu Pattern
    if SCAN_ALL or args.marubozu:
        MARUBOZU_WICK_RATIO = candlestickScanner.getfloat('marubozuShadow')
        getBullishMarubozu(df, MARUBOZU_WICK_RATIO)
    
    #Bullish Engulfing Pattern
    if SCAN_ALL or args.engulfing:
        getBullishEngulfing(df, found)

    #Bullish Outside Bar Pattern
    if SCAN_ALL or args.outside:
        getBullishOutsideBar(df, found)

    #Bullish Harami Pattern
    if SCAN_ALL or args.harami:
        getBullishHarami(df, found)
        

if __name__  == "__main__":
    main()