import config as cfg
from fetch_data import fetch_product_names, fetch_product_timeserie

# TODO: Get all time courses of the valid products.
# TODO: Get all valid products and store them with keys as their fetch date.
# TODO: Add fetch date as a column.
# TODO: Create a processing pipeline to fetch and process the data.
# TODO: Create a thread that regularly fetches new data every 15 minutes.
# TODO: The fetch data processor triggers the processor pipeline.
# TODO: Create a processor for MA and save these DFs as separate csv files with MA parameter.
# TODO: Make logging also to a file.
# TODO: Show the log file in DASH
# TODO: Trigger the fetch pipeline.
# TODO: Make a consistency check for the stored data.


def fetch():
    [fetch_product_timeserie(product_id=p, granularity=cfg.GRANULARITY) for p in ['ETH-EUR']]

fetch()
# {'fetch'  : get_data,
#  'preprocessors': [flatten, center],
#  'splitter'     : splitter,
#  'model'        : two_hidden_layer,
#  'model_args'   : {'activation':'sigmoid','N_HIDDEN':64}
#  }