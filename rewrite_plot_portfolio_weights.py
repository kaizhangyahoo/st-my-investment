import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_portfolio_weights(df, weights: list, exchange_rate: dict):
    company_list = df['Market']
    # calculate cost in GBP if df['Currency'] is USD, use exchange_rate['GBPUSD=X'], else if EUR use exchange_rate['GBPEUR=X']
    df['Cost in GBP'] = df.apply(
        lambda row: row['Cost/Proceeds'] / exchange_rate['GBPUSD=X'] 
        if row['Currency'] == 'USD' else (row['Cost/Proceeds'] / exchange_rate['GBPEUR=X'] 
        if row['Currency'] == 'EUR' else row['Cost/Proceeds']), axis=1)
    

    fig = make_subplots(rows=1, cols=2, specs=[[{"type": "domain"}, {"type": "domain"}]]) # specs explained in https://plotly.com/python/subplots/
    fig.add_trace(go.Pie(
            labels = company_list,
            values = df['Market Value GBP'],
            pull = weights, 
            name = "Current Position",
        ), 1, 1)
    fig.add_trace(go.Pie(
            labels = company_list,
            values = abs(df['Cost in GBP']),
            pull = weights, 
            name = "Investment",
        ), 1, 2)
    fig.update_layout(
            title_text="Current position and total investment on each instrument",
            width=1000, 
            height=800,
            showlegend=False)
    return fig
# annotations=[dict(text='Current position', x=0.18, y=0.5, font_size=20, showarrow=False),
#              dict(text='£ invested', x=0.82, y=0.5, font_size=20, showarrow=False)])