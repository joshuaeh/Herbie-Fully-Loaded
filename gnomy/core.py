"""Python utility to create Actual Meteorological Year datafiles"""
# Author: Joshua Hammond
# Date: 2023-07-26
 #TODO fix docstrings
 #TODO make flexible for 15 min/1 hr

# imports
## standard library
import datetime
import logging
import os

## third party
from herbie import Herbie
import numpy as np
import pandas as pd
from pvlib import location, solarposition
## local
import constants, utils

# declarations
logger = logging.getLogger(__name__)

# Class definition
class AMY:
    def __init__(self,
        latitude:float=None,
        longitude:float=None,
        name:str=None,
        ):
        """AMY class constructor
        
        PARAMETERS
        ----------
        latitude : float
            latitude of location. Must be between 21.14 N and 52.6 N for HRRR
        longitude : float
            longitude of the location. HRRR uses longitude of the form (0-360) where
            0 is th eprime meridian and then works eastward. Must be (225.9 - 299) E.
            Inputs must be in range (225.9 - 229) or (-134.1 - -61) 
        """
        # validate inputs
        assert 21.14 <= self.latitude <= 52.6, "latitude must be between 21.14 N and 52.6 N for HRRR"
        assert (225.9 <= self.longitude <= 299) or (-134.1 <= self.longitude <= -61), "longitude must be between (225.9 - 299) or (-134.1 - -61) for HRRR"
        
        # transform longitude if neccessary
        if self.longitude < 0:
            self.longitude = 360 + self.longitude
            
        # general parameters
        self.latitude = latitude
        self.longitude = longitude
        if name is not None:
            self.name = name
        else:
            self.name = f"{self.latitude:.2f} N {self.longitude:.2f} E"
        return
    
    def create_amy(self,
        year:int=None,
        start_date:str=None,
        end_date:str=None,
        n_workers:int=1,
        cache_dir:str=None,
        rm_cache:bool=False,
        amy_target_path:str=None,
        verbose:int=0
        ):
        """create amy datafile
        1. preprocess
        2. process each hour
        3. postprocess
        
        PARAMETERS
        ----------
        year : int
            year of data to be generated. Will use Jan 1 - Dec 31 of that year.
            If not used, must provide start_date and end_date.
            NOTE: all times are in UTC
        start_date : str, datetime-like
            start date of data to be generated. Must provide end_date as well.
            NOTE: all times are in UTC
        end_date : str, datetime-like
            end date of data to be generated. Must provide start_date as well.
            NOTE: all times are in UTC
        n_workers : int
            number of workers to use for parallel processing. Default is 1.
        cache_dir : str, path-like
            directory to store cached data. Default is cwd/cache
        rm_cache : bool
            remove cache directory after processing. Default is False.
        amy_target_path : str, path-like
            path to store amy file. Default is cwd/amy
        verbose : int
            level of verbosity. Default is 0.
            0: no output
            1: only errors
            2: errors, progress
            
        RETURNS
        ----------
        amy file is created at amy_target_path
        """
        # validate inputs
        if year is None:
            assert start_date is not None, "must provide start_date if year is not provided"
            assert end_date is not None, "must provide end_date if year is not provided"
        elif year is not None:
            assert start_date is None, "cannot provide both year and start_date"
            assert end_date is None, "cannot provide both year and end_date"
            self.start_date = datetime.datetime(year, 1, 1)
            self.end_date = datetime.datetime(year, 12, 31)
        assert start_date.year >= constants.HRRR_first_year, f"First year of HRRR data is {constants.HRRR_first_year}"
        # TODO: add check for 1 complete year of data. or figrue how to account for less than a full year
        # TODO: design so that preprocessing/downloading and subsequent processing can be done separately
        # preprocess
        self.preprocess(cache_dir)
        
        # download and cache analysis data
        utils.get_grib_data(self.uncached_dates,
            self.latitude, 
            self.longitude, 
            self.search_string_0h, 
            self.search_string_1h, 
            n_workers,
            self.site_cache_dir
            )
        
        return
    
    def preprocess(self,
        cache_dir,
        start_date,
        latitude,
        longitude
        ):
        """Prepare for AMY Generation and  initialize data structures
        1. create site cache directory
        2. identify uncached dates
        3. create search strings
        4. estimate coordinate projection components
        """
        self.site_cache_dir = self._prep_chache_dir(cache_dir)
        self.uncached_dates = self._identify_uncached_dates(cache_dir)
        self.search_string_0h = utils.get_search_string(
            [i.get("searchstring") for i in constants._grib_variables_0h.values()]
            )
        self.search_string_1h = utils.get_search_string(
            [i.get("searchstring") for i in constants._grib_variables_1h.values()]
            )
        self.uc, self.vc = utils.get_coordinate_projections(start_date, latitude, longitude)
        return
    
    def _prep_chache_dir(self,
        cache_dir
        ):
        """create cache directory and subdirectory for site"""
        os.makedirs(cache_dir, exist_ok=True)
        site_cache_dir = os.path.join(cache_dir, self.name)
        os.makedirs(site_cache_dir, exist_ok=True)
        return site_cache_dir
    
    def _identify_uncached_dates(self,
        specified_dir,
        start_date,
        end_date,
        freq="1H"
        ):
        """identify dates that are not cached in the site cache directory.
        cache files are saved as "%Y%m%d%H%M.csv"""
        all_dates = pd.date_range(start_date, end_date, freq=freq)
        uncached_dates = [i for i in all_dates if not 
            os.path.exists(os.path.join(specified_dir, i.strftime("%Y%m%d%H%M.csv")))]
        return uncached_dates     
    
    def post_process_cached_data(self,
        cache_dir,
        start_date,
        end_date,
        latitude,
        longitude,
        freq="1H"
        ):
        # combine all cache files into one df
        cache_df = utils.combine_cache_files(cache_dir, start_date, end_date, freq=freq)
        intermediate_df = self._intermediate_calculations(cache_df, latitude, longitude)
        amy_df = self._amy_data_df(intermediate_df)
        
        return
    
    def _intermediate_calculations(self,
        cache_df,
        latitude,
        longitude
        ):
        intermediate_df = cache_df.copy()
        # calculate solar position
        intermediate_df["zenith"] = utils.calculate_solar_zenith_angle(
            intermediate_df.index, latitude, longitude)
        intermediate_df["opaque_sky_cover"] = utils.cloud_cover_to_opaque_sky_cover(
            intermediate_df["lcc"].values, intermediate_df["mcc"].values,
            intermediate_df["hcc"].values, intermediate_df["tcc"].values)
        intermediate_df["extraterrestrial_normal_radiation"] = \
            utils.calculate_extraterrestrial_normal_radiation(intermediate_df.index.dayofyear)
        intermediate_df["extraterrestrial_horizontal_irradiance"] = \
            utils.calculate_extraterrestrial_horizontal_irradiance(
                intermediate_df["zenith"].values, intermediate_df["extraterrestrial_normal_radiation"].values)
        intermediate_df["horizontal_ir"] = utils.horizontal_ir(
            intermediate_df["t2m"].values, intermediate_df["d2m"].values, intermediate_df["opaque_sky_cover"].values)
        intermediate_df["ghi"] = intermediate_df["vbdsf"].values * np.cos(np.deg2rad(intermediate_df["zenith"])) + \
            intermediate_df["vddsf"].values
        intermediate_df["global illuminance"] = utils.solar_irradiance_to_lux(intermediate_df["ghi"].values)
        intermediate_df["normal illuminance"] = utils.solar_irradiance_to_lux(intermediate_df["vbdsf"].values)
        intermediate_df["horizontal illuminance"] = utils.solar_irradiance_to_lux(intermediate_df["vddsf"].values)
        intermediate_df["zenith illuminance"] = utils.solar_irradiance_to_lux(intermediate_df["vbdsf"].values * \
            np.cos(np.deg2rad(intermediate_df["zenith"].values)))
        wind_e, wind_n = utils.convert_uv_projection_to_en(
            intermediate_df["u10"].values, intermediate_df["v10"].values,
            self.uc, self.vc)
        intermediate_df["wind_E"] = wind_e
        intermediate_df["wind_N"] = wind_n
        intermediate_df["wind direction"] = utils.get_wind_direction(wind_e, wind_n)
        intermediate_df["wind speed"] = utils.get_wind_speed(wind_e, wind_n)
        intermediate_df["aod"] = intermediate_df["unknown"]
        intermediate_df["albedo"] = utils.get_albedo(latitude, longitude)
        # days since last snowfall
        intermediate_df["snow_day"] = intermediate_df.groupby(intermediate_df.index.date)["csnow"].transform("sum") > 0
        snow_days = intermediate_df[intermediate_df["snow_day"]].copy()
        snow_days["last_snow_day"] = snow_days.index
        intermediate_df = pd.merge_asof(intermediate_df, snow_days['last_snow_day'],
                        left_index=True, right_index=True,
                        direction='backward')

        intermediate_df['Days Since Last Snowfall [Days]'] = (intermediate_df.index-intermediate_df['last_snow_day']).dt.days
        intermediate_df['Days Since Last Snowfall [Days]'].clip(0, 99)
        return intermediate_df
        
    def _amy_data_df(self,
        df
        ):
        amy_df = pd.DataFrame()
        amy_df["year"] = df.index.year
        amy_df["month"] = df.index.month
        amy_df["day"] = df.index.day
        amy_df["hour"] = df.index.hour
        amy_df["minute"] = df.index.minute
        amy_df["data_flags"] = "NOAA HRRR"
        amy_df["dry bulb temperature [C]"] = df["t2m"].values - 273.15
        amy_df["dew point temperature [C]"] = df["d2m"].values - 273.15
        amy_df["relative humidity [%]"] = df["r2"].values
        amy_df["atmospheric station pressure [Pa]"] = df["sp"].values
        amy_df["extraterrestrial horizontal radiation [Wh/m^2]"] = df["extraterrestrial_horizontal_irradiance"].values
        amy_df["extraterrestrial direct normal radiation [Wh/m^2]"] = df["extraterrestrial_normal_radiation"].values
        amy_df["horizontal infrared radiation intensity [Wh/m^2]"] = df["horizontal_ir"].values
        amy_df["global horizontal radiation [Wh/m^2]"] = df["ghi"].values
        amy_df["direct normal radiation [Wh/m^2]"] = df["vddsf"].values
        amy_df["diffuse horizontal radiation [Wh/m^2]"] = df["vbdsf"].values
        amy_df["global horizontal illuminance [lux]"] = df["global illuminance"].values
        amy_df["direct normal illuminance [lux]"] = df["normal illuminance"].values
        amy_df["diffuse horizontal illuminance [lux]"] = df["horizontal illuminance"].values
        amy_df["zenith luminance [cd/m^2]"] = df["zenith illuminance"].values
        amy_df["wind direction [deg]"] = df["wind direction"].values
        amy_df["wind speed [m/s]"] = df["wind speed"].values
        amy_df["total sky cover [tenths]"] = df["tcc"].values / 10
        amy_df["opaque sky cover [tenths]"] = df["opaque_sky_cover"]
        amy_df["visibility [km]"] = df["vis"].values / 1000
        amy_df["ceiling height [m]"] = df["gh"].values 
        amy_df["present weather observation"] = 0 ##########
        amy_df["present weather codes"] = df.apply(
            lambda x: utils.parse_weather_code(
                accumulated_precipitation = x["tp"],
                freezing_rain=x["cfrzr"],
                ice_pellets=x["cicep"],
                lightning=x["ltng"],
                rain=x["crain"],
                snow=x["csnow"],
                pct_frozen_precipitation=x["cpofp"],
                visibility=x["vis"],
                wind_gust_speed=x["gust"],
                smoke=x["tc_mdens"]
            ), axis=1).values
        amy_df["precipitable water [mm]"] = df["pwat"].values
        amy_df["aerosol optical depth [thousandths]"] = df["aod"].values
        amy_df["snow depth [cm]"] = df["sde"].values * 100
        amy_df["days since last snowfall"] = df['Days Since Last Snowfall [Days]'].values
        amy_df["albedo [nondim]"] = df["albedo"]
        amy_df["liquid precipitation depth [mm]"] = df["tp"].values
        amy_df["liquid precipitation quantity [hr]"] = 
        # TODO: check is this 1, or how long it has been precipitating?
        return amy_df  
    
    def _create_header(
        city,
        state,
        country,
        data_type,
        WMO_code,
        latitude,
        longitude,
        TZ,
        altitude,
        heating_design_conditions,
        cooling_design_conditions,
        extreme_design_conditions,
        extreme_hot_weeks,
        extreme_cold_weeks,
        typical_weeks,
        monthly_ground_temps,
        is_ip,
        is_leap_year,
        daylight_savings_start,
        daylight_savings_end,
        comments_1,
        comments_2):
        """The Header is the first 8 lines of the file. THey contain summary and context information.
        1. (location): city, state, country, data type, WMO code, latitude, longitude, time zone, altitude
        2. (design conditions): 
        3. (typical/extreme periods):
        4. (Ground temperatures):
        5. (Holidays/daylight savings):
        6. (Comments 1):
        7. (Comments 2):
        8. (Data periods)
        
        see: https://pvlib-python.readthedocs.io/en/stable/_modules/pvlib/iotools/epw.html
        https://github.com/building-energy/epw
        https://github.com/ladybug-tools/ladybug/blob/master/ladybug/epw.py
        """
        # 1. location
        string_1_location = f"LOCATION,{city},{state},{country},{data_type},{WMO_code},{latitude},{longitude},{TZ},{altitude}\n"
        # 2. design conditions
        string_2_design_conditions = f"DESIGN CONDITIONS,"
        
        return
    
    def _get_heating_days():
        return
    
    def _get_cooling_days():
        return

    
    def _post_process():
        """finalize data structures and export data
        1. collect all data measurements
        2. irradiance calculations (10 min, solar position, 
        dni_extra: pvlib.irradiance.extraradiation
        nrel or pyephem most accurate but only +- 2 W/m^2 over all year
        dhi_extra,
        resample to timespan of HRRR
        3. calculate secondary and tertiary variables
        4. impute if neccesary
        5. header information
        6. export data
        """
        return
    
    