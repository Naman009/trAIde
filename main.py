import trading
import company_selection
import time
import datetime
import os
import yfinance as yf

companies = []
while True:
    # --- checking current time to see what part of code to execute ---
    # date = datetime.date.today()
    # x = datetime.datetime.now()
    # t = x.strftime("%X")
    # if t >= '15:30:00':
        companies, split = company_selection.main() # execute the ML code to select best comapnies for trading

        # --- deleting historic csv's once used ---
        dir = r'C:\Users\naman\Documents\VS code\Algotrading\datasets'
        for f in os.listdir(dir):
            os.remove(os.path.join(dir, f))

        # --- downloading current and previous days datasets ---
        today = datetime.date.today()
        today = today - datetime.timedelta(days=1)
        if today.weekday() == 5 or today.weekday() == 6:
            # time.sleep(86400) # if sat or sun sleep for 1 day
            continue
        elif today.weekday()==0:
            yesterday = today - datetime.timedelta(days=3)
        else:
            yesterday = today - datetime.timedelta(days=1)
        if yesterday.weekday() == 0:
            day_before = yesterday - datetime.timedelta(days=3)
        else:
            day_before = yesterday - datetime.timedelta(days=1)
        today = today.strftime('%Y-%m-%d')
        yesterday = yesterday.strftime('%Y-%m-%d')
        day_before = day_before.strftime('%Y-%m-%d')
        for i in companies:
            df = yf.download(tickers=i+'.NS',start=yesterday, end=today, interval='5m')
            df = df.reset_index()
            if '15:30' in str(df['Datetime'][len(df)-1]):
                df = df.head(len(df)-1)
            df.to_csv('datasets\\'+i+'.csv')
            df_old = df = yf.download(tickers=i+'.NS',start=day_before, end=yesterday, interval='5m')
            df_old.to_csv('datasets\\'+i+'preproc.csv')
        
        # --- time based activation (put code to sleep till next days market opens) --- 
        # sleep_until = '09:15:00' 
        # sleep_until = time.strftime("%m/%d/%Y " + sleep_until, time.localtime())
        # curr_time = time.time()
        # sleep_until = time.mktime(time.strptime(sleep_until, "%m/%d/%Y %H:%M:%S"))
        # if curr_time > sleep_until: #If we are already past the alarm time today.
        #     sleep_until = sleep_until + 86400
        # time.sleep(sleep_until - curr_time)
    # else:
        trading.main(companies, split) # execute the trading function with top 5 selected companies

        # --- time based activation (put code to sleep until market closes) ---
        # sleep_until = '15:30:00'
        # sleep_until = time.strftime("%m/%d/%Y " + sleep_until, time.localtime())
        # curr_time = time.time()
        # sleep_until = time.mktime(time.strptime(sleep_until, "%m/%d/%Y %H:%M:%S"))
        # time.sleep(sleep_until - curr_time) # sleep until 3:30PM of the next day when the market closes
        
        # --- deleting the csv's once used ---
        dir = r'C:\Users\naman\Documents\VS code\Algotrading\datasets'
        for f in os.listdir(dir):
            os.remove(os.path.join(dir, f))
        break