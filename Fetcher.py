import datetime
import time
import os
import pandas as pd
from utils import get_logger, round_now_to_minute, get_client, column_names, filename, read_data
import config as cfg


class Fetcher:
    """
        Fetches data from CB and saves to disk.
    """
    def __init__(self, product_id='ETH-EUR', granularity=cfg.GRANULARITY):

        self.logger = get_logger("Fetcher")
        self.logger.info(f'Spawning Fetcher.')
        self.product_id = product_id
        self.granularity = granularity
        self.start_year = cfg.START_YEAR

    def fetch_product(self):
        # check if the csv is saved
        # if not, make the first query
        # if yes, load it and check the last timestamp and make a query to get the new data.
        time_now = round_now_to_minute(15)
        # time_now = 1610535600

        filepath = filename(self.product_id)
        exists = os.path.isfile(filepath)
        self.logger.info(f'Data for product {self.product_id} will be stored in {filepath}.')
        self.logger.info(f'Granularity is {self.granularity}.')

        # infer start time.
        start = datetime.datetime(self.start_year, 1, 1, 0, 0, 0)

        if exists:
            self.logger.info('Previously saved file found, will get the last time point stored and use it as start '
                               'time.')
            old_df = read_data(self.product_id)
            last_stop = old_df.index.max()
            start = datetime.datetime.fromtimestamp(last_stop + self.granularity-1, tz=datetime.timezone.utc)
            self.logger.debug(old_df)
            self.logger.info(f'Found {datetime.datetime.fromtimestamp(last_stop, tz=datetime.timezone.utc)} as the '
                               f'latest stored data point, will use {start.isoformat()} as starting point.')
        else:
            self.logger.info("Virgin call.")
        # find the stop time based on granularity. Only 300 data points fit to one request.
        stop = datetime.datetime.fromtimestamp(start.timestamp() + self.granularity * 300, tz=datetime.timezone.utc)

        self.logger.info(f'Getting historical data for with start: {start.isoformat()}\n stop: {stop.isoformat()}.')

        # make the query with the start time
        auth_client = get_client()
        data = auth_client.get_product_historic_rates(product_id=self.product_id,
                                                      start=start.isoformat(),
                                                      end=stop.isoformat(),  # if end not provided than start is
                                                      # ignored.
                                                      granularity=self.granularity)

        # data is contained in a list, errors in a dict.
        if isinstance(data, list):
            if not bool(data):  # if empty
                self.logger.error(f"Data is an empty list")
            else:
                new_df = pd.DataFrame(data)
                new_df = self.preprocess(new_df)
                # store the data as a file.
                self.logger.info(f"Got data with {new_df.shape} rows.")
                self.logger.debug(new_df)
                # merge old new
                self.logger.info(f"Adding new {new_df.shape[0]} rows to local file.")

                new_df.to_csv(filepath, mode='a', header=not exists, index=True)

                # decide if we should continue getting historical date
                self.logger.debug(f"START: {start.timestamp()} - END: {stop.timestamp()} ==> "
                                    f"{start.timestamp() - stop.timestamp()} checks {self.granularity * 300}")
                self.logger.debug(f"LAST_DOWNLOADED_TIME: {new_df['epoch'].max()} - END: {stop.timestamp()} ==> "
                                    f"{new_df['epoch'].max() - stop.timestamp()}")
                self.logger.debug(f"TIME NOW: {int(time_now.timestamp())} - LAST_DOWNLOADED_TIME: {new_df['epoch'].max()} "
                                  f"== > {int(time_now.timestamp()) - new_df['epoch'].max()} seconds to go...")
                if time_now.timestamp() > new_df['epoch'].max():
                    self.logger.debug(f"Fetching more...")
                    self.fetch_product()

        else:
            self.logger.error(f"Could not get historical data, instead got this:\n{data}")

    @staticmethod
    def preprocess(df):
        df.columns = column_names()[:-1]
        df[column_names()[-1]] = df['epoch'].apply(datetime.datetime.fromtimestamp, tz=datetime.timezone.utc)
        df = df.sort_values(by='epoch', ascending=True)
        df.reset_index(drop=True, inplace=True)
        return df

    def run(self):
        while True:
            self.fetch_product()
            # blocking sleeper, need to use thread package later.
            time.sleep(cfg.GRANULARITY)


if __name__ is '__main__':
    f = Fetcher()
    f.run()
