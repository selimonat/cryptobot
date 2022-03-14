import dash
from dash import dcc, html
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import utils
import time

color = ['red', 'green', 'blue']

logger = utils.get_logger('visuals')

# TODO: Left Right columns for buy and sell signals with a header.
# TODO: Show only first 10, ranked by signal strength.
# TODO: Add Sell to Buy switches to the graph
# TODO: Regular updates.


def get_data(product_id):
    bot_name = 'MaBot'
    coin = utils.read_timeseries(product_id)
    features = utils.read_features(bot_name, product_id=product_id)
    if features is not None:
        features.index = features.index.map(utils.parse_epoch)
    return coin, features


def subplot_traces(product_id):

    trace_ = list()
    start_time = time.time()
    df, df2 = get_data(product_id)
    logger.debug(f"get_data for {product_id} took: {time.time()-start_time} s")
    start_time = time.time()
    trace_.append(go.Scatter(x=df.datetime,
                             y=df.close,
                             mode='lines',
                             name=product_id,
                             line=dict(color='black', width=1, ),
                             showlegend=False,
                             hoverinfo='none'
                             ))

    for n_line, col in enumerate(df2.columns):
        trace_.append(go.Scatter(x=df2.index,
                                 y=df2[col],
                                 mode='lines',
                                 name=col,
                                 showlegend=False,
                                 hoverinfo='none',
                                 line=dict(color=color[n_line], width=2, )))
    logger.debug(f"trace_generation for {product_id} took: {time.time()-start_time} s")
    return trace_


products = utils.list_local_products()
# collect titles for each subplot
titles = list()
for i, p in enumerate(products):
    titles.append(f"({i}) - {p} updated {utils.round_now_to_minute(1)}")

fig_ = make_subplots(rows=len(products),
                     cols=1,
                     # shared_xaxes=True,
                     # horizontal_spacing=0.05,
                     subplot_titles=titles,
                     print_grid=False)

traces_ = list()
row_ids = list()
for row_id, p in enumerate(products):
    for _ in subplot_traces(p):
        traces_.append(_)
        row_ids.append(row_id+1)

logger.debug("Adding traces...")
start_time = time.time()
fig_.add_traces(traces_, rows=row_ids, cols=[1]*len(row_ids))
logger.debug(f"trace_appending for took: {time.time()-start_time} s")

fig_.update_layout(title_font_size=45, )

fig_.update_xaxes(showline=True,
                  ticks="inside",
                  tickwidth=2,
                  tickcolor='black',
                  ticklen=5,
                  linecolor='black',
                  showgrid=True,
                  gridwidth=1,
                  gridcolor='gray',
                  showticklabels=True)

fig_.update_yaxes(showline=True,
                  ticks="inside",
                  tickwidth=2,
                  tickcolor='black',
                  ticklen=5,
                  col=1,
                  linecolor='black',
                  showgrid=True,
                  gridwidth=1,
                  gridcolor='gray',
                  )

fig_.layout.update(showlegend=False,
                   height=300 * len(products),
                   width=800,
                   paper_bgcolor='rgba(0,0,0,0)',
                   plot_bgcolor='rgba(0,0,0,0)',
                   font_size=12,
                   yaxis_title="EUR")

app = dash.Dash(__name__)

app.layout = html.Div(dcc.Graph(id='test', figure=fig_))

if __name__ == "__main__":
    app.run_server(debug=False, dev_tools_hot_reload=False)
