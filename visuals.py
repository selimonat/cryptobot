import dash
from dash import dcc, html
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import utils
import time
from collections import defaultdict
from base64 import b64encode
import config as cfg

color = ['red', 'green', 'blue']

logger = utils.get_logger('visuals')


# TODO: Show only first 10, ranked by signal strength.
# TODO: Add Sell to Buy switches to the graph
# TODO: Regular updates.


def get_data(product):
    """
    Gets all data of a given product.
    :param product:
    :return: 3 df for coin, feature timeseries and rec history.
    """
    bot_name = 'MaBot'
    coin = utils.read_timeseries(product)
    features = utils.read_features(bot_name, product_id=product)
    if features is not None:
        features.index = features.index.map(utils.parse_epoch)
    history = utils.read_history(bot_name, product_id=product)
    if history is not None:
        history.index = history.index.map(utils.parse_epoch)
    return coin, features, history


def subplot_traces(product):
    trace_ = list()
    start_time = time.time()
    df, df2, df3 = get_data(product)
    logger.debug(f"get_data for {product} took: {time.time() - start_time} s")
    if df3.empty:
        reco = None
    else:
        reco = df3.loc[df3.index == df3.index.max()].values[0][0]  # sell or buy or whatever

    start_time = time.time()
    trace_.append(go.Scatter(x=df.datetime,
                             y=df.close,
                             mode='lines',
                             name=product,
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
    logger.debug(f"trace_generation for {product} took: {time.time() - start_time} s")
    return {reco: trace_}


def get_subplot(sp_traces):
    """
    Builds a subplot object. Infers number of subplots based on sp_traces.
    This is basically a wrapper over make_subplots.
    :param sp_traces: All traces that are plotted in a subplot.
    :return: Figure object, the output a wrapper make_subplot
    """
    # collect titles for each subplot
    titles = list()
    for i, p in enumerate(sp_traces.keys()):
        titles.append(f"({i}) - {p} updated {utils.round_now_to_minute(1)}")
    t_rows = len(titles)

    panel = make_subplots(rows=t_rows,
                          cols=1,
                          subplot_titles=titles,
                          print_grid=False)
    axes_params = {'showline': True,
                   'ticks': "inside",
                   'tickwidth': 2,
                   'tickcolor': 'black',
                   'ticklen': 5,
                   'linecolor': 'black',
                   'showgrid': True,
                   'gridwidth': 1,
                   'gridcolor': 'gray'}
    layout_params = {'showlegend': False,
                     'height': 300 * t_rows,
                     'width': 600,
                     'font_family': "Courier New",
                     'paper_bgcolor': 'rgba(0,0,0,0)',
                     'plot_bgcolor': 'rgba(0,0,0,0)',
                     'font_size': 12,
                     'title_font_size': 45}
    panel.update_xaxes(**axes_params, showticklabels=True)
    panel.update_yaxes(**axes_params)
    panel.layout.update(layout_params)
    return panel


def tree(): return defaultdict(tree)


products = utils.list_local_products()

# First get the sp_traces
all_traces = tree()
for row_id, p in enumerate(products):
    for rec, trace in subplot_traces(p).items():
        all_traces[str(rec)][p] = trace  # example: panel_trances['Sell']['BTC-EUR'] = trace str conversion ensures
        # that nans are converted to 'nan'. This is necessary as nan's cannot be used as keys.

# Here one can add selection logic based on importance of coins.
pass

# Add the sp_traces to figure
logger.debug("Adding sp_traces...")
panels = dict()
start_time = time.time()
for rec, subplot_traces in all_traces.items():
    # generate a panel to contain sp_traces.
    panels[rec] = get_subplot(subplot_traces)
    for row_id, (product_id, trace) in enumerate(subplot_traces.items()):
        n_trace = len(trace)
        panels[rec].add_traces(trace, rows=[row_id + 1] * n_trace, cols=[1] * n_trace)
logger.debug(f"trace_appending for took: {time.time() - start_time} s")

app = dash.Dash(__name__)
h1_style = {'text-align': 'center', 'fontSize': 36, 'fontFamily': "Courier New"}
div_style = {'float': 'left', 'margin': 'auto', 'width': '33%'}
im_style = {'float': 'left', 'margin': 'auto', 'width': '600'}

if cfg.RENDER_OPTION == "image":
    # image rendering
    def to_image(fig):
        img_bytes = fig.to_image(format="png")
        encoding = b64encode(img_bytes).decode()
        img_b64 = "data:image/png;base64," + encoding
        return html.Img(src=img_b64, style=im_style)
    start_time = time.time()
    app.layout = html.Div([
        html.Div([html.H1(str(k), style=h1_style), to_image(panels[k])], style=div_style) for k in panels.keys()])
    logger.debug(f"Final layout generation took: {time.time() - start_time} s")
else:
    # vector rendering
    start_time = time.time()
    app.layout = html.Div([
        html.Div([html.H1(str(k), style=h1_style),
                  html.Div(dcc.Graph(id=k, figure=panels[k]))], style=div_style) for k in panels.keys()])
    logger.debug(f"Final layout generation took: {time.time() - start_time} s")
if __name__ == "__main__":
    app.run_server(debug=False, dev_tools_hot_reload=False)
