import dash
from dash import dcc, html
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import utils

bot_name = 'MaBot'
color = ['red', 'green', 'blue']


def fig():
    products = utils.list_local_products()[:4]
    # collect titles for each subplot
    titles = list()
    for i, p in enumerate(products):
        titles.append(f"({i}) - {p} updated {utils.round_now_to_minute(1)}")

    fig_ = make_subplots(rows=len(products),
                         cols=1,
                         shared_xaxes=True,
                         horizontal_spacing=0.05,
                         subplot_titles=titles)

    for n_row, product_id in enumerate(products):
        df = utils.read_timeseries(product_id)

        fig_.add_trace(go.Scatter(x=df.datetime,
                                  y=df.close,
                                  mode='lines',
                                  name=product_id,
                                  line=dict(color='black', width=1,)
                                  ),
                       row=n_row+1, col=1)

        df2 = utils.read_features('MaBot', product_id=product_id)
        if df2 is not None:
            df2.index = df2.index.map(utils.parse_epoch)
            for n_line, col in enumerate(df2.columns):
                fig_.add_trace(go.Scatter(x=df2.index,
                                          y=df2[col],
                                          mode='lines',
                                          name=col,
                                          line=dict(color=color[n_line], width=2,)),
                               row=n_row+1, col=1)

            fig_.update_layout(title_font_size=45,)

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
                           height=300*len(products),
                           width=800,
                           paper_bgcolor='rgba(0,0,0,0)',
                           plot_bgcolor='rgba(0,0,0,0)',
                           font_size=12,
                           yaxis_title="EUR")
    return html.Div(dcc.Graph(id='test', figure=fig_))


app = dash.Dash(__name__)

app.layout = fig

if __name__ == "__main__":
    app.run_server(debug=False, dev_tools_hot_reload=True)
