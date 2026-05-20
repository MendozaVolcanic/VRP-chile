"""Test fixture: TIF sintético controlado para validar el método R2 (top-N ponderado).

Razón: antes de aplicar el método sobre TIFs reales de MIROVA, demostrar que sobre
un TIF con un cluster conocido (9 pix x 10 MW = 90 MW total) el método R2 recupera
correctamente:
  1) el centroide del cluster
  2) la suma top-10 ~ 90 MW (con tolerancia por noise incluido en top-10)

Si el método falla aquí, no tiene sentido aplicarlo sobre data real.
"""
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

# Importar la función del audit principal (mismo dir, mismo método)
import sys
sys.path.insert(0, str(Path(__file__).parent))
from audit_lastarria import top_n_centroid, haversine_km  # noqa: E402


def make_synthetic_tif(path: Path) -> np.ndarray:
    """Crea TIF 100x100 con 1 cluster en (50,50) de 9 pixels valor 10 MW c/u
    y ~90 pixels noise valor 0.1 MW dispersos.

    Returns el array generado (para comparar contra lo que rasterio reescribió).
    """
    arr = np.zeros((100, 100), dtype=np.float32)
    arr[49:52, 49:52] = 10.0  # cluster 9 pix x 10 MW = 90 MW
    rng = np.random.default_rng(42)
    noise_mask = rng.random((100, 100)) < 0.09
    noise_only = noise_mask & (arr == 0)
    arr[noise_only] = 0.1
    # Origen en lon=-69, lat=-25 (Andes chilenos genéricos), pixel 0.001 deg ~ 100m
    transform = from_origin(-69.0, -25.0, 0.001, 0.001)
    with rasterio.open(
        path, "w", driver="GTiff", height=100, width=100, count=1,
        dtype=np.float32, crs="EPSG:4326", transform=transform,
    ) as dst:
        dst.write(arr, 1)
    return arr


def test_top_n_centroid_recovers_cluster():
    """El centroide top-10 debe caer dentro del cluster (49-51, 49-51 en grid)."""
    out_path = Path(__file__).parent / "_synthetic.tif"
    arr = make_synthetic_tif(out_path)
    with rasterio.open(out_path) as src:
        arr_read = src.read(1)
        transform = src.transform

    lat_c, lon_c, mw_top10, n_used = top_n_centroid(arr_read, transform, n=10)

    # El cluster (filas 49..51, cols 49..51) en lon/lat corresponde a:
    #   lon ~ -69.0 + 50 * 0.001 = -68.95   (col offset 50 -> mid del cluster)
    #   lat ~ -25.0 - 50 * 0.001 = -25.05   (row offset 50)
    expected_lon = -68.95
    expected_lat = -25.05

    # Tolerancia: 1 pixel = 0.001 deg
    assert abs(lon_c - expected_lon) < 0.002, f"lon_c={lon_c} expected~{expected_lon}"
    assert abs(lat_c - expected_lat) < 0.002, f"lat_c={lat_c} expected~{expected_lat}"

    # Top-10 incluye 9 pix del cluster (10 MW) + 1 pix noise (0.1 MW) = 90.1 MW
    assert 89.0 < mw_top10 < 91.0, f"mw_top10={mw_top10} expected ~90"
    assert n_used == 10

    # El array completo: 9 pix x 10 + ~810 pix x 0.1 = ~90 + ~81 = ~171
    full_sum = float(arr[arr > 0].sum())
    assert full_sum > mw_top10, "full sum debe ser mayor (incluye noise pixels)"
    return {
        "lat_c": lat_c, "lon_c": lon_c, "mw_top10": mw_top10,
        "full_sum": full_sum, "n_pos": int((arr > 0).sum()),
    }


if __name__ == "__main__":
    result = test_top_n_centroid_recovers_cluster()
    print(f"OK test_top_n_centroid_recovers_cluster")
    print(f"  centroide top10: ({result['lat_c']:.4f}, {result['lon_c']:.4f})")
    print(f"  esperado:        (-25.0500, -68.9500)")
    print(f"  suma top10:      {result['mw_top10']:.2f} MW  (esperado ~90)")
    print(f"  suma full TIF:   {result['full_sum']:.2f} MW  (cluster 90 + noise ~81)")
    print(f"  pixels > 0:      {result['n_pos']}")
    print()
    print("Conclusion: el metodo R2 mide correctamente sobre un TIF con cluster real.")
    print("Ahora podemos aplicarlo sobre TIFs reales de MIROVA Lastarria.")
