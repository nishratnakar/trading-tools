""" To calculate average buy/sell price of stocks/units bought in multiple orders
User inputs a series of quantity+price values. The user enters a blank value to end the loop
The program should calculate average price and display it to the user"""


def getValue(message):
    """Displays a message to the User.Returns the command line input from user"""
    return input(message)

def getQuantity():
    """Returns the user input quantity for an order
    Returns None if no quantity is entered by the User"""
    while True:
        qty = getValue('Enter quantity (Press Enter to exit)')
        if len(qty) < 1:return None
        if qty.isdecimal():break
        print('Incorrect value. Try again')
    return qty

def getPrice():
    """Returns user input Price for an order"""
    while True:
        price = getValue('Enter price:')
        try: #dirty way of checking if a input string is float.
            float(price) # python has no string method to check for float
            break
        except Exception as e:
            print('Incorrect value. Please try again')
    return price

#Main program
def mainloop():
    '''This method allows it to run as a standalone program'''
    orders = dict()
    while True:
        qty = getQuantity()
        if qty == None:
            break
        price = getPrice()
        orders[price] = orders.get(price,0)+int(qty)
        #print('# DEBUG: orders',orders)

    if len(orders) > 0:
        #print('# DEBUG: len(orders)',len(orders))
        #print('# DEBUG: orders',orders)
        orderValue = 0.0
        cnt = 0
        for key,val in orders.items():
            #print('# DEBUG: qty, price',val,key)
            orderValue+= val *float(key)
            cnt+=val
        print('Average Price is ',orderValue/cnt)
    print('Exiting program...')
    pass

if __name__ == '__main__':
    mainloop()
