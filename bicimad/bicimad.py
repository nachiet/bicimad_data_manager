import io
import pandas as pd
import re
import requests
import zipfile
from typing import TextIO


class UrlEMT:
    """
    Clase para manejar las urls de la página de la EMT y descargar la información sobre el uso de Bicimad.

    Atributos:
        EMT (str): URL base de la EMT.
        GENERAL (str): Ruta a los datos generales.
        _valid_urls (set): Conjunto de URLs válidas para los datos de los viajes.
    """

    EMT = 'https://opendata.emtmadrid.es/'
    GENERAL = "/Datos-estaticos/Datos-generales-(1)"


    def __init__(self) -> None:
        """
        Inicializa una instancia de la clase UrlEMT y selecciona las URLs válidas de la web para los datos de los viajes.
        """
        self._valid_urls = UrlEMT.select_valid_urls()


    @staticmethod
    def select_valid_urls() -> set:
        """
        Selecciona y devuelve un conjunto de urls válidas para los datos del uso de Bicimad.

        :returns: Conjunto de urls con los datos de uso de Bicimad.
        :raises ConnectionError: Si la solicitud HTTP no tiene éxito.
        """
        r = requests.get(f'{UrlEMT.EMT}{UrlEMT.GENERAL}')

        if r.status_code != 200:
            raise ConnectionError("No se pudo conectar con la página de la EMT.")

        def get_links(html_txt: str) -> set :
            """
           Devuelve un conjunto de enlaces válidos a partir de un texto html.

           :param html_txt: Texto html de la web que contiene las urls de uso Bicimad
           :return: Conjunto de urls con los datos de uso de Bicimad

           """
            valid_urls = set()

            urls_re = re.compile(r"(href=\")(?P<link>.*trips.*aspx)")

            for i in urls_re.finditer(html_txt):
                valid_urls.add(i.group('link'))

            return valid_urls

        return get_links(r.text)


    def get_url(self, month: int, year: int) -> str:
        """
        Devuelve la url correspondiente a los datos de uso del mes y año proporcionados.

        :param month: Mes del que se obtienen los datos.
        :param year: Año del que se obtienen los datos.
        :return: URL correspodiente al mes y año introducidos, en formato de texto.
        :raises: ValueError: Si los valores de mes y año no se corresponden con un enlace válido.
        """
        filename_re = re.compile(fr".*trips_{year}_{month:02}.*")

        for i in self._valid_urls:
            s = filename_re.search(i)
            if s:
                return s.group()

        raise ValueError(f" No existe un enlace para el mes {month} del año 20{year}. \n"
        "Los datos se encuentran disponibles para el periodo comprendido entre junio de 2021 y febrero de 2023.")


    def get_csv(self, month: int, year: int) -> TextIO:
        """
        Devuelve un objeto tipo archivo csv con los datos correspondientes al mes y año proporcionados.

        :param month: Mes del que se obtienen los datos.
        :param year: Año del que se obtienen los datos.
        :return: Objeto tipo archivo (TextIO) que contiene los datos solicitados en formato csv.
        """
        url = self.get_url(month, year)

        r = requests.get(f'{UrlEMT.EMT}{url}')

        if r.status_code != 200:
            raise ConnectionError("No se pudo conectar con la página de la EMT.")

        content = io.BytesIO(r.content)
        zfile = zipfile.ZipFile(content)

        filename_re = re.compile(r"(trips.*)-")
        filename = filename_re.search(url).group(1) + ".csv"

        with zfile.open(filename) as f:
            contents = f.read().decode('utf-8')
            csv = io.StringIO(contents)

        return csv


class BiciMad:
    """
        Clase para manejar los datos de los viajes en bicicletas de Bicimad.

        Atributos:
            _month (int): Mes del que se obtienen los datos.
            _year (int): Año del que se obtienen los datos.
            _data (pd.DataFrame): DataFrame que contiene la información de los viajes.
        """


    def __init__(self, month: int, year: int) -> None:
        """
        Inicializa una instancia de la clase Bicimad.

        :param int month: Mes del que se obtienen los datos.
        :param int year: Año del que se obtienen los datos.
        """
        self._month = month
        self._year = year
        self._data = BiciMad.get_data(month, year)


    @staticmethod
    def get_data(month: int, year: int) -> pd.DataFrame:
        """
        Devuelve un DataFrame con los datos de los viajes de Bicimad para el mes y año proporcionados.

        :param month: Mes del que se obtienen los datos.
        :param year: Año del que se obtienen los datos.
        :return: Un DataFrame con los datos de los viajes de Bicimad solicitados.
        """
        csv = UrlEMT().get_csv(month, year)

        df = pd.read_csv(csv, delimiter = ';', index_col = ['fecha'] )

        columns = ['idBike', 'fleet', 'trip_minutes', 'geolocation_unlock', 'address_unlock', 'unlock_date', 'locktype',
                   'unlocktype', 'geolocation_lock', 'address_lock', 'lock_date', 'station_unlock',
                   'unlock_station_name', 'station_lock', 'lock_station_name']

        delete = []

        for column in list(df.columns):
            if column not in columns:
                delete.append(column)

        df.drop(columns=delete, inplace=True)
        df.index = pd.to_datetime(df.index, errors='coerce')

        return df


    @property
    def data(self) -> pd.DataFrame:
        self.clean()
        return self._data


    def __str__(self) -> str:
        return str(self.data)


    def clean(self) -> None:
        """
        Limpia el DataFrame almacenado en `self._data`, eliminando filas con todos sus valores NaN y convirtiendo valores
        de columnas específicas a cadenas de texto.

        :return: None. Modifica el DataFrame en el atributo `self._data`.
        """
        self._data.dropna(axis=0, how='all', inplace=True)

        for col_name in ['fleet', 'idBike', 'station_lock', 'station_unlock']:
            self._data[col_name] = self._data[col_name].map(lambda x: str(int(x)) if isinstance(x, float) and not pd.isna(x) else x)


    def resume(self) ->pd.Series:
        """
        Devuelve un resumen de los datos de los viajes en una serie de pandas.

        El resumen incluye:
            - Año de los datos consultados.
            - Mes de los datos consultados.
            - Número total de viajes (usos).
            - Tiempo total de los viajes (en horas).
            - Estación de desbloqueo más popular.
            - Número de usos desde la estación más popular.

        :return: Serie de pandas con el resumen de los datos.
        """
        data = self.data

        sr = pd.Series(
            data = [
                '20'+str(self._year),
                self._month,
                data.size,
                data['trip_minutes'].sum() / 60,
                data['address_unlock'].value_counts().index[0],
                data['address_unlock'].value_counts().iloc[0]
            ],
            index = ['year', 'month', 'total_uses', 'total_time', 'most_popular_station', 'uses_from_most_popular']
        )

        return sr

