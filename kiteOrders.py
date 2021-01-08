"""
Developing a feature to read the orders.csv file downloaded from Zerodha kite dashboard
and create a csv file with single entry for each squared-off intraday MIS trade in Equities
segment. The entry for each row will including the strategy name in a column. This would be
for maintaining a trade journal as csv.

Future plans:
1. Append to master csv file
2. Options to Generate reports
3. Visualizations on strategy/daily performance/cummilative performance.
4. Add taxes/brokerage/charges calculation to add approximate trade costs for net P&L

"""
import datetime
import json
import os
import csv
import configparser
import stockfinder
from operator import itemgetter

def getConfigData(key="foldername"):
    config = configparser.ConfigParser()
    config.read("config.ini")
    kiteConfig = config["KiteOrders"]
    return kiteConfig[key]

def getDataDirectory():
    """Creates and gets the relative path to the data directory from config file"""
    dataDirectory = getConfigData("foldername")
    try:
        os.makedirs(dataDirectory)
        # print("#Debug: The directory {} created".format(dataDirectory))
    except Exception:
        # print("#Debug: The directory {} exists".format(dataDirectory))
        pass
    return dataDirectory

def getOrdersFilepath():
    """Opens and read the orders.csv"""
    filename = getConfigData("ordersFileName")
    # print("#Debug: orders filename is:", filename)
    dataDirectory = getDataDirectory()
    fullPath = os.path.join(dataDirectory,filename)
    # print("#Debug: Full path to orders file:", fullPath)
    return fullPath

def getOrders():
    """get Orders as dictionary

        Each row in CSV file will be returned as dictionary with below keys
        Time : 2020-11-27 14:05:26
        Type : SELL
        Instrument : IGL
        Product : MIS
        Qty. : 3/3
        Avg. price : 498
        Status : COMPLETE

        For intraday equities, 
        1. The value for key "Product" must be MIS and
        2. The value for key "Instrument" must be part of the segment we trade. 
            Example: Securities in FO, Nifty50 etc
        3. Also, for "Qty." we need to replace values like 3/3 as 3.i.e., Order fill 3 out of 3 as 3.

    """
    ordersFilePath = getOrdersFilepath()
    allOrders = {}
    try:
        with open(ordersFilePath,"r") as csvfile:
            csv_dict_reader = csv.DictReader(csvfile, delimiter=',')
            sorted_csv_dict = sorted(csv_dict_reader,key=itemgetter('Time'))
            for row in sorted_csv_dict:
                if not isTodaysOrder(row):
                    break
                # print("#debug:",csv_dict_reader.line_num)
                if isProductMIS(row):
                    # print("#Debug:{} is MIS".format(row.get("Instrument")))
                    if isInstrumentinFO(row):
                        #if open order exisit, then squareoff
                        openOrderID = checkIfOpenOrderExists(row, allOrders)
                        if openOrderID:
                            #square-off the order
                            # print("#Debug. Open order ID {0} exists for {1}".format(openOrderID, row["Instrument"]))
                            squareOffOrder(openOrderID, row, allOrders)
                        else:
                            #Else create new order
                            # print("#Debug. New order created for {}".format(row["Instrument"]))
                            newOrder = createNewOrder(row)
                            id = str(len(allOrders)+1)
                            # print(type(id), id)
                            allOrders[id] = allOrders.get(id, newOrder)
                    else:
                        print("#Intrument {} not in traded Segment. Skipping it".format(row.get("Instrument")))
                        pass
                else:
                    # print("#debug:Line No:",csv_dict_reader.line_num)
                    print("#Instrument {} is not intraday MIS".format(row.get("Instrument")))
                    print("#Debug:Product type is {}".format(row.get("Product")))
    except Exception as e:
        print("Exception:", e)
    if len(allOrders) < 1:
        print("#Debug: No Orders found in {}".format(ordersFilePath))
        pass
    return allOrders

def isProductMIS(row):
    """Checks if order is of type Product = MIS and returns if condition is met, else returns False"""
    if row.get("Product").upper() == "MIS":
        return True
    else:
        return False

def isInstrumentinFO(row):
    """Checks to see if Instrument is in the segment we use to do intraday trade. Example: F&O segment
    returns True if Instrument is in segment.
    Else asks user input
        If to update the segment list with new Instrument name and return True
        Else return False"""
    foFilename = getConfigData("FnOListJsonFileName")
    lookuptable = stockfinder.loadFoJson(foFilename)
    if lookuptable == None or len(lookuptable) < 1:
        print('Warning! No Lookup Table to search correct Stock symbols!')
        return False
    # print("#Debug: lookuptable created and available to search Instrument")
    if row["Instrument"].upper().strip() in lookuptable:
        # print("# Debug:{} is in the Segment we trade.".format(row["Instrument"]))
        return True
    else:
        print("# Debug:{} is not found in the Segment we trade.".format(row["Instrument"]))
        choice = input("Update the Segment list with this new Instrument?(Y/N): ")
        if len(choice) < 1 or (choice.upper() == "N"):
            return False
        else:
            newInstrument = row["Instrument"]
            lookuptable[newInstrument] = lookuptable.get(newInstrument, 0) + 1
            toJsonStatus = stockfinder.dct_to_json(lookuptable,foFilename)
            if toJsonStatus == False:
                print('JSON file',foFilename,'could not be updated with new symbol:',newInstrument)
    return True

def isTodaysOrder(row):
    '''Checks if the order (row) in the csv file is today's order
    and returns True if date of order is today, else returns False.'''
    orderDateString = row['Time'].strip().split(" ")[0]
    orderDate = datetime.date.fromisoformat(orderDateString)
    if orderDate == datetime.date.today():
        return True
    else:
        print('Warning: Order date:{} in the CSV file. The data is not today\'s order. Possible old Orders.csv file'.format(orderDateString))
        return False

def createNewOrder(row):
    """Creates a new open order and returns it as a dictionary"""
    newOrder = {}
    #Extract and add the "date" from row[Time] (format "2020-11-27 14:05:26")
    date_ , entry = row["Time"].strip().split(" ")
    # print("#Debug: date_ : {0} , entry : {1}".format(date_, entry))
    newOrder["date"] = date_
    #Extract and the "entry" from row[Time]
    newOrder["entry"] = entry
    #Add "trade" (LONG/SHORT) based on row[TYPE] (SELL/BUY)
    if row["Type"].strip().upper() == "SELL":
        newOrder["trade"] = "SHORT"
    else:
        newOrder["trade"] = "LONG"
    #Extract and add "name" from row[Instrument]
    newOrder["name"] = row["Instrument"].strip().upper()
    #Extract and "quantity" from row[Qty.] (format"3/3")
    newOrder["quantity"] = row["Qty."].strip().split("/")[0]
    #Extract from row[Avg. price] and add either "sell" or "buy" price based on "trade"
    if newOrder["trade"] == "SHORT":
        newOrder["sell"] = row["Avg. price"].strip()
    else:
        newOrder["buy"] = row["Avg. price"].strip() 
    return newOrder

def checkIfOpenOrderExists(row, allOrders):
    """Checks to see if the order details in row dictionary has a matching open order already created.
    if there is a matching open order then it returns the ID (>0).
    Else returns False"""
    if len(allOrders) < 1:
        return False #No open orders exist
    for orderID in allOrders:
        oldOrder = allOrders[orderID]
        if "exit" in oldOrder:
            continue #skip already squared-off trades/orders
        #Check if the Intrument name and position size has a match in existing orders
        if (row["Instrument"].strip() == oldOrder["name"]) and (row["Qty."].strip().split("/")[0] == oldOrder["quantity"]):
            #Check if the matched combination has opposite order type/1st leg of the trade entered.
            if row["Type"].strip().upper() == "SELL" and oldOrder["trade"] == "LONG":
                return orderID #An open order exists for this combination
            elif row["Type"].strip().upper() == "BUY" and oldOrder["trade"] == "SHORT":
                return orderID #An open order exists for this combination
    return False #No match found

def squareOffOrder(orderID, row, allOrders):
    """Squares off an open order with orderID in allOrders dictionary by getting trade details from row"""
    #get 'exit' time from row[Time] format: "2020-11-27 09:50:21"
    allOrders[orderID]['exit'] = row['Time'].strip().split(" ")[1]
    if row["Type"].strip().upper() == "SELL":
        allOrders[orderID]['sell'] = row['Avg. price'].strip() #get sell price Or
    else:
        allOrders[orderID]['buy'] = row['Avg. price'].strip() #buy price
    return

def assignStrategies(allOrders):
    '''Assigns predefined Strategy names from config file based on user action to orders
    present in allOrders dictionary'''
    strategyList = getConfigData('strategies').strip().split(",")
    strategyID = getConfigData('strategiesID').strip().split("/")
    defaultStrategy = getConfigData('strategiesDefault').strip()
    print('#Debug: Number of strategies is', len(strategyList))
    for strategy in strategyList:
        print(strategy)
    print('The Default Strategy is', defaultStrategy)
    #Loop through orders
    for orderID in allOrders:
        closedOrder = allOrders[orderID]
        print(orderID,".",end=" ")
        for key, val in closedOrder.items():
            print("{0}:{1}".format(key,val),end=" ")
        print("")
        choice = input('Assign Strategy ('+getConfigData('strategiesID').strip()+'): ')
        if len(choice.strip()) < 1 or choice.strip().upper() not in strategyID:
            closedOrder['strategy'] = defaultStrategy
            print('Assigning Default Strategy:',defaultStrategy)
        else:
            index = strategyID.index(choice.strip().upper())
            closedOrder['strategy'] = strategyList[index]
            print('Assigned Strategy:',closedOrder['strategy'])
    return

def closedTrades(trades):
    """Displays all squared-off Trades"""
    ctr = 0
    pnl = 0.0 #Added pnl to display the values.
    for tradeID in trades:
        if 'exit' not in trades[tradeID]:
            continue
        if ctr == 0:
            print('CLOSED TRADES FOR THE DAY')
            print('-------------------------')
            displayClosedTradeHeader()
        ctr+= 1
        pnl = pnl + displayClosedTrade(trades,tradeID)
    if ctr == 0: print('No closed trades')
    else: print('Squared-off PnL:',round(pnl,2))
    input('Press Enter key to continue.')
    return

def displayClosedTradeHeader():
    print('{0:>4}{1:^12}{2:<5}{3:<7}{4:<10}{5:<9}{6:>5}{7:>8}{8:>8}{9:>10}'.format('ID',
    'STOCK','ALGO','TRADE','ENTRY','EXIT','QTY','BUY','SELL','P/L'))
    return

def displayClosedTrade(trades,id):
    qty = float(trades[id]['quantity'])
    buy = float(trades[id]['buy'])
    sell = float(trades[id]['sell'])
    pl = qty * (sell - buy)
    pl = round(pl,2)
    print('{0:>4}{1:^12}{2:<5}{3:<7}{4:<10}{5:<9}{6:>5}{7:>8}{8:>8}{9:>10}'.format(id,trades[id]['name'],
    trades[id]['strategy'],trades[id]['trade'],trades[id]['entry'],trades[id]['exit'],trades[id]['quantity'],
    round(buy,2),round(sell,2),pl))
    return pl #return PnL after display.

def loadJSON():
    """Initiliazes a json or loads the already saved json from file
    and returns the json"""
    #Get today's date to name files for the day's operation.
    fname = datetime.date.today().isoformat()+'.json'
    # print('# DEBUG: today',fname)
    dataDirectory = getDataDirectory()
    # print('# DEBUG: pathname',pathname)
    fullpath = os.path.join(dataDirectory,fname)
    #if json already created for the day, then load the saved trade data from JSON
    if os.path.exists(fullpath):
        print('File for the day exists:',fullpath)
        try:
            fhandle = open(fullpath,'r')
        except Exception as e:
            print('Error opening file:',fhandle)
            print(e)
            return None
        data = fhandle.read()
        if len(data)<1:
            print('0 data in file.')
            return {}
        trades = json.loads(data)
        #print('# DEBUG: type(trades):',type(trades))
        fhandle.close()
        return trades
    #else return empty DICT to start the day's trade entries
    print('No file created for the day yet')
    trades ={}
    return trades

def saveJSON(trades):
    """Saves the data to be serilaized into a file with today's date as filename
    and extension as .json"""
    fname = datetime.date.today().isoformat()+'.json'
    pathname = getDataDirectory()
    fullPath = os.path.join(pathname,fname)
    with open(fullPath,'w') as jsonfile:
        json.dump(trades,jsonfile,indent=6)
    return

def writeCSV(trades):
    """Write the trade details to csv file"""
    header =['date','entry','name','trade','exit','strategy','quantity','buy','sell']
    allRows = []
    for tradeID in trades:
        if 'exit' not in trades[tradeID]:
            print('One or more trades is yet to be squared-off:',trades[tradeID]['name'])
            print('Cannot write CSV file before all trades are squared-ff for the day')
            input('Press the ENTER key to continue')
            return False
        row = []
        row.append(trades[tradeID]['date'])
        row.append(trades[tradeID]['entry'])
        row.append(trades[tradeID]['name'])
        row.append(trades[tradeID]['trade'])
        row.append(trades[tradeID]['exit'])
        row.append(trades[tradeID]['strategy'])
        row.append(trades[tradeID]['quantity'])
        row.append(trades[tradeID]['buy'])
        row.append(trades[tradeID]['sell'])
        #print('# DEBUG: row[]:',row)
        allRows.append(row)
    #print('# DEBUG: allRows[]',allRows)
    fname = datetime.date.today().isoformat()+'.csv'
    dataDirectory = getDataDirectory()
    fullPath = os.path.join(dataDirectory, fname)
    with open(fullPath,'w',encoding='UTF-8',newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(header)
        csvwriter.writerows(allRows)
        fullPath = os.path.join(os.getcwd(),fullPath) #os.getcwd()+'\\'+csvfile.name
        print('Trade details written to CSV file:',fullPath)
    return True

def initializeStockLookupTable():
    fname = getConfigData('FnOListJsonFileName')
    if os.path.exists(fname):
        #print('# DEBUG: JSON file with FO segment exists:',fname)
        return
    inp = input('Enter csv file with FO segment stock data (to create JSON file with stock hashtable):')
    if len(inp) < 1:
        inp = 'FO.csv'
    dataDirectory = getDataDirectory()
    fname = os.path.join(dataDirectory,inp)
    # fname = makedatadir()+inp
    stock_dict = stockfinder.csv_to_dictionary(fname)
    if stock_dict == None or len(stock_dict) < 1:
        print('# DEBUG: Invalid CSV file with FO stocks list')
        print('## DEBUG: JSON file with F&O segment stock hashtable will not be created')
        return
    fname = getConfigData('FnOListJsonFileName')
    toJsonStatus = stockfinder.dct_to_json(stock_dict,fname)
    if toJsonStatus == False:
        print('# DEBUG: JSON file with F&O segment stock hashtable could not be created')
        return
    print('JSON file with F&O segment stock hashtable created:',os.getcwd()+'\\'+fname)
    return

def mainloop():
    """Main loop to execute this as standalone program"""
    initializeStockLookupTable()
    allOrders = loadJSON() #Load any previously parsed and saved data for the day
    if len(allOrders) < 1: #if not previously saved orders for the day is found
        allOrders = getOrders() #Get orders for the day
        if len(allOrders) > 0: assignStrategies(allOrders)
    closedTrades(allOrders)
    saveJSON(allOrders)
    if len(allOrders) > 0:
        choice = input("Generate consolidated CSV file for the day(Y/N): ")
        if len(choice.strip()) < 1 or choice.strip().upper() == "Y":
            writeCSV(allOrders)
    return

mainloop()