"""Dias con al menos un record por volcan en 2026-01 y 2026-02 (produccion). P1: un hueco de backfill se ve como
dias faltantes contiguos. P2: volcan sin records en el mes = 0 dias, listado explicitamente."""
import json, pathlib, collections, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = pathlib.Path(__file__).resolve().parents[3] / "data" / "mirova_equivalent"
for v in ["Lascar","Villarrica","NevadosDeChillan"]:
    dias = sorted({(r.get("datetime_utc") or "")[:10] for r in json.load(open(D/f"{v}.json", encoding="utf-8"))["records"]
                   if (r.get("datetime_utc") or "")[:7] in ("2026-01", "2026-02")})
    ene = [d for d in dias if d.startswith("2026-01")]
    print(v, "enero dias=", len(ene), "primero/ultimo", ene[:1], ene[-1:], "| febrero dias=", len(dias) - len(ene), "primero", [d for d in dias if d.startswith("2026-02")][:1])
