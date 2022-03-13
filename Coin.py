import config as cfg
from utils import get_logger, read_timeseries
import os
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


class Coin:
    """
    Representation of a coin described by the coinbase pro product name.
    """
    def __init__(self, product: str = 'ETH-EUR'):
        self.product = product
        self.coinname, self.denomination = product.split('-')


class CoinTimeSeries(Coin):
    """
    Holds time series (hence ts). Reads data from local disk, does not fetch from the server.
    """

    def __init__(self, product="ETH-EUR"):
        super().__init__(product)
        self._ts_filename = self.product + '.csv'
        self._ts_filepath = os.path.join(cfg.PATH_DB_TIMESERIES, self._ts_filename)
        self._raw_data = read_timeseries(product)

    def update(self):
        self._raw_data = read_timeseries(self.product)
        self._raw_data[self.denomination] = self._raw_data['close']

    @property
    def data(self):
        """DataFrame representing the fetched data stored locally.
        """
        self.update()
        return self._raw_data[self.denomination].to_frame()

    @property
    def time(self):
        """Series representing time samples in epoch seconds.
        """
        self.update()
        return pd.Series(self.data.index)

    @property
    def value(self):
        """ Value of the coin.
        """
        return self.data[self.denomination]

    @property
    def last_time_point(self):
        return self.time.iloc[-1]

    @property
    def first_time_point(self):
        return self.time.iloc[0]


if __name__ is "__main__":
    c = CoinTimeSeries()
    c.time
    c.value
    c.data
