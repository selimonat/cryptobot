import dash
from dash import dcc, html
import plotly.express as px
import plotly.graph_objects as go
import utils

bot_name = 'MaBot'


def fig(product_id):
    df = utils.read_timeseries(product_id)
    fig_ = px.line(df, x='datetime', y='close', title=product_id)

    df2 = utils.read_features('MaBot', product_id=product_id)
    df2.index = df2.index.map(utils.parse_epoch)
    [fig_.add_traces(go.Scatter(x=df2.index, y=df2[col], mode='lines', name=col)) for col in df2.columns]
    fig_.update_layout(title_font_size=30)

    # TODO: append feature traces as well.
    # TODO: Append decisions
    return fig_


logger = utils.get_logger(__name__)
app = dash.Dash(__name__)

app.layout = html.Div([dcc.Graph(id=p, figure=fig(p)) for p in utils.list_local_products()[:10]])

if __name__ == "__main__":
    app.run_server(debug=True)
