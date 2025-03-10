""" """
# imports

# constants

# functions
# imports
import logging

logger = logging.getLogger(__name__)

import datetime
import glob
import os
import warnings

from herbie import Herbie
from joblib import delayed, Parallel
import numpy as np
import pandas as pd
from pvlib import solarposition
import pytz

from . import constants

# declarations
warnings.filterwarnings(
    "ignore", message="More than one time coordinate present for variable  "
)  # warning from parsing grib files
warnings.filterwarnings(
    "ignore",
    message="Calling float on a single element Series is deprecated and will raise a TypeError in the future. Use float(ser.iloc[0]) instead",
)  # warning from Herbie. TODO: update Herbie to fix this


# functions
## Data Acquisition
def get_search_string(list_of_searches):
    """Create a search string for pygrib based on a list of search strings

    Parameters
    ----------
    list_of_searches : list
        list of search strings

    Returns
    ----------
    search_string : str
        search string for herbie
    """
    mid_string = ")|(".join(list_of_searches)
    return "?:(" + mid_string + ")"


def parse_xarray_data(xarray_data, latitude, longitude):
    """ """
    parsed_data = {}

    for data_i in xarray_data:
        logger.debug("----Individual dataset selected")
        # data_i = data_i.drop_vars(["time", "step", "valid_time", "gribfile_projection"], errors="ignore")
        data_i.drop_vars(["time", "step", "valid_time"], errors="ignore")
        logger.debug("----Locating nearest point")
        data_i = data_i.herbie.nearest_points((longitude, latitude))
        for data_var in list(data_i.data_vars):
            if data_var != "gribfile_projection":
                logger.debug("--------Adding variable value at location")
                parsed_data[data_var] = data_i[data_var].values[0]
    return parsed_data


def get_grib_hour_data(
    grib_dt, search_string_0h, search_string_1h, latitude, longitude
):
    """Get HRRR Analysis Data for a single hour at a point location

    PARAMETERS
    ----------
    grib_dt : datetime
        datetime of the HRRR analysis
    search_string : str
        string to search for in the HRRR analysis
    latitude : float
        latitude of location. Must be between 21.14 N and 52.6 N for HRRR
    longitude : float
        longitude of the location. HRRR uses longitude of the form (0-360)

    RETURNS
    ----------
    df : pandas.DataFrame
        dataframe of the HRRR analysis data for the hour
    """
    try:
        logger.debug("Creating Herbie Objects")
        H0 = Herbie(grib_dt, model="hrrr", product="sfc", fxx=0, verbose=False)
        H1 = Herbie(
            grib_dt - datetime.timedelta(hours=1),
            model="hrrr",
            product="sfc",
            fxx=1,
            verbose=False,
        )
        logger.debug("Using XARRAY")
        H0_data = H0.xarray(searchString=search_string_0h)
        H1_data = H1.xarray(searchString=search_string_1h)
        logger.debug("Finding Individual Data Values at location")
        H0_selected_data = parse_xarray_data(H0_data, latitude, longitude)
        H1_selected_data = parse_xarray_data(H1_data, latitude, longitude)
        analysis_data = H0_selected_data | H1_selected_data
        logger.debug("Creating Dataframe")
        df = pd.DataFrame(data=analysis_data, index=[grib_dt])
        return df
    except Exception as e:
        logger.debug("exception:" + e)
        return None


def get_grib_data(
    grib_datetimes,
    latitude,
    longitude,
    search_string_0h,
    search_string_1h,
    n_jobs,
    cache_dir,
):
    """Get grib data from HRRR analysis, save in cache dir

    PARAMETERS
    ----------
    TODO

    RETURNS
    ----------
    list of datetimes with errors
    """
    logger.debug("Starting get_grib_data")

    def grib_download_wrapper(grib_datetime):
        """wrapper for grib_download"""
        logger.debug(f"starting: grib_datetime.strftime('%Y%m%d%H%M%S')")
        save_path = os.path.join(cache_dir, grib_datetime.strftime("%Y%m%d%H%M%S.csv"))
        df = get_grib_hour_data(
            grib_datetime, search_string_0h, search_string_1h, latitude, longitude
        )
        if df is not None:
            df.to_csv(save_path)
            logger.debug(f"Saving: grib_datetime.strftime('%Y%m%d%H%M%S')")
            return None
        else:
            logger.debug(f"Failed: grib_datetime.strftime('%Y%m%d%H%M%S')")
            return grib_datetime

    # download data
    try:
        logging.debug("--get_grib_data: Starting Parallel")
        out = Parallel(n_jobs=n_jobs)(
            delayed(grib_download_wrapper)(i) for i in grib_datetimes
        )
        logging.debug(f"--get_grib_data: finished Parallel")
    except Exception as e:
        logging.debug(e)

    return [i for i in out if i is not None]


def combine_cache_files(cache_dir, start_date, end_date, freq):
    all_dates = pd.date_range(start_date, end_date, freq=freq)
    all_cache_file_paths = [
        os.path.join(cache_dir, i.strftime("%Y%m%d%H%M%S.csv")) for i in all_dates
    ]
    all_cache_file_paths.sort()
    cache_dfs = []
    for data_file in all_cache_file_paths:
        cache_dfs.append(pd.read_csv(data_file, index_col=0))
    cache_df = pd.concat(cache_dfs)
    cache_df.index = pd.to_datetime(
        all_dates,
    )
    cache_df.sort_index(inplace=True)
    return cache_df


def calculate_solar_zenith_angle(original_datetime_index, latitude, longitude):
    """Calculate values related to solar position and irradiance"""
    offset_timedelta = pd.Timedelta(original_datetime_index.freq)
    dt_index_resampled = pd.date_range(
        original_datetime_index[0] - offset_timedelta,
        original_datetime_index[-1],
        freq="5Min",
    )
    sp = solarposition.get_solarposition(dt_index_resampled, latitude, longitude)
    zenith_df = (
        sp["zenith"]
        .resample(offset_timedelta, label="right")
        .mean()[original_datetime_index[0] : original_datetime_index[-1]]
    )
    zenith_df = zenith_df[original_datetime_index[0] : original_datetime_index[-1]]
    return zenith_df


## Data Processing Functions
# Radiation functions
# HOMER documentation was very helpful here
# see https://www.homerenergy.com/products/pro/docs/3.11/how_homer_calculates_the_radiation_incident_on_the_pv_array.html
# PVLib notebooks also good: https://notebook.community/pvlib/pvlib-python/docs/tutorials/irradiance
# NOTE: Holmgren cites recent lit for 1361 as solar constant. TODO find source
def cloud_cover_to_opaque_sky_cover(lcc, mcc, hcc, tcc, tcc_translucent_ratio=0.5):
    """Convert cloud cover to opaque sky cover.
    High clouds are often more transmissive than low or clouds. This corrects for
    transmissive clouds that scatter light into the atmosphere. [1,2]

    Opaque cloud cover and percentage of possible sunshine approximate insolation better than
    total sky cover. The first two do so very similarly [3]

    Parameters
    ----------
    lcc : float
        low cloud cover (tenths)
    mcc : float
        mid cloud cover (tenths)
    hcc : float
        high cloud cover (tenths)
    tcc : float
        total cloud cover (tenths)

    Returns
    -----------
    opaque_sky_cover : float
        opaque sky cover (tenths)

    References
    -----------
    [1] https://doi.org/10.1016/0038-092X(74)90017-6
    [2] http://dx.doi.org/10.1029/2008JD010278
    [3] https://doi.org/10.1016/0038-092X(69)90054-1
    """
    translucent_cloud_cover = (
        np.clip(tcc - lcc - mcc, 0, 100) * tcc_translucent_ratio
    )  # estimate of tcc that is only hcc.
    return (tcc - translucent_cloud_cover) / 10


def get_extraterrestrial_direct_normal_radiation(day_of_year, G_solar_constant=1361):
    """ """
    return G_solar_constant * (1 + 0.033 * np.cos(np.radians(360 * day_of_year / 365)))


def get_extraterrestrial_horizontal_radiation(solar_zenith_angle, G_normal):
    """Theoretical solar radiation intensity on a horizontal surface at the top of the atmosphere

    Parameters
    ----------
    solar_zenith_angle : float
        solar zenith angle (degrees)
    G_normal : float
        extraterrestrial direct normal radiation (W/m2)

    Returns
    ----------
    extraterrestrial_horizontal_radiation : float
        extraterrestrial horizontal radiation (W/m2)
    """
    return G_normal * np.cos(np.radians(solar_zenith_angle))


def sky_emissivity(T_dew, opaque_sky_cover):
    """Approximation for sky emissivity

    Parameters
    ----------
    T_dew : float
        Dew point temperature (K)
    opaque_sky_cover : int
        Opaque sky cover (tenths) 0 clear sky, 10 overcast

    Returns
    ----------
    #TODO: Add Sky Emmisivity units
    sky_emissivity : float

    References
    ----------
    [1] Walton, G.N. Thermal Analysis Research Program Reference Manual; US Department of Commerce, National Bureau of Standards: Washington, DC, USA, March 1983.
    [2] Clark, G.; Allen, C. The estimation of atmospheric radiation for clear and cloudy skies. In Proceedings of the 2nd National Passive Solar Conference (AS/ISES), Philadelphia, PA, USA, 16–18 March 1978; pp. 675–678.
    """
    return (
        (0.787 + 0.767 * np.log(T_dew / 273))
        + (0.0224 * opaque_sky_cover)
        - 0.0035 * opaque_sky_cover**2
        + 0.00028 * opaque_sky_cover**3
    )


def horizontal_ir(T_dry, T_dew, opaque_sky_cover, sig=5.6697e-8):
    """Approximation for horizontal infrared radiation intensity

    Parameters
    ----------
    T_dry : float
        Dry bulb temperature (K)
    T_dew : float
        Dew point temperature (K)
    opaque_sky_cover : int
        Opaque sky cover (tenths) 0 clear sky, 10 overcast
    sig: float
        Stefan-Boltzmann constant (W/m2/K4) default value is 5.6697e-8

    Returns
    ----------
    horizontal infrared radiation intensity : float

    References
    ----------
    [1] Walton, G.N. Thermal Analysis Research Program Reference Manual; US Department of Commerce, National Bureau of Standards: Washington, DC, USA, March 1983.
    [2] Clark, G.; Allen, C. The estimation of atmospheric radiation for clear and cloudy skies. In Proceedings of the 2nd National Passive Solar Conference (AS/ISES), Philadelphia, PA, USA, 16–18 March 1978; pp. 675–678.
    """
    return sky_emissivity(T_dew, opaque_sky_cover) * sig * T_dry**4


def solar_irradiance_to_lux(G):
    """Convert solar irradiance to luminance which only measures visible light
    Assumes Linear approximation of luminous efficacy of solar radiation.
    TODO Could use NREL SRRL BMS (https://midcdmz.nrel.gov/apps/html.pl?site=BMS;page=instruments#LI-210) for more accurate conversion dependent on sza, dni, dhi, aod, etc.

    Parameters
    ----------
    G : float
        solar irradiance (W/m2)

    Returns
    ---------
    lux : float
        luminance (lux)

    References
    ----------
    [1] https://dx.doi.org/10.21227/mxr7-p365 1 W/m^2 = 122 +/- 1 lux for outdoor applications
    [2] https://physics.stackexchange.com/a/193212/373511 cites 1 lux = 0.0079W/m2
    """
    return G * 122


def get_coordinate_projections(date, latitude, longitude):
    """use surrounding grid points to estimate the compass direction of the coordinate vectors
    to be used in the form:
    wind E/W = u_speed * u[0] + v_speed * v[0]
    wind N/S = u_speed * u[1] + v_speed * v[1]

    PARMAETERS
    ----------
    date : string, datetime
        date of the HRRR analysis
    latitude : float
        latitude of location. Must be between 21.14 N and 52.6 N for HRRR
    longitude : float
        longitude of the location. HRRR uses longitude of the form (0-360)

    RETURNS
    ----------
    u : tuple
        tuple of floats representing the longitude and latitude components of the u vector
    v : tuple
        tuple of floats representing the longitude and latitude components of the v vector
    """
    H = Herbie(date, model="hrrr", product="sfc", fxx=0)
    ds = H.xarray("(:UGRD:10 m above ground:anl)|(:VGRD:10 m above ground:anl)")
    latitudes = ds.latitude.values
    longitudes = ds.longitude.values
    distance = (ds.longitude.values - longitude) ** 2 + (
        ds.latitude.values - latitude
    ) ** 2
    argmin_y, argmin_x = divmod(distance.argmin(), distance.shape[1])

    x_lon = (
        longitudes[argmin_y, argmin_x + 1] - longitudes[argmin_y, argmin_x - 1]
    ) / 2
    x_lat = (latitudes[argmin_y, argmin_x + 1] - latitudes[argmin_y, argmin_x - 1]) / 2
    y_lon = (
        longitudes[argmin_y + 1, argmin_x] - longitudes[argmin_y - 1, argmin_x]
    ) / 2
    y_lat = (latitudes[argmin_y + 1, argmin_x] - latitudes[argmin_y - 1, argmin_x]) / 2

    u_lon = x_lon / (x_lon**2 + x_lat**2) ** 0.5
    v_lon = y_lon / (y_lon**2 + y_lat**2) ** 0.5
    u_lat = x_lat / (x_lon**2 + x_lat**2) ** 0.5
    v_lat = y_lat / (y_lon**2 + y_lat**2) ** 0.5
    uc = (u_lon, u_lat)
    vc = (v_lon, v_lat)
    return uc, vc


def convert_uv_projection_to_en(u, v, uc, vc):
    """convert u and v vectors to east and north vectors using the components calculated in get_coordinate_projections

    PARAMETERS
    ----------
    u : float
        u wind component (m/s) (positive roughly eastward)
    v : float
        v wind component (m/s) (positive roughly northward)
    uc : tuple
        tuple of floats representing the longitude and latitude components of the u vector
    vc : tuple
        tuple of floats representing the longitude and latitude components of the v vector

    RETURNS
    ----------
    e : float
        eastward wind component (m/s)
    n : float
        northward wind component (m/s)
    """
    e = u * uc[0] + v * vc[0]
    n = u * uc[1] + v * vc[1]
    return e, n


def get_wind_direction(e, n):
    """Use u and v wind components to calculate compass wind direction

    Parameters
    ----------
    u : float
        u wind component (m/s) (positive eastward)
    v : float
        v wind component (m/s) (positive northward)

    Returns
    ----------
    wind direction (degrees)
    """
    deg = np.rad2deg(np.arctan2(e, n))
    # if deg < 0:
    #     deg = 360 + deg
    return deg


def get_wind_speed(e, n):
    """Use u and v wind components to calculate wind speed

    Parameters
    ----------
    u : float
        u wind component (m/s) (positive eastward)
    v : float
        v wind component (m/s) (positive northward)

    Returns
    ----------
    wind speed (m/s)
    """
    return np.sqrt(e**2 + n**2)


def T_wet(T_dry, RH, allow_estimation=True):
    """Approximation to estimate wet bulb temperature
    Analytical equation from "Wet-Bulb Temperature from Relative Humidity and Air Temperature" Roland Stull
    https://doi.org/10.1175/JAMC-D-11-0143.1

    Parameters
    ----------
    T_dry : float (253.15 - 323.15)
        Dry bulb temperature (K)
    RH : float (5-99)
        Relative Humidity (%)

    Returns
    ----------
    T_wet : float
        Wet bulb temperature (K)
    """
    # convert T_dry to C
    T_dry = T_dry - 273.15

    # validate the ranges of the inputs
    estimated_output = False
    # RH limits
    if RH < 5:
        if not allow_estimation:
            raise ValueError("RH must be greater than 5% for this approximation")
        estimated_output = True
    if RH > 99:
        RH = 99
    # T_dry limits
    if T_dry < -20 or T_dry > 50:
        raise ValueError("T_dry must be between -20 and 50 C")
    # low T, low RH region
    # valid_limit_1 = (-20, 75)  # (T_dry, RH)
    # valid_limit_2 = (11, 0)    # (T_dry, RH)
    # line: -75 * T_dry + -31 * RH + 825 = 0
    if (-75 * T_dry - 31 * RH + 825) < 0:
        if not allow_estimation:
            raise ValueError(
                "T_dry and RH combination is not valid for this approximation"
            )
        estimated_output = True

    # approximated fit
    if not estimated_output:
        T_wet = (
            20 * np.arctan(0.151_977 * (RH + 8.313_659) ** 0.5)
            + np.arctan(T_dry + RH)
            - np.arctan(RH - 1.676_331)
            - 0.003_918_38 * RH**1.5 * np.arctan(0.023_101 * RH)
            - 4.686_035
        )
    else:
        T_wet = T_dry
    return T_wet + 273.15


def get_albedo(latitude, longitude):
    """"""
    H = Herbie("2022-1-1 00:00", model="hrrr", product="sfc", fxx=0)
    ds = H.xarray(":VGTYP:")
    distances = (ds.longitude.values - longitude) ** 2 + (
        ds.latitude.values - latitude
    ) ** 2
    argmin_y, argmin_x = divmod(distances.argmin(), distances.shape[1])
    vgtyp = int(ds.gppbfas.isel(y=argmin_y, x=argmin_x).values)
    albedo = constants.land_use_categories.get(vgtyp).get("albedo")
    return albedo


def parse_weather_code(
    accumulated_precipitation,
    freezing_rain,
    ice_pellets,
    lightning,
    rain,
    snow,
    pct_frozen_precipitation,
    visibility,
    wind_gust_speed,
    smoke,
):
    """
    Parse weather data into a 9-character string for energy plus use.
    see : https://bigladdersoftware.com/epx/docs/8-3/auxiliary-programs/energyplus-weather-file-epw-data-dictionary.html

    Parameters
    ----------
    # TODO: add arguments

    Returns
    ----------
    weather_code : str
        9-character string of weather data.
    """

    def code1_thunderstorms(lightning, wind_gusts):
        """
        possible values: 0,1,2,4,6,7,8,9
        default: 9

        0 = Thunderstorm – lightning and thunder. Wind gusts less than 25.7 m/s, and hail, if any, less than 1.9 cm diameter
        1 = Heavy or severe thunderstorm – frequent intense lightning and thunder. Wind gusts greater than 25.7 m/s and hail, if any, 1.9 cm or greater diameter
        2 = Report of tornado or waterspout (seemingly depricated?)
        4 = Moderate squall – sudden increase of wind speed by at least 8.2 m/s, reaching 11.3 m/s or more and lasting for at least 1 minute
        6 = Water spout (beginning January 1984)
        7 = Funnel cloud (beginning January 1984)
        8 = Tornado (beginning January 1984)

        """
        # TODO: need I worry about 2-8?
        if lightning:
            if wind_gusts > 25.7:
                code = "1"
            else:
                code = "0"
        else:
            code = "9"
        return code

    def code2_rain(accumulated_precipitation, freezing_rain):
        """0 = Light rain
        1 = Moderate rain
        2 = Heavy rain
        3 = Light rain showers
        4 = Moderate rain showers
        5 = Heavy rain showers
        6 = Light freezing rain
        7 = Moderate freezing rain
        8 = Heavy freezing rain
        9 = None

        Notes: Light = up to 0.25 cm per hour ()
        Moderate = 0.28 to 0.76 cm per hour
        Heavy = greater than 0.76 cm per hour

        TODO: not sure the distinction between rain and rain showers"""
        code = "9"
        if accumulated_precipitation > 0:
            if not freezing_rain:
                if accumulated_precipitation < 2.5:
                    code = "0"
                elif accumulated_precipitation < 7.6:
                    code = "1"
                else:
                    code = "2"
            else:
                if accumulated_precipitation < 2.5:
                    code = "6"
                elif accumulated_precipitation < 7.6:
                    code = "7"
                else:
                    code = "8"
        return code

    def code3_combined_rain(
        accumulated_precipitation,
        pct_freezing_precipitation,
        visibility,
        wind_gust_speed,
    ):
        """
        0 = Light rain squalls
        1 = Moderate rain squalls
        3 = Light drizzle
        4 = Moderate drizzle
        5 = Heavy drizzle
        6 = Light freezing drizzle
        7 = Moderate freezing drizzle
        8 = Heavy freezing drizzle
        9 = None

        Notes: When drizzle or freezing drizzle occurs with other weather phenomena
        Light = up to 0.025 cm per hour
        Moderate = 0.025 to 0.051 cm per hour
        Heavy = greater than 0.051 cm per hour

        When drizzle or freezing drizzle occurs alone:
        Light = visibility 1 km or greater
        Moderate = visibility between 0.5 and 1 km
        Heavy = visibility 0.5 km or less

        TODO: distinction between a squall and drizzle? combined weather?"""
        code = 9
        # squalls
        if wind_gust_speed > 15:
            if accumulated_precipitation < 2.5:
                code = "0"
            else:
                code = "1"
        # drizzle
        if pct_freezing_precipitation <= 0:
            if visibility > 1:
                code = "3"
            elif visibility > 0.5:
                code = "4"
            else:
                code = "5"
        else:  # freezing drizzle
            if visibility > 1:
                code = "6"
            elif visibility > 0.5:
                code = "7"
            else:
                code = "8"
        return code

    def code4_snow_ice(accumulated_precipitation, ice_pellets):
        """0 = Light snow
        1 = Moderate snow
        2 = Heavy snow
        3 = Light snow pellets
        4 = Moderate snow pellets
        5 = Heavy snow pellets
        6 = Light ice crystals
        7 = Moderate ice crystals
        8 = Heavy ice crystals
        9 = None

        Notes: Beginning in April 1963, any occurrence of ice crystals is recorded as a 7.
        TODO: distinction between snow pellets and ice crystals?"""
        code = "9"
        if ice_pellets:
            code = "7"
        else:
            if accumulated_precipitation < 2.5:
                code = "0"
            elif accumulated_precipitation < 7.6:
                code = "1"
            else:
                code = "2"
        return code

    def code5_snow_showers(accumulated_precipitation, wind_gust_speed, ice_pellets):
        """0 = Light snow
        1 = Moderate snow showers
        2 = Heavy snow showers
        3 = Light snow squall
        4 = Moderate snow squall
        5 = Heavy snow squall
        6 = Light snow grains
        7 = Moderate snow grains
        9 = None"""
        code = "9"
        if ice_pellets:
            if accumulated_precipitation < 2.5:
                code = "6"
            else:
                code = "7"
        # squalls
        elif wind_gust_speed > 15:
            if accumulated_precipitation < 2.5:
                code = "3"
            elif accumulated_precipitation < 7.6:
                code = "4"
            else:
                code = "5"
        # snow
        else:
            if accumulated_precipitation < 2.5:
                code = "0"
            elif accumulated_precipitation < 7.6:
                code = "1"
            else:
                code = "2"
        return code

    def code6_sleet(accumulated_precipitation):
        """0 = Light ice pellet showers
        1 = Moderate ice pellet showers
        2 = Heavy ice pellet showers
        4 = Hail
        9 = None

        Notes: Prior to April 1970, ice pellets were coded as sleet.
        Beginning in April 1970, sleet and small hail were redefined as ice pellets and are coded as 0, 1, or 2.
        """
        code = "9"
        if accumulated_precipitation < 2.5:
            code = "0"
        elif accumulated_precipitation < 7.6:
            code = "1"
        else:
            code = "2"
        return code

    # def code7_fog_dust_sand():
    #     """0 = Fog
    #     1 = Ice fog
    #     2 = Ground fog
    #     3 = Blowing dust
    #     4 = Blowing sand
    #     5 = Heavy fog
    #     6 = Glaze (beginning 1984)
    #     7 = Heavy ice fog (beginning 1984)
    #     8 = Heavy ground fog (beginning 1984)
    #     9 = None

    #     Notes: These values recorded only when visibility is less than 11 km."""
    #     # NOTE: not used as these aren't measured
    #     return

    def code8_smoke_haze(smoke):
        """
        0 = Smoke
        1 = Haze
        2 = Smoke and haze
        3 = Dust
        4 = Blowing snow
        5 = Blowing spray
        6 = Dust storm (beginning 1984)
        7 = Volcanic ash
        9 = None

        Notes: These values recorded only when visibility is less than 11 km."""
        # NOTE: not used as these aren't measured
        code = 9
        if smoke > 5e-4:  # kg/m^3
            code = 1
        elif smoke > 1e-5:
            code = 0
        return code

    # def code9_ice_pellets():
    #     """
    #     0 = Light ice pellets
    #     1 = Moderate ice pellets
    #     2 = Heavy ice pellets
    #     9 = None
    #     """
    #     # Note: same as code6, use that
    #     return

    weather_code = list("999999999")

    # conditions

    # process each code
    # code 1
    if lightning:
        weather_code[0] = code1_thunderstorms(lightning, wind_gust_speed)

    # codes 2-6, 9
    if accumulated_precipitation > 0:
        # code 2 - 3
        if rain:
            weather_code[1] = code2_rain(accumulated_precipitation, freezing_rain)
            weather_code[2] = code3_combined_rain(
                accumulated_precipitation,
                pct_frozen_precipitation,
                visibility,
                wind_gust_speed,
            )

        # code 4
        if snow:
            weather_code[3] = code4_snow_ice(accumulated_precipitation, ice_pellets)
            weather_code[4] = code5_snow_showers(
                accumulated_precipitation, wind_gust_speed, ice_pellets
            )

        if ice_pellets:
            ice_code = code6_sleet(accumulated_precipitation)
            weather_code[5] = ice_code
            weather_code[8] = ice_code
    if smoke > 1e5:
        weather_code[7] = code8_smoke_haze(smoke)

    return "".join(weather_code)
