"""Common constants and utilities for ease of use."""

# imports
import logging
logger = logging.getLogger(__name__)

import datetime
import os

from herbie import Herbie
import pandas as pd
import pytz

# constants
## locations
san_antonio = {
    "latitude" : 29.25,  # N
    "longitude" :   360-98.31,  # W
    "tz" : pytz.timezone('America/Chicago'),
    "begin_date" : datetime.datetime(2022,1,1),
    "end_date" : datetime.datetime(2023,1,1)
}

## HRRR stuff
land_use_categories = {
    # category number: {description, albedo}
    # for use categories see https://www2.mmm.ucar.edu/wrf/users/wrf_users_guide/build/html/wps.html#table-2-igbp-modified-modis-20-category-land-use-categories
    # for albedo see: https://doi.org/10.1175/1520-0442(2003)016<1511:UIRFDT>2.0.CO;2
    # https://www.pvsyst.com/help/albedo.htm, https://en.wikipedia.org/wiki/Albedo
    #
    1 : {"description" : "Evergreen Needleleaf Forest", "albedo" : 0.12},   
    2 : {"description" : "Evergreen Broadleaf Forest", "albedo" : 0.12},
    3 : {"description" : "Deciduous Needleleaf Forest", "albedo" : 0.15},
    4 : {"description" : "Deciduous Broadleaf Forest", "albedo" : 0.15},
    5 : {"description" : "Mixed Forests", "albedo" : 0.12},
    6 : {"description" : "Closed Shrublands", "albedo" : 0.18},
    7 : {"description" : "Open Shrublands", "albedo" : 0.15},
    8 : {"description" : "Woody Savannas", "albedo" : 0.18},
    9 : {"description" : "Savannas", "albedo" : 0.12},
    10 : {"description" : "Grasslands", "albedo" : 0.20},
    11 : {"description" : "Permanent Wetlands", "albedo" : 0.18},  # ? albedo
    12 : {"description" : "Croplands", "albedo" : 0.18},
    13 : {"description" : "Urban and Built-up", "albedo" : 0.18},
    14 : {"description" : "Cropland/Natural Vegetation Mosaic", "albedo" : 0.18},
    15 : {"description" : "Snow and Ice", "albedo" : 0.8},
    16 : {"description" : "Barren or Sparsely Vegetated", "albedo" : 0.18},
    17 : {"description" : "Water", "albedo" : 0.08},
    18 : {"description" : "Wooded Tundra", "albedo" : 0.18},
    19 : {"description" : "Mixed Tundra", "albedo" : 0.18},
    20 : {"description" : "Barren Tundra", "albedo" : 0.18},
    21 : {"description" : "Lakes", "albedo" : 0.08},
}

variable_properties = {
    # variable name: {min, max, default_value, grib_byte_range, grib_location_indices}
    "year": {"units":"years", "position":0, "ep_used" : False},
    "month": {"units":"months", "position":1, "ep_used" : False},
    "day": {"units":"day", "position":2, "ep_used" : False},
    "hour": {"units":"hours", "position":3, "ep_used" : False},
    "minute": {"units":"minutes", "position":4, "ep_used" : False},
    "data_flags": {"units":"none", "position":5, "ep_used" : False},  # data source and uncertainty flags
    "dry bulb temperature": {"units":"C", "position":6, "min": -70, "max": 70, "missing":99.9, "ep_used" : True},
    "dew point temperature": {"units":"C", "position":7, "min": -70, "max": 70, "missing":99.9, "ep_used" : True},
    "relative humidity": {"units":"%", "position":8, "min": 0, "max": 110, "missing":999, "ep_used" : True},
    "atmospheric station pressure": {"units":"Pa", "position":9, "min": 31_000, "max": 120_000, "missing":999_999, "ep_used" : True},
    "extraterrestrial horizontal radiation": {"units":"Wh/m^2", "position":10, "min": 0, "missing":9_999, "ep_used" : False},
    "extraterrestrial direct normal radiation": {"units":"Wh/m^2", "position":11, "min": 0, "missing":9_999, "ep_used" : False},
    "horizontal infrared radiation intensity": {"units":"Wh/m^2", "position":12, "min": 0, "missing":9_999, "ep_used" : True},
    "global horizontal radiation": {"units":"Wh/m^2", "position":13, "min": 0, "missing":9_999, "ep_used" : False},
    "direct normal radiation": {"units":"Wh/m^2", "position":14, "min": 0, "missing":9_999, "ep_used" : True},
    "diffuse horizontal radiation": {"units":"Wh/m^2", "position":15, "min": 0, "missing":9_999, "ep_used" : True},
    "global horizontal illuminance": {"units":"lux", "position":16, "min": 0, "max": 999_998, "missing":999_999, "ep_used" : False},
    "direct normal illuminance": {"units":"lux", "position":17, "min": 0, "max": 999_998, "missing":999_999, "ep_used" : False},
    "diffuse horizontal illuminance": {"units":"lux", "position":18, "min": 0, "max": 999_998, "missing":999_999, "ep_used" : False},
    "zenith luminance": {"units":"cd/m^2", "position":19, "min": 0, "max": 9_998, "missing":9_999, "ep_used" : False},
    "wind direction": {"units":"degrees", "position":20, "min": 0, "max": 360, "missing":999, "ep_used" : True},
    "wind speed": {"units":"m/s", "position":21, "min": 0, "max": 40, "missing":999, "ep_used" : True},
    "total sky cover": {"units":"tenths", "position":22, "min": 0, "max": 10, "missing":99, "ep_used" : False},
    "opaque sky cover": {"units":"tenths", "position":23, "min": 0, "max": 10, "missing":99, "ep_used" : False},
    "visibility": {"units":"km", "position":24, "missing":999, "ep_used" : False},
    "ceiling height": {"units":"m", "position":25, "missing":99_999, "ep_used" : False},
    "present weather observation": {"units":"code", "position":26, "missing":9, "ep_used" : True},
    "present weather codes": {"units":"code", "position":27, "missing":"999999999", "ep_used" : True},
    "precipitable water": {"units":"mm", "position":28, "missing":999, "ep_used" : False},
    "aerosol optical depth": {"units":"thousandths", "position":29, "missing":0.999, "ep_used" : False},
    "snow depth": {"units":"cm", "position":30, "missing":999, "ep_used" : True},
    "days since last snowfall": {"units":"days", "position":31, "missing":99, "ep_used" : False},
    "albedo": {"units":"none", "position":32, "missing":999, "ep_used" : False},
    "liquid precipitation depth": {"units":"mm", "position":33, "missing":999, "ep_used" : False},
    "liquid precipitation quantity": {"units":"hours", "position":34, "missing":99, "ep_used" : False}
}

_body_column_order = [] # TODO sort with "position" in variable_properties values
_grib_variables_sfc = {
    # variable name: {search_string, byte_start, byte_end, location_indices}
    # PRIMARY VARIABLES
    "dry bulb temperature" : {"searchstring" : ":TMP:2 m above ground:anl"},  # [K]
    "dew point temperature" : {"searchstring" : ":DPT:2 m above ground:anl"},  # [K]
    "relative humidity" : {"searchstring" : ":RH:2 m above ground:anl"},  # [%]
    "atmospheric station pressure" : {"searchstring" : ":PRES:surface:anl"},  # [Pa]
    "direct normal radiation" : {"searchstring" : ":VBDSF:surface:anl"},  # [W/m^2]
    "diffuse horizontal radiation" : {"searchstring" : ":VDDSF:surface:anl"},  # [W/m^2]
    "wind speed u": {"searchstring" : ":UGRD:10 m above ground:anl"},  # [m/s]
    "wind speed v": {"searchstring": ":VGRD:10 m above ground:anl"},  # [m/s]
    "total sky cover": {"searchstring" : ":TCDC:entire atmosphere:anl"},  # [%]
    "visibility": {"searchstring" : ":VIS:surface:anl"},  # [m]
    "ceiling height": {"searchstring" : ":HGT:cloud ceiling:anl"},  # [gpm]
    "precipitable water": {"searchstring" : ":PWAT:entire atmosphere (considered as a single layer)"},  # [kg/m^2]
    "aerosol optical depth": {"searchstring" : ":AOTK:entire atmosphere (considered as a single layer)"},  # [Numeric] optical thickness and depth used interchangably
    "snow depth": {"searchstring" : ":SNOD:surface:anl"},  # [m]
    "liquid precipitation depth" : {"searchstring":":APCP:surface:0-0 day acc fcst"},  # [kg/m^2]
    # OTHER VARIABLES NEEDED FOR WEATHER CODES
    "wind gust speed" : {"searchstring" : ":GUST:surface:anl"},  # [m/s]
    "lightning" : {"searchstring" : ":LTNG:entire atmosphere:anl"},  # [0,1]
    "snow cover" : {"searchstring" : ":SNOWC:surface:anl"},  # [%]
    "surface temperature" : {"searchstring" : ":TMP:surface:anl"},  # [K]
    "percent frozen precipitation" : {"searchstring" : ":CPOFP:surface:anl"},  # [%]
    "precipitation rate" : {"searchstring" : ":PRATE:surface:anl"},  # [kg/m^2/s]
    "categorical snow" : {"searchstring" : ":CSNOW:surface:anl"},  # [0,1]
    "categorical ice pellets" :  {"searchstring" : ":CICEP:surface:anl"},  # [0,1]
    "categorical rain" : {"searchstring" : ":CRAIN:surface:anl"},  # [0,1]
    "categorical freezing rain" : {"searchstring" : ":CFRZR:surface:anl"},  # [0,1]
    "low cloud cover" : {"searchstring" : ":LCDC:low cloud layer:anl"},  # [%]
    "mid cloud cover" : {"searchstring" : ":MCDC:middle cloud layer:anl"},  # [%]
    "high cloud cover" : {"searchstring" : ":HCDC:high cloud layer:anl"},  # [%]
    "near surface smoke" : {"searchstring" : "MASSDEN:8 m above ground:anl"},  # [kg/m3]
    "vertically integrated smoke" : {"searchstring" : ":COLMD:entire atmosphere (considered as a single layer):anl"},  # [kg/m3]
    # LAND USE TYPE FOR ALBEDO
    "vegetation type" : {"searchstring" : ":VGTYP:surface:anl"},  # [0-20]
}
_primary_variables = ["dry bulb temperature", "dew point temperature", "relative humidity", 
    "atmospheric station pressure", "direct normal radiation", "diffuse horizontal radiation", 
    "wind speed u", "wind speed v", "total sky cover", "visibility", "ceiling height",
    "precipitable water", "aerosol optical depth", "snow depth", "liquid precipitation depth"]  
_secondary_variables = ["global horizontal radiation", "global horizontal illuminance", "horizontal infrared radiation intensity"]
_post_process_variables = ["global horizontal illuminance", "direct normal illuminance", "diffuse horizontal illuminance", "zenith luminance", "days since last snowfall", "albedo", "liquid precipitation quantity"]

# functions
# Radiation functions
# HOMER documentation was very helpful here
# see https://www.homerenergy.com/products/pro/docs/3.11/how_homer_calculates_the_radiation_incident_on_the_pv_array.html
# PVLib notebooks also good: https://notebook.community/pvlib/pvlib-python/docs/tutorials/irradiance
# NOTE: Holmgren cites recent lit for 1361 as solar constant. TODO find source
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

def cloud_cover_to_opaque_sky_cover(lcc, mcc, hcc, tcc):
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
    translucent_cloud_cover = max(tcc - lcc - mcc, 0)
    return tcc - translucent_cloud_cover * 0.3

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
    sky_emissivity : float
    
    References
    ----------
    [1] Walton, G.N. Thermal Analysis Research Program Reference Manual; US Department of Commerce, National Bureau of Standards: Washington, DC, USA, March 1983.
    [2] Clark, G.; Allen, C. The estimation of atmospheric radiation for clear and cloudy skies. In Proceedings of the 2nd National Passive Solar Conference (AS/ISES), Philadelphia, PA, USA, 16–18 March 1978; pp. 675–678.
    """
    return (0.787 + 0.767 * np.log(T_dew/273)) +\
        (0.0224 * opaque_sky_cover) -\
        0.0035 * opaque_sky_cover**2 +\
        0.00028 * opaque_sky_cover**3

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
    

def get_wind_direction(u, v):
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
    return 180 + (180 / np.pi) * np.arctan2(v,u) % 360

def get_wind_speed(u, v):
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
    return np.sqrt(u**2 + v**2)

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
            raise ValueError("T_dry and RH combination is not valid for this approximation")
        estimated_output = True
        
    # approximated fit
    if not estimated_output:
        T_wet = 20 * np.arctan(0.151_977 * (RH + 8.313_659)**0.5) +\
            np.arctan(T_dry + RH) -\
            np.arctan(RH - 1.676_331) -\
            0.003_918_38 * RH**1.5 * np.arctan(0.023_101 * RH) -\
            4.686_035
    else:
        T_wet = T_dry
    return T_wet + 273.15

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
    return "(" + mid_string + ")"

def get_grib_data(grib_dt, data_dir, search_string, longitude, latitude):
    try:
        data_path = os.path.join(data_dir, grib_dt.strftime("%Y%m%d%H.csv"))
        if not os.path.exists(data_path):
            logger.debug("JEH: Creating Herbie Object")
            H = Herbie(
                grib_dt,
                model='hrrr',
                product='sfc'
            )
            analysis_data = {}
            logger.debug("JEH: Using XARRAY")
            h_data = H.xarray(searchString=search_string)
            logger.debug("JEH: Finding Individual Data Values at location")
            for h_data_i in h_data:
                logger.debug("JEH: ----Individual dataset selected")
                h_data_i = h_data_i.drop_vars(["time", "step", "valid_time"])
                logger.debug("JEH: ----Locating nearest point")
                h_data_i = h_data_i.herbie.nearest_points((longitude, latitude))
                for data_var in list(h_data_i.data_vars)[:-1]:
                        logger.debug("JEH: --------Adding variable value at location")
                        analysis_data[data_var] = h_data_i[data_var].values[0]
            logger.debug("JEH: Creating Dataframe")
            df = pd.DataFrame(data=analysis_data, index=[grib_dt])
            logger.debug("JEH: Saving CSV")
            df.to_csv(data_path)
            logger.debug("JEH: Done")
            return df
    except Exception as e:
        print(e)
    return 

