import pandas as pd

df = pd.read_csv(r'C:\Users\naman\Documents\GitHub\Algo-Trading\Algotrading\datasets\\COALINDIA.csv')
df_old = pd.read_csv(r'C:\Users\naman\Documents\GitHub\Algo-Trading\Algotrading\datasets\\COALINDIApreproc.csv')
rsi_all = {'COALINDIA': []}
transaction = pd.DataFrame(columns = ['ticker', 'buy_time', 'buy_cost', 'sell_time', 'sell_cost', 'volume', 'p/l', 'indicator'])
companies = ['COALINDIA','TITAN','ITC','HDFCLIFE','RELIANCE']
transactions = {x: {'ticker': None, 'buy_time': None, 'buy_cost': None, 'sell_time': None, 'sell_cost': None, 'volume': None, 'p/l': None, 'indicator': None} for x in companies}
amount = {'COALINDIA': 100000, 'TITAN': 100000, 'ITC': 100000, 'HDFCLIFE': 100000, 'RELIANCE': 100000}

def buy(df, ticker, i, indicator):
    global transactions, amount
    transactions[ticker]['buy_time'] = df['Datetime'][i]
    transactions[ticker]['buy_cost'] = df['Close'][i]
    transactions[ticker]['volume'] = amount[ticker]/df['Close'][i]
    amount[ticker] = 0
    transactions[ticker]['indicator'] = indicator


def sell(df, ticker, i):
    global transactions, transaction, amount
    transactions[ticker]['sell_time'] = df['Datetime'][i]
    transactions[ticker]['sell_cost'] = df['Close'][i]
    amount[ticker] = transactions[ticker]['volume'] * df['Close'][i]
    transactions[ticker]['p/l'] = transactions[ticker]['sell_cost'] - transactions[ticker]['buy_cost']
    transactions[ticker]['ticker'] = ticker
    transaction = transaction.append(transactions[ticker], ignore_index = True)
    transactions[ticker] = {'ticker': None, 'buy_time': None, 'buy_cost': None, 'sell_time': None, 'sell_cost': None, 'volume': None, 'p/l': None, 'indicator': None}


def avggain(t, df, df_old, i):
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


def avgloss(t, df, df_old, i):
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


def calcRSI(t, df, df_old, ticker, i):
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


def RSI(link, link_old, ticker, i):
    df = pd.read_csv(link)
    df_old = pd.read_csv(link_old)
    calcRSI(14, df, df_old, ticker, i)
    if rsi_all[ticker][i] > 70 and transactions[ticker]['buy_cost'] != None:
        sell(df, ticker, i)
    elif rsi_all[ticker][i] < 30 and transactions[ticker]['buy_cost'] == None:
        buy(df, ticker, i, 'RSI')

    if i == 525 and transactions[ticker]['buy_cost'] != None:
        sell(df, ticker, i)


for i in range(525):
    RSI(r'C:\Users\naman\Documents\GitHub\Algo-Trading\Algotrading\datasets\\COALINDIA.csv', r'C:\Users\naman\Documents\GitHub\Algo-Trading\Algotrading\datasets\\COALINDIApreproc.csv', 'COALINDIA', i)

# print(rsi_all['COALINDIA'])
print(transaction)
print(len(rsi_all['COALINDIA']))
net = 0
for i in range(len(transaction)):
    net = net + transaction['volume'][i]*transaction['p/l'][i]
print('Net:', net)