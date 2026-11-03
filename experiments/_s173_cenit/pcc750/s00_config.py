# -*- coding: utf-8 -*-
"""s00 (S173, cenit PCC V750): deja por escrito la configuración que leen los demás scripts: commits, sha256 de los
insumos, y los valores del perfil de producción que definen el fondo de K (leídos de pipeline.profile, A89, no del YAML).
Uso: python -B s00_config.py > s00_salida.txt"""
import hashlib, os, sys
from pathlib import Path
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI / "repo"))
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import pipeline.profile as p  # noqa: E402
print("repo (origin/main):", (AQUI / "repo" / "COMMIT.txt").read_text().strip())
print("src (origin/loop/activo):", (AQUI / "src" / "COMMIT_loop_activo.txt").read_text().strip())
print("insumos N (origin/s159-pruebas):", (AQUI / "insumos" / "REF_SHA.txt").read_text().strip())
for f in ("repo/data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv",
          "repo/data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv",
          "repo/data/mirova_equivalent/PuyehueCordonCaulle.json", "repo/data/audit_continuous/latest.json",
          "src/s162/oraculo_ablacion.py", "src/s162/ablacion.py", "insumos/oraculo_r2/mirova_v750_r2.py"):
    print(f, hashlib.sha256((AQUI / f).read_bytes()).hexdigest())
for k in ("BG_INNER_KM", "BG_OUTER_KM", "ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750", "VRP_BG_NEIGHBOR_MAX_HALF_PX",
          "ENABLE_V750_CODIGO_MIROVA", "ENABLE_UTM_REGRID", "ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS"):
    print(k, getattr(p, k, "NO EXISTE"))
