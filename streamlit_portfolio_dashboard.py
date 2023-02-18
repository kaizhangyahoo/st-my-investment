import streamlit as st
import pandas as pd
import ticker_resolution as tr
import getEODprice as g12
import macro_widgets as mw
import plot_portfolio_weights as ppw
import datetime as dt
from market_data_api import Finage
from pandas.tseries.holiday import USFederalHolidayCalendar

def replace_duplicated_ticker(df_in: pd.DataFrame) -> pd.DataFrame:
    """Due to corp events such as SPAC conversion, ticker may change. 
    This function will call the add_ticker function and update company name that has the same ticker to the latest company name
    The dataframe then would be ready for the position calculation"""
    # st.write(os.path.dirname(os.path.realpath(__file__)) + '/company_name_to_ticker.json')
    df = tr.add_ticker(df_in).sort_values('Settlement date', ascending=False)
    df_find_dup_ticker = df[['Ticker','Market', 'Settlement date']].drop_duplicates(subset=['Ticker','Market'], keep='first')
    df_find_dup_ticker = df_find_dup_ticker[df_find_dup_ticker.duplicated(subset=['Ticker'], keep=False)].sort_values('Settlement date', ascending=False)
    df_find_dup_ticker = df_find_dup_ticker.reset_index(drop=True)
    for i in df_find_dup_ticker['Market'][1:len(df_find_dup_ticker)]:
        print(f"{df_find_dup_ticker['Market'][0]} to replace {i}")
        df.loc[df['Market'] == i, 'Market'] = df_find_dup_ticker['Market'][0]
    return df

def dollar_format():
    return "${:,.2f}"

def pound_format():
    return "£{:,.2f}"

def color_green_red(val):
    color = 'green' if val > 0 else 'red'
    return f'background-color: {color}'

@st.cache
def openPositionsCosts(df_in: pd.DataFrame) -> pd.DataFrame:
    """Calculate open position and costs for each ticker"""
    df = replace_duplicated_ticker(df_in)
    df_op = df.groupby(['Market','Ticker']).sum()
    symbols_with_position = df_op[df_op['Quantity'] > 0].index.get_level_values('Ticker').tolist()
    us_symbols_with_position = [x for x in symbols_with_position if x.count('.') == 0]
    uk_symbols_with_position = [x for x in symbols_with_position if x[-2:] == '.L'] # todo: add more market in other region in future
    all_symbols_close_price = {**g12.getEODpriceUSA(us_symbols_with_position), **g12.getEODpriceUK(uk_symbols_with_position)}
    df_op['Last Close'] = df_op.index.get_level_values("Ticker").map(all_symbols_close_price).astype(float)
    df_op['current position'] = df_op['Quantity'] * df_op['Last Close']
    return df_op[['Quantity', 'Consideration', 'current position','Cost/Proceeds', 'Commission','Charges']]


def format_df_for_display(df_in: pd.DataFrame) -> pd.DataFrame:
    df_op_display = df_in.copy()
    df_op_display['PandL'] = df_op_display['current position'] + df_op_display['Cost/Proceeds']
    all_currency_columns = ['Consideration', 'Cost/Proceeds', 'Commission', 'Charges', 'current position']
    has_us_columns = ['Consideration', 'current position']
    df_op_display[all_currency_columns] = df_op_display[all_currency_columns].applymap(pound_format().format)
    us_symbols_with_position = [x for x in df_in.index.get_level_values('Ticker') if x.count('.') == 0]
    df_us = df_op_display[df_op_display.index.get_level_values('Ticker').isin(us_symbols_with_position)]
    df_us[has_us_columns] = df_us[has_us_columns].applymap(lambda x: x.replace('£', '$'))
    df_op_display.update(df_us)
    df_op_display.dropna(inplace=True)
    # df_op_display = df_op_display.style.applymap(color_green_red, subset=['PandL'])
    column_rename = {'Consideration': '$ invested excl costs', 'Cost/Proceeds': 'ttl £ invested'}
    df_op_display.rename(columns=column_rename, inplace=True)
    return df_op_display.sort_values('Quantity', ascending=False)

@st.cache
def sector_etf_price_and_changes(api: str):
    vanguard_etf = ['VGT', 'VHT','VCR', 'VOX', 'VFH', 'VIS', 'VDC', 'VPU', 'VAW', 'VNQ', 'VDE', 'VOO']
    sectors = ['Information Technology', 'Health Care', 'Consumer Discretionary', 'Communication Services', 
                'Financials', 'Industrials', 'Consumer Staples',  'Utilities',  'Materials', 'Real Estate', 'Energy', 'S&P500' ]
    df_dict = pd.DataFrame(list(zip(sectors, vanguard_etf)), columns=['Sector', 'ETF'])
    setf = Finage(api)
    df_sector_ETF_change = setf.get_finage_changes(vanguard_etf)
    df_sector_ETF_change = df_sector_ETF_change.merge(df_dict, left_on='s', right_on='ETF')
    df_sector_ETF_change.set_index("s", inplace=True)
    return df_sector_ETF_change

@st.cache
def get_sp500_changes(api: str):
    # get a list of S&P500 companies from wikipedia
    start_timer = dt.datetime.now()
    print("getting sp500 data from Finage at: ", start_timer)
    df_sp500_wiki = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    df_sp500_wiki = df_sp500_wiki[0][["Symbol", "Security", "GICS Sector", "GICS Sub-Industry"]]
    # get the dataframe for S&P500 changes
    setf = Finage(api)
    df_sp500_changes = setf.get_finage_changes(df_sp500_wiki['Symbol'].tolist())
    print("total time taken to get sp500 data from Finage: ", dt.datetime.now() - start_timer)
    return df_sp500_changes.merge(df_sp500_wiki, left_on='s', right_on='Symbol')
    
def threeTabs():
    st.title("My Portfolio")


    tab1, tab2, tab3, tab4 = st.tabs(["Positions", "Macro", "FICC", "Fire"])

    with tab1:
        st.header("Upload Trade/Transaction History")
        uploaded_file = st.file_uploader('''\
        Upload your trade/transaction history in CSV format. Filename must be in the format of: \n
        1. trade file must have filename start with Trade*.csv \n
        2. transaction file must have filename start with Transaction*.csv''', type=["csv"], accept_multiple_files=True)
        if uploaded_file is not None:
            for f in uploaded_file:
                if f.name.startswith("Trade") and f.name.endswith(".csv"):
                    df_trade_history = pd.read_csv(f)
                    df_trade_history['Settlement date'] = pd.to_datetime(df_trade_history['Settlement date'], format='%d-%m-%Y')
                    st.subheader("latest trade history")
                    st.dataframe(df_trade_history.head(3))

                    st.subheader("Open positions and costs")
                    with st.spinner("Loading tickers into dataframe, take up to 30 seconds..."):
                        df_op = openPositionsCosts(df_trade_history)
                        st.dataframe(format_df_for_display(df_op).style.applymap(color_green_red, subset=['PandL']))

                    market_list = df_trade_history['Market'].unique()
                    market = st.selectbox("Select Stock", market_list)
                    st.subheader("Trade history for {}".format(market))
                    st.dataframe(df_trade_history[df_trade_history['Market'] == market])

                    df_op_has_position = df_op[df_op['Quantity'] > 0]
                    if market in df_op_has_position.index.get_level_values('Market'):
                        company_list = df_op_has_position.index.get_level_values('Market').tolist()
                        standout = [0]*len(company_list)
                        standout[company_list.index(market)] = 0.5
                        fig = ppw.plot_portfolio_weights(df_op_has_position, company_list, standout)
                        st.plotly_chart(fig, use_container_width=True)


                elif f.name.startswith("Transaction") and f.name.endswith(".csv"):
                    df_transactions = pd.read_csv(f)
                    st.subheader("latest transaction history")
                    st.write(df_transactions.head())

                    df_transactions['PL Amount'] = df_transactions['PL Amount'].str.replace(',','')
                    type_dict = {'Date': 'datetime64', 'PL Amount': 'float', 'Summary': 'category', 'Transaction type': 'category', 'Cash transaction': 'boolean', 'MarketName': 'string'}
                    df_transactions = df_transactions.astype(type_dict)
                    df_transactions['Date'] = pd.to_datetime(df_transactions['Date'], format='%Y-%m-%d')
                    # df_transactions.set_index('Date', inplace=True)
                    df_cashIn = df_transactions[(df_transactions['Summary']=='Cash In') | (df_transactions['MarketName'] == 'Bank Deposit')]
                    df_cashIn.rename(columns={'ProfitAndLoss': 'Deposits'}, inplace=True)
                    df_cashIn['Date'] = df_cashIn['Date'].dt.strftime('%Y-%m-%d')
                    df_cashIn.set_index('Date', inplace=True)
                    print(df_cashIn['Deposits'])
                    st.metric(label="Total Cash Deposit in GBP", value=df_cashIn['PL Amount'].sum())
                    with st.expander("Cash In Details"):
                        st.table(df_cashIn['Deposits'])
                    
                    
                else:
                    st.write("filename must begin with 'Trades' or 'Transaction' and format must be a csv")
            


    with tab2:
        st.header("Macro ecconomic environment")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("VIX")
            fig, current_vix = mw.get_vix_from_yahoo("2019-12-01")
            st.plotly_chart(fig, use_container_width=True)
            st.write(current_vix)
        with col2:
            st.subheader("Real GDP Percentage Change")
            fig, last4qtr = mw.real_gdp_pct_change("2012-01-01")
            st.plotly_chart(fig, use_container_width=True)
            st.write(last4qtr)
        st. write('***')

        row1_col1, row1_col2, = st.columns(2)
        with row1_col1:
            st.subheader("PCE")
            fig, last3monthpce = mw.pce_from_fred("2019-01-01")
            st.plotly_chart(fig, use_container_width=True)
            st.write(last3monthpce)
        with row1_col2:
            st.subheader("CPI")
            fig, last3monthcpi = mw.cpi_from_fred("2019-01-01")
            st.plotly_chart(fig, use_container_width=True)
            st.write(last3monthcpi)
        st. write('***')

        st.subheader("CPI & PCE % Change")
        fig, last3month_cpi_pce = mw.cpi_pce_pct_change_from_fred("2020-01-01")
        st.plotly_chart(fig, use_container_width=True)
        st.write(last3month_cpi_pce)
            
        st.subheader("Unemployment Rate and Consumer Confidence")
        row2_col1, row2_col2, = st.columns(2, gap="medium")
        with row2_col1:
            fig, last3month_unemployment = mw.unemployment_rate_from_fred("2020-01-01")
            st.plotly_chart(fig)
            st.write(last3month_unemployment)
            
        with row2_col2:
            fig, last3month_consumer_confidence = mw.consumer_confidence_from_fred("2020-01-01")
            st.plotly_chart(fig, use_container_width=True)
            st.write(last3month_consumer_confidence)
        st. write('***')

        st.subheader("[Buffett Indicator](https://www.investopedia.com/terms/m/marketcapgdp.asp)")
        st.plotly_chart(mw.buffet_indicator_calc_from_fred("1980-01-01"))        
        st. write('***')
        
        # TODO: st.subheader("ISM Manufacturing")

        inputed_api = st.text_input("Enter API key to access changes in sectors", value="finage api key", max_chars=100, help="register at https://moon.finage.co.uk/register")
        if (inputed_api != "finage api key") and (inputed_api != ""):
            st.subheader("sector ETFs")
            change_length = st.selectbox("change period", 
                                        ["Daily Percentage Change", "Weekly Percentage Change", "Monthly Percentage Change", 
                                        "Six Monthly Percentage Change", "Yearly Percentage Change"],
                                        help="select the period to show the change", index=4, key="sector_etf_change_length")
            df = sector_etf_price_and_changes(inputed_api)
            print(df)
            st.plotly_chart(mw.sector_etf_map(df[['Sector', 'ETF', 'Last Price', change_length]]))

            if st.checkbox("show s&p500 winner loser", help="finage allowance might reach", key="sp500_win_lose"):
                change_length = st.selectbox("change period", 
                                ["Daily Percentage Change", "Weekly Percentage Change", "Monthly Percentage Change", 
                                "Six Monthly Percentage Change", "Yearly Percentage Change"],
                                help="select the period to show the change", index=4, key="sp500_win_lose_change_length")
                df = get_sp500_changes(inputed_api)
                df = df.astype({"Last Price": float, change_length: float})
                df.to_csv("sp500_changes.csv")
                df = df[df[change_length]>0]
                st.subheader("S&P500 Winners")
                st.plotly_chart(mw.sp500_win_lose_tree(df[["Symbol","Last Price","Security","GICS Sector","GICS Sub-Industry", change_length]]))
                df = get_sp500_changes(inputed_api)
                df = df[df[change_length]<0]
                df[change_length] = df[change_length] * -1
                st.subheader("S&P500 Losers")
                st.plotly_chart(mw.sp500_win_lose_tree(df[["Symbol","Last Price","Security","GICS Sector","GICS Sub-Industry", change_length]]))



    with tab3:
        st.header("Commodity and Treasury Yield Curve")
        st.subheader("Treasury Yield Curve")
        
        last_business_day = dt.datetime.today() - pd.offsets.BDay(1)
        # check if last_business_day is a federal holiday
        cal = USFederalHolidayCalendar()
        usa_holidays = cal.holidays(start='2022-12-01', end='2028-12-31').date
        if last_business_day.date() in usa_holidays:
            last_business_day = dt.datetime.today() - pd.offsets.BDay(2)

        t_curve_date = st.date_input("Select date", last_business_day, help="present or future date show max history, data from NASDAQ data link").strftime("%Y-%m-%d")
        st.plotly_chart(mw.treasury_curve(t_curve_date), use_container_width=True)

        st.subheader("Gold and Silver")
        show_recession_highlights = st.checkbox("show recession dates")
        st.plotly_chart(mw.gold_silver_price(show_recession_highlights), use_container_width=True)

    with tab4:
        st.header("Financial Independent and Retire Early")
        if 'df_transactions' in locals():
            st.write("df_transactions exists in local")
            st.metric(label="Current available cash in GBP", value=df_transactions['PL Amount'].sum())
        st.image("https://static.streamlit.io/examples/owl.jpg", width=200)


# def main():
#     pass

if __name__ == "__main__":
    threeTabs()