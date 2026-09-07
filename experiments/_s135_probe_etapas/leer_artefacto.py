"""S135 — lee el artefacto del probe (out/*.json) y re-evalúa el criterio pre-registrado.

Uso: python experiments/_s135_probe_etapas/leer_artefacto.py [dir_out]
No baja nada ni toca el pipeline: sólo lee los JSON que subió el workflow.
"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
from analisis import evaluar_criterio  # noqa: E402


def main():
    d = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "out"
    filas = [json.loads(p.read_text(encoding="utf-8"))
             for p in sorted(d.glob("*.json")) if p.name != "criterio.json"]
    print(f"{len(filas)} pasadas en {d}\n")
    for f in filas:
        print(f"== {f['volcan']} {f['pasada_utc']} {f['sensor']} [{f['clase']}] ok={f['ok']}")
        if not f["ok"]:
            print("   error:", f.get("error"))
            continue
        rec, r = f["record"], f["resumen"]
        t1, kp, it = r["test1"], r.get("keep_peak"), r.get("interseccion_sin_pico")
        print(f"   record: source={rec.get('final_hotspot_source')} d_final={rec.get('final_hotspot_dist_km')} "
              f"vrp={rec.get('vrp_mw')} pc={rec.get('primary_cluster')} t_bg={rec.get('t_bg_k')} "
              f"n_fp={rec.get('diag_n_first_pass_pixels')}")
        if t1.get("corrio"):
            print(f"   Test1: trig={t1['triggered']} n_mask={t1['n_contributing']}/{t1['n_en_disco']} disco · "
                  f"cráter<0,5km en mask: {t1['n_mask_a_menos_0_5km']} · <1km: {t1['n_mask_a_menos_1km']} · "
                  f"rango BT cráter: {t1['rango_bt_crater_en_mask']} · mediana dist mask {t1['mediana_dist_vent_mask_km']} km")
            pc = t1.get("pixel_mas_cercano_al_vent")
            if pc:
                print(f"   px más cercano al vent: {pc['dist_vent_km']} km · BT {pc['bt_k']} K "
                      f"({pc['bt_menos_t_bg_global_k']} K vs fondo) · en mask={pc['en_mask_contributing']}")
            for p in t1.get("pixeles_crater_en_mask", []):
                print(f"      cráter: {p['dist_vent_km']} km · BT {p['bt_k']} K ({p['bt_menos_t_bg_global_k']} K vs fondo)")
        if kp:
            print(f"   keep_peak: {kp['dist_vent_km']} km ({kp['octante']}) · BT {kp['bt_k']} K "
                  f"({kp['bt_menos_t_bg_global_k']} K vs fondo) · argmax disco={kp['es_argmax_del_disco']}")
            print(f"   (Test1 ∩ dNTI) sin pico: {it['n']} px · dNTI total {it['n_dnti_ctx_total']} · salida {it['n_mask_out']} px")
        else:
            print("   keep_peak no aplicó")
        for i, sp in enumerate(r.get("second_pass", [])):
            print(f"   second_pass[{i}]: active_in={sp['n_active_in']} newly={sp['n_newly_active']} "
                  f"≤3K={sp['n_newly_bajo_compuerta_3k']}")
        perfil = r.get("perfil_bt") or []
        print("   perfil BT (km→K): " + " ".join(
            f"{x['hasta_km']:.2f}:{x['bt_mediana']:.1f}" for x in perfil if x["bt_mediana"] is not None))
        # octantes: BT mediana del último anillo con datos menos la del primero con datos
        oct_line = []
        for o in ("N", "NE", "E", "SE", "S", "SW", "W", "NW"):
            ser = [x["por_octante"][o]["bt_mediana"] for x in perfil if x["por_octante"][o]["bt_mediana"] is not None]
            if len(ser) >= 2:
                oct_line.append(f"{o}:{ser[-1]-ser[0]:+.1f}")
        print("   Δ BT borde−centro por octante (K): " + " ".join(oct_line))
        print(f"   anillo [1,3] {r.get('bt_mediana_anillo_1.0_3.0_km')} K · [1.5,3] {r.get('bt_mediana_anillo_1.5_3.0_km')} K")
        print()
    c = evaluar_criterio(filas)
    print("=" * 70)
    print("H1:", c["h1"], f"[nevado {c['n_nevado_confirman']} · control {c['n_control_ok']}]")
    print("H2:", c["h2"])
    for d_ in c["detalle"]:
        print(f"   {d_['volcan']} {d_['pasada_utc']} → {d_.get('h1')} (cráter {d_.get('n_crater')}, "
              f"pico {d_.get('keep_peak_dist_vent_km')} km, fp {d_.get('n_first_pass')})")


if __name__ == "__main__":
    main()
