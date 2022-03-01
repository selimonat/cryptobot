import pandas as pd
from utils import get_logger
import datetime
from Coin import CoinTimeSeries
from numpy.random import choice


class Bot(CoinTimeSeries):
    """
    Base class for all bots.

    A bot must do the following things:
     (1) should know about how to generate Buy, Sell and Hodl recommendations from the data.
     (2) it must know how to access data. Currently only reads local data updated by Fetchers.
     (3) Stores the historical transactions.

    A bot (in its current implementation) doesn't know:
        (1) How to get new data, can only read it from the local ressources.
        (2) How to regularly poll data. It needs to be instantiated for each new recommendation. This can change in
        the future, so as to make bots "live" longer and be more autonomous.
        (3) Doesn't know about the concept of training. It only receives its parameters and that is it. The
        optimality of these parameters must be found out prior..




    """
    outcomes = ["Buy", "Sell", "Hodl"]

    def __init__(self, product: str = 'ETH-EUR', **kwargs):
        """
        For each index generates a Buy, Sell or Hold outcome.

        :param df: Series with an index of type pd.DatetimeIndex
        :param kwargs:
        """
        super().__init__(product)
        self.logger = get_logger(__name__)
        self.created = datetime.datetime.now().isoformat()
        self.params = kwargs
        self.features = pd.DataFrame(index=self.data.index)
        self.recommendation = pd.Series(index=self.data.index, dtype='category')
        self.transactions = list()


    def __repr__(self):
        return f"filepath: {self._ts_filepath}\ncreated: {self.created}\ncoinname: {self.coinname}\ndenominated in {self.denomination}\nrows:{self.data.shape}"

    def get_recommendation(self):
        """Generate decision from features for each timestamp. Updates self.decision.
        """
        pass


    def performance(self):
        """Evaluates the bot for the full range of available data. It assumes an initial investment of 1 $."""
        # TODO: This requires we go serially through all recommendations. For BUY recommendation we buy the coin from
        #  its price at that time point, for SELL recommendation we sell it, and for HODL we keep it whatever it is.

        # Is the bot estimated?
        for i in self.data.index:



class RandomBot(Bot):

    def __init__(self, product: str = 'ETH-EUR', **kwargs):
        super().__init__(product, **kwargs)

    def get_recommendation(self):
        self.recommendation = self.data.to_frame().apply(lambda x: choice(self.outcomes))


if __name__ == '__main__':
    bot = Bot()
    botr = RandomBot()


