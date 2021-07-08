#!/usr/bin/env python
# coding: utf-8

# # Brokerage Calculator for trades on Zerodha

# ## For Equity Trades

# * For all three conditions : Delivery, BTST and Intraday trades
# * To account for holidays/weekends to determine DP charges is to be applied for Delivery trades(non BTST)
# * STT for ETFs would be different. Need to determine this too



from datetime import date, datetime, timedelta
import sys # for commandline arguments
import argparse
import configparser
#would need to add configparser for setting constants.



def getBrokerage(buy, sell, qty, delta=timedelta(days=0)):
    '''For Delivery and BTST, Zero Brokerage.
    For Intrday(0.03% or Rs. 20/executed order whichever is lower'''
    if delta > timedelta(days = 0):
        return 0
    else:
        order01 = 0.03 / 100 * ( buy * qty )
        if order01 > 20:
            order01 = 20
        order02 = 0.03 / 100 * ( sell * qty )
        if order02 > 20:
            order02 = 20
        return order01 + order02


def getSTT(buy, sell, qty, delta = timedelta(days=0), isETF = False):
    '''Security Transaction Tax: 
    (Delivery)0.1% on buy & sell. 
    (Delivery equity ETF) STT is only applicable for Equity Oriented Funds on the sell side at a rate of 0.001%
    It is not applicable to debt (Liquid/Gilt), commodity (Gold) and International ETFs (N100).
    (Intraday)0.025% on the sell side'''
    #Need to add logic for ETFs    
    if delta < timedelta(days = 1):
        return round (0.025 / 100 * (sell * qty))
    elif isETF:
        return round (0.001 / 100 * (sell * qty),2)
    else:
        return round (0.1 / 100 * getTurnover(buy,sell,qty))


def getTransactCharges(turnover):
    '''Transaction charges by the exchange NSE/BSE NSE: 0.00345%'''
    return round(0.00345 / 100 * turnover, 2)


def getGST(brokerage,transactionCharges):
    '''18% on (brokerage + transaction charges)'''
    return round(18 / 100 * (brokerage + transactionCharges),2)


def getSEBIcharges(turnover):
    '''₹10 / crore'''
    return round(10 / 10000000 * turnover, 2) #Sebi charges updated to Rs 10 per crore


def getStampCharges(buy, qty, delta = timedelta(days = 0)):
    '''For Delivery: 0.015% or ₹1500 / crore on buy side
    For Intraday: 0.003% or ₹300 / crore on buy side'''
    if delta < timedelta(days = 1):
        return round( 0.003 / 100 * (buy * qty) ,2)
    else:
        return round( 0.015 / 100 * (buy * qty) ,2)


def getDPCharges(delta):
    '''₹13.5 + GST per scrip (irrespective of quantity), 
    on the day, is debited when stocks are sold. '''
    if delta <= timedelta(days = 1):
        return 0
    else: #Need to add logic of previous trading day holiday/weekend for BTST
        return round(13.5 + (18 / 100 * 13.5 ), 2)


def getTurnover(buy, sell, qty):
    '''calculates and returns the turnover'''
    # print('#Debug: buy, sell, qty :', buy, sell, qty)
    return (buy + sell) * qty


def getNetPL(buy,sell,qty,charges):
    '''Net PnL before any DP charges'''
    pl = (sell - buy) * qty
    return pl - charges


def main():
    # buyDate = None
    # sellDate = None
    delta = timedelta(days=0)
    buy = 0
    sell = 0
    qty = 0
    isETF = False
    is_stt = True
    # today = date.today()

    parser = argparse.ArgumentParser('Brokerage calculator')
    
    #Common features
    parser.add_argument('-d', '--delta', action='count', default=0, help='Increase holding period. Default is %(default)s')
    parser.add_argument('buy_price', type=float, help='The buy price', metavar='BuyPrice')
    parser.add_argument('sell_price', type=float, help='The sell price', metavar='SellPrice')
    parser.add_argument('quantity', type=int, help='Quantity of shares traded', metavar='QTY')
    parser.add_argument('-e', '--etf', action='store_true', help='If the stock is ETF' )
    parser.add_argument('-n', '--nostt', action='store_true', help='Sets STT as not applicable' )

    #Parse arguments
    args = parser.parse_args()

    delta = timedelta(days=args.delta)
    buy = args.buy_price
    sell = args.sell_price
    qty = args.quantity

    #Common optional arguments
    if args.etf:
        isETF = True
    if args.nostt:
        is_stt = False
    
    turnover = getTurnover(buy,sell,qty)
    print('Turnover:',round(turnover,2))

    brokerage = getBrokerage(buy, sell, qty, delta)
    print('Brokerage:',round(brokerage,2))

    #Get STT eligibility
    STT = 0
    if is_stt:
        STT = getSTT(buy, sell, qty, delta, isETF)
    print('STT:',STT)

    transCharges = getTransactCharges(turnover)
    print('Transaction Charges:',transCharges)

    GST = getGST(brokerage,transCharges)
    print('GST:',GST)

    sebiCharges = getSEBIcharges(turnover)
    print('SEBI Charges:',sebiCharges)

    stampDuty = getStampCharges(buy, qty, delta)
    print('Stamp Duty:',stampDuty)

    taxnCharges = brokerage + STT + transCharges + GST + sebiCharges + stampDuty
    taxnCharges = round(taxnCharges,2)

    print('Gross PL:',round((sell-buy)*qty, 2))
    print('Total Tax and Transaction Charges',round(taxnCharges,2))
    dpCharges = getDPCharges(delta)
    if dpCharges > 0:
        print('DP charges:',dpCharges)
        print(f'Total Charges: {round(taxnCharges + dpCharges,2)}')
    netPL = getNetPL(buy,sell,qty,taxnCharges) - dpCharges
    print('Net PL:',round(netPL,2))

main()

