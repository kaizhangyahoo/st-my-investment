import streamlit as st
import pandas as pd
import ticker_resolution as tr
import getEODprice as g12
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas_datareader.data as web

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


def threeTabs():
    st.title("My Portfolio")


    tab1, tab2, tab3 = st.tabs(["Positions", "Macro", "Fire"])

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
                        print(df_op)
                        # format the dataframe for display
                        df_op_display = df_op.copy()
                        all_currency_columns = ['Consideration', 'Cost/Proceeds', 'Commission', 'Charges', 'current position']
                        has_us_columns = ['Consideration', 'current position']
                        df_op_display[all_currency_columns] = df_op_display[all_currency_columns].applymap(pound_format().format)
                        us_symbols_with_position = [x for x in df_op.index.get_level_values('Ticker') if x.count('.') == 0]
                        df_us = df_op_display[df_op_display.index.get_level_values('Ticker').isin(us_symbols_with_position)]
                        df_us[has_us_columns] = df_us[has_us_columns].applymap(lambda x: x.replace('£', '$'))
                        df_op_display.update(df_us)
                        column_rename = {'Consideration': '$ invested excl costs', 'Cost/Proceeds': 'ttl £ invested'}
                        df_op_display = df_op_display.rename(columns=column_rename)
                        st.dataframe(df_op_display.sort_values('Quantity', ascending=False))

                    market_list = df_trade_history['Market'].unique()
                    market = st.selectbox("Select Stock", market_list)
                    st.subheader("Trade history for {}".format(market))
                    st.dataframe(df_trade_history[df_trade_history['Market'] == market])

                    df_op_has_position = df_op[df_op['Quantity'] > 0]
                    if market in df_op_has_position.index.get_level_values('Market'):
                        company_list = df_op_has_position.index.get_level_values('Market').tolist()
                        standout = [0]*len(company_list)
                        standout[company_list.index(market)] = 0.5
                        print(standout)
                        fig = make_subplots(rows=1, cols=2, specs=[[{"type": "domain"}, {"type": "domain"}]]) # specs explained in https://plotly.com/python/subplots/
                        fig.add_trace(go.Pie(
                            labels = company_list,
                            values = df_op_has_position['current position'],
                            pull = standout, 
                            name = "Current Position",
                        ), 1, 1)
                        fig.add_trace(go.Pie(
                            labels = company_list,
                            values = abs(df_op_has_position['Cost/Proceeds']),
                            pull = standout, 
                            name = "Investment",
                        ), 1, 2)
                        fig.update_layout(
                            title_text="Current position and total investment on each instrument",
                            width=1000, 
                            height=800,
                            showlegend=False
                        )
                            # annotations=[dict(text='Current position', x=0.18, y=0.5, font_size=20, showarrow=False),
                            #              dict(text='£ invested', x=0.82, y=0.5, font_size=20, showarrow=False)])
                        st.plotly_chart(fig, use_container_width=True)




                elif f.name.startswith("Transaction") and f.name.endswith(".csv"):
                    df_transactions = pd.read_csv(f)
                    st.subheader("latest transaction history")
                    st.write(df_transactions.head())

                    df_transactions['PL Amount'] = df_transactions['PL Amount'].str.replace(',','')
                    type_dict = {'Date': 'datetime64', 'PL Amount': 'float', 'Summary': 'category', 'Transaction type': 'category', 'Cash transaction': 'boolean', 'MarketName': 'string'}
                    df_transactions = df_transactions.astype(type_dict)
                    df_transactions['Date'] = pd.to_datetime(df_transactions['Date'], format='%Y-%m-%d')
                    df_transactions.set_index('Date', inplace=True)
                    df_cashIn = df_transactions[(df_transactions['Summary']=='Cash In') | (df_transactions['MarketName'] == 'Bank Deposit')]
                    df_cashIn.rename(columns={'ProfitAndLoss': 'Deposits'}, inplace=True)
                    st.metric(label="Total Cash Deposit in GBP", value=df_cashIn['PL Amount'].sum())
                    with st.expander("Cash In Details"):
                        st.table(df_cashIn['Deposits'])
                    
                    
                else:
                    st.write("filename must begin with 'Trades' or 'Transaction' and format must be a csv")
            
        else:
            st.error("no file uploaded")
        



    with tab2:
        st.header("Macro ecconomic environment")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("VIX")
            df_vix = web.DataReader('^VIX', 'yahoo', start='2019-01-01')
            fig = go.Figure(data=[go.Candlestick(x=df_vix.index,
                    open=df_vix['Open'],
                    high=df_vix['High'],
                    low=df_vix['Low'],
                    close=df_vix['Close'])])
            fig.update_layout(yaxis_title='VIX', xaxis_title='Date')
            st.plotly_chart(fig, use_container_width=True)
            st.write(df_vix.tail(1).reset_index())
        with col2:
            st.subheader("Real GDP Percentage Change")
            df_gdp = web.DataReader('A191RL1Q225SBEA', 'fred', start='2007-01-01')
            fig = go.Figure(data=[go.Bar(x=df_gdp.index, y=df_gdp["A191RL1Q225SBEA"])])
            fig.update_layout(xaxis_title="Year", yaxis_title="% Change")
            st.plotly_chart(fig, use_container_width=True)
            df_gdp.rename(columns={'A191RL1Q225SBEA': 'GDP % Change'}, inplace=True)
            st.write(df_gdp.tail(4)[::-1])
        st.image("https://static.streamlit.io/examples/dog.jpg", width=200)

    with tab3:
        st.header("Financial Independent and Retire Early")
        if 'df_transactions' in locals():
            st.write("df_transactions exists in local")
            st.metric(label="Current available cash in GBP", value=df_transactions['PL Amount'].sum())
        st.image("https://static.streamlit.io/examples/owl.jpg", width=200)


# def main():
#     pass

if __name__ == "__main__":
    threeTabs()