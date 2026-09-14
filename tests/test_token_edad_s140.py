# -*- coding: utf-8 -*-
"""Fase 0 tarea 8c (S140): aviso de vencimiento del EARTHDATA_TOKEN leyendo el `exp` del JWT.

POR QUE: en julio de 2026 el token vencio sin aviso y el NRT paso 13 dias sin datos (S123). Con JWT
sinteticos (no se usa el token real) se fija que el estado cambia en los bordes correctos y que un
token ilegible no se confunde con uno sano.
"""
import base64
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.token_edad import DIAS_AVISO, estado_token, vencimiento_jwt  # noqa: E402

AHORA = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)


def _jwt(exp_dt):
    b = lambda d: base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip("=")
    return f"{b({'alg': 'RS256', 'typ': 'JWT'})}.{b({'exp': int(exp_dt.timestamp()), 'uid': 'x'})}.firma"


def test_lee_exp_del_jwt():
    vence = AHORA + timedelta(days=19)
    assert vencimiento_jwt(_jwt(vence)) == vence.replace(microsecond=0)


def test_estados_en_los_bordes():
    assert estado_token(_jwt(AHORA + timedelta(days=30)), AHORA)["estado"] == "ok"
    assert estado_token(_jwt(AHORA + timedelta(days=DIAS_AVISO)), AHORA)["estado"] == "renovar"
    assert estado_token(_jwt(AHORA + timedelta(days=2)), AHORA)["estado"] == "renovar"
    assert estado_token(_jwt(AHORA - timedelta(hours=1)), AHORA)["estado"] == "vencido"


def test_token_ilegible_es_desconocido_no_ok():
    for t in ("", "no-es-un-jwt", "a.b.c", "a.%%%.c"):
        r = estado_token(t, AHORA)
        assert r["estado"] == "desconocido" and r["dias_restantes"] is None, t


def test_dias_restantes():
    r = estado_token(_jwt(AHORA + timedelta(days=19, hours=12)), AHORA)
    assert r["dias_restantes"] == 19.5


def test_el_healthcheck_diario_corre_el_aviso_con_el_secret():
    """Sin este cableado el script existe y nadie lo llama (la familia de A89)."""
    import yaml
    wf = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "nrt-healthcheck.yml"
    pasos = yaml.safe_load(wf.read_text(encoding="utf-8"))["jobs"]["healthcheck"]["steps"]
    paso = next((p for p in pasos if "scripts/token_edad.py" in (p.get("run") or "")), None)
    assert paso is not None, "nrt-healthcheck.yml no corre scripts/token_edad.py"
    assert paso.get("env", {}).get("EARTHDATA_TOKEN") == "${{ secrets.EARTHDATA_TOKEN }}"
    assert paso.get("id") == "token" and "always()" in paso.get("if", "")
