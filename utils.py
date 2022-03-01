import logging
import yaml
import cbpro
import pandas as pd
import os
import config as cfg
from pathlib import Path


def get_logger(name):
    # create logger
    logger_ = logging.getLogger(name)
    logger_.setLevel(logging.DEBUG)
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger_.addHandler(ch)
    return logger_


logger = get_logger(__name__)


def list_local_products():
    """
    Returns locally available product names.
    :return:
    """
    all_files = list(os.walk(cfg.PATH_DB_TIMESERIES, topdown=False))[0][-1]
    return [Path(f).stem for f in all_files]


def product_list():
    """
    Fetches cb product names excluding those denominated in Dollar or Pound.
    Wraps auth_client's get_products methods.
    :return:
    """
    logger.debug('Fetching product names.')
    auth_client = get_client()
    df = pd.DataFrame(auth_client.get_products())
    # discard USD and GBP denominated products.
    df = df.loc[~df['quote_currency'].isin(['USD', 'GBP'])]
    df.reset_index(drop=True, inplace=True)
    logger.debug(f'Found {df.shape[0]} products.')
    return df['id'].to_list()


def filename(product_id):
    return os.path.join(cfg.PATH_DB_TIMESERIES, product_id) + '.csv'


def column_names():
    """
    Columns names of the returned data.
    :return:
    """
    return ["epoch", "low", "high", "open", "close", "volume", "datetime"]


def round_now_to_minute(g=15):
    """
    Floors datetime object at a given granularity level defined in minutes.
    :param g: granularity level
    :return:
    """

    from datetime import datetime
    from math import floor
    from time import time

    t = datetime.fromtimestamp(time())
    return datetime.fromtimestamp(floor(t.timestamp() / (60*g)) * (60*g))


def get_client(cred_file='./cred.yaml'):
    """
        Returns an authenticated cbpro client.

        Credentials file must contain the following lines.
        api_key: XXX
        api_secret: XXX
        passphrase: XXX

    :return: authenticated client.
    """
    try:
        logger.debug('Getting an authenticated client.')
        with open(cred_file, 'r') as f:
            cred = yaml.safe_load(f)
        key, b64secret, passphrase = cred['api_key'], cred['api_secret'], cred['passphrase'],
        auth_client = cbpro.AuthenticatedClient(key, b64secret, passphrase)
        return auth_client
    except FileNotFoundError:
        logger.exception('The cred you passed does not exist. Make sure you have a cred file.')
    except KeyError:
        logger.exception('One of the required keys in the cred file is missing.')


def read_data(product_id):
    """
    Simple read_csv wrapper returning a df with correct column names and index.
    """
    df = pd.read_csv(product_id, index_col=0, header=0)
    df.set_index('epoch', inplace=True)
    return df

class MetaBase(type):
    # Metaclass to attach a logger object with the subclass name. Otherwise self.logger() will always call the logger
    # object of the highest parent.
    def __init__(cls, *args):
        super().__init__(*args)
        cls.__logger = None
        # Explicit name mangling
        logger_attribute_name = '_' + cls.__name__ + '__logger'

        # Logger name derived accounting for inheritance for the bonus marks
        logger_name = '.'.join([c.__name__ for c in cls.mro()[-2::-1]])

        setattr(cls, logger_attribute_name, get_logger(logger_name))

