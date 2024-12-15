# BiciMad Project README

## Introduction
The BiciMad project focuses on analyzing the usage data of Madrid's electric bicycle service, BiciMAD, utilizing publicly available data from the EMT (Madrid Transport Authority). The data includes information on bike trips, such as trip durations, start and end locations, and more, collected from April 2019 to February 2023. However, the dataset format is standardized for use with the module only from June 2021 to February 2023.

A Python module has been developed to manage the BiciMad data efficiently. Based on the `Urlemt` and `BiciMad` classes, this module downloads data from the official web sources and creates pandas DataFrames, making it easier to manipulate and analyze the dataset. By leveraging DataFrames, users can quickly perform operations such as filtering, grouping, and aggregating data, significantly enhancing data handling efficiency. Additionally, several methods have been implemented to perform specific data operations quickly.

## Data Source
The datasets are available on the EMT's open data portal:
- General portal: [EMT Open Data Portal](https://opendata.emtmadrid.es/Home)
- Specific BiciMAD data: [BiciMAD Usage Data](https://opendata.emtmadrid.es/Datos-estaticos/Datos-generales-(1))

The data is organized in ZIP files, each containing a CSV file named in the format: `trips_YY_MM_monthName.csv`, where `YY` represents the year, `MM` represents the month, and `monthName` is the English name of the month.

## Metadata
Each CSV file contains the following key fields:
- **date**: Date of the trip.
- **idbike**: Unique identifier for the bicycle used.
- **fleet**: Bicycle fleet type.
- **trip_minutes**: Duration of the trip in minutes.
- **geolocation_unlock**: Geographical coordinates of the starting point.
- **address_unlock**: Address where the bike was unlocked.
- **unlock_date**: Exact date and time when the trip started.
- **locktype**: Lock status before the trip (e.g., docked or free-floating).
- **unlocktype**: Lock status after the trip.
- **geolocation_lock**: Geographical coordinates of the endpoint.
- **address_lock**: Address where the bike was locked after the trip.
- **lock_date**: Exact date and time when the trip ended.
- **station_unlock**: Number of the station where the bike was unlocked.
- **dock_unlock**: Dock number at the unlocking station.
- **unlock_station_name**: Name of the unlocking station.
- **station_lock**: Number of the station where the bike was locked.
- **dock_lock**: Dock number at the locking station.
- **lock_station_name**: Name of the locking station.

## Usage

### UrlEMT Class
The `UrlEMT` class is responsible for managing URLs associated with the BiciMAD datasets. Its main functionalities include:
- **`select_valid_urls()`**: Retrieves and returns a set of valid URLs for BiciMAD usage data from the EMT website.
- **`get_url(month: int, year: int) -> str`**: Returns the URL corresponding to the usage data for the specified month and year. Raises a `ValueError` if no valid URL exists for the specified month and year.
- **`get_csv(month: int, year: int) -> TextIO`**: Downloads and returns a CSV file object containing the data for the specified month and year.

### BiciMad Class
The `BiciMad` class encapsulates the usage data for a specific month and includes methods for:
- **`get_data(month: int, year: int) -> pd.DataFrame`**: Retrieves a DataFrame with the usage data for the specified month and year, cleaning it in the process.
- **`clean()`**: Cleans the DataFrame by removing rows with all NaN values and converting specific columns to string types.
- **`resume()`**: Returns a summary of the trip data in a pandas Series, including the total number of trips and the most popular unlocking station.

## Tests
Unit tests are included to verify the functionality of the classes, ensuring that all methods behave as expected.

