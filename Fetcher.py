import datetime
import time
import os
import pandas as pd
from utils import get_logger, round_now_to_minute, get_client, column_names, filename_timeseries, read_timeseries, product_list, \
    parse_epoch
import config as cfg
from threading import Thread


class Fetcher:
    """
        Fetches data from CB and saves to disk.
    """

    def __init__(self, product_id='ETH-EUR', granularity=cfg.GRANULARITY):

        self.logger = logger = get_logger(self.__class__.__name__ + product_id)
        self.logger.info(f'Spawning a {product_id} Fetcher.')
        self.product_id = product_id
        self.granularity = granularity
        self.start_year = cfg.START_YEAR
        self.auth_client = get_client()

    @property
    def columns(self):
        return column_names()

    def fetch_product(self):
        # check if the csv is saved
        # if not, make the first query
        # if yes, load it and check the last timestamp and make a query to get the new data.
        self.logger.info(f"========================Starting Cycle for {self.product_id}========================")
        time_now = round_now_to_minute(15)
        # time_now = 1610535600

        filepath = filename_timeseries(self.product_id)
        exists = os.path.isfile(filepath)
        self.logger.info(f'{self.product_id}: Data will be stored in {filepath}.')
        self.logger.info(f'{self.product_id}: Granularity is {self.granularity}.')

        # infer start time.
        start = datetime.datetime(self.start_year, 1, 1, 0, 0, 0)

        if exists:
            self.logger.info('Saved file found, will get the last time point stored and use it as start time.')
            old_df = read_timeseries(self.product_id)
            # TODO: Take the index of the last non-None entry
            last_stop = old_df.index.max()
            # Overwrite start point based on database.
            start = parse_epoch(last_stop + self.granularity - 1)  # wouldn't just +1 the same?
            self.logger.info(f'{self.product_id}: Found {parse_epoch(last_stop)} as the '
                             f'latest stored data point, will use {start.isoformat()} as starting point.')
        else:
            self.logger.info(f"{self.product_id}: Virgin call.")
        # find the stop time based on granularity. Only 300 data points fit to one request.
        stop = parse_epoch(start.timestamp() + self.granularity * 300)

        self.logger.info(f'{self.product_id}: Getting historical data for with start: {start.isoformat()} stop:'
                         f' {stop.isoformat()}.')

        # make the query with the start time
        data = self.auth_client.get_product_historic_rates(product_id=self.product_id,
                                                           start=start.isoformat(),
                                                           end=stop.isoformat(),  # if end not provided than start is
                                                           # ignored.
                                                           granularity=self.granularity)

        # data is contained in a list, errors in a dict.
        if isinstance(data, list):

            if not bool(data):  # if empty
                # there are two reasons why data is returned empty.
                # 1: product was not yet rolled out
                # 2: time window is from future or is not yet ready.
                #
                # In case of 1, we need to hack it a bit so that we can still insert it in the
                # csv file. Because the epoch data in csv file will be used for the next call and the next call
                # should use the next time point.
                self.logger.info(f"{self.product_id}: Data is an empty list, will use a list of Nones instead.")
                data = [int(stop.timestamp()), *[None] * (len(self.columns) - 2)]  # one column less.
                data = [data]
                # In case of 2, we should not write this empty row to disk if there were already records on the
                # local db. Because empty data means also that we are asking data from future time points. In this
                # case we should just quit the loop
                if exists:
                    if not old_df.isna().iloc[-1, 2]:
                        self.logger.info(f"{self.product_id}: As the local file exists already we will not write this "
                                         f"list of Nones to DB.")
                        return

            new_df = pd.DataFrame(data, columns=self.columns[:-1])
            # new_df.columns = column_names()[:-1]
            new_df[self.columns[-1]] = new_df['epoch'].apply(datetime.datetime.fromtimestamp, tz=datetime.timezone.utc)
            new_df = new_df.sort_values(by='epoch', ascending=True)
            new_df.reset_index(drop=True, inplace=True)

            # merge old new
            self.logger.info(f"{self.product_id}: Adding new {new_df.shape[0]} rows to DB.")
            self.logger.debug(f'{self.product_id}: New data starting point {new_df.iloc[0,-1]}')
            self.logger.debug(f'{self.product_id}: New data stopping point {new_df.iloc[-1,-1]}')

            new_df.to_csv(filepath, mode='a', header=not exists, index=True)

            # decide if we should continue getting historical date
            self.logger.debug(f"{self.product_id}: START: {start.timestamp()} - END: {stop.timestamp()} ==> "
                              f"{start.timestamp() - stop.timestamp()} checks {self.granularity * 300}")
            self.logger.debug(f"{self.product_id}: LAST_DOWNLOADED_TIME: {new_df['epoch'].max()} - END:"
                              f" {stop.timestamp()} ==> "
                              f"{new_df['epoch'].max() - stop.timestamp()}")
            self.logger.debug(f"{self.product_id}: TIME NOW: {int(time_now.timestamp())} - LAST_DOWNLOADED_TIME:"
                              f" {new_df['epoch'].max()} "
                              f"== > {int(time_now.timestamp()) - new_df['epoch'].max()} seconds to go...")
            if time_now.timestamp() > new_df['epoch'].max():
                self.logger.debug(f"Fetching more...")
                self.fetch_product()

        else:
            self.logger.error(f"Could not get historical data, instead got this:\n{data}")

    def run(self):
        while True:
            self.fetch_product()
            # blocking sleeper, need to use thread package later.
            time.sleep(cfg.GRANULARITY)


class FetcherArmy:
    """ Multi-thread orchestration of individual Fetchers."""

    def __init__(self, ensemble: list):
        self.logger = get_logger("FetcherArmy...")
        self.logger.info(f'Spawning a FetcherArmy with {len(ensemble)} fetchers.')
        self.army = list()
        for c in ensemble:
            self.army.append(Fetcher(c))

    def run(self):

        threads = [Thread(target=soldier.run) for soldier in self.army]
        # start the threads
        for thread in threads:
            thread.start()


if __name__ is '__main__':
    products = product_list()[:10]
    army = FetcherArmy(products)
    army.run()
    # soldier = Fetcher(product_id="GALA-EUR")
    # soldier.run()
