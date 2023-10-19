import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s',
    filename='logs/0_get_data.log', filemode='w')

import datetime
import os
import sys

import pandas as pd

sys.path.append(os.path.join("..", "AMY"))
import constants, core, utils

# declarations
start_date = datetime.datetime(2021, 12, 31, 19)
# end_date = datetime.datetime(2023, 8, 1)
end_date = datetime.datetime(2022, 1, 2)
n_workers = 5
cache_dir = os.path.join("..", "cache")

san_antonio = {
    "latitude" : 29.25,  # N
    "longitude" :   360-98.31,  # W
    "begin_date" : datetime.datetime(2022,1,1),
    "end_date" : datetime.datetime(2023,1,1)
}

# 
all_dates = pd.date_range(start_date, end_date, freq="1H")
dl_dates = [i for i in all_dates if not 
            os.path.exists(os.path.join(cache_dir, i.strftime("%Y%m%d%H%M.csv")))]

search_string_0h = utils.get_search_string([i.get("searchstring") for i in constants._grib_variables_0h.values()])
search_string_1h = utils.get_search_string([i.get("searchstring") for i in constants._grib_variables_1h.values()])

utils.get_grib_data(dl_dates,
    san_antonio.get("latitude"), 
    san_antonio.get("longitude"), 
    search_string_0h, 
    search_string_1h, 
    n_workers,
    cache_dir
)
