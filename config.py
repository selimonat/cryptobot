import os

PATH_DB = os.path.join(os.getcwd(), 'db', '.')
PATH_DB_TIMESERIES = os.path.join(PATH_DB, 'timeseries')
PATH_DB_BOT_HISTORY = os.path.join(PATH_DB, 'history')
PATH_DB_BOT_FEATURE = os.path.join(PATH_DB, 'features')
GRANULARITY = 60*15 # 15 minutes
START_YEAR = 2021
