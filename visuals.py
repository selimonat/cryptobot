import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import utils


def fig(product_id):
    df = utils.read_timeseries(product_id)
    fig = px.line(df, x='datetime', y='close', title=product_id)
    fig.update_layout(title_font_size=30)
    # TODO: append feature traces as well.
    # TODO: Append decisions
    return fig


logger = utils.get_logger(__name__)
app = dash.Dash(__name__)

app.layout = html.Div([dcc.Graph(id=p, figure=fig(p)) for p in utils.list_local_products()])



if __name__ == "__main__":
    app.run_server(debug=True)