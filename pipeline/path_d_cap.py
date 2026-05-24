"""F50/S77 — Helper compartida para el cap D9 sobre vrp_mw scene-wide.

Bug F50 (PR #185): el cap `PATH_D_ONLY_CAP_MW` se aplicaba SOLO al
`primary_cluster.vrp_mw` en los 3 procesadores (process_modis.py:802+:1017,
simétricos VIIRS) pero NO al `vrp_mw = sum(per_pixel_vrp_mw)` scene-wide.
En condiciones de cirrus extendido (`_path_d_cap_active=True`) la suma
scene-wide alcanzaba 80-510 MW mientras el cluster summit era 0.6-5 MW.

Esta helper se llama desde los 3 procesadores en el sitio donde se computa
`vrp_mw` scene-wide (después de `nansum(per_pixel_vrp_mw)`), aplicando el
mismo cap que ya se usa en el cluster.

Referencia: docs/F50_MODIS_07_25_AUDIT_S77.md §5 "Opción A".
Tag defensivo: pre-s77-f50-vrp-mw-cap.
"""
from __future__ import annotations


def apply_d9_scene_cap(
    vrp_mw: float,
    path_d_cap_active: bool,
    cap_mw: float | None,
) -> float:
    """Aplica el cap D9 al vrp_mw scene-wide si está activo.

    Args:
        vrp_mw: la suma scene-wide pre-cap (W·m² → MW ya convertido).
        path_d_cap_active: predicado calculado por el procesador
            (cirrus + 0 BT/NTI duros, ver process_modis.py:693-700 etc).
        cap_mw: el threshold del cap (PATH_D_ONLY_CAP_MW del profile).
            None significa flag deshabilitado — passthrough.

    Returns:
        `cap_mw` si activo Y `vrp_mw > cap_mw`. Sino `vrp_mw` sin cambio.

    Examples:
        >>> apply_d9_scene_cap(150.47, True, 5.0)
        5.0
        >>> apply_d9_scene_cap(2.5, True, 5.0)
        2.5
        >>> apply_d9_scene_cap(150.47, False, 5.0)
        150.47
        >>> apply_d9_scene_cap(150.47, True, None)
        150.47
    """
    if cap_mw is None or not path_d_cap_active:
        return vrp_mw
    if vrp_mw > cap_mw:
        return cap_mw
    return vrp_mw
