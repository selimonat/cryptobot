import dash
from dash import dcc, html
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import utils
import time

color = ['red', 'green', 'blue']

logger = utils.get_logger('visuals')


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
                             line=dict(color='black', width=1, )
                             ))

    for n_line, col in enumerate(df2.columns):
        trace_.append(go.Scatter(x=df2.index,
                                 y=df2[col],
                                 mode='lines',
                                 name=col,
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

for n_row, p in enumerate(products):
    for trace in subplot_traces(p):
        fig_.add_trace(trace, row=n_row+1, col=1)

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
    app.run_server(debug=True, dev_tools_hot_reload=True)
