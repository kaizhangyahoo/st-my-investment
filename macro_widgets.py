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

def treasury_curve(start_date):
    ndqk = b'ud--wr-4nbzKnr-5tIzCmZjBo6o'
    nasdaq = enc.decode(enc.cccccccz, ndqk)

    if start_date < dt.datetime.today().strftime('%Y-%m-%d'):        
        df_treasuries_yield = pd.read_csv(f"https://data.nasdaq.com/api/v3/datasets/USTREASURY/YIELD.csv?api_key={nasdaq}&start_date={start_date}")
        df_treasuries_yield = df_treasuries_yield.set_index('Date')
        df_treasuries_yield.index = pd.to_datetime(df_treasuries_yield.index)
        fig = go.Figure(go.Scatter(x=df_treasuries_yield.columns, y=df_treasuries_yield.loc[start_date]))
        fig.add_vrect(x0="1 MO", x1="1 YR", fillcolor="LightSalmon", opacity=0.5, line_width=0, annotation_text = "Bill", annotation_position="top left")
        fig.add_vrect(x0="2 YR", x1="5 YR", fillcolor="LightGreen", opacity=0.5, line_width=0, annotation_text = "Note", annotation_position="top left")
        fig.add_vrect(x0="7 YR", x1="30 YR", fillcolor="LightBlue", opacity=0.5, line_width=0, annotation_text = "Bond", annotation_position="top left")
        return fig
    else:
        df_treasuries_yield = pd.read_csv(f"https://data.nasdaq.com/api/v3/datasets/USTREASURY/YIELD.csv?api_key={nasdaq}")
        df_treasuries_yield = df_treasuries_yield.set_index('Date')
        plot = px.line(df_treasuries_yield, x=df_treasuries_yield.index, y=df_treasuries_yield.columns, title='Treasury rates full history')
        return plot


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


