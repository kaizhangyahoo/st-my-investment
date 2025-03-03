import pandas as pd
import numpy as np
import json
import re
import os
import PyPDF2
from datetime import datetime
from difflib import get_close_matches
import tqdm
import requests

# reference_data_json_file = sys.path[0] + '/company_name_to_ticker.json'
pwd = os.path.dirname(os.path.realpath(__file__))
reference_data_json_file = pwd + '/company_name_to_ticker.json'
print("reference_data_json_file: ", reference_data_json_file)

def load_ticker_from_json(json_file: str, df_in: pd.DataFrame) -> pd.DataFrame:
    try: 
        with open(json_file) as f: 
            ticker_dict = json.load(f)
    except FileNotFoundError:
        print(f"Error: {json_file} not found")
        df_in['Ticker'] = np.nan
        return df_in
    # for k, v in ticker_dict.items():
    #     df_in.loc[df_in['Market'] == k, 'Ticker'] = v
    df_in['Ticker'] = df_in['Market'].map(ticker_dict)
    return df_in

def get_sec_tickers() -> dict:
    # get json from sec site and convert to dict
    url = "https://www.sec.gov/files/company_tickers.json"
    request_headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "priority": "u=0, i",
    "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    }
    try:
        response = requests.get(url, headers=request_headers, allow_redirects=True)
        list_of_dicts = [value for value in response.json().values()]
    except:
        print("Error: CANNOT get to sec tickers from https://www.sec.gov/files/company_tickers.json")
        return {}
    sec_site_mapping = pd.DataFrame(list_of_dicts)
    sec_site_mapping['title'] = sec_site_mapping['title'].str.replace('\.', '', regex=True)
    sec_site_mapping['title'] = sec_site_mapping['title'].str.replace('\,', '', regex=True)
    return dict(zip(sec_site_mapping['title'], sec_site_mapping['ticker']))   


def pdf_to_dataframe(pdf_path: str) -> pd.DataFrame:
    """read from local pdf and return_type accepts symbol or ticker or US-symbol """
    start = datetime.now()
    print("Start reading pdf file...")
    alltext = ""
    try:
        pdfReader = PyPDF2.PdfReader(pdf_path)
    except:
        print("Error: can not open pdf")
        return {}
    
    try:
        for page in tqdm.tqdm(pdfReader.pages):
            alltext += page.extract_text()
    except:
        print("Error: can not extract text from pdf")
        return {}
    
    print(f"total time to read {len(pdfReader.pages)} pages pdf: {datetime.now() - start}")

    mapping_lines = []
    for i in re.split(r'\n', alltext):    
        # if string ends with Y or N
        if i.endswith('Y') or i.endswith('N'):
            mapping_lines.append(i)
    print(f"Total usable lines found  in IG pdf: {len(mapping_lines)} and time taken: {datetime.now() - start}")
    pattern = r"(?P<name>^.*)\s(?P<ticker>\w+.\w+)\s\/\s(?P<symbol>\w+)\s(?P<region>\w+).*\s(?P<ISA>\w)\s(?P<SIPP>\w)$"
    print("Start parsing pdf lines...")
    all_pdf_data = pd.DataFrame()
    for i in tqdm.tqdm(mapping_lines):
        m = re.search(pattern, i)
        if m:
            # all_pdf_tickers = all_pdf_tickers.append(m.groupdict(), ignore_index=True) also works but futureWarning
            all_pdf_data = pd.concat([all_pdf_data, pd.DataFrame.from_dict(m.groupdict(), orient='index').T], ignore_index=True)
    pdf_uppercase_ticker_only = all_pdf_data[all_pdf_data['ticker'].apply(no_lowercase)] # remove ticker with lowercase to avoid duplication eg SDRt.L
    print(f"Total extracted records found in IG pdf: {len(pdf_uppercase_ticker_only)} and time taken: {datetime.now() - start}")
    return pdf_uppercase_ticker_only

def ig_pdf_dataframe_to_dict(df_in: pd.DataFrame, return_type: str = 'symbol') -> dict:
    """ from pdf dataframe to dict with key as company name and different kind of values:  
    1. ticker (MSCI.N, NDAQ.O, 888L) 
    2. symbol (FDS, PAY)
    3. free OHLCV data
      3.1. yahoo
      3.2. alphavantage
      3.3. iex
      3.4. polygon.io
      3.5. eodhd
      3.6. 12data
    example: ig_pdf_dataframe_to_dict(pdf_dataframe, return_type='symbol')"""    
    supported_free_ohlc_data = ['yahoo', 'alphavantage', 'iex', 'polygon.io', 'eodhd', '12data']
    region_suffix_mapping = {'AU':'AX', 'AV':'VI', 'BB':'BR', 'GY':'DE', 'TH':'DE', 'ID':'I', 'NA':'AS', 'LN':'L', 'PZ':'NXX', 'LI':'L', 'EF':'E'}
    if return_type == "ticker":
        all_tickers = dict(zip(df_in['name'], df_in['ticker']))
        return all_tickers
    elif return_type == "symbol":
        usa_noly = df_in[df_in['region'] == 'US']
        us_tickers = dict(zip(usa_noly['name'], usa_noly['symbol']))
        for k, v in region_suffix_mapping.items():
            df_in.loc[df_in['region'] == k, 'symbol'] = df_in['symbol'] + '.' + v
        all_other_symbols = dict(zip(df_in['name'], df_in['symbol']))
        return {**all_other_symbols, **us_tickers}    
    # elif return_type in supported_free_ohlc_data:
    #     usa_noly = df_in[df_in['region'] == 'US']
    #     us_tickers = dict(zip(usa_noly['name'], usa_noly['symbol']))
    #     lse_only = df_in[df_in['region'] == 'LN']
    #     if return_type == 'yahoo':
    #         lse_tickers = dict(zip(lse_only['name'], lse_only['symbol'] + '.L'))
    #         return {**lse_tickers, **us_tickers}
    #     elif return_type in ["eodhd","12data", "alphavantage"] : # US only -- todo: to check api document for alphavantage + polygon.io
    #         return us_tickers
    #     elif return_type == 'iex':
    #         lse_tickers = dict(zip(lse_only['name'], lse_only['symbol'] + '-LN'))
    #         return {**lse_tickers, **us_tickers}
    else:
        raise ValueError("return_type must be a valid option")


def no_lowercase(s: str) -> bool:
    return not bool(re.search(r'[a-z]', s))

def close_matched_tickers(unknown_ticker_list: list, tickers_dict: dict, cutoff_ratio = 0.801) -> dict:
    """
    compare company name without tickers against a ticker dictionary find close word match ratio above 0.8 by default
    """
    possible_resolute = {}
    ticker_keys = list(tickers_dict.keys())
    for i in unknown_ticker_list:
        closely_matched_name = get_close_matches(i, ticker_keys, cutoff=cutoff_ratio)
        if len(closely_matched_name) > 0:
            possible_resolute[i] = tickers_dict[closely_matched_name[0]]
    return possible_resolute


def match_tickers_dict(ticker_dict: dict, df_in: pd.DataFrame, close_match=False):
    ''' match ticker from dict to df_in, write dict to json file 
    return df_in with ticker column and number of unresolved tickers'''
    if close_match:
        df_in['Ticker'] = df_in['Market'].map(ticker_dict).fillna(df_in['Ticker'])
        add_ticker_to_json(ticker_dict, reference_data_json_file)
        resolved = len(df_in[df_in['Ticker'].notna()]['Market'].unique())
        return df_in, resolved

    if 'TPname' not in df_in.columns:
        df_in['TPname'] = df_in['Market'].str.replace(r'\(.*\)', '', regex=True).str.strip().str.upper()

    TICKER_dict = {k.upper(): v for k, v in ticker_dict.items()}
    
    df_in['Ticker'] = df_in['TPname'].map(TICKER_dict).fillna(df_in['Ticker']) #TODO: potential bug to overwrite the correct symbol in json file
    df_resolved = df_in[df_in['Ticker'].notna()]
    print(df_resolved.drop_duplicates(subset=['Market', 'Ticker'])[['Market', 'Ticker']])
    add_ticker_to_json(dict(zip(df_resolved['Market'], df_resolved['Ticker'])), reference_data_json_file)
    resolved = len(df_in[df_in['Ticker'].notna()]['Market'].unique())
    return df_in, resolved


def add_ticker_to_json(new_dict: dict, output_json_file: str):
    ''' open existing json, read to dict, add new dict, write to json'''
    with open(output_json_file, 'r+') as f:
        existing_dict = json.load(f)
        existing_dict.update(new_dict)
        f.seek(0)
        json.dump(existing_dict, f, indent=4)

def ticker_by_keyword(unresolved_tpname: list, tickers_dict: dict) -> dict:
    """
    find keyword in company name and search for relevant ticker in ticker dictionary, case insensitive
    """
    not_keyword = ["the", "inc", "corp", "ltd", "limited", "co", "corporation", 
    "company", "plc", "group", "lp", "holdings", "trust", "laboratories"] # non-keywords must be lower case
    possible_resolute = {}
    for i in unresolved_tpname: 
        for j in [x.lower() for x in i.split()]:
            if j not in not_keyword:
                for k in tickers_dict.keys():
                    if j in k.lower():
                        possible_resolute[i] = tickers_dict[k]
                        break
                break
    return possible_resolute      



def add_ticker(df_in: pd.DataFrame, output_json_file = reference_data_json_file) -> pd.DataFrame:
    total_instruments = len(df_in['Market'].unique())    

    if 'Ticker' in df_in.columns:
        print("csv already has ticker in it, no need to add ticker")
        return df_in

    # add ticker from json file
    df_in = load_ticker_from_json(reference_data_json_file, df_in)
    # check if df_in['Ticker] has na
    ttl_resolved_instrument = len(df_in[df_in['Ticker'].notna()]['Market'].unique()) 
    if ttl_resolved_instrument == total_instruments:
        print("all instruments resolved from json file")
        return df_in
    else:
        print(f"Total instruments resolved from json file: {ttl_resolved_instrument} out of {total_instruments}")

    # add ticker from SEC site
    sec_tickers = get_sec_tickers()
    df_in, ttl_resolved_instrument = match_tickers_dict(sec_tickers, df_in)
    print(f"Total instruments resolved after appending sec site: {ttl_resolved_instrument} out of {total_instruments}")
    if ttl_resolved_instrument == total_instruments:
        print("all instruments resolved from sec site")
        return df_in

    # add ticker from IG pdf
    df_pdf = pdf_to_dataframe(f'{pwd}/Stockbroking Share List.pdf')
    pdf_tickers = ig_pdf_dataframe_to_dict(df_pdf)
    df_in, ttl_resolved_instrument = match_tickers_dict(pdf_tickers, df_in)
    print(f"Total instruments resolved after appending json file: {ttl_resolved_instrument} out of {total_instruments}")
    if ttl_resolved_instrument == total_instruments:
        print("all instruments resolved after importing IG pdf")
        return df_in


    # close match tickers from sec site
    close_matched_result = close_matched_tickers(df_in[df_in['Ticker'].isna()]['Market'], sec_tickers)
    print(f"{close_matched_result} to be added to dataframe and json file, sec")
    df_in, ttl_resolved_instrument = match_tickers_dict(close_matched_result, df_in, close_match=True)
    if ttl_resolved_instrument == total_instruments:
        print("all instruments resolved after close match sec site dict")
        return df_in

    # close match tickers from IG pdf
    close_matched_result = close_matched_tickers(df_in[df_in['Ticker'].isna()]['Market'], pdf_tickers, cutoff_ratio=0.667)
    print(f"{close_matched_result} to be added to dataframe and json file, pdf")
    df_in, ttl_resolved_instrument = match_tickers_dict(close_matched_result, df_in, close_match=True)
    if ttl_resolved_instrument == total_instruments:
        print("all instruments resolved after close match pdf dict")
        return df_in

    # resolve by keyword
    unresolved_company_name = df_in[df_in['Ticker'].isna()]['Market'].unique()
    keyword_resolution = ticker_by_keyword(unresolved_company_name, sec_tickers)
    #keyword_resolution = ticker_by_keyword(unresolved_company_name, pdf_tickers)
    print(f"{keyword_resolution} to be added to dataframe and json file, keyword")
    df_in, ttl_resolved_instrument = match_tickers_dict(keyword_resolution, df_in, close_match=True)
    if ttl_resolved_instrument == total_instruments:
        print("all instruments resolved after keyword resolution")
        return df_in

    # check if there is any unresolved company name, for future manual resolution or function improvement
    unresolved_company_name = df_in[df_in['Ticker'].isna()]['Market'].unique()
    print(f"Unresolved company name: {unresolved_company_name}")
    print(f"Manually add new instrument to json file {output_json_file}")
    print("return dataframe with resolved tickers only")
    return df_in[df_in['Ticker'].notna()]


def main():
    with open('/mnt/f/Downloads/TradeHistory.csv', 'r') as f:
        df_in = pd.read_csv(f)
    df_out = add_ticker(df_in)
    print(df_out)

if __name__ == "__main__":
    main()