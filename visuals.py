import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from utils import read_data, filename
from utils import list_local_products, get_logger

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
        options=[{'label': k, 'value': k} for k in list_local_products()],
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
        logger.info(f'{coinname[0]} selected.')
        df = read_data(coinname[0])
        logger.info(df.head(10))
        fig = go.Figure(go.Candlestick(
            x=df.index,
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