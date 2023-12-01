"""Python utility to create Actual Meteorological Year datafiles"""
# Author: Joshua Hammond
# Date: 2023-07-26
# TODO fix docstrings
# TODO make flexible for 15 min/1 hr

# imports
## standard library
import datetime
import logging
import os
from typing import Union, Dict, List

## third party
from herbie import Herbie
import numpy as np
import pandas as pd
from pvlib import location, solarposition

## local
from . import constants, utils

# declarations
logger = logging.getLogger(__name__)


# Class definition
class AMY:
    def __init__(
        self,
        latitude: float = None,
        longitude: float = None,
        name: str = None,
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
        assert (
            21.14 <= self.latitude <= 52.6
        ), "latitude must be between 21.14 N and 52.6 N for HRRR"
        assert (225.9 <= self.longitude <= 299) or (
            -134.1 <= self.longitude <= -61
        ), "longitude must be between (225.9 - 299) or (-134.1 - -61) for HRRR"

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

    def create_amy(
        self,
        year: int = None,
        start_date: str = None,
        end_date: str = None,
        n_workers: int = 1,
        cache_dir: str = None,
        rm_cache: bool = False,
        amy_target_path: str = None,
        verbose: int = 0,
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
            assert (
                start_date is not None
            ), "must provide start_date if year is not provided"
            assert end_date is not None, "must provide end_date if year is not provided"
        elif year is not None:
            assert start_date is None, "cannot provide both year and start_date"
            assert end_date is None, "cannot provide both year and end_date"
            self.start_date = datetime.datetime(year, 1, 1)
            self.end_date = datetime.datetime(year, 12, 31)
        assert (
            start_date.year >= constants.HRRR_first_year
        ), f"First year of HRRR data is {constants.HRRR_first_year}"
        # TODO: add check for 1 complete year of data. or figrue how to account for less than a full year
        # TODO: design so that preprocessing/downloading and subsequent processing can be done separately
        # preprocess
        self.preprocess(cache_dir)

        # download and cache analysis data
        utils.get_grib_data(
            self.uncached_dates,
            self.latitude,
            self.longitude,
            self.search_string_0h,
            self.search_string_1h,
            n_workers,
            self.site_cache_dir,
        )

        # postprocess
        self.post_process_cached_data()

        return

    def preprocess(self, cache_dir, start_date, latitude, longitude):
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
        self.uc, self.vc = utils.get_coordinate_projections(
            start_date, latitude, longitude
        )
        return

    def _prep_chache_dir(self, cache_dir):
        """create cache directory and subdirectory for site"""
        os.makedirs(cache_dir, exist_ok=True)
        site_cache_dir = os.path.join(cache_dir, self.name)
        os.makedirs(site_cache_dir, exist_ok=True)
        return site_cache_dir

    def _identify_uncached_dates(self, specified_dir, start_date, end_date, freq="1H"):
        """identify dates that are not cached in the site cache directory.
        cache files are saved as "%Y%m%d%H%M.csv"""
        all_dates = pd.date_range(start_date, end_date, freq=freq)
        uncached_dates = [
            i
            for i in all_dates
            if not os.path.exists(
                os.path.join(specified_dir, i.strftime("%Y%m%d%H%M.csv"))
            )
        ]
        return uncached_dates

    def post_process_cached_data(
        self,
        cache_dir,
        target_path,
        start_date,
        end_date,
        latitude,
        longitude,
        freq="1H",
    ):
        # combine all cache files into one df
        cache_df = utils.combine_cache_files(cache_dir, start_date, end_date, freq=freq)
        # perform intermediate calculations and format data
        intermediate_df = self._intermediate_calculations(cache_df, latitude, longitude)
        amy_df = self._amy_data_df(intermediate_df)
        # create header
        header_lines = create_header(self.start_date, self.end_date)
        # export data
        with open(target_path, "w") as f:
            for line in header_lines:
                f.write(line + "\n")
            amy_df.to_csv(f, index=False, header=False)

        return

    def _intermediate_calculations(self, cache_df, latitude, longitude):
        intermediate_df = cache_df.copy()
        # calculate solar position
        intermediate_df["zenith"] = utils.calculate_solar_zenith_angle(
            intermediate_df.index, latitude, longitude
        )
        intermediate_df["opaque_sky_cover"] = utils.cloud_cover_to_opaque_sky_cover(
            intermediate_df["lcc"].values,
            intermediate_df["mcc"].values,
            intermediate_df["hcc"].values,
            intermediate_df["tcc"].values,
        )
        intermediate_df[
            "extraterrestrial_normal_radiation"
        ] = utils.calculate_extraterrestrial_normal_radiation(
            intermediate_df.index.dayofyear
        )
        intermediate_df[
            "extraterrestrial_horizontal_irradiance"
        ] = utils.calculate_extraterrestrial_horizontal_irradiance(
            intermediate_df["zenith"].values,
            intermediate_df["extraterrestrial_normal_radiation"].values,
        )
        intermediate_df["horizontal_ir"] = utils.horizontal_ir(
            intermediate_df["t2m"].values,
            intermediate_df["d2m"].values,
            intermediate_df["opaque_sky_cover"].values,
        )
        intermediate_df["ghi"] = (
            intermediate_df["vbdsf"].values
            * np.cos(np.deg2rad(intermediate_df["zenith"]))
            + intermediate_df["vddsf"].values
        )
        intermediate_df["global illuminance"] = utils.solar_irradiance_to_lux(
            intermediate_df["ghi"].values
        )
        intermediate_df["normal illuminance"] = utils.solar_irradiance_to_lux(
            intermediate_df["vbdsf"].values
        )
        intermediate_df["horizontal illuminance"] = utils.solar_irradiance_to_lux(
            intermediate_df["vddsf"].values
        )
        intermediate_df["zenith illuminance"] = utils.solar_irradiance_to_lux(
            intermediate_df["vbdsf"].values
            * np.cos(np.deg2rad(intermediate_df["zenith"].values))
        )
        wind_e, wind_n = utils.convert_uv_projection_to_en(
            intermediate_df["u10"].values,
            intermediate_df["v10"].values,
            self.uc,
            self.vc,
        )
        intermediate_df["wind_E"] = wind_e
        intermediate_df["wind_N"] = wind_n
        intermediate_df["wind direction"] = utils.get_wind_direction(wind_e, wind_n)
        intermediate_df["wind speed"] = utils.get_wind_speed(wind_e, wind_n)
        intermediate_df["aod"] = intermediate_df["unknown"]
        intermediate_df["albedo"] = utils.get_albedo(latitude, longitude)
        # days since last snowfall
        intermediate_df["snow_day"] = (
            intermediate_df.groupby(intermediate_df.index.date)["csnow"].transform(
                "sum"
            )
            > 0
        )
        snow_days = intermediate_df[intermediate_df["snow_day"]].copy()
        snow_days["last_snow_day"] = snow_days.index
        intermediate_df = pd.merge_asof(
            intermediate_df,
            snow_days["last_snow_day"],
            left_index=True,
            right_index=True,
            direction="backward",
        )

        intermediate_df["Days Since Last Snowfall [Days]"] = (
            intermediate_df.index - intermediate_df["last_snow_day"]
        ).dt.days
        intermediate_df["Days Since Last Snowfall [Days]"].clip(0, 99)
        return intermediate_df

    def _amy_data_df(self, df):
        amy_df = pd.DataFrame(index=df.index)
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
        amy_df["extraterrestrial horizontal radiation [Wh/m^2]"] = df[
            "extraterrestrial_horizontal_irradiance"
        ].values
        amy_df["extraterrestrial direct normal radiation [Wh/m^2]"] = df[
            "extraterrestrial_normal_radiation"
        ].values
        amy_df["horizontal infrared radiation intensity [Wh/m^2]"] = df[
            "horizontal_ir"
        ].values
        amy_df["global horizontal radiation [Wh/m^2]"] = df["ghi"].values
        amy_df["direct normal radiation [Wh/m^2]"] = df["vddsf"].values
        amy_df["diffuse horizontal radiation [Wh/m^2]"] = df["vbdsf"].values
        amy_df["global horizontal illuminance [lux]"] = df["global illuminance"].values
        amy_df["direct normal illuminance [lux]"] = df["normal illuminance"].values
        amy_df["diffuse horizontal illuminance [lux]"] = df[
            "horizontal illuminance"
        ].values
        amy_df["zenith luminance [cd/m^2]"] = df["zenith illuminance"].values
        amy_df["wind direction [deg]"] = df["wind direction"].values
        amy_df["wind speed [m/s]"] = df["wind speed"].values
        amy_df["total sky cover [tenths]"] = df["tcc"].values / 10
        amy_df["opaque sky cover [tenths]"] = df["opaque_sky_cover"]
        amy_df["visibility [km]"] = df["vis"].values / 1000
        amy_df["ceiling height [m]"] = df["gh"].values
        amy_df["present weather observation"] = 0  ##########
        amy_df["present weather codes"] = df.apply(
            lambda x: utils.parse_weather_code(
                accumulated_precipitation=x["tp"],
                freezing_rain=x["cfrzr"],
                ice_pellets=x["cicep"],
                lightning=x["ltng"],
                rain=x["crain"],
                snow=x["csnow"],
                pct_frozen_precipitation=x["cpofp"],
                visibility=x["vis"],
                wind_gust_speed=x["gust"],
                smoke=x["tc_mdens"],
            ),
            axis=1,
        ).values
        amy_df["precipitable water [mm]"] = df["pwat"].values
        amy_df["aerosol optical depth [thousandths]"] = df["aod"].values
        amy_df["snow depth [cm]"] = df["sde"].values * 100
        amy_df["days since last snowfall"] = df[
            "Days Since Last Snowfall [Days]"
        ].values
        amy_df["albedo [nondim]"] = df["albedo"]
        amy_df["liquid precipitation depth [mm]"] = df["tp"].values
        amy_df["liquid precipitation quantity [hr]"] = 1
        # TODO: enforce column order

        return amy_df

def create_header(start_date, end_date
    # city,
    # state,
    # country,
    # data_type,
    # WMO_code,
    # latitude,
    # longitude,
    # TZ,
    # elevation,
    # comments_1,
    # comments_2,
    # start_date,
    # end_date
):
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
    # string_1 = f"LOCATION,{city},{state},{country},{data_type},{WMO_code},{latitude},{longitude},{TZ},{elevation}"
    string_1 = f"LOCATION,"
    # 2. design conditions
    string_2 = f"DESIGN CONDITIONS,"
    # 3. typical/extreme periods
    string_3 = f"TYPICAL/EXTREME PERIODS,"
    # 4. ground temperatures
    string_4 = f"GROUND TEMPERATURES,"
    # 5. holidays/daylight savings
    string_5 = f"HOLIDAYS/DAYLIGHT SAVINGS,No,0,0,0"
    # 6. comments 1
    string_6 = f"COMMENTS 1,"
    # 7. comments 2
    string_7 = f"COMMENTS 2,"
    # 8. data periods
    string_8 = 

    return [
        string_1,
        string_2,
        string_3,
        string_4,
        string_5,
        string_6,
        string_7,
        string_8,
    ]

def _get_location_string(
    city: str,
    region: str,
    country: str,
    data_type: str,
    WMO_code: str,
    latitude: float,
    longitude: float,
    TZ: float,
    elevation: float,
):
    """create string for header line 1. Location information.

    Format: LOCATION,{city},{region},{country},{data type},{WMO code},{latitude},{longitude},{TZ},{altitude}
    ex: LOCATION,Maxwell Afb,AL,USA,TMY3,722265,32.38,-86.35,-6.0,53.0

    INPUTS
    ----------
    city : str
        city name
    region : str
        region name (State, Province, etc.)
    country : str
        country name
    data_type : str
        data type. TMY3, TMY2, etc.
    WMO_code : str
        WMO code used as alpha in Energy Plus
    latitude : float
        latitude of location (-90 to 90) with 0.5 representing 30 minutes
    longitude : float
        longitude of location (-180 to 180) with 0.5 representing 30 minutes
    TZ : float
        time zone of location relative to GMT (-12.0 to 12.0)
    elevation : float
        elevation of location in meters (-1000.0 to 9999.9)

    OUTPUTS
    ----------
    formatted_location : string
        formatted string for header line 1

    References:
        [1] https://designbuilder.co.uk/cahelp/Content/EnergyPlusWeatherFileFormat.htm
    """
    formatted_location = f"LOCATION,{city},{region},{country},{data_type},{WMO_code},{latitude},{longitude},{TZ},{elevation}"
    return formatted_location

def _get_design_conditions_string():
    """create string for header line 2. Design conditions.

    Format: DESIGN CONDITIONS, N design conditions,
        --- repeat for each design condition ---
        source i,
        "Heating"
        ***
        "Cooling"
        ***
        "Extremes"
        ***
        --- end repeat ---
    ex: DESIGN CONDITIONS,1,Climate Design Data 2009 ASHRAE Handbook,,Heating,1,-2.3,-0.3,-10.9,1.5,2.9,-8.2,1.9,3.8,9.3,11.3,8.4,11.4,2.4,340,Cooling,7,10.3,36.2,24.7,35.1,24.8,34,24.6,26.9,32.7,26.4,32.1,25.9,31.4,3.1,240,25.5,20.9,29.4,25,20.2,29,24.4,19.5,28.5,84.7,32.6,82.3,32,80.1,31.6,758,Extremes,8,7,5.9,29.8,-5.8,37.8,1.7,1,-7,38.5,-8,39.1,-9,39.6,-10.3,40.3

    INPUTS
    ----------


    OUTPUTS
    ----------
    formatted_design_conditions : string
        formatted string for header line 2

    References:
        [1] https://designbuilder.co.uk/cahelp/Content/EnergyPlusWeatherFileFormat.htm
    """
    heating_design_conditions = f""
    cooling_design_conditions = f""
    extreme_design_conditions = f""
    formatted_design_conditions = f"DESIGN CONDITIONS,{heating_design_conditions},{cooling_design_conditions},{extreme_design_conditions}"
    return formatted_design_conditions

def _get_extreme_typical_periods_string():
    """create string for header line 3. Extreme and typical periods.

    Format: TYPICAL/EXTREME PERIODS,N periods,
        --- repeat for each period ---
        period name i
        period type i
        period start day  i
        period end day i
        --- end repeat ---
    ex: TYPICAL/EXTREME PERIODS,6,Summer - Week Nearest Max Temperature For Period,Extreme,7/10,7/16,Summer - Week Nearest Average Temperature For Period,Typical,5/ 1,5/ 7,Winter - Week Nearest Min Temperature For Period,Extreme,12/20,12/26,Winter - Week Nearest Average Temperature For Period,Typical,1/ 4,1/10,Autumn - Week Nearest Average Temperature For Period,Typical,9/19,9/25,Spring - Week Nearest Average Temperature For Period,Typical,3/22,3/28

    INPUTS
    ----------


    OUTPUTS
    ----------
    formatted_extreme_typical_periods : string
        formatted string for header line 3

    References:
        [1] https://designbuilder.co.uk/cahelp/Content/EnergyPlusWeatherFileFormat.htm
    """
    formatted_extreme_typical_periods = f"TYPICAL/EXTREME PERIODS,"
    return formatted_extreme_typical_periods

def _get_ground_temps_string():
    """create string for header line 4. Ground temperatures.

    Format: GROUND TEMPERATURES,{N depths},
        --- repeat for each depth ---
        Depth i (m),
        Soil Conductivity i (W/m-K),
        Soil Density i (kg/m3),
        Soil Specific Heat i (J/kg-K),
        January Average Ground Temperature i (C),
        February Average Ground Temperature i (C),
        March Average Ground Temperature i (C),
        April Average Ground Temperature i (C),
        May Average Ground Temperature i (C),
        June Average Ground Temperature i (C),
        July Average Ground Temperature i (C),
        August Average Ground Temperature i (C),
        September Average Ground Temperature i (C),
        October Average Ground Temperature i (C),
        November Average Ground Temperature i (C),
        December Average Ground Temperature i (C),
        --- end repeat ---
    ex: GROUND TEMPERATURES,6,0.5,1.5,2.5,3.5,4.5,5.5

    INPUTS
    ----------


    OUTPUTS
    ----------
    formatted_ground_temps : string
        formatted string for header line 4

    References:
        [1] https://designbuilder.co.uk/cahelp/Content/EnergyPlusWeatherFileFormat.htm
    """
    formatted_ground_temps = f"GROUND TEMPERATURES,"
    return formatted_ground_temps

def _get_holidays_daylight_savings_string():
    """create string for header line 5. Holidays and daylight savings.

    Format: HOLIDAYS/DAYLIGHT SAVINGS,
        Use Holidays/DST (Yes or No),
        Start Daylight Saving Time,
        End Daylight Saving Time,
        N Holidays
        --- repeat for each holiday ---
        Holiday Name i,
        Holiday Date i,
        --- end repeat ---
    ex: HOLIDAYS/DAYLIGHT SAVINGS,No,0,0,0

    INPUTS
    ----------


    OUTPUTS
    ----------
    formatted_holidays_daylight_savings : string
        formatted string for header line 5

    References:
        [1] https://designbuilder.co.uk/cahelp/Content/EnergyPlusWeatherFileFormat.htm
    """
    formatted_holidays_daylight_savings = f"HOLIDAYS/DAYLIGHT SAVINGS,No,0,0,0"
    return formatted_holidays_daylight_savings

def _get_data_periods_string(start_date, end_date):
    """format data periods for header line 8. Shows # records per hour then
    period name/description, start day of week, start month/day, end month/day
    for each period if more than one. According to [1], multiple data periods
    are not neccesary and may be detrimental to simulation results. Accordingly,
    we assume 1 data period.

    Format: DATA PERIODS,N periods,Records per hour
        --- repeat for each period ---
        i,
        name/description i,
        start day of week i,
        start date i,
        end date i
        --- end repeat ---
    ex: DATA PERIODS,1,1,Data,Sunday,1/1,12/31

    INPUTS
    ----------
    df : timeseries dataframe
        dataframe with datetime index

    OUTPUTS
    ----------
    formatted_data_periods : string

    References:
        [1] https://designbuilder.co.uk/cahelp/Content/EnergyPlusWeatherFileFormat.htm
        [2] https://bigladdersoftware.com/epx/docs/8-3/auxiliary-programs/energyplus-weather-file-epw-data-dictionary.html
        [3] https://pvlib-python.readthedocs.io/en/stable/_modules/pvlib/iotools/epw.html
    """
    first_date_day_of_week = start_date.strftime("%A")
    first_date_string = start_date.strftime("%m/%d")
    last_date_string = end_date.strftime("%m/%d")

    formatted_data_periods = f"DATA PERIODS,1,1,My Data Period,{first_date_day_of_week}, {first_date_string},\
    {last_date_string}"
    return formatted_data_periods
