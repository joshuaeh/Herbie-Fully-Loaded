"""constants for AMY generation"""
# imports

# Constants
## Default Values


## HRRR stuff
HRRR_first_year = 2014  # https://rapidrefresh.noaa.gov/hrrr/ notes archives go back to 2014
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
    "dry bulb temperature [C]": {"units":"C", "position":6, "min": -70, "max": 70, "missing":99.9, "ep_used" : True},
    "dew point temperature [C]": {"units":"C", "position":7, "min": -70, "max": 70, "missing":99.9, "ep_used" : True},
    "relative humidity [%]": {"units":"%", "position":8, "min": 0, "max": 110, "missing":999, "ep_used" : True},
    "atmospheric station pressure [Pa]": {"units":"Pa", "position":9, "min": 31_000, "max": 120_000, "missing":999_999, "ep_used" : True},
    "extraterrestrial horizontal radiation [Wh/m^2]": {"units":"Wh/m^2", "position":10, "min": 0, "missing":9_999, "ep_used" : False},
    "extraterrestrial direct normal radiation [Wh/m^2]": {"units":"Wh/m^2", "position":11, "min": 0, "missing":9_999, "ep_used" : False},
    "horizontal infrared radiation intensity [Wh/m^2]": {"units":"Wh/m^2", "position":12, "min": 0, "missing":9_999, "ep_used" : True},
    "global horizontal radiation [Wh/m^2]": {"units":"Wh/m^2", "position":13, "min": 0, "missing":9_999, "ep_used" : False},
    "direct normal radiation [Wh/m^2]": {"units":"Wh/m^2", "position":14, "min": 0, "missing":9_999, "ep_used" : True},
    "diffuse horizontal radiation [Wh/m^2]": {"units":"Wh/m^2", "position":15, "min": 0, "missing":9_999, "ep_used" : True},
    "global horizontal illuminance [lux]": {"units":"lux", "position":16, "min": 0, "max": 999_998, "missing":999_999, "ep_used" : False},
    "direct normal illuminance [lux]": {"units":"lux", "position":17, "min": 0, "max": 999_998, "missing":999_999, "ep_used" : False},
    "diffuse horizontal illuminance [lux]": {"units":"lux", "position":18, "min": 0, "max": 999_998, "missing":999_999, "ep_used" : False},
    "zenith luminance [cd/m^2]": {"units":"cd/m^2", "position":19, "min": 0, "max": 9_998, "missing":9_999, "ep_used" : False},
    "wind direction [deg]": {"units":"degrees", "position":20, "min": 0, "max": 360, "missing":999, "ep_used" : True},
    "wind speed [m/s]": {"units":"m/s", "position":21, "min": 0, "max": 40, "missing":999, "ep_used" : True},
    "total sky cover [tenths]": {"units":"tenths", "position":22, "min": 0, "max": 10, "missing":99, "ep_used" : False},
    "opaque sky cover [tenths]": {"units":"tenths", "position":23, "min": 0, "max": 10, "missing":99, "ep_used" : False},
    "visibility [km]": {"units":"km", "position":24, "missing":999, "ep_used" : False},
    "ceiling height [m]": {"units":"m", "position":25, "missing":99_999, "ep_used" : False},
    "present weather observation": {"units":"code", "position":26, "missing":9, "ep_used" : True},
    "present weather codes": {"units":"code", "position":27, "missing":"999999999", "ep_used" : True},
    "precipitable water [mm]": {"units":"mm", "position":28, "missing":999, "ep_used" : False},
    "aerosol optical depth [thousandths]": {"units":"thousandths", "position":29, "missing":0.999, "ep_used" : False},
    "snow depth [cm]": {"units":"cm", "position":30, "missing":999, "ep_used" : True},
    "days since last snowfall": {"units":"days", "position":31, "missing":99, "ep_used" : False},
    "albedo [nondim]": {"units":"none", "position":32, "missing":999, "ep_used" : False},
    "liquid precipitation depth [mm]": {"units":"mm", "position":33, "missing":999, "ep_used" : False},
    "liquid precipitation quantity [hr]": {"units":"hours", "position":34, "missing":99, "ep_used" : False}
}

_body_column_order = [] # TODO sort with "position" in variable_properties values
_grib_variables_preprocessing = {
    # variable name: {search_string, byte_start, byte_end, location_indices}
    # LAND USE TYPE FOR ALBEDO
    "vegetation type" : {"searchstring" : ":VGTYP:surface:anl", "variable_name" : "gppbfas"},  # [0-20]
}

_grib_variables_0h = {
    # variable name: {search_string, byte_start, byte_end, location_indices}
    # PRIMARY VARIABLES
    "dry bulb temperature" : {"searchstring" : ":TMP:2 m above ground:anl", "variable_name" : "t2m"},  # [K]
    "dew point temperature" : {"searchstring" : ":DPT:2 m above ground:anl", "variable_name" : "d2m"},  # [K]
    "relative humidity" : {"searchstring" : ":RH:2 m above ground:anl", "variable_name" : "r2"},  # [%]
    "atmospheric station pressure" : {"searchstring" : ":PRES:surface:anl", "variable_name" : "sp"},  # [Pa]
    "direct normal radiation" : {"searchstring" : ":VBDSF:surface:anl", "variable_name" : "vbdsf"},  # [W/m^2]
    "diffuse horizontal radiation" : {"searchstring" : ":VDDSF:surface:anl", "variable_name" : "vddsf"},  # [W/m^2]
    "wind speed u": {"searchstring" : ":UGRD:10 m above ground:anl", "variable_name" : "u10"},  # [m/s]
    "wind speed v": {"searchstring": ":VGRD:10 m above ground:anl", "variable_name" : "v10"},  # [m/s]
    "total sky cover": {"searchstring" : ":TCDC:entire atmosphere:anl", "variable_name" : "tcc"},  # [%]
    "visibility": {"searchstring" : ":VIS:surface:anl", "variable_name" : "vis"},  # [m]
    "ceiling height": {"searchstring" : ":HGT:cloud ceiling:anl", "variable_name" : "gh"},  # [gpm]
    "precipitable water": {"searchstring" : ":PWAT:", "variable_name" : "pwat"},  # [kg/m^2]
    "aerosol optical depth": {"searchstring" : ":AOTK:", "variable_name" : "unknown"},  # [Numeric] optical thickness and depth used interchangably
    "snow depth": {"searchstring" : ":SNOD:surface:anl", "variable_name" : "sde"},  # [m]
    # OTHER VARIABLES NEEDED FOR WEATHER CODES
    "wind gust speed" : {"searchstring" : ":GUST:surface:anl", "variable_name" : "gust"},  # [m/s]
    "snow cover" : {"searchstring" : ":SNOWC:surface:anl", "variable_name" : "snowc"},  # [%]
    "surface temperature" : {"searchstring" : ":TMP:surface:anl", "variable_name" : "t"},  # [K]
    "low cloud cover" : {"searchstring" : ":LCDC:low cloud layer:anl", "variable_name" : "lcc"},  # [%]
    "mid cloud cover" : {"searchstring" : ":MCDC:middle cloud layer:anl", "variable_name" : "mcc"},  # [%]
    "high cloud cover" : {"searchstring" : ":HCDC:high cloud layer:anl", "variable_name" : "hcc"},  # [%]
    "near surface smoke" : {"searchstring" : "MASSDEN:8 m above ground:anl", "variable_name" : "mdens"},  # [kg/m3]
    "vertically integrated smoke" : {"searchstring" : ":COLMD:", "variable_name" : "tc_mdens"},  # [kg/m3]
}

_grib_variables_1h = {
    "liquid precipitation depth" : {"searchstring":":APCP:", "variable_name" : "tp"},  # [kg/m^2]
    # OTHER VARIABLES NEEDED FOR WEATHER CODES # [m/s]
    "lightning" : {"searchstring" : ":LTNG:", "variable_name" : "ltng"},  # [0,1]
    "percent frozen precipitation" : {"searchstring" : ":CPOFP:", "variable_name" : "cpofp"},  # [%]
    "precipitation rate" : {"searchstring" : ":PRATE:", "variable_name" : "prate"},  # [kg/m^2/s]
    "categorical snow" : {"searchstring" : ":CSNOW:", "variable_name" : "csnow"},  # [0,1]
    "categorical ice pellets" :  {"searchstring" : ":CICEP:", "variable_name" : "cicep"},  # [0,1]
    "categorical rain" : {"searchstring" : ":CRAIN:", "variable_name" : "crain"},  # [0,1]
    "categorical freezing rain" : {"searchstring" : ":CFRZR:", "variable_name" : "cfrzr"},  # [0,1]
}

_grib_variable_groups_0h = [
    ["total sky cover"],
    ["aerosol optical depth", "precipitable water", "vertically integrated smoke"],
    ["ceiling height"],
    ["wind speed u", "wind speed v"],
    ["dry bulb temperature", "dew point temperature", "relative humidity"],
    ["near surface smoke"],
    ["high cloud cover"],
    ["mid cloud cover"],
    ["low cloud cover"],
    ["surface temperature", "atmospheric station pressure", "visibility", "snow depth",
     "snow cover", "wind gust speed", "direct normal radiation", "diffuse horizontal radiation"]
]

_grib_variable_groups_1h = [
    ["lightning"],
    ["liquid precipitation depth", "percent frozen precipitation", "precipitation rate",
    "categorical snow",  "categorical ice pellets", "categorical rain", "categorical freezing rain"]
]

_primary_variables = ["dry bulb temperature", "dew point temperature", "relative humidity", 
    "atmospheric station pressure", "direct normal radiation", "diffuse horizontal radiation", 
    "wind speed u", "wind speed v", "total sky cover", "visibility", "ceiling height",
    "precipitable water", "aerosol optical depth", "snow depth", "liquid precipitation depth"]  
_secondary_variables = ["global horizontal radiation", "global horizontal illuminance", "horizontal infrared radiation intensity"]
_post_process_variables = ["global horizontal illuminance", "direct normal illuminance", "diffuse horizontal illuminance", "zenith luminance", "days since last snowfall", "albedo", "liquid precipitation quantity"]
