import pandas as pd
import streamlit as st
import json
import os
from datetime import datetime
from rewrite_ticker_resolution import use_sec_site
from getEODprice import getEODpriceUK, getEODpriceUSA
from plotly import express as px
import rewrite_plot_portfolio_weights as ppw


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
        eur_to_gbp = GBP['GBPEUR=X']
        return row['Market Value'] / eur_to_gbp / 100 # convert EUR to GBP
    else:
        usd_to_gbp = GBP['GBPUSD=X']
        return row['Market Value'] / usd_to_gbp / 100 # convert USD to GBP

def color_green_red(val):
    color = 'green' if val > 0 else 'red'
    return f'background-color: {color}'

# @st.cache_data
# def search_companies(searchterm: str) -> list:
#     """Search company names and tickers by searchterm"""
#     matches = []
#     for company_name, ticker in company_name_to_ticker.items():
#         if searchterm.lower() in company_name.lower() or searchterm.lower() in ticker.lower():
#             matches.append(f"{company_name} ({ticker})")
#     return matches

@st.fragment
def single_ticker_trade_history_section(df_trade_history_not_null, company_name_to_ticker):
    """Only this section reruns when selectbox changes"""
    if "selected_company" not in st.session_state:
        st.session_state.selected_company = None
    
    trade_history_search_options1 = df_trade_history_not_null['Market'].unique()
    trade_history_search_options2 = df_trade_history_not_null['Ticker'].unique()
    trade_history_search_options = trade_history_search_options1.tolist() + trade_history_search_options2.tolist() 
    selected_company = st.selectbox(
        label="Select an instrument to see trade history",
        options=trade_history_search_options,
        key="select_company_ticker"
    )
    
    if selected_company != st.session_state.selected_company:
        st.session_state.selected_company = selected_company
    
    if st.session_state.selected_company:
        if st.session_state.selected_company in company_name_to_ticker.values():
            selected_ticker = st.session_state.selected_company
        else:
            selected_ticker = company_name_to_ticker[st.session_state.selected_company]
        df_ticker_trade_history = df_trade_history_not_null[
            (df_trade_history_not_null['Ticker'] == selected_ticker) & 
            (df_trade_history_not_null['Activity'] == "TRADE")
        ].sort_values(by='Date', ascending=False)
        
        st.subheader(f"Trade History for {st.session_state.selected_company} ({selected_ticker})")
        st.table(df_ticker_trade_history[['Market', 'Ticker', 'Date', 'Direction', 'Quantity','Price', 'Currency']])

    return selected_company




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
            
            # calculate current positions
            df_current_positions = df_trade_history_not_null.groupby('Ticker').agg({'Quantity':'sum', 'Market': 'last', 'Cost/Proceeds': 'sum', 'Charges': 'sum', 'Commission': 'sum', 'Currency': 'last'})
            df_current_positions = df_current_positions[df_current_positions['Quantity'] != 0]
            df_current_positions['Costs'] = df_current_positions['Cost/Proceeds'] + df_current_positions['Charges'] + df_current_positions['Commission']
            current_prices = get_current_price(df_current_positions.index.tolist())
            df_current_positions['Current Price'] = df_current_positions.index.map(current_prices) # add EOD price to current price TODO: change when market open
            df_current_positions['Quantity'] = pd.to_numeric(df_current_positions['Quantity'], errors='coerce')
            df_current_positions['Current Price'] = pd.to_numeric(df_current_positions['Current Price'], errors='coerce')
            df_current_positions['Market Value'] = df_current_positions['Quantity'] * df_current_positions['Current Price']
            GBP = getEODpriceUK(['GBPUSD=X', 'GBPEUR=X'])
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
            selected_instrument = single_ticker_trade_history_section(df_trade_history_not_null, company_name_to_ticker)


            # plot portfolio weights
            standout = [0.0] * len(df_current_positions)  # selected instrument highlight
            instruments_list = df_current_positions['Market'].tolist()
            if selected_instrument in instruments_list:
                idx = instruments_list.index(selected_instrument)
                standout[idx] = 0.5
            fig = ppw.plot_portfolio_weights(df_current_positions, standout, GBP)
            st.plotly_chart(fig, use_container_width=True)
