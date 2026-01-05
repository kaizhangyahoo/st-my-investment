import pandas as pd
import streamlit as st
import json
import os
from datetime import datetime, timedelta
from rewrite_ticker_resolution import use_sec_site
from getEODprice import getEODpriceUK, getEODpriceUSA
from plotly import express as px
import rewrite_plot_portfolio_weights as ppw
from market_data_api import OHLC_YahooFinance


@st.cache_data
def get_current_price(tickers: list) -> dict:
    eu_tickers = [ticker for ticker in tickers if ticker.endswith('.L') or ticker.endswith('.DE')]
    us_tickers = [ticker for ticker in tickers if '.' not in ticker]
    us_tickers_positions = getEODpriceUSA(us_tickers)
    eu_tickers_positions = getEODpriceUK(eu_tickers)
    return {**us_tickers_positions, **eu_tickers_positions}

def convert_to_gbp(row):
    if row.name.endswith('.L'):
        return row['Market Value']  # already in GBP
    elif row.name.endswith('.DE'):
        eur_to_gbp = GBPEUR.iloc[-1]
        return row['Market Value'] / eur_to_gbp  # convert EUR to GBP
    else:
        usd_to_gbp = GBPUSD.iloc[-1]
        return row['Market Value'] / usd_to_gbp  # convert USD to GBP

def color_green_red(val):
    color = 'green' if val > 0 else 'red'
    return f'background-color: {color}'

def calculate_past_date(period: str) -> datetime:
    today = datetime.today()
    if period == '1y':
        past_date = today - timedelta(days=365)
    elif period == '6m':
        past_date = today - timedelta(days=182)
    elif period == '3m':
        past_date = today - timedelta(days=91)
    elif period == '1m':
        past_date = today - timedelta(days=30)
    elif period == '1w':
        past_date = today - timedelta(days=7)
    elif period == '1d':
        past_date = today - timedelta(days=1)
    else:
        raise ValueError("Invalid period. Use '1y', '6m', '3m', '1m', '1w', or '1d'.")
    
    # Adjust to business day (if Saturday or Sunday, move to preceding Friday)
    if past_date.weekday() == 5: # Saturday
        past_date -= timedelta(days=1)
    elif past_date.weekday() == 6: # Sunday
        past_date -= timedelta(days=2)
        
    return past_date

@st.cache_data
def get_historical_fx(start_date: str):
    fx_data ={}
    for pair in ['GBPUSD=X', 'GBPEUR=X']:
        try:
            data = OHLC_YahooFinance(pair, start_date).yahooDataV8()
            fx_data[pair] = data['close']
        except Exception as e:
            print(f"Error retrieving data for {pair}: {e}")
    return fx_data


# copilot generated code for ticker holding period
def symbol_trading_summary(df_trade_history):
    df = df_trade_history.copy()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(0)

    g = df.groupby('Ticker')
    first_date = g['Date'].min()
    last_appearance = g['Date'].max()
    current_qty = g['Quantity'].sum()

    out = pd.DataFrame({
        'Ticker': first_date.index,
        'FirstBuyDate': pd.to_datetime(first_date).dt.date,
        'CurrentQuantity': current_qty.values,
        'LastDate': pd.to_datetime(last_appearance).dt.date
    }).reset_index(drop=True)

    # If still held (non-zero quantity) set LastDate to None
    out.loc[out['CurrentQuantity'] != 0, 'LastDate'] = None

    return out

def synthetic_historical_data_generator(df_each_ticker: pd.DataFrame, ticker: str) -> pd.DataFrame:
    df_each_ticker = df_each_ticker.sort_values(by='Date', ascending=True).reset_index(drop=True)
    rows = []
    for i in range(len(df_each_ticker)-1):
        start = df_each_ticker.at[i, 'Date']
        end = df_each_ticker.at[i+1, 'Date']
        start_price = df_each_ticker.at[i, 'Price']
        end_price = df_each_ticker.at[i+1, 'Price']
        biz = pd.bdate_range(start=start, end=end)
        prices = np.linspace(start_price, end_price, num=len(biz))

        for j, d in enumerate(biz):
            rows.append({
                "high": np.nan,
                "volume": 0,
                "open": np.nan,
                "close": prices[j]/100,
                "low": np.nan,
                "Date": d.date(),        # date only, no time
                "ticker": ticker
            })

    df_synthetic = pd.DataFrame(rows)
    df_synthetic = df_synthetic.drop_duplicates(subset=['Date'], keep='first').reset_index(drop=True)
    return df_synthetic

def historical_market_data_yahoo(market_data_collections: pd.DataFrame, df_trade_history: pd.DataFrame) -> pd.DataFrame:
    df_market_historical_data = pd.DataFrame()
    for idx, row in market_data_collections.iterrows():
        print(f"Fetching data for {row['Ticker']} from {row['FirstBuyDate']}")
        try: 
            if row['LastDate'] is None:
                market_historical_data = OHLC_YahooFinance(row['Ticker'], row['FirstBuyDate'].strftime('%Y-%m-%d')).yahooDataV8()
            else:
                market_historical_data = OHLC_YahooFinance(row['Ticker'], row['FirstBuyDate'].strftime('%Y-%m-%d'), row['LastDate'].strftime('%Y-%m-%d')).yahooDataV8()
            market_historical_data['ticker'] = row['Ticker']
            df_market_historical_data = pd.concat([df_market_historical_data, market_historical_data], ignore_index=True)
        except Exception as e:
            print(f"Error retrieving data for {row['Ticker']}: {e}")
            
            # Fallback to synthetic data
            df_synthetic = synthetic_historical_data_generator(df_trade_history[df_trade_history['Ticker'] == row['Ticker']], row['Ticker'])
            df_market_historical_data = pd.concat([df_market_historical_data, df_synthetic], ignore_index=True)

            continue
    return df_market_historical_data


st.title("Portfolio Management Dashboard and Analytics")

st.header("Upload Trade/Transaction History")
uploaded_file = st.file_uploader('''\
Upload your trade/transaction history in CSV format. Filename must be in the format of: \n
1. trade file must have filename start with Trade*.csv \n
2. transaction file must have filename start with Transaction*.csv''', type=["csv"], accept_multiple_files=True)
if uploaded_file is not None:
    for f in uploaded_file:
        if f.name.startswith("Trade") and f.name.endswith(".csv"):
            df_trade_history = pd.read_csv(f)
            df_trade_history['Date'] = pd.to_datetime(df_trade_history['TextDate'], errors='coerce', dayfirst=True)
            
            # add ticker to trade history table
            pwd = os.path.dirname(os.path.realpath(__file__))
            reference_data_json_file = pwd + '/company_name_to_ticker.json'
            with open(reference_data_json_file, 'r') as json_file:
                company_name_to_ticker = json.load(json_file)
            df_trade_history['Ticker'] = df_trade_history['Market'].map(company_name_to_ticker)
            
            ## find missing symbols
            missing_symbols = df_trade_history[~df_trade_history['Market'].isin(company_name_to_ticker.keys())]['Market'].unique()
            if len(missing_symbols) > 0:
                print("The following company names are not recognized and have no Ticker assigned:")
                for symbol in missing_symbols:
                    print(f"• {symbol}") 
                print("Attempting to resolve missing company names using SEC data...")
                resolved_symbols = use_sec_site(missing_symbols.tolist())
                # compare resolved_symbols with missing_symbols, if there is still missing, add them as None to allow user to add them manually
                if len(missing_symbols) != len(resolved_symbols): # TODO: find another way to resolve symbols
                    for ms in missing_symbols:
                        if ms not in resolved_symbols:
                            resolved_symbols[ms] = None
                st.write(f"Resolved Symbols: {resolved_symbols}")
                st.write(f"unresolved Symbols: {[k for k,v in resolved_symbols.items() if v is None]}")

                # Allow user to edit resolved symbols
                st.subheader("Review and edit resolved mappings:")
                edited_symbols = {}
                
                for market_name, ticker in resolved_symbols.items():
                    col1, col2, col3 = st.columns([2, 2, 1])
                    col1.write(f"**{market_name}**")
                    # User can edit the ticker in text_input
                    edited_ticker = col2.text_input(
                        label="Ticker",
                        value=ticker if ticker else "",
                        key=f"ticker_{market_name}",
                        label_visibility="collapsed"
                    )
                    edited_symbols[market_name] = edited_ticker
                    # Checkbox to confirm inclusion
                    if col3.checkbox("✓ Include", key=f"include_{market_name}", value=True):
                        pass  # will be saved if checked
                
                # Save confirmed mappings
                col_save, col_cancel = st.columns(2)
                if col_save.button("✅ Save to company_name_to_ticker.json"):
                    # Filter: only save if checkbox is checked AND ticker is not empty
                    confirmed_mappings = {
                        market_name: ticker 
                        for market_name, ticker in edited_symbols.items() 
                        if ticker.strip() and st.session_state.get(f"include_{market_name}", False)
                    }
                    
                    if confirmed_mappings:
                        company_name_to_ticker.update(confirmed_mappings)
                        with open(reference_data_json_file, 'w') as json_file:
                            json.dump(company_name_to_ticker, json_file, indent=2)
                        st.success(f"✅ Saved {len(confirmed_mappings)} new mappings!")
                        st.rerun()
                        # check if trade history dataframe has no missing tickers now
                        if df_trade_history['Ticker'].isnull().any():
                            st.write("There are still unresolved tickers in trade history:")
                            st.table(df_trade_history[df_trade_history['Ticker'].isnull()])
                    else:
                        st.error("No valid mappings to save (empty tickers or unchecked items).")
                
                if col_cancel.button("❌ Cancel"):
                    st.info("Cancelled. No changes made.")




            
            # print trade history this quarter
            st.subheader("Trade History This Quarter")
            today = datetime.now()
            current_quarter = pd.Period(today, freq='Q')
            current_quarter_trade_history = df_trade_history[(df_trade_history['Date'].dt.to_period('Q') == current_quarter) & (df_trade_history['Activity']=="TRADE")] # type: ignore[attr-defined]
            st.dataframe(current_quarter_trade_history)


            # remove df_trade_history row that Ticker is null
            df_trade_history_not_null = df_trade_history[df_trade_history['Ticker'].notnull()]
            if len(df_trade_history_not_null) != len(df_trade_history):
                st.warning(f"⚠️ {len(df_trade_history) - len(df_trade_history_not_null)} rows with unresolved Ticker were excluded from analysis.Result might not be accurate.")
            
            # update ticker
            df_trade_history_ticker_updated = df_trade_history_not_null.copy()
            df_trade_history_ticker_updated['Ticker'] = df_trade_history_ticker_updated['Ticker'].replace(company_name_to_ticker)

            # calculate current positions
            df_current_positions = df_trade_history_ticker_updated.groupby('Ticker').agg({'Quantity':'sum', 'Market': 'last', 'Cost/Proceeds': 'sum', 'Charges': 'sum', 'Commission': 'sum', 'Currency': 'last'})
            df_current_positions = df_current_positions[df_current_positions['Quantity'] != 0]
            df_current_positions['Costs'] = df_current_positions['Cost/Proceeds'] + df_current_positions['Charges'] + df_current_positions['Commission']
            current_prices = get_current_price(df_current_positions.index.tolist())
            df_current_positions['Current Price'] = df_current_positions.index.map(current_prices) # add EOD price to current price TODO: change when market open
            df_current_positions['Quantity'] = pd.to_numeric(df_current_positions['Quantity'], errors='coerce')
            df_current_positions['Current Price'] = pd.to_numeric(df_current_positions['Current Price'], errors='coerce')
            df_current_positions['Market Value'] = df_current_positions['Quantity'] * df_current_positions['Current Price']
            GBPUSD = get_historical_fx(df_trade_history_ticker_updated['Date'].min().strftime('%Y-%m-%d'))['GBPUSD=X']
            GBPEUR = get_historical_fx(df_trade_history_ticker_updated['Date'].min().strftime('%Y-%m-%d'))['GBPEUR=X']
            df_current_positions['Market Value GBP'] = df_current_positions.apply(convert_to_gbp, axis=1)

            Total_market_value_gbp = df_current_positions['Market Value GBP'].sum()
            USD_market_value_in_gbp = df_current_positions[df_current_positions['Currency']=='USD']['Market Value GBP'].sum()
            EUR_market_value_in_gbp = df_current_positions[df_current_positions['Currency']=='EUR']['Market Value GBP'].sum()
            GBP_market_value_in_gbp = df_current_positions[df_current_positions['Currency']=='GBP']['Market Value GBP'].sum()
            st.plotly_chart(px.pie(
                names=['USD', 'EUR', 'GBP'],
                values=[USD_market_value_in_gbp, EUR_market_value_in_gbp, GBP_market_value_in_gbp],
                title=f'Portfolio Currency Breakdown (Total Market Value: £{Total_market_value_gbp:,.2f})'
            ))
            df_current_positions['PandL GBP'] = df_current_positions['Market Value GBP'] + df_current_positions['Costs']
            df_present_positions = df_current_positions[['Market', 'Quantity', 'Current Price', 'Market Value GBP', 'PandL GBP']]
            st.dataframe(df_present_positions.style.format({
                'Market Value GBP': '£{:,.2f}',
                'PandL GBP': '£{:,.2f}'
            }).map(color_green_red, subset=['PandL GBP']), height=800)

            
            # single ticker trade history section
            trade_history_search_options1 = df_trade_history_ticker_updated['Market'].unique()
            trade_history_search_options2 = df_trade_history_ticker_updated['Ticker'].unique()
            trade_history_search_options = trade_history_search_options1.tolist() + trade_history_search_options2.tolist() 
            selected_company = st.selectbox(
                label="Select an instrument to see trade history",
                options=trade_history_search_options,
                key="select_company_ticker"
            )

            if selected_company in company_name_to_ticker.values():
                selected_ticker = selected_company
            else:
                selected_ticker = company_name_to_ticker[selected_company]
                # check if the ticker itself is a key in the map (chained mapping)
                if selected_ticker in company_name_to_ticker:
                     selected_ticker = company_name_to_ticker[selected_ticker]
                print(selected_ticker)
    
            if selected_company:
                df_ticker_trade_history = df_trade_history_ticker_updated[
                    (df_trade_history_ticker_updated['Ticker'] == selected_ticker) & 
                    (df_trade_history_ticker_updated['Activity'] == "TRADE")
                ].sort_values(by='Date', ascending=False)
        
                st.subheader(f"Trade History for {selected_company} ({selected_ticker})")
                st.table(df_ticker_trade_history[['Market', 'Ticker', 'Date', 'Direction', 'Quantity','Price', 'Currency']])



            # plot portfolio weights TODO: buggy, eg use any symbol highlight won't work
            standout = [0.0] * len(df_current_positions)  # selected instrument highlight
            instruments_list = df_current_positions['Market'].tolist()
            if selected_company in instruments_list:
                idx = instruments_list.index(selected_company)
                standout[idx] = 0.5
            current_GBP_rate = {'GBPUSD=X': GBPUSD.iloc[-1], 'GBPEUR=X': GBPEUR.iloc[-1]}
            fig = ppw.plot_portfolio_weights(df_current_positions, standout, current_GBP_rate)
            st.plotly_chart(fig, use_container_width=True)


            # ============ PORTFOLIO VALUE OVER TIME WIDGET ============
            st.subheader("Portfolio Value Over Time")

            # Date Range Slider
            today_date = datetime.now().date()
            one_year_ago = today_date - pd.DateOffset(years=1)
            two_years_ago = today_date - pd.DateOffset(years=2)

            selected_date_range = st.slider(
                "Select Date Range",
                min_value=two_years_ago.date(),
                max_value=today_date,
                value=(one_year_ago.date(), today_date),
                format="YYYY-MM-DD"
            )
            
            start_date_selected, end_date_selected = selected_date_range
            st.write(f"Showing data from {start_date_selected} to {end_date_selected}")
            
            left1, left2, middle1, middle2, right1, right2 = st.columns(6)
            if left1.button("1y", width="stretch"):
                selected_date = calculate_past_date("1y")
            if left2.button("6m", width="stretch"):
                selected_date = calculate_past_date("6m")
            if middle1.button("3m", width="stretch"):
                selected_date = calculate_past_date("3m")
            if middle2.button("1m", width="stretch"):
                selected_date = calculate_past_date("1m")
            if right1.button("1w", width="stretch"):
                selected_date = calculate_past_date("1w")
            if right2.button("1d", width="stretch"):
                selected_date = calculate_past_date("1d")
            