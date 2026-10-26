"""Agregar campo `proyecto: "[[VRP Chile]]"` al frontmatter de papers MIROVA en Vault.

Resuelve desacople S21: 25 papers MIROVA-relevantes en
`../../Vault/10_Bibliografia/99_por_clasificar/` no estaban linkeados a VRP Chile.

Idempotente: si el paper ya tiene VRP Chile en su frontmatter, no toca nada.
NO mueve archivos físicamente (instrucción de Nicolás).

Uso:
    python scripts/vault_link_papers_to_project.py [--dry-run]

Volver a correr cuando se procesen papers MIROVA nuevos en el Vault.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path


# Path Vault relativo al CWD del proyecto VRP Chile
VAULT_BIBLIO = Path("../../Vault/10_Bibliografia/99_por_clasificar").resolve()

# 25 papers MIROVA-relevantes auditados S17-S21 + ATBD VIIRS
MIROVA_PAPERS = [
    "wooster2003fire.md",
    "coppola2010comparison.md",
    "coppola2013rheological.md",
    "coppola2016enhanced.md",
    "coppola2016fifteen.md",
    "coppola2020thermal.md",
    "coppola2021thermal.md",
    "coppola2022shallow.md",
    "coppola2023global.md",
    "coppola2025rapid.md",
    "coppola2025thermalbook.md",
    "campus2022transition.md",
    "campus2024thermal.md",
    "aveni2023capabilities.md",
    "aveni2024tirvolch.md",
    "aveni2025tracking.md",
    "aveni2025volcanic.md",
    "dibella2024advancing.md",
    "laiolo2017evidences.md",
    "laiolo2017evidencesa.md",
    "laiolo2026switching.md",
    "massimetti2020volcanic.md",
    "massimetti2024stromboli.md",
    "massimetti2024thermal.md",
    "massimettithermal.md",
    "2014jpss_viirs_radiometric_calibration_atbd_2014.md",
]

PROYECTO_LINE = 'proyecto: "[[VRP Chile]]"'


def _split_frontmatter(text: str) -> tuple[str | None, str]:
    """Devuelve (frontmatter_yaml, body). frontmatter_yaml=None si no hay."""
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return None, text
    # Buscar cierre `\n---\n`
    end = text.find("\n---\n", 4)
    if end < 0:
        end = text.find("\r\n---\r\n", 4)
        if end < 0:
            return None, text
        body_start = end + 7
    else:
        body_start = end + 5
    fm = text[4:end]
    body = text[body_start:]
    return fm, body


def _has_vrp_chile(fm: str) -> bool:
    """True si el frontmatter ya menciona VRP Chile en cualquier campo."""
    return "VRP Chile" in fm


def _append_proyecto(fm: str) -> str:
    """Agrega línea proyecto al final del frontmatter (idempotente upstream)."""
    return fm.rstrip() + f"\n{PROYECTO_LINE}\n"


def update_paper(path: Path, dry_run: bool = False) -> str:
    """Devuelve etiqueta de estado: 'updated', 'already_linked', 'no_frontmatter', 'not_found'."""
    if not path.exists():
        return "not_found"

    text = path.read_text(encoding="utf-8")
    fm, body = _split_frontmatter(text)

    if fm is None:
        # Sin frontmatter previo — agregar uno mínimo
        new_text = f"---\n{PROYECTO_LINE}\n---\n\n{text}"
        if not dry_run:
            path.write_text(new_text, encoding="utf-8")
        return "no_frontmatter_added"

    if _has_vrp_chile(fm):
        return "already_linked"

    new_fm = _append_proyecto(fm)
    new_text = f"---\n{new_fm}---\n{body}"
    if not dry_run:
        path.write_text(new_text, encoding="utf-8")
    return "updated"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="No escribe archivos, solo imprime qué haría")
    ap.add_argument("--vault-biblio", default=str(VAULT_BIBLIO),
                    help="Path al directorio del Vault con papers")
    args = ap.parse_args()

    biblio = Path(args.vault_biblio).resolve()
    if not biblio.exists():
        print(f"ERROR: Vault path no existe: {biblio}", file=sys.stderr)
        sys.exit(1)

    print(f"Vault biblio: {biblio}")
    print(f"Papers MIROVA target: {len(MIROVA_PAPERS)}")
    print(f"Dry-run: {args.dry_run}\n")

    counters = {"updated": 0, "already_linked": 0,
                "no_frontmatter_added": 0, "not_found": 0}
    for paper in MIROVA_PAPERS:
        path = biblio / paper
        status = update_paper(path, dry_run=args.dry_run)
        counters[status] = counters.get(status, 0) + 1
        print(f"  [{status}] {paper}")

    print(f"\nResumen: {counters}")
    print(f"Total tocados: {counters['updated'] + counters['no_frontmatter_added']}")


if __name__ == "__main__":
    main()
