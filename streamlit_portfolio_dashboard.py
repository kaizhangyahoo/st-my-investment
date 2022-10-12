import streamlit as st
import pandas as pd
import ticker_resolution as tr
import getEODprice as g12
import plotly.graph_objects as go

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

                    company_list = df_op.index.get_level_values('Market').tolist()
                    standout = [0]*len(company_list)
                    standout[company_list.index(market)] = 0.5
                    print(standout)
                    fig = go.Figure(data =[go.Pie(
                        labels = df_op.index.get_level_values('Market'),
                        values = df_op['current position'],
                        pull = standout
                    )])
                    st.plotly_chart(fig)



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
        st.header("Financial Independence and Retire Early")
        # isa_annual_contrib = 20000
        # current_ttl = 86700
        # if df_transactions exists
        if 'df_transactions' in locals():
            st.write("df_transactions exists in local")
            st.metric(label="Current available cash in GBP", value=df_transactions['PL Amount'].sum())

        st.image("https://static.streamlit.io/examples/dog.jpg", width=200)

    with tab3:
        st.header("An owl")
        st.image("https://static.streamlit.io/examples/owl.jpg", width=200)


# def main():
#     pass

if __name__ == "__main__":
    threeTabs()