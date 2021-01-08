import re
import json
import csv
import configparser

def csv_to_dictionary(fname):
    '''Reads a csv file containing stocks in FO list and Returns
    a dictionary containing the stock Symbols'''
    stock_dict = {}
    header = True
    try:
        with open(fname) as fhandle:
            csvfile = csv.reader(fhandle)
            for row in csvfile:
                #print('# DEBUG:len(row)', len(row))
                if header == True:
                    header = False
                    continue
                if len(row) < 14:
                    continue
                #print('# DEBUG: ',row[0])
                symbol = row[0].upper()
                stock_dict[symbol] = stock_dict.get(symbol,0) + 1
    except Exception as e:
        print('CSV File not found/could not be processed:',fname)
        print('Error message:',e)
        return None
    return stock_dict

def dct_to_json(stock_dict,fname):
    '''Writes a dictionary to a given filename. Returns True if the file
    writing is successful, else Returns False'''
    try:
        with open(fname,'w') as jsonfile:
            json.dump(stock_dict,jsonfile,indent=6)
            print('# DEBUG: Successful writing JSON to file')
            return True
    except Exception as e:
        print('Error writing JSON to File:',e)
    return False

def loadFoJson(fname):
    '''Loads JSON from a given filename and returns the dictionary
    containing the stock symbols in F&O segment. Returns None if
    there is error in processing JSON from file'''
    stock_dict ={}
    data =''
    try:
        with open(fname,'r') as jsonfile:
            data = jsonfile.read()
    except Exception as e:
        print('The JSON file could not be opened or processed:', fname)
        print('Eror message',e)
        return None
    if len(data) < 1:
        print('No data in JSON file:',fname)
        return stock_dict
    try:
        stock_dict = json.loads(data)
    except Exception as e:
        print('Error loading JSON:',e)
        return None
    return stock_dict

def getStockinFO(pattern,stock_dict):
    '''Tries to match a Pattern with the stock symbols in the stock_dict
    dictionary. Returns the stock if user input confirms the pattern match.
    else returns None'''
    for stock in stock_dict.keys():
        try:
            if re.search(pattern,stock) == None:
                continue
        except Exception as e:
            print('Eror matching pattern:',e)
            return None
        inp = input('Did you mean '+stock+'?(Y/N):')
        if len(inp) < 1 or inp.lower() == 'y':
            return stock
        continue
    return None

#mainloop
def mainloop():
    config = configparser.ConfigParser()
    config.read('config.ini')
    finderConfig = config['StockFinder']
    #Step 1: Read CSV file and Create DiCtionary
    fname =  finderConfig['FnOListCSVFileName'] #'data/FO27Aug2020.csv'
    inp = input('Enter F&O Lost csv file name:')
    if len(inp) > 1:
        fname = inp
    stock_dict = csv_to_dictionary(fname)
    if stock_dict == None or len(stock_dict) < 1:
        print('CSV File Couldn\'t be opened. Exiting Program...')
        exit()
    print('# DEBUG: len(stock_dict):',len(stock_dict))
    #Step 2: Write dictionary to JSON file
    jsonFname = finderConfig['FnOListJsonFileName'] #'data/FO.json'
    inp = input('Input JSON File name:')
    if len(inp) > 1:
        jsonFname=inp
    toJsonStatus = dct_to_json(stock_dict,jsonFname)
    if toJsonStatus == False:
        print('Couldn\'t write dictionary to JSON. Exiting Program...')
        exit()
    #Step 3: Load json file
    stock_dict = loadFoJson(jsonFname)
    #print('# DEBUG: loaded stock_dict from JSON',stock_dict)
    print('# DEBUG: len(stock_dict):', len(stock_dict))

    #Step 4: testing the finding of the stock in dictionary
    while True:
        pattern = input('Enter Symbol keyword:')
        if len(pattern) < 1:
            break
        pattern = pattern.upper()
        stock = getStockinFO(pattern,stock_dict)
        if stock == None or len(stock) < 1:
            print('Pattern not found:',pattern)
            inp = input('Add pattern as new stock in FO list?(Y/N):')
            if len(inp) < 1 or inp.upper() == 'Y':
                stock_dict[pattern] = stock_dict.get(pattern,0) + 1
            continue
        print('Pattern matched with Stock:',stock)
    print('# DEBUG: len(stock_dict):', len(stock_dict))

if __name__ == '__main__':
    mainloop()
