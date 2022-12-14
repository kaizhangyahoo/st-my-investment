import pandas as pd
import miniEnc as enc

class Finage:
    baseurl = "https://api.finage.co.uk/last/stock/changes/"
    finage = b'tbW808C4vtO8o6urmH15lnjCucbHxb6Ys2uIpcKbvsnHpbqiq5yr'
    finageapi = enc.decode(enc.cccccccz, finage)

    def sector_etf_change(self):
        vanguard_etf = ['VGT', 'VHT','VCR', 'VOX', 'VFH', 'VIS', 'VDC', 'VPU', 'VAW', 'VNQ', 'VDE', 'VOO']
        df_sector_ETF_change = pd.DataFrame()
        for i in vanguard_etf:
            df = pd.read_json(self.baseurl + i + "?apikey=" + self.finageapi, typ="series")
            df_sector_ETF_change = pd.concat([df_sector_ETF_change, df], axis=1)
        col_renames = {'lp': 'Last Price', 'cpd': 'Day Pctage Change', 
                'cpw': 'Week Pctage Change', 'cpm': 'Month Pctage Change', 
                'cpsm': 'Six Month Pctage Change', 'cpy': 'Year Pctage Change'}
        df_sector_ETF_change_T = df_sector_ETF_change.T
        df_sector_ETF_change_T.drop(columns=["t"], inplace=True)
        df_sector_ETF_change_T.set_index("s", inplace=True)
        df_sector_ETF_change_T.rename(columns=col_renames, inplace=True)
        return df_sector_ETF_change_T
    
    def sp500_change_by_sector(self):
        df_sp500_changes = pd.DataFrame()
        col_renames = {'lp': 'Last Price', 'cpd': 'Day Pctage Change', 
               'cpw': 'Week Pctage Change', 'cpm': 'Month Pctage Change', 
               'cpsm': 'Six Month Pctage Change', 'cpy': 'Year Pctage Change'}
        df_sp500_wiki = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
        df_sp500_wiki = df_sp500_wiki[0][["Symbol", "Security", "GICS Sector", "GICS Sub-Industry"]]
        for i in df_sp500_wiki['Symbol']:
            df = pd.read_json(self.baseurl + i + "?apikey=" + self.finageapi, typ="series")
            df_sp500_changes = pd.concat([df_sp500_changes, df], axis=1)
        df_sp500_changes_T = df_sp500_changes.T
        df_sp500_changes_T.drop(columns=["t"], inplace=True)
        df_sp500_changes_T.rename(columns=col_renames, inplace=True)
        df_result = df_sp500_changes_T.merge(df_sp500_wiki, left_on='s', right_on='Symbol')
        df_result_positives = df_result[df_result['Day Pctage Change'] > 0]
        df_result_negatives = df_result[df_result['Day Pctage Change'] < 0]
        return df_result_positives, df_result_negatives

if __name__ == "__main__":
    finage = Finage()
    #print(finage.sector_etf_change())
    print(finage.sp500_change_by_sector())