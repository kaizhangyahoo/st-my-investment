import miniEnc as enc
import pandas as pd
import pandas_datareader.data as web
import plotly.graph_objects as go
import plotly.express as px
import datetime as dt
from getEODprice import chunks
from market_data_api import OHLC_YahooFinance


def get_vix_from_yahoo(start_date):
    # df_vix = web.DataReader('^VIX', 'yahoo', start=start_date)
    df_vix = OHLC_YahooFinance('^VIX', start_date).yahooDataV7()
    fig = go.Figure(data=[go.Candlestick(x=df_vix.index,
            open=df_vix['Open'],
            high=df_vix['High'],
            low=df_vix['Low'],
            close=df_vix['Adj Close'])])
    fig.update_layout(yaxis_title='VIX', xaxis_title='Date')
    # df_vix.index = df_vix.index.strftime('%Y-%m-%d')
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

def buffet_indicator_calc_from_fred(start_date: str):
    indicator_range = [0,0.5,0.75,0.9,1.15,10]
    indicator_description = ['Very Undervalued', 'Undervalued','Fair Value','Overvalued','Extremely Overvalued']
    df_gdp = web.DataReader("GDP", "fred", start=start_date)
    df_wilshire = web.DataReader('WILL5000PR','fred', start=start_date)
    df_wb = df_wilshire.join(df_gdp, how='left')
    df_wb['GDP'] = df_wb['GDP'].ffill()
    df_wb.dropna(subset = ['WILL5000PR'], inplace=True)
    df_wb['Market Value / GDP'] = df_wb['WILL5000PR'] / df_wb['GDP']
    df_wb['Indicator-Category'] = pd.cut(df_wb['Market Value / GDP'], indicator_range, labels=indicator_description)
    fig = px.scatter(df_wb, x=df_wb.index, y="Market Value / GDP", color="Indicator-Category", title="Buffet Indicator")
    return fig


def treasury_curve(start_date):
    treasury_codes_mapping = {'DGS1MO': '1 MO', 'DGS3MO': '3MO', 'DGS6MO': '6 MO', 'DGS1': '1 YR', 'DGS2': '2 YR', 'DGS3': '3 YR', 'DGS5': '5 YR', 'DGS7': '7 YR', 'DGS10': '10 YR', 'DGS20': '20 YR', 'DGS30': '30 YR'}
    treasury_yield = pd.DataFrame()

    if start_date < dt.datetime.today().strftime('%Y-%m-%d'):        
        for code, maturity in treasury_codes_mapping.items():
            data = web.DataReader(code, 'fred', start_date)
            treasury_yield[maturity] = data[code]

        fig = go.Figure(go.Scatter(x=treasury_yield.columns, y=treasury_yield.loc[start_date]))
        fig.add_vrect(x0="1 MO", x1="1 YR", fillcolor="LightSalmon", opacity=0.5, line_width=0, annotation_text = "Bill", annotation_position="top left")
        fig.add_vrect(x0="2 YR", x1="5 YR", fillcolor="LightGreen", opacity=0.5, line_width=0, annotation_text = "Note", annotation_position="top left")
        fig.add_vrect(x0="7 YR", x1="30 YR", fillcolor="LightBlue", opacity=0.5, line_width=0, annotation_text = "Bond", annotation_position="top left")
        return fig       
    else:
        df_treasuries_yield = treasury_yield       
        if start_date == dt.datetime.today().strftime('%Y-%m-%d'): 
            df_long=pd.melt(df_treasuries_yield, id_vars=['Date'], value_vars=['1 MO', '3 MO', '6 MO', '1 YR', '2 YR', '3 YR', '5 YR', '7 YR', '10 YR', '20 YR', '30 YR'])
            plot = px.line(df_long, x="variable", y="value", range_y=[df_long["value"].min(), df_long["value"].max()], animation_frame="Date", title="Treasury Yields")
        else:
            df_treasuries_yield = df_treasuries_yield.set_index('Date')
            plot = px.line(df_treasuries_yield, x=df_treasuries_yield.index, y=df_treasuries_yield.columns, title='Treasury rates full history')
        return plot

def gold_silver_price(highlight_recession=False):
    ndqk = b'ud--wr-4nbzKnr-5tIzCmZjBo6o'
    nasdaq = enc.decode(enc.cccccccz, ndqk)
    df_gold = pd.read_csv(f"https://data.nasdaq.com/api/v3/datasets/LBMA/GOLD.csv?api_key={nasdaq}")
    df_silver = pd.read_csv(f"https://data.nasdaq.com/api/v3/datasets/LBMA/SILVER.csv?api_key={nasdaq}")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_gold['Date'], y=df_gold['USD (PM)'], name="Gold"))
    fig.add_trace(go.Scatter(x=df_silver['Date'], y=df_silver['USD'], name="Silver", yaxis="y2"))
    y2 = go.layout.YAxis(side='right', overlaying='y', title='Silver')
    fig.update_layout(yaxis2=y2, title='Gold and Silver prices')
    if highlight_recession:
        fig.add_vrect(x0="2020-02-11", x1="2020-05-31", fillcolor="LightSalmon", opacity=0.5, line_width=0)
        fig.add_vrect(x0="2007-12-01", x1="2009-06-01", fillcolor="LightSalmon", opacity=0.5, line_width=0)
        fig.add_vrect(x0="2001-03-01", x1="2001-11-01", fillcolor="LightSalmon", opacity=0.5, line_width=0)
        fig.add_vrect(x0="1990-07-01", x1="1991-03-01", fillcolor="LightSalmon", opacity=0.5, line_width=0)
        fig.add_vrect(x0="1981-07-01", x1="1982-11-01", fillcolor="LightSalmon", opacity=0.5, line_width=0)
        fig.add_vrect(x0="1973-11-01", x1="1975-03-01", fillcolor="LightSalmon", opacity=0.5, line_width=0)
        fig.add_vrect(x0="1969-12-01", x1="1970-11-01", fillcolor="LightSalmon", opacity=0.5, line_width=0)
    return fig


def sp500_winner_loser_treemap():
    """ Treemap continous color scale: https://plotly.com/python/builtin-colorscales/#continuous-color-scales-in-dash
    discrete color scale: https://plotly.com/python/discrete-color/ """
    df = pd.read_csv('sp500_changes.csv')
    df_result_positives = df[df['Day Pctage Change'] > 0]
    df_result_negatives = df[df['Day Pctage Change'] < 0]
    winner_fig = px.treemap(
        df_result_positives, 
        path=['GICS Sector' , 'GICS Sub-Industry', 'Security'], 
        values='Day Pctage Change', 
        color='Day Pctage Change', 
        hover_data=['Last Price', 'Day Pctage Change', 'Symbol'], 
        color_continuous_scale='greens',)
        #color_discrete_map={'Day Pctage Change': px.colors.sequential.Greens})
    df_result_negatives['Day Pctage Change'] = df_result_negatives['Day Pctage Change'] * -1
    loser_fig = px.treemap(
        df_result_negatives, 
        path=['GICS Sector' , 'GICS Sub-Industry', 'Security'], 
        values='Day Pctage Change', 
        color='Day Pctage Change',
        hover_data=['Last Price', 'Day Pctage Change', 'Symbol'], 
        #color_discrete_sequence=px.colors.sequential.RdYlBu)
        color_continuous_scale='burg')
        #color_discrete_map={'Day Pctage Change': px.colors.sequential.speed})
    return winner_fig, loser_fig

def sector_etf_map(df: pd.DataFrame):
    last_column = df.columns[-1]
    #df['display_no'] = df[last_column].apply(lambda x: "+" + str(x) if x > 0 else str(x))
    df['display_no'] = df[last_column].apply(lambda x: "+" + str(round(x, 2)) if x > 0 else str(round(x, 2)))
    df['display'] = df['Sector'] + " (" + df['display_no'] + "%)"
    df['hovertext'] = df['ETF'] + "  " + df['Last Price'].astype(str)
    df.sort_values(by=last_column, inplace=True, ascending=False)
    tiles = list(chunks(df['display'], 3))
    tile_index = list(chunks(df[last_column], 3))
    hovertexts = list(chunks(df['hovertext'], 3))

    # fig = px.imshow(tile_index, labels=dict(x="Sector", color="PCT Change"), color_continuous_scale=px.colors.sequential.speed, aspect='auto')
    # fig.update_layout(title_text=last_column)
    # fig.update_traces(text=tiles, texttemplate='%{text}')
    
    fig = go.Figure(data=go.Heatmap(z=tile_index[::-1], colorscale=px.colors.sequential.speed, texttemplate="%{text}",
                                    text=tiles[::-1], textfont={'size': 12}, hovertemplate='%{hovertext}', hovertext=hovertexts[::-1]))
    return fig

def sp500_win_lose_tree(df: pd.DataFrame):
    fig = px.treemap(df, path = ['GICS Sector', 'GICS Sub-Industry', 'Security'], values = df.columns[-1], color = df.columns[-1],
                    hover_data = ['Last Price', df.columns[-1], 'Symbol'], color_discrete_map={df.columns[-1]: px.colors.sequential.RdBu})
    return fig




def main():
    start_date = '2022-11-01'
    print(treasury_curve(start_date))
    
if __name__ == '__main__':
    main()


