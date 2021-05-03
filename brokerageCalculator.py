#!/usr/bin/env python
# coding: utf-8

# # Brokerage Calculator for trades on Zerodha

# ## For Equity Trades

# * For all three conditions : Delivery, BTST and Intraday trades
# * To account for holidays/weekends to determine DP charges is to be applied for Delivery trades(non BTST)
# * STT for ETFs would be different. Need to determine this too

# In[153]:


from datetime import datetime, timedelta
import sys # for commandline arguments
import configparser
#would need to add configparser for setting constants.


# ### Constants (Brokerage, charges, taxes,etc)

# In[154]:


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


# In[155]:


def getSTT(buy, sell, qty, delta=timedelta(days=0)):
    '''Security Transaction Tax: 
    (Delivery)0.1% on buy & sell. 
    (Intraday)0.025% on the sell side'''
    #Need to add logic for ETFs
    if delta < timedelta(days = 1):
        return round (0.025 / 100 * (sell * qty))
    else:
        return round (0.1 / 100 * getTurnover(buy,sell,qty))


# In[156]:


def getTransactCharges(turnover):
    '''Transaction charges by the exchange NSE/BSE NSE: 0.00345%'''
    return round(0.00345 / 100 * turnover, 2)


# In[157]:


def getGST(brokerage,transactionCharges):
    '''18% on (brokerage + transaction charges)'''
    return round(18 / 100 * (brokerage + transactionCharges),2)


# In[158]:


def getSEBIcharges(turnover):
    '''₹5 / crore'''
    return round(5 / 10000000 * turnover, 2)


# In[159]:


def getStampCharges(buy, qty, delta = timedelta(days = 0)):
    '''For Delivery: 0.015% or ₹1500 / crore on buy side
    For Intraday: 0.003% or ₹300 / crore on buy side'''
    if delta < timedelta(days = 1):
        return round( 0.003 / 100 * (buy * qty) ,2)
    else:
        return round( 0.015 / 100 * (buy * qty) ,2)


# In[160]:


def getDPCharges(buyDate,sellDate):
    '''₹13.5 + GST per scrip (irrespective of quantity), 
    on the day, is debited when stocks are sold. '''
    if (sellDate - buyDate) <= timedelta(days = 1):
        return 0
    else: #Need to add logic of previous trading day holiday/weekend for BTST
        return 13.5 + (18 / 100 * 13.5 )


# In[161]:


def getTurnover(buy, sell, qty):
    '''calculates and returns the turnover'''
    # print('#Debug: buy, sell, qty :', buy, sell, qty)
    return (buy + sell) * qty


# In[162]:


def getNetPL(buy,sell,qty,charges):
    '''Net PnL before any DP charges'''
    pl = (sell - buy) * qty
    return pl - charges


# In[169]:


buyDate = None
sellDate = None
buy = 0
sell = 0
qty = 0
if len(sys.argv) > 1:
    buyDate = datetime.strptime(sys.argv[1],'%d-%m-%Y')
if len(sys.argv) > 2:
    sellDate = datetime.strptime(sys.argv[2],'%d-%m-%Y')
if len(sys.argv) > 3:
    buy = float(sys.argv[3])
if len(sys.argv) > 4:
    sell = float(sys.argv[4])
if len(sys.argv) > 5:
    qty = int(sys.argv[5])

# In[133]:


if buyDate == None:
    inp = input('Buy Date (\'ddmmYY\'):')
    buyDate = datetime.strptime(inp,'%d%m%y')
buyDate


# In[134]:


if sellDate == None:
    inp = input('Sell Date (\'ddmmYY\'):')
    sellDate = datetime.strptime(inp,'%d%m%y')
sellDate


# In[135]:


delta = sellDate - buyDate
delta


# In[136]:


if buy == 0:
    inp = input('Buy Price:')
    buy = float(inp)
buy


# In[137]:


if sell == 0:
    inp = input('Sell Price:')
    sell = float(inp)
sell


# In[170]:


if qty == 0:
    inp = input('Qty:')
    qty = float(inp)
qty


# In[139]:


turnover = getTurnover(buy,sell,qty)
print('Turnover:',turnover)


# In[140]:


brokerage = getBrokerage(buy, sell, qty, delta)
print('Brokerage:',brokerage)


# In[141]:


STT = getSTT(buy,sell,qty,delta)
print('STT:',STT)


# In[142]:


transCharges = getTransactCharges(turnover)
print('Transaction Charges:',transCharges)


# In[143]:


GST = getGST(brokerage,transCharges)
print('GST:',GST)


# In[144]:


sebiCharges = getSEBIcharges(turnover)
print('SEBI Charges:',sebiCharges)


# In[145]:


stampDuty = getStampCharges(buy, qty, delta)
print('Stamp Duty:',stampDuty)


# In[146]:


taxnCharges = brokerage + STT + transCharges + GST + sebiCharges + stampDuty


# In[150]:

print('Gross PL:',round((sell-buy)*qty, 2))
print('Total Tax and Transaction Charges',round(taxnCharges,2))
dpCharges = getDPCharges(buyDate, sellDate)
if dpCharges > 0:
    print('DP charges:',dpCharges)
    print(f'Total Charges: {taxnCharges + dpCharges}')
netPL = getNetPL(buy,sell,qty,taxnCharges) - dpCharges
print('Net PL:',round(netPL,2))

