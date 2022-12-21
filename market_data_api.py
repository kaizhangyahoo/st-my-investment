import pandas as pd
import miniEnc as enc
import threading
import time
import tqdm


class Finage:
    def __init__(self, api_key) -> None:     
        self.baseurl = "https://api.finage.co.uk/last/stock/changes/"
        finage = b'tbW808C4vtO8o6urmH15lnjCucbHxb6Ys2uIpcKbvsnHpbqiq5yr'
        self.finageapi = enc.decode(enc.cccccccz, finage)
        self.dl_lock = threading.Lock()
        max_concurrent_query = 8 # max concurrent query
        self.dl_semaphore = threading.Semaphore(max_concurrent_query)
        self.err_results = {}
        self.result = []
        self.api_key = api_key
    
    def sp500_change_by_sector(self):
        df_sp500_wiki = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
        df_sp500_wiki = df_sp500_wiki[0][["Symbol", "Security", "GICS Sector", "GICS Sub-Industry"]]
        start = time.perf_counter()
        df_sp500_changes = self.get_finage_changes(df_sp500_wiki['Symbol'])
        df_result = df_sp500_changes.merge(df_sp500_wiki, left_on='s', right_on='Symbol')
        df_result_positives = df_result[df_result['Day Pctage Change'] > 0]
        df_result_negatives = df_result[df_result['Day Pctage Change'] < 0]
        end = time.perf_counter()
        print(f"Time taken: {end - start}")
        return df_result_positives, df_result_negatives

    def get_finage_changes(self, symbol_list: list) -> pd.DataFrame:
        col_renames = {'lp': 'Last Price', 'cpd': 'Daily Percentage Change', 
        'cpw': 'Weekly Percentage Change', 'cpm': 'Monthly Percentage Change', 
        'cpsm': 'Six Monthly Percentage Change', 'cpy': 'Yearly Percentage Change'}
        df_changes = pd.DataFrame()
        threads = []
        for i in symbol_list:
            t = threading.Thread(target=self.query_threads, args=(i,))
            t.start()
            threads.append(t)            
        for thread in tqdm.tqdm(threads):
            thread.join()


        for i in self.result:
            df_changes = pd.concat([df_changes, i], axis=1)

        df_changes_T = df_changes.T
        df_changes_T.drop(columns=["t"], inplace=True)
        df_changes_T.rename(columns=col_renames, inplace=True)
        return df_changes_T
    
    def query_threads(self, symbol: str) -> pd.DataFrame:
        df = pd.DataFrame()
        self.dl_semaphore.acquire()
        try:
            df = pd.read_json(self.baseurl + symbol + "?apikey=" + self.api_key, typ="series")
            self.result.append(df)
        except Exception as e:
            print(e)
            self.err_results[symbol] = e
        finally:
            self.dl_semaphore.release()

if __name__ == "__main__":
    finage = Finage()
    print(finage.sp500_change_by_sector())
    if finage.err_results:
        print("Error: ", finage.err_results)