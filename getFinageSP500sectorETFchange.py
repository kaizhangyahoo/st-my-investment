import pandas as pd
import miniEnc as enc

def sector_etf_change():
    baseurl = "https://api.finage.co.uk/last/stock/changes/"
    vanguard_etf = ['VGT', 'VHT','VCR', 'VOX', 'VFH', 'VIS', 'VDC', 'VPU', 'VAW', 'VNQ', 'VDE', 'VOO']
    finage = b'tbW808C4vtO8o6urmH15lnjCucbHxb6Ys2uIpcKbvsnHpbqiq5yr'
    finageapi = enc.decode(enc.cccccccz, finage)
    df_sector_ETF_change = pd.DataFrame()
    for i in vanguard_etf:
        df = pd.read_json(baseurl + i + "?apikey=" + finageapi, typ="series")
        df_sector_ETF_change = pd.concat([df_sector_ETF_change, df], axis=1)
    col_renames = {'lp': 'Last Price', 'cpd': 'Day Pctage Change', 
               'cpw': 'Week Pctage Change', 'cpm': 'Month Pctage Change', 
               'cpsm': 'Six Month Pctage Change', 'cpy': 'Year Pctage Change'}
    df_sector_ETF_change_T = df_sector_ETF_change.T
    df_sector_ETF_change_T.drop(columns=["t"], inplace=True)
    df_sector_ETF_change_T.set_index("s", inplace=True)
    df_sector_ETF_change_T.rename(columns=col_renames, inplace=True)
    return df_sector_ETF_change_T
    