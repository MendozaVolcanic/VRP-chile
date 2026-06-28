# ════════════════════════════════════════════════════════════════════
# FICHA SDA · single_pixel_mode.py · SDA: VRP Chile (clon MIROVA) · ID: VRP-CL
# Objetivo      : Alinear la magnitud reportada con MIROVA NRT en regimen sub-MW, donde MIROVA reporta
#                 single-pixel y nuestra suma de cluster inflaba el VRP (Tupungatito 30×, Chaiten 2.5×).
# Lógica        : Si un cluster cae en regimen sub-MW (vrp_mw < threshold Y n_pixels ≤ max_pixels),
#                 reporta vrp_mw = max(per_pixel_vrp) (pixel mas caliente) en vez de la suma del cluster.
# Modelo/método : Regla determinista (seleccion de magnitud por umbral). Funcion pura, sin I/O.
# Datos entrada : VRP por pixel del cluster (radiancia derivada). SIN datos personales.
# Variables     : threshold (vrp_mw sub-MW), max_pixels, flag de activacion (mirova_equivalent.yaml).
# Limitaciones  : Solo corrige magnitud (no deteccion ni posicion); mantiene n_pixels y marca
#                 single_pixel_mode=True para auditoria. No aplica a regimen alto-MW (Villarrica F52-A).
# Refs/datos    : mirova_equivalent.yaml:281-283; audit PRs #191/#192. Entrenamiento: No aplica.
#                 Ficha: docs/FICHA_SDA_VRP_CHILE.md
# ════════════════════════════════════════════════════════════════════
"""F52-B (S77, A45) — Single-pixel mode para régimen sub-MW.

Causa raíz F52-B (drift T1.5 S72, documentado en
`pipeline/profiles/mirova_equivalent.yaml:281-283`): el path D dNTI-contextual
produce clusters de varios pixels en el cráter cuando MIROVA NRT reporta
single-pixel en el mismo evento. La suma `pc.vrp_mw = Σ per_pixel_vrp_mw`
inflaba el reporte vs MIROVA en régimen sub-MW (0.21-0.45 MW canónicos):

    | Volcán          | Ratio ours/MIROVA mediano (audit PRs #191+#192) |
    |-----------------|--------------------------------------------------|
    | Tupungatito     | 30.15× (peor)                                    |
    | Chaitén         | 2.53×                                            |
    | PlanchónPeteroa | 2.10×                                            |
    | PCC             | 0.48× (sub-estimación, ver nota)                 |

Nota PCC: ratio <1 ocurre porque MIROVA reporta single pixel hottest mientras
nuestro pipeline sumaba el cluster contiguo. Mismo bug arquitectural,
manifestación opuesta. El fix corrige ambos lados.

Volcanes NO afectados (régimen alto-MW o sin path D dominante): Villarrica
(es F52-A), Copahue, Isluga, Lascar, Lastarria, Llaima, NdC.

Fix: cuando un cluster cae en régimen sub-MW (`vrp_mw < threshold` Y
`n_pixels <= max_pixels`), reportar `vrp_mw = max(per_pixel_vrp)` (single
pixel hottest, alineado con MIROVA NRT single-pixel detection) en vez de la
suma. Mantiene `n_pixels` y agrega `single_pixel_mode=True` para audit.

Flags en `mirova_equivalent.yaml`:
    enable_single_pixel_sub_mw_mode: true
    sub_mw_regime_threshold_mw: 5.0
    single_pixel_max_cluster_pixels: 3

Tag defensivo: pre-s77-f52b-single-pixel-sub-mw.
Refs: PRs #191 + #192, experiments/146 + 147, CLAUDE.md A45.
"""
from __future__ import annotations

from typing import Sequence


def apply_single_pixel_mode(
    primary_cluster: dict,
    per_pixel_vrp: Sequence[float],
    *,
    enabled: bool,
    threshold_mw: float,
    max_pixels: int,
) -> dict:
    """Aplica single-pixel mode al primary_cluster si el régimen es sub-MW.

    Pure function: no side effects, devuelve dict nuevo (no muta entrada).

    Args:
        primary_cluster: dict del cluster primario (al menos keys 'vrp_mw' y
            'n_pixels'). Si es None o falta alguna key crítica, devuelve sin
            cambios.
        per_pixel_vrp: iterable con los VRPs individuales de los pixels que
            componen el cluster (mismo orden que `pixel_indices` del cluster).
        enabled: flag maestro. Si False → passthrough sin cambios.
        threshold_mw: si `primary_cluster.vrp_mw >= threshold_mw` → passthrough
            (régimen alto-MW, sum reporting es correcto).
        max_pixels: si `primary_cluster.n_pixels > max_pixels` → passthrough
            (cluster grande, no es régimen single-pixel MIROVA NRT).

    Returns:
        Dict modificado con `vrp_mw = max(per_pixel_vrp)` y
        `single_pixel_mode = True` si las dos condiciones de régimen sub-MW
        se cumplen Y enabled=True. Sino, dict idéntico a entrada (con
        `single_pixel_mode = False` agregado para audit explícito).

    Examples:
        >>> pc = {"vrp_mw": 2.5, "n_pixels": 3}
        >>> out = apply_single_pixel_mode(
        ...     pc, [1.2, 0.8, 0.5],
        ...     enabled=True, threshold_mw=5.0, max_pixels=3,
        ... )
        >>> out["vrp_mw"]
        1.2
        >>> out["single_pixel_mode"]
        True

        >>> pc2 = {"vrp_mw": 10.0, "n_pixels": 3}
        >>> out2 = apply_single_pixel_mode(
        ...     pc2, [5.0, 3.0, 2.0],
        ...     enabled=True, threshold_mw=5.0, max_pixels=3,
        ... )
        >>> out2["vrp_mw"]
        10.0
        >>> out2["single_pixel_mode"]
        False
    """
    if primary_cluster is None:
        return primary_cluster

    # Copia defensiva
    out = dict(primary_cluster)

    if not enabled:
        # No marcar flag: backward-compat con records pre-fix.
        return out

    vrp_mw = out.get("vrp_mw")
    n_pixels = out.get("n_pixels")
    if vrp_mw is None or n_pixels is None:
        out["single_pixel_mode"] = False
        return out

    # Régimen sub-MW: ambas condiciones tienen que cumplirse (AND).
    in_sub_mw_regime = float(vrp_mw) < float(threshold_mw)
    in_single_pixel_size = int(n_pixels) <= int(max_pixels)

    if not (in_sub_mw_regime and in_single_pixel_size):
        out["single_pixel_mode"] = False
        return out

    # Defensa: per_pixel_vrp vacío o todos NaN/0 → no podemos reportar max.
    # Fallback: passthrough (preferimos sum legacy a 0 espurio).
    if per_pixel_vrp is None or len(per_pixel_vrp) == 0:
        out["single_pixel_mode"] = False
        return out

    finite_vrps = [float(v) for v in per_pixel_vrp
                   if v is not None and not _isnan(v)]
    if not finite_vrps:
        out["single_pixel_mode"] = False
        return out

    max_vrp = max(finite_vrps)
    out["vrp_mw"] = round(max_vrp, 3)
    out["single_pixel_mode"] = True
    return out


def _isnan(x: float) -> bool:
    try:
        return x != x  # NaN no es igual a sí mismo
    except Exception:
        return False
