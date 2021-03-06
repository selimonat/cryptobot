import datetime
from Coin import CoinTimeSeries
from utils import round_now_to_minute, list_local_products, filename_history, filename_features, dir_history, \
                  dir_features, get_logger
import time
from numpy.random import choice
import pandas as pd
import os
from threading import Thread
import config as cfg

class Bot(CoinTimeSeries):
    """
    Base class for all bots. Bots are specific to a product id.

    A bot must do the following things:
     (1) should know about how to generate Buy, Sell and Hodl recommendations from the data.
     (2) it must know how to access data. Currently only reads local data updated by Fetchers.
     (3) Stores the historical transactions.

    A bot (in its current implementation) doesn't know:
        (1) How to get data remotely, can only read it from the local ressources.
        (2) How to regularly poll data. It needs to be instantiated for each new recommendation. This can change in
        the future, so as to make bots "live" longer and be more autonomous.
        (3) Doesn't know about the concept of training. It only receives its parameters and that is it. The
        optimality of these parameters must be found out prior..

    """
    outcomes = ["Buy", "Sell", "Hodl"]

    def __init__(self, product: str = 'ETH-EUR', **params):
        """
        A bot is created for a given product.
        """
        super().__init__(product)
        self.logger = get_logger(product + '_' + self.__class__.__name__ )
        self.logger.info(f'Creating bot for {product}.')
        self.created = datetime.datetime.now().isoformat()
        self.params = params
        self._rec_status = None
        self._rec_time = None
        self.bot_name = self.__class__.__name__
        # TODO: all this file i/o business should be heandled with another class actually.
        self._filepath_history = filename_history(self.bot_name, self.product)
        self._filepath_feature = filename_features(self.bot_name, self.product)

        # make the directories if necessary
        for d in [dir_features(self.bot_name), dir_history(self.bot_name)]:
            if not os.path.exists(d):
                self.logger.info(f"Creating directory {d}")
                os.makedirs(d, exist_ok=True)

        self._history = pd.DataFrame(columns=list(self.rec_status.keys()))
        self._history.to_csv(self._filepath_history)
        self.default_value = pd.DataFrame()

    def __repr__(self):
        return f"file path: {self._ts_filepath}\n" \
               f"created: {self.created}\n" \
               f"coin name: {self.coinname}\n" \
               f"denominated in {self.denomination}\n" \
               f"rows: {self.data.shape}\n" \
               f"first data point: {self.first_time_point }\n" \
               f"last data point: {self.last_time_point }\n"

    @property
    def current_time(self):
        return int(round_now_to_minute().timestamp())

    @property
    def history(self):
        self._history = pd.read_csv(self._filepath_history, index_col=0, header=0)
        return self._history

    def update_history(self, value: dict):
        self.logger.info(f"Updating history file for bot {self.__class__.__name__}.")
        self._history = self._history.append(pd.DataFrame.from_dict([value]))
        # TODO: Can be switched to append mode.
        self._history.to_csv(self._filepath_history)

    def feature_fun(self):
        """
        Executed to obtain features. Must be overwritten according to the subclass behavior.
        :return:
        """
        return self.default_value

    @property
    def features(self) -> pd.DataFrame:
        """
        Transforms params to features.
        :return:
        """
        f = self.feature_fun()
        f.to_csv(self._filepath_feature)
        return f

    @property
    def last_feature_value(self):
        """
        Returns the latest available feature values
        :return:
        """
        if isinstance(self.features, pd.DataFrame):
            return self.features.loc[self.features.index.max()].to_frame().T
        else:
            return self.features

    def decision_fun(self):
        """
        Executed to obtain a decision. Must be overwritten according to the subclass behavior.
        :return:
        """
        return choice(self.outcomes)

    def decision(self):  # TODO: Make time argument
        """
        Transforms features to decision.
        :return:
        """
        return self.decision_fun()

    @property
    def rec_status(self):
        """
        Current recommendation status.
        """
        # self.logger.info(f'Recommendation at time {self.last_rec_time} is {self._rec_status}.')
        return {'time': self._rec_time, 'rec': self._rec_status}

    def update_rec(self):

        self._rec_time = self.current_time
        rec = self.decision()
        self._rec_status = rec
        self.logger.debug(f'Last reco for bot {self.__class__.__name__} working on {self.product}:\n'
                            f'{self.rec_status}.')
        self.update_history(self.rec_status)
        self.logger.debug(f'History (last 3 entries) for bot {self.__class__.__name__} working on {self.product}:\n'
                            f'{self.history.tail(3)}.')

    def run(self):
        """
        Starts the life of a bot. A bot generates a reco for every new clock tick.
        """
        while True:
            self.update_rec()
            time.sleep(cfg.GRANULARITY)

    # TODO: Make a fun to retrospectively generate recos.


class MaBot(Bot):
    """
        Moving average bot.
    """
    def __init__(self, product: str = 'ETH-EUR', **params):
        super().__init__(product, **params)
        if 'window_length' not in list(params):
            raise ValueError("ma_Bot needs a param argument with keys 'window_length'.")

    def feature_fun(self):
        c = list()
        for params in self.params['window_length']:
            c.append(
                self.data.rolling(4*24*params).mean().rename(columns={'EUR': params})
            )
        return pd.concat(c, axis=1)

    @property
    def large_window(self):
        """
        Returns the parameters with large window.
        """
        return max(self.params['window_length'])

    @property
    def small_window(self):
        """
        Returns the parameters with small window.
        """
        return min(self.params['window_length'])

    def decision_fun(self):
        last_value_small_window = self.last_feature_value[self.small_window].values
        last_value_large_window = self.last_feature_value[self.large_window].values
        self.logger.info(f"Last value small window: {last_value_small_window}")
        self.logger.info(f"Last value big window: {last_value_large_window}")
        if last_value_large_window > last_value_small_window:
            return "Sell"
        elif last_value_large_window < last_value_small_window:
            return "Buy"
        else:
            return None


if __name__ == '__main__':
    bots = [MaBot(product=p, window_length=[90, 30]) for p in list_local_products()]
    threads = [Thread(target=b.run) for b in bots]
    for thread in threads:
        thread.start()




