import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from utils import read_csv
from utils import available_coins, get_logger

logger = get_logger(__name__)

app = dash.Dash(__name__)


app.layout = html.Div([
    dcc.Checklist(
        id='toggle-rangeslider',
        options=[{'label': 'Include Rangeslider',
                  'value': 'slider'}],
        value=['slider']
    ),
    dcc.Checklist(
        id='selector',
        options=[{'label': k, 'value': k} for k in available_coins()],
        value=[],
        labelStyle={'display': 'inline-block'}
    ),
    dcc.Graph(id="graph"),
])


@app.callback(Output("graph", "figure"),
              [Input("selector", "value"),
               Input("toggle-rangeslider", "value")])
def display_candlestick(coinname, slider_toggle):

    if coinname:
        logger.info(f'{coinname} selected.')
        df = read_csv('./db/' + coinname[0])
        fig = go.Figure(go.Candlestick(
            x=df['epoch'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close']
        ))
    else:
        fig = go.Figure()

    fig.update_layout(
        xaxis_rangeslider_visible='slider' in slider_toggle
    )

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)