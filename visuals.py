import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
from utils import read_data, list_local_products, get_logger


def fig(product_id):
    df = read_data(product_id)
    fig = px.line(df, x='datetime', y='close', title=product_id)
    fig.update_layout(title_font_size=30)
    return fig


logger = get_logger(__name__)
app = dash.Dash(__name__)

app.layout = html.Div([dcc.Graph(id=p, figure=fig(p)) for p in list_local_products()])

#
# def display_candlestick(coinname, slider_toggle):
#
#     if coinname:
#         logger.info(f'{coinname[0]} selected.')
#         df = read_data(coinname[0])
#         logger.info(df.head(10))
#         fig = go.Figure(go.Candlestick(
#             x=df.index,
#             open=df['open'],
#             high=df['high'],
#             low=df['low'],
#             close=df['close']
#         ))
#     else:
#         fig = go.Figure()
#
#     fig.update_layout(
#         xaxis_rangeslider_visible='slider' in slider_toggle
#     )
#
#     return fig


if __name__ == "__main__":
    app.run_server(debug=True)