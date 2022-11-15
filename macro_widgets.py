import miniEnc as enc
import pandas as pd
import pandas_datareader.data as web
import plotly.graph_objects as go

def get_vix_from_yahoo(start_date):
    df_vix = web.DataReader('^VIX', 'yahoo', start=start_date)
    fig = go.Figure(data=[go.Candlestick(x=df_vix.index,
            open=df_vix['Open'],
            high=df_vix['High'],
            low=df_vix['Low'],
            close=df_vix['Close'])])
    fig.update_layout(yaxis_title='VIX', xaxis_title='Date')
    df_vix.index = df_vix.index.strftime('%Y-%m-%d')
    return fig, df_vix.tail(1)

def real_gdp_pct_change(start_date):
    df_gdp = web.DataReader('A191RL1Q225SBEA', 'fred', start=start_date)
    fig = go.Figure(data=[go.Bar(x=df_gdp.index, y=df_gdp["A191RL1Q225SBEA"])])
    fig.update_layout(xaxis_title="Year", yaxis_title="% Change")
    df_gdp.rename(columns={'A191RL1Q225SBEA': 'GDP % Change'}, inplace=True)
    df_gdp.index = df_gdp.index.strftime('%Y-%m-%d')
    return fig, df_gdp.tail(4)[::-1]

def pce_from_fred(start_date):
    df_pce = web.DataReader('PCE', 'fred', start=start_date)
    fig = go.Figure(data=[go.Scatter(x=df_pce.index, y=df_pce["PCE"])])
    fig.update_layout(xaxis_title="Year", yaxis_title="PCE (USD Billion)")
    df_pce.index = df_pce.index.strftime('%Y-%m-%d')
    return fig, df_pce.tail(3)

def cpi_from_fred(start_date):
    df_cpi = web.DataReader('CPIAUCSL', 'fred', start=start_date)
    fig = go.Figure([go.Scatter(x=df_cpi.index, y=df_cpi['CPIAUCSL'])])
    fig.update_layout(xaxis_title="Year", yaxis_title="Index 1982-1984=100")
    df_cpi.index = df_cpi.index.strftime('%Y-%m-%d')
    return fig, df_cpi.tail(3)

def cpi_pce_pct_change_from_fred(start_date):
    cpi = web.DataReader('CORESTICKM159SFRBATL', 'fred', start=start_date)
    cpi.rename(columns={"CORESTICKM159SFRBATL": "CPI less food energy"}, inplace=True)
    pce_start = pd.to_datetime(start_date) - pd.DateOffset(years=1)
    pce = web.DataReader('PCEPI', 'fred', start=pce_start)
    pce['pct change'] = pce.pct_change(periods=12)*100
    pce.dropna(inplace=True)
    cpi_pce = pd.concat([cpi, pce], axis=1)
    fig = go.Figure(data=[go.Scatter(x=cpi_pce.index, y=cpi_pce["CPI less food energy"], name='CPI less food energy % yoy'),
                            go.Scatter(x=cpi_pce.index, y=cpi_pce["pct change"], name='PCE % change')])
    fig.update_layout(xaxis_title="Date", yaxis_title="% Change")
    return fig, cpi_pce.tail(3)

def unemployment_rate_from_fred(start_date):
    df_unemployment = web.DataReader('UNRATE', 'fred', start=start_date)
    fig = go.Figure(data=[go.Scatter(x=df_unemployment.index, y=df_unemployment["UNRATE"])])
    fig.update_layout(xaxis_title="Year", yaxis_title="Unemployment Rate")
    return fig, df_unemployment.tail(3)

def consumer_confidence_from_fred(start_date):
    df_consumer_confidence = web.DataReader('UMCSENT', 'fred', start=start_date)
    fig = go.Figure(data=[go.Scatter(x=df_consumer_confidence.index, y=df_consumer_confidence["UMCSENT"])])
    fig.update_layout(xaxis_title="Year", yaxis_title="Consumer Confidence")
    return fig, df_consumer_confidence.tail(3)

def treasury_curve(start_date):
    ndqk = b'ud--wr-4nbzKnr-5tIzCmZjBo6o'
    nasdaq = enc.decode(enc.cccccccz, ndqk)
    df_treasuries_yield = pd.read_csv(f"https://data.nasdaq.com/api/v3/datasets/USTREASURY/YIELD.csv?api_key={nasdaq}&start_date={start_date}")
    df_treasuries_yield = df_treasuries_yield.set_index('Date')
    df_treasuries_yield.index = pd.to_datetime(df_treasuries_yield.index)
    fig = go.Figure(go.Scatter(x=df_treasuries_yield.columns, y=df_treasuries_yield.loc[start_date]))
    fig.add_vrect(x0="1 MO", x1="1 YR", fillcolor="LightSalmon", opacity=0.5, line_width=0, annotation_text = "Bill", annotation_position="top left")
    fig.add_vrect(x0="2 YR", x1="5 YR", fillcolor="LightGreen", opacity=0.5, line_width=0, annotation_text = "Note", annotation_position="top left")
    fig.add_vrect(x0="7 YR", x1="30 YR", fillcolor="LightBlue", opacity=0.5, line_width=0, annotation_text = "Bond", annotation_position="top left")
    return fig

def main():
    start_date = '2022-11-01'
    print(treasury_curve(start_date))
    
if __name__ == '__main__':
    main()


