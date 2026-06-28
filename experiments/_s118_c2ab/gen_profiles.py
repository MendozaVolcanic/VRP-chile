"""S118 C2 A/B — genera los 4 profiles desde el operacional por reemplazo de strings.

POR QUÉ: el A/B aísla los dos gates intra-radio. Cada brazo difiere del operacional
SOLO en los flags `enable_path_d_intra_radio_gate` / `enable_second_pass_intra_radio_gate`
y en `data_subdir` (aislamiento A47). Reemplazo a nivel string (NO yaml.safe_dump —
destruiría los comentarios que documentan cada flag, CLAUDE.md). Reproducible.
"""
from __future__ import annotations
from pathlib import Path

PROF_DIR = Path(__file__).resolve().parents[2] / "pipeline" / "profiles"
BASE = PROF_DIR / "mirova_equivalent.yaml"

# (nombre, path_d_gate, second_pass_gate)
ARMS = [
    ("_c2ab_baseline", True, True),    # = operacional, aislado (control)
    ("_c2ab_pathd_off", False, True),  # aísla gate MODIS Path-D
    ("_c2ab_2pass_off", True, False),  # aísla gate second-pass (MODIS+VIIRS)
    ("_c2ab_both_off", False, False),  # clon-literal puro + interacción
]

HEADER = (
    "# VRP-Chile — profile: {name}\n"
    "# S118 A/B GATES INTRA-RADIO C2 — brazo generado por experiments/_s118_c2ab/gen_profiles.py.\n"
    "# Difiere del operacional mirova_equivalent SOLO en: enable_path_d_intra_radio_gate={pd},\n"
    "# enable_second_pass_intra_radio_gate={sp}, data_subdir (aislado A47). Resto idéntico.\n"
    "# Diseño: docs/superpowers/specs/2026-06-28-c2-gates-intra-radio-ab-design.md. NO operacional.\n"
)


def gen():
    base = BASE.read_text(encoding="utf-8")
    # Sanity: los anclas de reemplazo deben existir exactamente una vez.
    for anchor in ("  enable_path_d_intra_radio_gate: true\n",
                   "  enable_second_pass_intra_radio_gate: true\n",
                   "  data_subdir: mirova_equivalent\n",
                   "profile: mirova_equivalent\n"):
        assert base.count(anchor) == 1, f"ancla no única: {anchor!r} ({base.count(anchor)})"

    written = []
    for (name, pd, sp) in ARMS:
        txt = base
        txt = txt.replace("  enable_path_d_intra_radio_gate: true\n",
                          f"  enable_path_d_intra_radio_gate: {str(pd).lower()}\n")
        txt = txt.replace("  enable_second_pass_intra_radio_gate: true\n",
                          f"  enable_second_pass_intra_radio_gate: {str(sp).lower()}\n")
        txt = txt.replace("  data_subdir: mirova_equivalent\n",
                          f"  data_subdir: {name}\n")
        txt = txt.replace("profile: mirova_equivalent\n", f"profile: {name}\n")
        # Reemplazar la primera línea (header del operacional) por el header A/B.
        body = txt.split("\n", 1)[1]
        txt = HEADER.format(name=name, pd=str(pd).lower(), sp=str(sp).lower()) + body
        out = PROF_DIR / f"{name}.yaml"
        out.write_text(txt, encoding="utf-8")
        written.append((name, pd, sp, out))
    return written


if __name__ == "__main__":
    for (name, pd, sp, out) in gen():
        print(f"{name:20s} path_d={str(pd):5s} 2pass={str(sp):5s} -> {out.name}")
