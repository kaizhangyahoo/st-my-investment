import requests
import pandas as pd
from datetime import datetime
import json
import io
import re
import ast
import miniEnc as enc

class OHLCData:
    ''' requests call to yahoo, iex, alpha vantage, polygon, eodhd, 12Data
    eg. MSCI = OHLCData("MSCI", "2022-08-08") # end date default to "today" and interval default to "1d"

    yahooV8:        MSCI = OHLCData("MSCI", "2022-08-08", "2022-08-12", interval="1h").yahooDataV8()
                    supported interval ["1m", "2m", "5m", "15m", "30m", "1h", "1d","5d", "1wk", "1mo"]
    yahooV7:        MSCI = OHLCData("MSCI", "2022-08-08", "2022-08-12").yahooDataV7() # interval hardcode to 1d

    alpha_vantage:  Obselete, no longer free
                    MSCI = OHLCData("MSCI", "2022-08-08").alpha_vantage_request() 
                    only symbol required, set a dummy start date
                    US symbol only? to check!
                    will load all ohlc data for the symbol, TODO: more work needed
            
    polygon:        MSCI = OHLCData("MSCI", "2022-08-08", "2022-08-12", interval="2h").polygon_io_vw()
                    2 yrs historical data
                    allowed interval in ["day", "minute", "hour", "week", "month", "quarter", "year"]
                    eg "1d", "1m", "1h", "1w", "1mo", "1q", "1y"
                    polygon.io use muliplier and timespan, interval is regex-ed to assign interge to multiplier and letter/word to timespan
                    
    eodhd:          MSCI = OHLCData("MSCI", "2022-01-02", "2022-08-08", interval="1w").eodhd()
                    symbol default to have suffix .US, other instruments should have exchangeCode, eg trade on LSE should have .LSE
                    list of exchange on https://eodhistoricaldata.com/api/exchanges-list/?api_token=(json format)
                    list of symbols on https://eodhistoricaldata.com/api/exchange-symbol-list/LSE?api_token=
                    interval only support on daily d, weekly w and monthly m

    12Data:         MSCI = OHLCData("MSCI", "2022-08-08", "2022-08-12", interval="1m").twelveData()
                    MULTI = OHLCData(["MSCI","FDS","AAPL"], "2022-09-28", interval="1day").twelveData() 
                    interval supports 1min, 5min, 15min, 30min, 45min, 1h, 2h, 4h, 1day, 1week, 1month
                    US market symbol only for free tier
                    allow multiple symbols

    iex:            IEX stops responding to api requests
                    MSCI = OHLCData("MSCI", "2022-07-18", interval="3days").iex_request()
                    up to 15 yrs historical data, mostly only 5 to 10 yrs
                    special interval for 10min in last 5 work days and 30min in last month eg if today 2022-08-14
                    MSCI = OHLCData("MSCI", "2022-08-08", interval="10m").iex_request()
                    otherwise, interval can be 1day (default) and n days 
                    for international symbols: ref data at https://cloud.iexapis.com/stable/ref-data/exchange/{xlon}/symbols?token=api_key
                    for exchanges: https://cloud.iexapis.com/stable/ref-data/exchanges?token=api_key
    
    lastly, don't forget pickletest
    '''

    def __init__(self, symbol, start_date, end_date = datetime.now().strftime('%Y-%m-%d'), interval = '1d'):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.interval = str(interval)
        self.header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9'}

    def __repr__(self):
        return "MarketData({}, {})".format(self.symbol, self.start_date)

    def __str__(self):
        return "MarketData({}, {})".format(self.symbol, self.start_date)

    @staticmethod
    def answers_api():
        keyboard = [b'74zU4OXbxtHQuMLFr7KtbHyZncDKt6Cqm3x8osGpxci4wbiZhnd7urPDb39ioObez8-',
        b'hmJmYcJKmx6TZpqfI2I2PhLWFhH55c7Grpaeim8zIXWSBm87Y7NTm0JmUd3vEuaqAq3PapqrWns-',
        b'dm5dsxNWarNWq18aowIiItLGvqXxyqZ2fkJTTzNxoX5uUjOPf1KWX1JKKuImGf3x6da3Z1NWloZ6bm5vDpMas1taqxqmKfoBxdbStvXTY6d6Xp4qO16GXlqibqKap1seoj4-',
        b'JhX-',
        b'tgKd1rqrUp6CjzcqYnJrZx6mboZOM27_Ps8Svuaq0uqCwk5fB2tLDZp7GrJqkqKikx6uQi7aysIN_qKXd2NmloZ6XlmdslK2Mn5Sc49Te077Dv3WFaGya3trBvcG-',
        b'1Lt5pLu7mb7pqeewpNLRxaCDvI2Zje3m2peZio7JpZzJ2IytlJypl9iRj4yJgH9-',
        b'dXmuraGmpKCXlW5ulpuRk5umpanTzrh7i25yrnV3rKzZ1s_OzJacbJOqxtWrpdWZqb65hbWErnh6ea6d8A']
        piano = b"".join(keyboard)
        return  ast.literal_eval(enc.decode(enc.cccccccz, piano))

    def get_epoch_time(self, date):
        return int(datetime.strptime(date, '%Y-%m-%d').timestamp())
    
    def convert_json_to_df(self, json_data):
        p = json.loads(json_data)
        ohlc_json = p['chart']['result'][0]['indicators']['quote'][0]
        dates = p['chart']['result'][0]['timestamp']
        ohlc_df = pd.DataFrame.from_dict(ohlc_json)

        if self.interval == "1d":
            ohlc_df['Date'] = [datetime.fromtimestamp(x).date() for x in dates]
        else:
            ohlc_df['Date'] = [datetime.fromtimestamp(x) for x in dates] 
        
        ohlc_df.index = ohlc_df['Date']
        
        return ohlc_df


    def yahooDataV8(self):
        if self.interval not in ["1m", "2m", "5m", "15m", "30m", "1h", "1d","5d", "1wk", "1mo"]:
            raise ValueError("Invalid Parameter for YahooV8 interval!")
        
        start_epoch = self.get_epoch_time(self.start_date)
        end_epoch = self.get_epoch_time(self.end_date)
        baseurl = "https://query1.finance.yahoo.com/v8/finance/chart/" + self.symbol
        url = f"{baseurl}?period1={start_epoch}&period2={end_epoch}&interval={self.interval}&events=history"
      
        try:
            r = requests.get(url, headers=self.header)
            return self.convert_json_to_df(r.text)
        except Exception as e:
            print(e)
            return None
        
    def yahooDataV7(self):
        url = "https://query1.finance.yahoo.com/v7/finance/download/" + self.symbol
        start_epoch = self.get_epoch_time(self.start_date)
        end_epoch = self.get_epoch_time(self.end_date)
        url += "?period1=" + str(start_epoch) + "&period2=" + str(end_epoch) + "&interval=1d&events=history&includeAdjustedClose=true"
        print(url)

        try:
            r = requests.get(url, headers=self.header)
            df = pd.read_csv(io.StringIO(r.text), index_col=0, parse_dates=True)
            return df
        except Exception as e:
            print(e)
            return None
    
    def alpha_vantage_request(self):
        '''full daily ohlc data covering 20 years
        no start date or end date required'''
        API_URL = "https://www.alphavantage.co/query" 
        k = self.answers_api()
        data = { "function": "TIME_SERIES_DAILY", 
                "symbol": self.symbol,
                "outputsize" : "full",
                "datatype": "csv", 
                "apikey": k['alpha_vantage'] } 

        try:
            r = requests.get(API_URL, data, headers=self.header)
            df=pd.read_csv(io.StringIO(r.text))
            return df
        except Exception as e:
            print(e)
            return None

    def calculate_iex_batch_size(self,yyyymmdd):
        '''
        Calculate the batch size for the IEX API.
        The batch size is the number of days that can be requested at once.
        '''
        today = datetime.now().date()
        start_date = datetime.strptime(yyyymmdd, "%Y-%m-%d").date()
        delta = (today - start_date).days


        if self.interval in ["10m", "10minute", "10minutes", "10mins"] and delta <= 7:
            return {"range": "5dm"} #special case for 10 minute data last 5 days
        elif self.interval in ["30m", "30minute", "30minutes", "30mins"] and delta <= 31:
            return {"range": "1mm"} #special case for 30min data only from today for a month
        elif delta <= 7:
            return {"range": "5d"}
        elif delta <=31:
            return {"range": "1m"}
        elif delta <=92:
            return {"range": "3m"}
        elif delta <=183:
            return {"range": "6m"}
        elif delta <=366:
            return {"range": "1y"}
        elif delta <=731:
            return {"range": "2y"}
        elif delta <=1828:
            return {"range": "5y"}
        else:
            return {"range": "max"}

    def iex_request(self):
        '''interval = 1d default, special interval are 5dm (interval = 10m) and 1mm (interval = 30m)
        TODO interval =1m, to get the data between start and end date is a best effort, 
        below is an example, 
        
        sandbox_token = "Tpk_0fe851431b964bab87ccdbf544021439"
        symbol = "tsla"
        start_date = "2022-08-01"
        OHLC_url = f"https://sandbox.iexapis.com/stable/stock/{symbol}/chart/{start_date}"
        data1 = { "format": "csv", "token": sandbox_token}

        however, data quality doesn't seem good so probably won't do it
        '''
        
        batch_details = self.calculate_iex_batch_size(self.start_date)


        if batch_details["range"] not in ["5dm", "1mm"]: # no chartInterval if range is 5dm, 1mm
            if self.interval.isdigit(): # if interval is a number
                batch_details["chartInterval"] = int(self.interval)
            else:
                pattern = re.compile(r'^(?P<multiplier>\d+)(?P<timespan>\w+)$')
                match = pattern.match(self.interval)
                mt = match.groupdict()
                if mt['timespan'] not in ["d", "day", "days"]:
                    raise ValueError("Invalid Parameter for IEX interval!")
                else:
                    batch_details["chartInterval"] = int(mt['multiplier'])

        # if self.interval == "1d":
        #     batch_details["chartByDay"] = "true"
        api = self.answers_api()

        data = {"format": "csv", "token": api['iex']}
        params = {**batch_details, **data}
        OHLC_URL = "https://cloud.iexapis.com/stable/stock/" + self.symbol.lower() + "/chart" # symbol must be lower case
        print(OHLC_URL)
        print(params)
        
        try:
            r = requests.get(OHLC_URL, params)
            
            if len(r.text) > 0 and r.text!="Unknown symbol":
                df = pd.read_csv(io.StringIO(r.text))
                df = self.trim_eix_dataframe(df, params["range"])
                return df
            else:
                print("Check your symbol!")
                return None
        except Exception as e:
            print(e)
            return None

    def trim_eix_dataframe(self, df, range):
        '''
        Trim the dataframe to only keep dates between start_date and end_date,
        ohlc data and set date as index
        '''
        if range in ["1mm", "5dm"]: 
            df1 = df[["date", "minute", "open", "high", "low", "close", "volume", "symbol"]].sort_values(by=["date","minute"])
            df = df1[(df1["date"] <= self.end_date) & (df1["date"] >= self.start_date)].set_index(["date","minute"])
        else:
            df1 = df[["date", "open", "high", "low", "close", "volume", "symbol"]].sort_values(by="date")
            df = df1[(df1["date"] <= self.end_date) & (df1["date"] >= self.start_date)].set_index("date")
        return df
    
    def polygon_io_interval_match(self):
        '''matching interval to muliplier and timespan
        multiplier is an integer and timespan is minute, hour, day, week, month, quarter, year'''
        
        pattern = re.compile(r'^(?P<multiplier>\d+)(?P<timespan>[d-y]+)$')
        match = pattern.match(self.interval)
        mt = match.groupdict()

        if mt["timespan"] in ["day", "minute", "hour", "week", "month", "quarter", "year"]:
            return mt
        elif mt["timespan"] in ["days", "minutes", "hours", "weeks", "months", "quarters", "years"]:
            return {"multiplier": mt["multiplier"], "timespan": mt["timespan"][:-1]}

        if mt["timespan"] == "d":
            mt["timespan"] = "day"
        elif mt["timespan"] == "y":
            mt["timespan"] = "year"
        elif mt["timespan"] == "m":
            mt["timespan"] = "minute"
        elif mt["timespan"] == "h":
            mt["timespan"] = "hour"
        elif mt["timespan"] == "w":
            mt["timespan"] = "week"
        elif mt["timespan"] == "q":
            mt["timespan"] = "quarter"
        elif mt["timespan"] == "mo":
            mt["timespan"] = "month"
        else:
            ValueError("Invalid interval for polygon")
        
        return mt


    
    def polygon_io_vw(self):
        ''' 2 yrs historical data
        allowed interval in ["day", "minute", "hour", "week", "month", "quarter", "year"]
        eg "1d", "1m", "1h", "1w", "1mo", "1q", "1y"'''

        url = "https://api.polygon.io/v2/aggs"
        API = self.answers_api()
        # parse self.interval to multiplier and timespan
        interval_dict = self.polygon_io_interval_match()
        multiplier = interval_dict["multiplier"]
        timespan = interval_dict["timespan"]

        vw_url = f"/ticker/{self.symbol}/range/{multiplier}/{timespan}/{self.start_date}/{self.end_date}"
        data = { "apikey": API['polygon'], "sort": "asc", "limit": 50000 }
        full_url = url + vw_url

        column_names = { 
        "v": "Volume",
        "vw": "VWAP",
        "o": "Open",
        "c": "Adj Close",
        "h": "High",
        "l": "Low",
        "n": "transactions"
        }

        response = requests.get(full_url, data)
        parsed = json.loads(response.text)

        df_polygon = pd.DataFrame.from_dict(parsed['results'])
        df_polygon["Date"] = pd.to_datetime(df_polygon['t']/1000, unit='s').dt.date
        df_polygon['Time'] = pd.to_datetime(df_polygon['t']/1000, unit='s').dt.time
        df_polygon = df_polygon.rename(columns=column_names)
        df_polygon.set_index(['Date','Time'], inplace=True)
        # df_polygon.index=pd.to_datetime(df_polygon.index)
        return df_polygon

    def eodhd(self):
        '''
        symbol must have suffix such as .US or .LSE
        list of exchange on https://eodhistoricaldata.com/api/exchanges-list/?api_token= (json format)
        list of symbols on https://eodhistoricaldata.com/api/exchange-symbol-list/LSE?api_token=
        interval only on daily d, weekly w and monthly m'''

        api = self.answers_api()
        url = f"https://eodhistoricaldata.com/api/eod/{self.symbol}"
        intval = self.interval.lower()

        if intval in ["d", "w", "m"]:
            p = {"period": intval}
        elif intval == "1d":
            p = {"period": "d"}
        elif intval == "1w":
            p = {"period": "w"}
        elif intval == "1m":
            p = {"period": "m"}
        else:
            raise ValueError("Invalid interval for eodhd")

        data = {**p, "from": self.start_date, "to": self.end_date, "fmt": "csv", "api_token": api['eodhd']}
        response = requests.get(url, data)
        print(response.text)
        if response.text == "Ticker Not Found.":
            raise ValueError("Invalid symbol for eodhd")
        df = pd.read_csv(io.StringIO(response.text))
        df.set_index("Date", inplace=True)
        return df
    
    def twelveData(self):
        '''
        interval supports 1min, 5min, 15min, 30min, 45min, 1h, 2h, 4h, 1day, 1week, 1month
        '''
        url = "https://api.twelvedata.com/time_series"
        apikey = self.answers_api()["12Data"]
        symbol = self.symbol
        fmt = "csv"
        start_date = self.start_date
        end_date = self.end_date
        interval = self.interval

        if interval in ["1min", "5min", "15min", "30min", "45min", "1h", "2h", "4h", "1day", "1week", "1month"]:
            pass
        elif interval == "1d":
            interval = "1day"
        elif interval == "1m":
            interval = "1min"
        elif interval == "5m":
            interval = "5min"
        elif interval == "15m":
            interval = "15min"
        elif interval == "30m":
            interval = "30min"
        elif interval == "1hour":
            interval = "1h"
        elif interval == "1w":
            interval = "1week"
        elif interval == "1mo":
            interval = "1month"
        else:
            raise ValueError("Invalid interval for twelveData, use [1min, 5min, 15min, 30min, 45min, 1h, 2h, 4h, 1day, 1week, 1month]")

        if type(symbol) == str:
            data = {"symbol": symbol, "interval": interval,  "format": fmt, "start_date": start_date, "end_date": end_date, "apikey": apikey}
            response = requests.get(url, data)    
            print(response.text)
            df = pd.read_csv(io.StringIO(response.text), sep=";")
            df.set_index("datetime", inplace=True)
        elif type(symbol) == list:
            data = {"symbol": ",".join(symbol), "interval": interval,  "start_date": start_date, "end_date": end_date, "apikey": apikey}
            response = requests.get(url, data)    
            df = pd.read_json(response.text)
            # concat all dict df into one
            l = []
            count = 0
            for i in df.columns:
                l.append(pd.json_normalize(response.json()[i]['values']))
                l[count]['symbol'] = i
                count += 1
            df = pd.concat(l)
        return df


def main():
    MSCI = OHLCData("MSCI", "2025-07-18", interval="3days").iex_request()
    print(MSCI)
    # MORN = OHLCData("MORN", "2022-09-03", interval="1week").eodhd()
    # print(MORN)
    FDS = OHLCData("SDR.L", "2022-09-29", interval="1h").yahooDataV8()
    print(FDS)
#     FDS = OHLCData("PAY.L", "2022-09-08").yahooDataV7()
#     print(FDS)

if __name__ == "__main__":
    main()
