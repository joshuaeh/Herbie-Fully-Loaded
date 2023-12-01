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

Below is a table of the values used, their limits, conventions for missing data, and the source of the data using gnomy

| Field | Name | Units | Min. | Max. | Missing | Used in Energy Plus | gnomy source |
|-------|------|-------|------|------|---------|---------------------|--------------|
|   1   | Year |       |      |      |         |                     |              |
|   2   | Month |       |      |      |         |                     |              |
|   3   | Hour |       |      |      |         |                     |              |
| 4 | Minute |  |  |  |  |  |  |
| 5 | Data Source and Uncertainty |  |  |  |  |  |  |
| 6 | Dry Bulb Temerature | C | -70 | 70 | 99.9 | Yes |  |
| 7 | Dew Point Temerature | C | -70 | 70 | 99.9 | Yes |  |
| 8 | Relative Humidity |  | 0 | 110 | 999 | Yes |  |
| 9 | Atmospheric Station Pressure | Pa | 31,000 | 120,000 | 999,999 | Yes |  |
| 10 | Extraterrestrial Horizontal Radiation | Wh/m$^2$ |0 |  | 9,999 |  |  |
| 11 | Extraterrestrial Direct Normal Radiation | Wh/m$^2$ | 0 |  | 9,999 |  |  |
| 12 | Horizontal Infrared Radiation Intensity | Wh/m$^2$ | 0 |  | 9,999 | Yes |  |
| 13 | Global Horizontal Radiation | Wh/m$^2$ | 0 |  | 9,999 |  |  |
| 14 | Direct Normal Radiation | Wh/m$^2$ | 0 |  | 9,999 | Yes |  |
| 15 | Diffuse Horizontal Radiation | Wh/m$^2$ | 0 |  | 9,999 | Yes |  |
| 16 | Global Horizontal Illuminance | lux |  |  | >=999,900 |  |  |
| 17 | Direct Normal Illuminance | lux |  |  | >=999,900 |  |  |
| 18 | Diffuse Horizontal Illuminance | lux |  |  | >=999,900 |  |  |
| 19 | Zenith Luminance | Cd/m$^2$ |  |  | >=9999 |  |  |
| 20 | Wind Direction | Degrees | 0 | 360 | 999 | Yes |  |
| 21 | Wind Speed | m/s | 0 | 40 | 999 | Yes |  |
| 22 | Total Sky Cover |  | 0 | 10 | 99 |  |  |
| 23 | Opaque Sky Cover |  | 0 | 10 | 99 | Used if horizontal IR intensity is missing |  |
| 24 | Visibility | km |  |  |  | 9,999 |  |
| 25 | Ceiling Height | m |  |  |  | 99,999 |  |
| 26 | Present Weather Observation |  |  |  |  | Yes, primarily to know if exterior surfaces are wet or frozen |  |
| 27 | Present Weather Codes |  |  |  |  | Yes, primarily to know if exterior surfaces are wet or frozen |  |
| 28 | Precipitable Water | mm |  |  | 999 | Yes |  |
| 29 | Aerosol Optical Depth | thousandths |  |  | 0.999 |  |  |
| 30 | Snow Depth | cm |  |  | 999 |  |  |
| 31 | Days Since Last Snowfall |  |  |  | 99 |  |  |
| 32 | Albedo |  |  |  | 999 |  |  |
| 33 | Liquid Precipitation Depth | mm |  |  | 999 |  |  |
| 34 | Liquid Precipitation Quantity | hr |  |  | 99 |  |  |
