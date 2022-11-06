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
    return fig, df_vix.tail(1)



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


