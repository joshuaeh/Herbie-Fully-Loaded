# GNOMY

A Python package for weather data gathering for further use.

---

## Quick Start



## Info

The name "Gnomy" (while a working name) comes from the initial name of the effort
to create a _"NOAA-based AMY file"_. After being said repeatedly, "NOAA AMY" began
to mumble together into _"no-my"_ or gnomy.

Gnomy began with my personal need to collect actual measured weather data rather
than typical meteorological year data in order to fit home energy models to measured
data. Having worked with the [Herbie python package](https://github.com/blaylockbk/Herbie),
this package has the goal to make parallelized collection of weather data and export
in the required format more accessible.

## AMY Parameters

An epw file consists of 8 rows of header information followed by the body of the data with 34 columns

### epw Header Information

Each line contains contextual information about the location and weather. See [Climate Analytics](https://designbuilder.co.uk/cahelp/Content/EnergyPlusWeatherFileFormat.htm) for more information on each field specifically.

1. Location
2. Design conditions
3. Typical and extreme periods
4. ground temperatures
5. Holidays and daylight savings
6. Comments 1
7. Comments 2
8. Data Periods

### epw Data Body

The columns of an AMY file are not labeled within the file itself. [The energy plus documentation](https://bigladdersoftware.com/epx/docs/8-3/auxiliary-programs/energyplus-weather-file-epw-data-dictionary.html) identifies many if the fields of interest.

Below is a table of the values used, their limits, conventions for missing data, and the source of the data using gnomy. Values in **bold** are used by EnergyPlus

| Field | Name | Units | Min. | Max. | Missing | Used in Energy Plus | gnomy source |
|-------|------|-------|------|------|---------|---------------------|--------------|
|   1   | Year |       |      |      |         |                     |              |
|   2   | Month |       |      |      |         |                     |              |
|   3   | Hour |       |      |      |         |                     |              |
| 4 | Minute |  |  |  |  |  |  |
| 5 | Data Source and Uncertainty |  |  |  |  |  |  |
| 6 | **Dry Bulb Temerature** | C | -70 | 70 | 99.9 | Yes | NOAA analysis air temperature 2m above ground |
| 7 | **Dew Point Temerature** | C | -70 | 70 | 99.9 | Yes | NOAA analysis dew point 2m above ground |
| 8 | **Relative Humidity** |  | 0 | 110 | 999 | Yes | NOAA analysis relative humidity 2m above ground |
| 9 | **Atmospheric Station Pressure** | Pa | 31,000 | 120,000 | 999,999 | Yes | NOAA Analysis surface pressure |
| 10 | Extraterrestrial Horizontal Radiation | Wh/m$^2$ |0 |  | 9,999 |  | Calculated from Solar Zenith Angle and the solar constant. See [1] |
| 11 | Extraterrestrial Direct Normal Radiation | Wh/m$^2$ | 0 |  | 9,999 |  | Calculated from the day of year and the solar constant. See: [2] |
| 12 | **Horizontal Infrared Radiation Intensity** | Wh/m$^2$ | 0 |  | 9,999 | Yes | Calculated from Sky Emissivity and dry bulb temperature. See [3] |
| 13 | Global Horizontal Radiation | Wh/m$^2$ | 0 |  | 9,999 |  | Calculated from DNI, DHI, and Solar Zenith Angle. See [4] |
| 14 | **Direct Normal Radiation** | Wh/m$^2$ | 0 |  | 9,999 | Yes | NOAA Analysis Visible Beam Downward Solar Flux |
| 15 | **Diffuse Horizontal Radiation** | Wh/m$^2$ | 0 |  | 9,999 | Yes | NOAA Analysis Visible Diffuse Downward Solar Flux |
| 16 | Global Horizontal Illuminance | lux |  |  | >=999,900 |  | Estimated using Irradiance. See [5] |
| 17 | Direct Normal Illuminance | lux |  |  | >=999,900 |  | Estimated using Irradiance. See [5] |
| 18 | Diffuse Horizontal Illuminance | lux |  |  | >=999,900 |  | Estimated using Irradiance. See [5] |
| 19 | Zenith Luminance | Cd/m$^2$ |  |  | >=9999 |  | Estimated using Irradiance. See [5] |
| 20 | **Wind Direction** | Degrees | 0 | 360 | 999 | Yes | NOAA Analysis Wind Speed in U and V directions converted to compass directions. See [6] |
| 21 | **Wind Speed** | m/s | 0 | 40 | 999 | Yes | NOAA Analysis Wind Speeds in U and V components used for total wind speed |
| 22 | Total Sky Cover |  | 0 | 10 | 99 |  | NOAA Analysis Total Sky Cover |
| 23 | **Opaque Sky Cover** |  | 0 | 10 | 99 | Used if horizontal IR intensity is missing | Calculated by estimating sky cover that is only Low or Medium Cloud Cover or 50% high cloud cover. See [7] |
| 24 | Visibility | km |  |  |  | 9,999 | NOAA Analysis Visibility |
| 25 | Ceiling Height | m |  |  |  | 99,999 | NOAA Analysis Geopotential Height |
| 26 | **Present Weather Observation** | Boolean |  |  |  | Yes, primarily to know if exterior surfaces are wet or frozen. |  |
| 27 | **Present Weather Codes** | str |  |  |  | Yes, primarily to know if exterior surfaces are wet or frozen | Estimated using precipitation forecasts. See [8] |
| 28 | **Precipitable Water** | mm |  |  | 999 | Yes | NOAA Analysis Precipitable Water |
| 29 | Aerosol Optical Depth | thousandths |  |  | 0.999 |  | NOAA Analysis Aeorosol Optical Thickness |
| 30 | **Snow Depth** | cm |  |  | 999 | Yes | NOAA Analysis Snow Depth |
| 31 | Days Since Last Snowfall |  |  |  | 99 |  | Calculated after collecting precipitation data |
| 32 | Albedo |  |  |  | 999 |  | Estimated using the land use category. See [9] |
| 33 | Liquid Precipitation Depth | mm |  |  | 999 |  | NOAA *1 hour forecast* Total Precipitation. See [9] |
| 34 | Liquid Precipitation Quantity | hr |  |  | 99 |  | Calculated. The interval 33 accumulates over, which is 1 hour. |
