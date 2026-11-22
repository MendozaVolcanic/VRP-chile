"""S182: la descarga va siempre por HTTPS, también cuando el runner cae en AWS us-west-2.

Qué pasaba: desde noviembre de 2026 algunos runners `ubuntu-24.04` de GitHub corren en
AWS us-west-2 (cabecera del log: «Region: us-west-2 / Cloud: AWS»). earthaccess consulta el
servicio de metadatos de AWS, se cree «en la región de los datos» (`in_region=True`) y baja
por S3 directo. Con Python 3.11 el pip se queda en earthaccess 0.17.0 (0.18 y 0.19 exigen
Python >= 3.12), y en 0.17.0 esa vía está rota: `Store.download_cloud_file` llama
`s3_fs.get([archivo], partial_xxx)` con una LISTA, fsspec trata el destino como carpeta y
hace makedirs sobre el archivo temporal recién creado -> `FileExistsError: [Errno 17] File
exists: '.../partial_xxx'`. Todas las descargas del job fallan; los jobs en Azure no.

Arreglo: `download_granules` fuerza `in_region=False` antes de bajar, la misma vía HTTPS que
usan todas las corridas verdes del NRT.
"""
import inspect
import os

import fsspec
import pytest

import pipeline.fetch as fetch


class _GranuloFalso(dict):
    def __init__(self, ur="LAADS:10079513486"):
        super().__init__(umm={"GranuleUR": ur})

    def data_links(self):
        return [f"https://data.laadsdaac.earthdatacloud.nasa.gov/prod-lads/MOD021KM/{self['umm']['GranuleUR']}.hdf"]


def _bajar_un_archivo(local_path):
    # S190 (F6-101): una lista vacía ya no es una descarga buena; el doble deja un archivo como la biblioteca real.
    ruta = os.path.join(local_path, "MOD021KM.falso.hdf")
    open(ruta, "wb").close()
    return [ruta]


class _StoreFalso:
    """Store de earthaccess tal como queda en un runner de AWS us-west-2."""
    in_region = True


@pytest.fixture(autouse=True)
def _sin_esperas(monkeypatch):
    fetch._DOWN_DOWNLOAD_HOSTS.clear()
    monkeypatch.setattr("time.sleep", lambda *a, **k: None)
    yield
    fetch._DOWN_DOWNLOAD_HOSTS.clear()


def test_runner_en_us_west_2_descarga_por_https(monkeypatch, tmp_path):
    store = _StoreFalso()
    monkeypatch.setattr(fetch.earthaccess, "__store__", store, raising=False)
    visto = {}

    def descarga(granulos, local_path=None, **k):
        visto["in_region"] = fetch.earthaccess.__store__.in_region
        return _bajar_un_archivo(local_path)

    monkeypatch.setattr(fetch.earthaccess, "download", descarga)
    fetch.download_granules([_GranuloFalso()], tmp_path)
    assert visto["in_region"] is False, (
        "con in_region=True earthaccess 0.17.0 baja por S3 y cada descarga muere con "
        "FileExistsError sobre partial_*; la descarga tiene que ir por HTTPS")


def test_sin_login_no_revienta(monkeypatch, tmp_path):
    """Sin login (store None) el forzado no debe romper la descarga."""
    monkeypatch.setattr(fetch.earthaccess, "__store__", None, raising=False)
    monkeypatch.setattr(fetch.earthaccess, "download", lambda g, local_path=None, **k: _bajar_un_archivo(local_path))
    assert len(fetch.download_granules([_GranuloFalso()], tmp_path)) == 1


def test_mecanismo_via_s3_de_earthaccess_rompe_con_partial(tmp_path):
    """Documenta el defecto de earthaccess que motiva el forzado (control de que el
    instrumento puede dar rojo). Si earthaccess ya baja con `get_file` (>= 0.19), el
    defecto no existe en esa versión y la prueba se salta: entonces se puede revisar si
    conviene volver a dejar que earthaccess elija la vía."""
    import earthaccess.store as eastore
    fuente = inspect.getsource(eastore.Store.download_cloud_file)
    if "get_file(" in fuente:
        pytest.skip("earthaccess ya no tiene el defecto de get([..]) en la vía S3")
    fs = fsspec.filesystem("memory")
    fs.pipe("/prod-lads/MOD021KM/MOD021KM.A2026290.0220.061.hdf", b"x" * 10)
    sin_reintento = getattr(eastore.Store.download_cloud_file, "__wrapped__",
                            eastore.Store.download_cloud_file)
    with pytest.raises(FileExistsError, match="partial_"):
        sin_reintento(None, fs, "/prod-lads/MOD021KM/MOD021KM.A2026290.0220.061.hdf", tmp_path)
