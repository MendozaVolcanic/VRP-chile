# -*- coding: utf-8 -*-
"""Cuántos días le quedan al EARTHDATA_TOKEN (Fase 0, tarea 8c del plan de paridad).

POR QUÉ. El token de NASA Earthdata vive 60 días (docs/EARTHDATA_TOKEN_SETUP.md:12). En julio de
2026 venció sin aviso y el NRT pasó 13 días "verde" sin datos (S123). Nadie se entera de un
vencimiento hasta que ya pasó, así que hace falta un aviso ANTES.

Cómo. El token es un JWT: su parte central trae el campo `exp` (segundos UNIX) con la fecha de
vencimiento REAL. Se decodifica sin verificar la firma (no hace falta: sólo se lee una fecha) y sin
llamar a ninguna API. El plan proponía leer `updated_at` del secret, pero eso es la fecha en que
alguien lo pegó, no la de vencimiento, y exige un permiso sobre secrets que el token del workflow
no necesita tener.

SEGURIDAD: el valor del token nunca se imprime ni se escribe; sólo la fecha y los días.

Estados: `ok` (> DIAS_AVISO), `renovar` (<= DIAS_AVISO), `vencido` (< 0), `desconocido` (no hay
token o no es un JWT legible).
"""
from __future__ import annotations

import base64
import json
import os
import sys
from datetime import datetime, timezone

DIAS_AVISO = 10   # vida 60 días, rotar a los 50 (REGISTRO_CREDENCIALES.md, docs/EARTHDATA_TOKEN_SETUP.md:42)


def vencimiento_jwt(token: str) -> datetime | None:
    """Fecha de vencimiento (UTC) del campo `exp` de un JWT; None si no se puede leer."""
    partes = (token or "").strip().split(".")
    if len(partes) != 3:
        return None
    carga = partes[1] + "=" * (-len(partes[1]) % 4)
    try:
        exp = json.loads(base64.urlsafe_b64decode(carga.encode("ascii")))["exp"]
        return datetime.fromtimestamp(int(exp), tz=timezone.utc)
    except (ValueError, KeyError, TypeError):
        return None


def estado_token(token: str, ahora: datetime) -> dict:
    vence = vencimiento_jwt(token)
    if vence is None:
        return {"estado": "desconocido", "vence_utc": None, "dias_restantes": None}
    dias = (vence - ahora).total_seconds() / 86400
    estado = "vencido" if dias < 0 else ("renovar" if dias <= DIAS_AVISO else "ok")
    return {"estado": estado, "vence_utc": vence.isoformat(timespec="minutes"),
            "dias_restantes": round(dias, 1)}


def main() -> int:
    res = estado_token(os.environ.get("EARTHDATA_TOKEN", ""), datetime.now(timezone.utc))
    print(f"EARTHDATA_TOKEN: estado={res['estado']} vence={res['vence_utc']} "
          f"dias_restantes={res['dias_restantes']}")
    salida = os.environ.get("GITHUB_OUTPUT")
    if salida:
        with open(salida, "a", encoding="utf-8") as fh:
            for k, v in res.items():
                fh.write(f"{k}={'' if v is None else v}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
