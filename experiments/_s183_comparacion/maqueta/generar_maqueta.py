# -*- coding: utf-8 -*-
"""S183: maqueta de la vista «Vía, K y MIROVA» para la propuesta a Nicolás (fase 2). No es el tablero.

Inserta salida/via_k_mirova.json en una página estática con el estilo de frontend/comparacion.html. Los números salen
del JSON; la página sólo los ordena.
"""
import json
from pathlib import Path

AQUI = Path(__file__).parent
d = json.loads((AQUI.parent / "salida" / "via_k_mirova.json").read_text(encoding="utf-8"))
datos = {"meta": {k: d["meta"][k] for k in ("generado_utc", "referencia", "regla_minimas")}, "r": {}}
for clave, r in d["resultados"].items():
    datos["r"][clave] = {"n": r["n_pasadas_pareadas"], "via": r["via"], "k": r["k"],
                         "por_volcan": r.get("por_volcan", {}), "disc": r["protegidas_discordantes_pasadas"]}

HTML = r"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Maqueta S183: vía, K y MIROVA</title>
<style>
:root{--bg:#0a1929;--panel:#0e2236;--blue:#4fc3f7;--muted:#7a8fa6;--line:#1a3a5c;--via:#66bb6a;--k:#ffb74d;--mir:#e57373}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:#cfe3f5;font-family:system-ui,Segoe UI,Roboto,sans-serif;font-size:14px}
header{padding:14px 20px;border-bottom:1px solid var(--line)}h1{margin:0;font-size:1.1rem;color:#fff}
.badge{background:#5b3a00;color:#ffc107;border:1px solid #ffc107;border-radius:4px;padding:2px 8px;font-size:.66rem;margin-left:8px}
main{padding:16px 20px;max-width:1200px}.explain{color:var(--muted);font-size:.8rem;line-height:1.55;max-width:980px}
.explain b{color:#cfe3f5}.controls{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}
.tbtn{background:var(--panel);color:#cfe3f5;border:1px solid var(--line);border-radius:5px;padding:6px 10px;font-size:.8rem;cursor:pointer}
.tbtn.on{border-color:var(--blue);color:var(--blue)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px}
.card h3{margin:0 0 8px;font-size:.95rem;color:#fff}.card table{width:100%;border-collapse:collapse;font-size:.8rem}
.card td,.card th{padding:4px 6px;border-bottom:1px solid var(--line);text-align:right}
.card td:first-child,.card th:first-child{text-align:left;color:var(--muted)}
th.via{color:var(--via)}th.k{color:var(--k)}.mejor{font-weight:700;color:#fff;background:#1b3b2a}
.n{color:var(--muted);font-size:.72rem}
h2{font-size:.95rem;color:#fff;margin:22px 0 6px}
.grid{border-collapse:collapse;font-size:.78rem}.grid td,.grid th{border:1px solid var(--line);padding:4px 7px;text-align:center}
.grid th{color:var(--muted);font-weight:normal}.cel{min-width:120px}.vv{color:var(--via)}.kk{color:var(--k)}
.disc{border-collapse:collapse;font-size:.78rem;width:100%}.disc td,.disc th{border-bottom:1px solid var(--line);padding:4px 6px;text-align:left}
.disc th{color:var(--muted);font-weight:normal}.si{color:var(--via)}.no{color:#ef5350}
</style></head><body>
<header><h1>Vía «código MIROVA», K y MIROVA, lado a lado <span class="badge">MAQUETA S183, no es el tablero</span></h1></header>
<main>
<p class="explain">Cada noche, cada satélite que pasa sobre un volcán es una pregunta: ¿hay calor anómalo en el cráter?
MIROVA da su respuesta y nosotros la nuestra con dos detectores: la <b class="vv">vía «código MIROVA»</b> (producción desde
el 2 de noviembre en MODIS y el 11 en VIIRS) y <b class="kk">K</b> (el detector anterior, hoy de guardia). Aquí sólo cuentan
las pasadas que <b>los dos</b> procesaron, juzgadas con el mismo criterio del tablero. <b>Acierto</b>: MIROVA alertó y publicamos.
<b>Silencio</b>: MIROVA alertó y no publicamos (lo más grave). <b>Falsa alarma</b>: MIROVA miró y no vio nada, y publicamos.
Las alertas de 1 MW o más son las <b>protegidas</b>: no se puede perder ninguna.</p>
<div class="controls" id="ctl-ref"></div><div class="controls" id="ctl-vent"></div>
<div class="cards" id="cards"></div>
<h2>Volcán por volcán (alertas de MIROVA publicadas · falsas alarmas)</h2>
<p class="explain">Verde: vía. Naranjo: K. Cada celda dice cuántas alertas de MIROVA publicó cada detector y cuántas falsas alarmas dio.</p>
<div style="overflow-x:auto"><table class="grid" id="grid"></table></div>
<h2>Alertas protegidas en que la vía y K no coinciden</h2>
<p class="explain">La lista que hay que mirar una por una. «Lejos» es la distancia de nuestro foco más fuerte al centro de la
grilla de MIROVA; si el VRP de la vía calza con el de MIROVA y el foco está lejos, MIROVA midió ese foco lejano.</p>
<table class="disc" id="disc"></table>
<p class="explain" id="pie"></p>
</main>
<script>
const D = __DATOS__;
const SENS = [["MODIS","MODIS"],["VIIRS375","VIIRS 375 m"],["VIIRS750","VIIRS 750 m"]];
const VOLS = ["Lascar","Lastarria","Isluga","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Llaima","Villarrica","Copahue","PuyehueCordonCaulle","Chaiten"];
const REFS = [["tabla","Tabla de MIROVA (lo más creíble)"],["combinado","Tabla más lectura de imagen (OCR)"]];
const VENTS = [["historia","Historia: mar a oct 2026"],["adopcion","Desde la adopción"],["guardia_viirs","VIIRS desde el 3 nov (con guardia)"]];
let ref = "tabla", vent = "historia";
const pct = x => x == null ? "sin dato" : (100*x).toFixed(1).replace(".", ",") + " %";
const num = x => x == null ? "sin dato" : x.toFixed(2).replace(".", ",");
const lugar = (dc, km) => dc == null ? "sin foco" : (dc === "summit" ? "cumbre " : "lejos ") + num(km) + " km";
function botones(id, ops, get, set){ const el = document.getElementById(id); el.innerHTML = "";
  ops.forEach(([k,t]) => { const b = document.createElement("button"); b.className = "tbtn" + (get()===k?" on":""); b.textContent = t;
    b.onclick = () => { set(k); pintar(); }; el.appendChild(b); }); }
// fila(nombre, textoVia, textoK, puntajeVia, puntajeK): el resaltado compara puntajes numéricos (mayor = mejor);
// sin puntaje no se resalta.
function fila(nombre, ta, tb, pa, pb){ let ca="", cb="";
  if (typeof pa === "number" && typeof pb === "number" && pa !== pb){ ca = pa>pb?"mejor":""; cb = pa>pb?"":"mejor"; }
  return `<tr><td>${nombre}</td><td class="${ca}">${ta}</td><td class="${cb}">${tb}</td></tr>`; }
const lejania = q => q == null ? null : -Math.abs(Math.log(q));
function pintar(){
  botones("ctl-ref", REFS, () => ref, k => ref = k); botones("ctl-vent", VENTS, () => vent, k => vent = k);
  const cards = document.getElementById("cards"); cards.innerHTML = "";
  SENS.forEach(([b, nom]) => { const r = D.r[`${ref}|${vent}|${b}`]; if (!r) return; const v = r.via, k = r.k;
    cards.insertAdjacentHTML("beforeend", `<div class="card"><h3>${nom} <span class="n">${r.n} pasadas pareadas</span></h3>
    <table><tr><th></th><th class="via">vía</th><th class="k">K</th></tr>
    ${fila("Alertas de MIROVA publicadas (recall)", pct(v.recall), pct(k.recall), v.recall, k.recall)}
    ${fila("&nbsp;&nbsp;aciertos / silencios", v.TP + " / " + v.FN, k.TP + " / " + k.FN)}
    ${fila("Precisión", pct(v.precision), pct(k.precision), v.precision, k.precision)}
    ${fila("&nbsp;&nbsp;falsas alarmas en noches tranquilas", v.FP + " de " + (v.FP+v.TN), k.FP + " de " + (k.FP+k.TN))}
    ${fila("Protegidas (1 MW o más) perdidas", v.protegidas_perdidas + " de " + v.protegidas, k.protegidas_perdidas + " de " + k.protegidas, -v.protegidas_perdidas, -k.protegidas_perdidas)}
    ${fila("VRP nuestro / MIROVA (mediana; 1 = igual)", num(v.mediana_cociente), num(k.mediana_cociente), lejania(v.mediana_cociente), lejania(k.mediana_cociente))}
    </table></div>`); });
  const g = document.getElementById("grid");
  let h = "<tr><th>Volcán</th>" + SENS.map(([,n]) => `<th class="cel">${n}</th>`).join("") + "</tr>";
  VOLS.forEach(vol => { h += `<tr><th style="text-align:left">${vol}</th>`; SENS.forEach(([b]) => {
    const r = D.r[`${ref}|${vent}|${b}`]; const p = r && r.por_volcan[vol];
    if (!p) { h += "<td class='n'>sin pasadas</td>"; return; }
    const c = m => `${m.TP}/${m.TP+m.FN} · ${m.FP}`;
    h += `<td><span class="vv">${c(p.via)}</span> &nbsp; <span class="kk">${c(p.k)}</span></td>`; }); h += "</tr>"; });
  g.innerHTML = h;
  const t = document.getElementById("disc"); let rows = [];
  SENS.forEach(([b, nom]) => { const r = D.r[`${ref}|${vent}|${b}`]; if (r) r.disc.forEach(p => rows.push([nom, p])); });
  t.innerHTML = rows.length ? "<tr><th>Sensor</th><th>Volcán</th><th>Satélite</th><th>Pasada (UTC)</th><th>MIROVA</th><th>vía</th><th>K</th></tr>" +
    rows.map(([nom,p]) => `<tr><td>${nom}</td><td>${p.volcan}</td><td>${p.satelite}</td><td>${p.dt.slice(0,16).replace("T"," ")}</td>
      <td>${num(p.vrp_mirova)} MW${p.dist_ref_tabla==null?" (sólo OCR)":" a "+num(p.dist_ref_tabla)+" km"}</td>
      <td class="${p.via_pub?"si":"no"}">${p.via_pub?"publica "+num(p.via_disp)+" MW":"calla"} · ${lugar(p.via_dc, p.via_d_mc)}</td>
      <td class="${p.k_pub?"si":"no"}">${p.k_pub?"publica "+num(p.k_disp)+" MW":"calla"} · ${lugar(p.k_dc, p.k_d_mc)}</td></tr>`).join("")
    : "<tr><td class='n'>Ninguna en esta ventana y referencia.</td></tr>";
  document.getElementById("pie").textContent = `Medido el ${D.meta.generado_utc.slice(0,16).replace("T"," ")} UTC; referencia ${D.meta.referencia.fuente}; regla D-9 ${D.meta.regla_minimas}.`;
}
pintar();
</script></body></html>
"""
(AQUI / "maqueta_comparacion.html").write_text(HTML.replace("__DATOS__", json.dumps(datos, ensure_ascii=False)),
                                               encoding="utf-8")
print("->", AQUI / "maqueta_comparacion.html")
