from bicimad import UrlEMT, BiciMad
import requests
import io
import pandas as pd
import pytest
from pathlib import Path


FIXTURE_DIR = Path(__file__).parent.resolve() / 'datos'

FILES = pytest.mark.datafiles(
    FIXTURE_DIR / 'emt_datos.html',
    FIXTURE_DIR / 'trips_23_02_February.csv',
    FIXTURE_DIR / 'bicimad_clean.csv',
    FIXTURE_DIR / 'trips_23_02_February-csv.zip'
)


@pytest.fixture
def files(datafiles):
    d = dict()
    for fname in datafiles.iterdir():
        d[fname.name] = fname.as_posix()
    return d

@pytest.fixture
def emt_datos(files):
    with open(files['emt_datos.html'], encoding='utf-8', errors='replace') as f:
        return f.read()

@pytest.fixture
def bicimad_raw(files):
    with open(files['trips_23_02_February.csv'], encoding='utf-8', errors='replace') as f:
        return io.StringIO(f.read())

@pytest.fixture
def bicimad_clean(files):
    with open(files['bicimad_clean.csv'], encoding='utf-8', errors='replace') as f:
        csv = (io.StringIO(f.read()))
        df = pd.read_csv(csv, delimiter=',', index_col=['fecha'])
        df.index = pd.to_datetime(df.index, errors='coerce')

        for col_name in ['fleet', 'idBike', 'station_lock', 'station_unlock']:
            df[col_name] = df[col_name].map(lambda x: str(int(x)) if pd.notna(x) else x)
        return df

@pytest.fixture
def bicimad_zip(files):
    with open(files['trips_23_02_February-csv.zip'], 'rb') as f:
        return f.read()


@pytest.fixture
def mock_response(monkeypatch, emt_datos):
    class MockResponse:
        def __init__(self, text):
            self.status_code = 200
            self.text = text

    def mock_get(*args, **kwargs):
        return MockResponse(emt_datos)

    monkeypatch.setattr(requests, 'get', mock_get)

@pytest.fixture
def mock_response_error(monkeypatch):
    class MockResponse:
        def __init__(self):
            self.status_code = 404
            self.text = "Not Found"

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, 'get', mock_get)

@FILES
def test_select_valid_urls(mock_response):
    url_emt = UrlEMT()
    valid_urls = url_emt.select_valid_urls()

    assert len(valid_urls) == 21
    assert "/getattachment/20b8509b-97a8-4831-b9d2-4900322e1714/trips_23_01_January-csv.aspx" in valid_urls
    assert "/getattachment/e1ea5e02-4ba9-471a-bb95-8cb327220b05/trips_22_03_March-csv.aspx" in valid_urls
    assert "/getattachment/ab3776ab-ba7f-4da3-bea6-e70c21c7d8be/trips_21_06_June-csv.aspx" in valid_urls

def test_select_valid_urls_error(mock_response_error):
    with pytest.raises(ConnectionError):
        UrlEMT()


@pytest.mark.parametrize(
"month , year, expected", [(1, 23,"/getattachment/20b8509b-97a8-4831-b9d2-4900322e1714/trips_23_01_January-csv.aspx" ),
                           (3, 22, "/getattachment/e1ea5e02-4ba9-471a-bb95-8cb327220b05/trips_22_03_March-csv.aspx"),
                           (6, 21, "/getattachment/ab3776ab-ba7f-4da3-bea6-e70c21c7d8be/trips_21_06_June-csv.aspx")])

@FILES
def test_get_url(mock_response, month, year, expected):
    url_emt = UrlEMT()
    assert url_emt.get_url(month, year) == expected


@pytest.mark.parametrize(
"month , year", [(16, 22), (12, 16), ('patata', 22), (1, 21)])

@FILES
def test_get_url_error(mock_response, month, year):
    with pytest.raises(ValueError):
        url_emt = UrlEMT()
        url_emt.get_url(month, year)


@pytest.fixture
def mock_response_zip(monkeypatch, bicimad_zip, emt_datos):
    class MockResponse:
        def __init__(self, content, text):
            self.status_code = 200
            self.text = text
            self.content = content

    def mock_get(*args, **kwargs):
        return MockResponse(bicimad_zip, emt_datos)

    monkeypatch.setattr(requests, 'get', mock_get)

@pytest.fixture
def mock_get_url(monkeypatch):
    def mock_get_url(*args, **kwargs):
        return f'fake_url'

    monkeypatch.setattr(UrlEMT, 'get_url', mock_get_url)

@FILES
def test_get_csv(mock_response_zip, bicimad_raw):
    csv = UrlEMT().get_csv(2, 23)
    assert csv.getvalue()[:100] == bicimad_raw.getvalue()[:100]

@pytest.mark.parametrize(
"month , year", [(16, 22), (12, 16), ('patata', 22), (1, 21)])

@FILES
def test_get_csv_error(mock_response_error, mock_get_url, month, year):
    with pytest.raises(ConnectionError):
        url_emt = UrlEMT()
        url_emt.get_csv(month, year)


@pytest.fixture
def mock_csv(monkeypatch, bicimad_raw):
    def mock_get_csv(*args, **kwargs):
        return bicimad_raw

    monkeypatch.setattr(UrlEMT, 'get_csv', mock_get_csv)

@FILES
def test_get_data(mock_csv, bicimad_clean):
    # Sirve para testar a la vez los métodos BiciMad.get_data(), self.clean(), y el getter del atributo 'self._data'.
    a = BiciMad(2, 3)
    pd.testing.assert_frame_equal(a.data, bicimad_clean)

@FILES
def test_bicimad_str(mock_csv, bicimad_clean):
    a = BiciMad(2,23)
    assert str(a) == str(bicimad_clean)

@FILES
def test_resume(mock_csv):
    a = BiciMad(2, 23)
    resume_8_22 = pd.Series( ['2023', 2, 2527410, 53890.1, "'Plaza de la Cebada nº 16 '", 2189],
             index =['year', 'month', 'total_uses', 'total_time', 'most_popular_station', 'uses_from_most_popular'])

    pd.testing.assert_series_equal(a.resume(), resume_8_22)

