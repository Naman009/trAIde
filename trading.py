import pandas as pd
import threading
import sqlite3

connection = sqlite3.connect(r'MiniProject\datasets\transactions.sqlite',check_same_thread=False)
cursor=connection.cursor()
try:
    cursor.execute('''CREATE TABLE transactions (ticker text, buy_time text, buy_cost real, sell_time text, sell_cost real,volume real, p_l real, indicator text);''')
except:
    pass


net = 0

transaction = pd.DataFrame(columns = ['ticker', 'buy_time', 'buy_cost', 'sell_time', 'sell_cost', 'volume', 'p/l', 'indicator'])
companies = ['COALINDIA','TITAN','ITC','HDFCLIFE','RELIANCE']
amount = {x: 100000 for x in companies}
flag = {x: -1 for x in companies}
rsi_all = {x: [] for x in companies}
sma_all = {x: {9:[], 20:[]} for x in companies}
ema_all = {x: {9:[], 20:[]} for x in companies}
transactions = {x: {'ticker': None, 'buy_time': None, 'buy_cost': None, 'sell_time': None, 'sell_cost': None, 'volume': None, 'p/l': None, 'indicator': None} for x in companies}

def buy(df, ticker, i, indicator): # execute buy trades command
    global transactions, amount
    transactions[ticker]['buy_time'] = df['Datetime'][i]
    transactions[ticker]['buy_cost'] = df['Close'][i]
    transactions[ticker]['volume'] = amount[ticker]/df['Close'][i]
    amount[ticker] = 0
    transactions[ticker]['indicator'] = indicator
    transactions[ticker]['ticker'] = ticker
    flag[ticker] = -1


def sell(df, ticker, i): # execute sell trade commands
    global transactions, transaction, amount,cursor
    transactions[ticker]['sell_time'] = df['Datetime'][i]
    transactions[ticker]['sell_cost'] = df['Close'][i]
    amount[ticker] = transactions[ticker]['volume'] * df['Close'][i]
    transactions[ticker]['p/l'] = transactions[ticker]['sell_cost'] - transactions[ticker]['buy_cost']
    sql = """INSERT INTO transactions
                          (ticker,buy_time,buy_cost,sell_time,sell_cost,volume,p_l,indicator) 
                          VALUES (?,?,?,?,?,?,?,?);"""

    task = (transactions[ticker]['ticker'],transactions[ticker]['buy_time'],transactions[ticker]['buy_cost'],transactions[ticker]['sell_time'],transactions[ticker]['sell_cost'],transactions[ticker]['volume'],transactions[ticker]['p/l'],transactions[ticker]['indicator'])
    cursor.execute(sql,task)
    connection.commit()
    transaction = transaction.append(transactions[ticker], ignore_index = True)
    transactions[ticker] = {'ticker': None, 'buy_time': None, 'buy_cost': None, 'sell_time': None, 'sell_cost': None, 'volume': None, 'p/l': None, 'indicator': None}
    flag[ticker] = -1


def avggain(t, df, df_old, i): # calculate avggain for RSI
    g = 0
    if i < 14:
        lc = list(df_old.tail(t-i)['Close']) + list(df['Close'][:i])
        lo = list(df_old.tail(t-i)['Open']) + list(df['Open'][:i])
    else:
        lc = list(df['Close'][i-t:i])
        lo = list(df['Open'][i-t:i])
    for k in range(len(lo)):
        if lc[k] > lo[k]:
            g += (lc[k]-lo[k])
    return g/t


def avgloss(t, df, df_old, i): # calculate avgloss for RSI
    l = 0
    if i < 14:
        lc = list(df_old.tail(t-i)['Close']) + list(df['Close'][:i])
        lo = list(df_old.tail(t-i)['Open']) + list(df['Open'][:i])
    else:
        lc = list(df['Close'][i-t:i])
        lo = list(df['Open'][i-t:i])
    for k in range(len(lo)):
        if lo[k] > lc[k]:
            l += lo[k]-lc[k]
    return l/t


def calcRSI(t, df, df_old, ticker, i): # calculates the RSI and appends it into RSI list
    gain = avggain(t, df, df_old, i)
    loss = avgloss(t, df, df_old, i)
    if df['Close'][i] > df['Open'][i]:
        currgain = df['Close'][i] - df['Open'][i]
        currloss = 0
    elif df['Close'][i] < df['Open'][i]:
        currloss = df['Open'][i] - df['Close'][i]
        currgain = 0
    else:
        currloss = currgain = 0
    rsi_all[ticker].append(100 - (100/(1 + ((gain*13 + currgain)/(loss*13 + currloss)))))


def RSI(link, link_old, ticker, i): # check for trade possibilities based on current RSI
    df = pd.read_csv(link)
    df_old = pd.read_csv(link_old)
    calcRSI(14, df, df_old, ticker, i)
    if rsi_all[ticker][i] > 70 and transactions[ticker]['buy_cost'] != None:
        sell(df, ticker, i)
    elif rsi_all[ticker][i] < 30 and transactions[ticker]['buy_cost'] == None and amount[ticker] > 0:
        buy(df, ticker, i, 'RSI')

    if i == 525 and transactions[ticker]['buy_cost'] != None:
        sell(df, ticker, i)


def preproc(t, df_old): # calculate SMA of previous days data when current day just starts
    return sum(list(df_old.tail(t)['Close']))/t


def calcEMA(t, df_old, closept, ticker, i): #calculcates the ema and appends it into the ema list
    global ema_all
    if i==0:
        prev = preproc(t, df_old)
    else:
        prev = ema_all[ticker][t][i-1]
    ema_all[ticker][t].append(((closept - prev)*(2/(t+1)))+prev)


def EMA(link, link_old, ticker, i): # checks for transaction possibilities based on the current EMA
    df = pd.read_csv(link)
    df_old = pd.read_csv(link_old)
    t9=threading.Thread(target=calcEMA, args=(9, df_old, df['Close'][i], ticker, i,))
    t20=threading.Thread(target=calcEMA, args=(20, df_old, df['Close'][i], ticker, i,))
    t9.start()
    t20.start()
    t9.join()
    t20.join()
    
    if flag[ticker] == 1:
        if df['Close'][i] < df['Open'][i]:
            buy(df, ticker, i, 'EMA')
    elif flag[ticker] == 0:
        if df['Close'][i] > df['Open'][i]:
            sell(df, ticker, i)
    elif i > 1:
        if (ema_all[ticker][9][i-1]-ema_all[ticker][20][i-1])>0 and (ema_all[ticker][9][i]-ema_all[ticker][20][i])<0 and transactions[ticker]['buy_cost'] == None and amount[ticker] > 0:
            flag[ticker] = 1
            
        if (ema_all[ticker][9][i-1]-ema_all[ticker][20][i-1])<0 and (ema_all[ticker][9][i]-ema_all[ticker][20][i])>0 and transactions[ticker]['buy_cost'] != None and (transactions[ticker]['indicator'] == 'EMA' or transactions[ticker]['indicator'] == 'RSI'):
            flag[ticker] = 0
        
        if i == 525 and transactions[ticker]['buy_cost'] != None:
            flag[ticker] = -1


def calcSMA(t, df_old, df, ticker, i): # calculates the sma and appends it into sma list
    global sma_all
    if i < t:
        sma_all[ticker][t].append((preproc(t-i, df_old)*(t-i)+sum(list(df.head(i)['Close'])))/t)
    else:
        sma_all[ticker][t].append(sum(list(df['Close'][i-t:i]))/t)


def SMA(link, old_link, ticker, i): # checks for transaction possibilities based on current SMA
    df = pd.read_csv(link)
    df_old = pd.read_csv(old_link)
#     sma = []
    t9=threading.Thread(target=calcSMA, args=(9, df_old, df, ticker, i,))
    t20=threading.Thread(target=calcSMA, args=(20, df_old, df, ticker, i,))
    t9.start()
    t20.start()
    t9.join()
    t20.join()
    
    if flag[ticker] == 1:
        if df['Close'][i] < df['Open'][i]:
            buy(df, ticker, i, 'SMA')
            flag[ticker] = -1
    elif flag[ticker] == 0:
        if df['Close'][i] > df['Open'][i]:
            sell(df, ticker, i)
            flag[ticker] = -1
    elif i > 1:
        if (sma_all[ticker][9][i-1]-sma_all[ticker][20][i-1])>0 and (sma_all[ticker][9][i]-sma_all[ticker][20][i])<0 and transactions[ticker]['buy_cost'] == None and amount[ticker] > 0:
            flag[ticker] = 1
            
        if (sma_all[ticker][9][i-1]-sma_all[ticker][20][i-1])<0 and (sma_all[ticker][9][i]-sma_all[ticker][20][i])>0 and transactions[ticker]['buy_cost'] != None and (transactions[ticker]['indicator'] == 'SMA' or transactions[ticker]['indicator'] == 'RSI'):
            flag[ticker] = 0
        
        if i == 525 and transactions[ticker]['buy_cost'] != None:
            flag[ticker] = -1


def indicators(link, old_link, ticker, i): # starts threads to calculate all indicators values simultaneously
    indicators = [SMA, EMA, RSI]
    threadList=[]
    for k in indicators:
        t=threading.Thread(target=k,args=(link, old_link, ticker, i,))
        t.start()
        threadList.append(t)
        t.join()


if __name__ == '__main__':
    scrips = ['COALINDIA','TITAN','ITC','HDFCLIFE','RELIANCE']
    for i in range(525):
        threadList=[]
        for j in range(len(scrips)):
            t = threading.Thread(target = indicators, args=(r'D:\Documents\KJSCE\VS\PHP\MiniProject\datasets\\' + scrips[j] + '.csv', r'D:\Documents\KJSCE\VS\PHP\MiniProject\datasets\\' + scrips[j] +'preproc.csv', scrips[j], i,))
            # indicators(r'C:\Users\naman\Documents\GitHub\Algo-Trading\Algotrading\datasets\\' + scrips[j] + '.csv', r'C:\Users\naman\Documents\GitHub\Algo-Trading\Algotrading\datasets\\' + scrips[j] +'preproc.csv', scrips[j], i)
            t.start()
            threadList.append(t)
            t.join()
            

    net = 0
    transaction['net'] = transaction['volume'] * transaction['p/l']
    print(transaction)
    


    
    print(sum(list(transaction['net'])))
    for i in range(len(transaction)):
        net = net + transaction['volume'][i]*transaction['p/l'][i]
    print('Net:', net)