import datetime
import os
import pandas as pd
from utils import get_logger, round_now_to_minute, get_client, read_csv, column_names, get_filename

logger = get_logger(__name__)


def fetch_product_list():
    """
    Fetches product names excluding those denominated in Dollar or Pound.
    :return:
    """
    logger.debug('Fetching product names.')
    auth_client = get_client()
    df = pd.DataFrame(auth_client.get_products())
    # discard USD and GBP denominated products.
    df = df.loc[~df['quote_currency'].isin(['USD', 'GBP'])]['id']
    df.reset_index(drop=True, inplace=True)
    logger.debug(f'Found {df.shape[0]} products.')
    return df['id'].to_list()


def fetch_product(product_id, granularity=900, start_year=2021):
    # check if the csv is saved
    # if not, make the first query
    # if yes, load it and check the last timestamp and make a query to get the new data.
    logger.info(f'\n\n======================== Calling {__name__} ========================\n\n')
    time_now = round_now_to_minute(15)
    time_now = 1610535600

    filepath = get_filename(product_id)
    exists = os.path.isfile(filepath)
    logger.info(f'Data for product {product_id} will be stored in {filepath}.')
    logger.info(f'Granularity is {granularity}.')

    # infer start time.
    start = datetime.datetime(start_year, 1, 1, 0, 0, 0)

    if exists:
        logger.info('Previously saved file found, will get the last time point stored and use it as start time.')
        old_df = read_csv(filepath)
        last_stop = old_df['epoch'].max()
        start = datetime.datetime.fromtimestamp(last_stop + granularity-1, tz=datetime.timezone.utc)
        logger.debug(old_df)
        logger.info(f'Found {datetime.datetime.fromtimestamp(last_stop, tz=datetime.timezone.utc)} as the latest '
                    f'stored data point, will use {start.isoformat()} as starting point.')
    else:
        logger.info("Virgin call.")
    # find the stop time based on granularity. Only 300 data points fit to one request.
    stop = datetime.datetime.fromtimestamp(start.timestamp() + granularity * 300, tz=datetime.timezone.utc)

    logger.info(f'Getting historical data for with start: {start.isoformat()}\n stop: {stop.isoformat()}.')

    # make the query with the start time
    auth_client = get_client()
    data = auth_client.get_product_historic_rates(product_id=product_id,
                                                  start=start.isoformat(),
                                                  end=stop.isoformat(),  # if end not provided than start is ignored.
                                                  granularity=granularity)

    # data is contained in a list, errors in a dict.
    if isinstance(data, list):
        new_df = pd.DataFrame(data)
        new_df = preprocess(new_df)
        # store the data as a file.
        logger.info(f"Got data with {new_df.shape} rows.")
        logger.debug(new_df)
        # merge old new
        logger.info(f"Adding new {new_df.shape[0]} rows to local file.")

        new_df.to_csv(filepath, mode='a', header=not exists, index=True)

        # decide if we should continue getting historical date
        logger.debug(f"START: {start.timestamp()} - END: {stop.timestamp()} ==> "
                     f"{start.timestamp() - stop.timestamp()} checks {granularity * 300}")
        logger.debug(f"LAST_DOWNLOADED_TIME: {new_df['epoch'].max()} - END: {stop.timestamp()} ==> "
                     f"{new_df['epoch'].max() - stop.timestamp()}")
        logger.debug(f"TIMENOW: {time_now} - LAST_DOWNLOADED_TIME: {new_df['epoch'].max()} == > "
                     f"{time_now - new_df['epoch'].max()} seconds to go...")
        if time_now > new_df['epoch'].max():
            logger.debug(f"Fetching more...")
            fetch_product(product_id, granularity=granularity, start_year=start_year)
    else:
        logger.error(f"Could not get historical data, instead got this:\n{data}")


def preprocess(df):
    df.columns = column_names()[:-1]
    df[column_names()[-1]] = df['epoch'].apply(datetime.datetime.fromtimestamp, tz=datetime.timezone.utc)
    df = df.sort_values(by='epoch', ascending=True)
    df.reset_index(drop=True, inplace=True)
    return df
