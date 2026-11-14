// S183: pestaña «Vía, K y MIROVA» de comparacion.html.
// POR QUÉ: Nicolás quiere ver, sin abrir scripts, si la vía «código MIROVA» (producción) se parece más a MIROVA que K
// (el detector anterior, hoy de guardia). La página NO recalcula nada: lee data/audit_continuous/comparacion_via_k.json,
// que escribe scripts/comparacion_via_k.py una vez al día con el predicado del tablero. Las métricas se juzgan por
// noche-satélite y sólo en pasadas que los dos detectores procesaron.
// Guard: tests/test_comparacion_via_k_s183.py (los campos que lee esta página existen en la salida del script).
(function () {
  "use strict";
  const URL_JSON = (typeof BASE_PATH === "string" ? BASE_PATH : "") + "data/audit_continuous/comparacion_via_k.json";
  const SENS = [["MODIS", "MODIS"], ["VIIRS375", "VIIRS 375 m"], ["VIIRS750", "VIIRS 750 m"]];
  const VOLS = [["Lascar", "Láscar"], ["Lastarria", "Lastarria"], ["Isluga", "Isluga"], ["Tupungatito", "Tupungatito"],
    ["PlanchonPeteroa", "Planchón-Peteroa"], ["NevadosDeChillan", "Nevados de Chillán"], ["Llaima", "Llaima"],
    ["Villarrica", "Villarrica"], ["Copahue", "Copahue"], ["PuyehueCordonCaulle", "Puyehue-Cordón Caulle"],
    ["Chaiten", "Chaitén"]];
  const NOMBRE_VOL = Object.fromEntries(VOLS);
  const REFS = [["tabla", "Tabla de MIROVA (lo más creíble)"], ["combinado", "Tabla más lectura de imagen (OCR)"]];
  // Historia: desde marzo de 2026 hasta el día antes de la adopción de cada sensor, K del estado guardado en el tag
  // pre-s180-reemplazo-historia. Desde la adopción: K de la guardia. Cada día cae en una sola ventana.
  const VENTS = [["historia", "Historia: desde marzo hasta la adopción"], ["adopcion", "Desde la adopción"]];
  const COLOR = { via: "#66bb6a", k: "#ffb74d", mir: "#ef5350", gris: "#7a8fa6" };
  const st = { ref: "tabla", vent: "historia", vol: "NevadosDeChillan", sens: "MODIS", soloProt: false, d: null };
  const $ = id => document.getElementById(id);
  const pct = x => x == null ? "sin dato" : (100 * x).toFixed(1).replace(".", ",") + " %";
  const num = x => x == null ? "sin dato" : Number(x).toFixed(2).replace(".", ",");
  const esc = s => String(s == null ? "" : s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const lugar = (dc, km) => dc == null ? "sin foco" : (dc === "summit" ? "cumbre" : "lejos") + (km == null ? "" : " a " + num(km) + " km");

  // Filas de noches como objetos por nombre de campo (el script manda "campos" y "filas").
  let NOCHES = [];
  function prepararNoches(d) {
    const c = d.noches.campos;
    const i = n => c.indexOf(n);
    const ix = {
      vol: i("vol"), sat: i("sat"), b: i("b"), noche: i("noche"), lab_tabla: i("lab_tabla"), lab_comb: i("lab_comb"),
      prot_tabla: i("prot_tabla"), prot_comb: i("prot_comb"), vrp_mirova: i("vrp_mirova"), via_pub: i("via_pub"),
      via_vrp: i("via_vrp"), via_dc: i("via_dc"), via_dmc: i("via_dmc"), k_pub: i("k_pub"), k_vrp: i("k_vrp"),
      k_dc: i("k_dc"), k_dmc: i("k_dmc"), k_fuente: i("k_fuente")
    };
    NOCHES = d.noches.filas.map(f => Object.fromEntries(Object.entries(ix).map(([k, j]) => [k, f[j]])));
  }
  const lab = n => st.ref === "tabla" ? n.lab_tabla : n.lab_comb;
  const prot = n => !!(st.ref === "tabla" ? n.prot_tabla : n.prot_comb);
  function rango(b) { const v = st.d.meta.ventanas[st.vent]; return v && v[b] ? v[b] : null; }

  function botones(id, ops, clave) {
    const el = $(id); el.innerHTML = "";
    ops.forEach(([k, t]) => {
      const btn = document.createElement("button");
      btn.className = "toggle-btn" + (st[clave] === k ? " active" : ""); btn.textContent = t;
      btn.addEventListener("click", () => { st[clave] = k; pintar(); });
      el.appendChild(btn);
    });
  }

  // fila(nombre, texto vía, texto K, puntaje vía, puntaje K): resalta el puntaje mayor; sin puntaje no resalta.
  function fila(nombre, ta, tb, pa, pb) {
    let ca = "", cb = "";
    if (typeof pa === "number" && typeof pb === "number" && pa !== pb) { ca = pa > pb ? "vk-mejor" : ""; cb = pa > pb ? "" : "vk-mejor"; }
    return `<tr><td>${nombre}</td><td class="${ca}">${ta}</td><td class="${cb}">${tb}</td></tr>`;
  }
  const lejania = q => q == null ? null : -Math.abs(Math.log(q));

  function pintarTarjetas() {
    const cont = $("vk-cards"); cont.innerHTML = "";
    SENS.forEach(([b, nom]) => {
      const r = st.d.resultados[`${st.ref}|${st.vent}|${b}`];
      if (!r) return;
      const v = r.via, k = r.k, rg = rango(b);
      cont.insertAdjacentHTML("beforeend", `<div class="card vk-card"><h3>${nom}
        <span class="vk-n">${rg ? rg[0] + " a " + rg[1] : ""} · ${r.n_pasadas_pareadas} pasadas de los dos</span></h3>
        <table><tr><th></th><th style="color:${COLOR.via}">vía</th><th style="color:${COLOR.k}">K</th></tr>
        ${fila("Alertas de MIROVA publicadas (recall)", pct(v.recall), pct(k.recall), v.recall, k.recall)}
        ${fila("&nbsp;&nbsp;aciertos / silencios", v.TP + " / " + v.FN, k.TP + " / " + k.FN)}
        ${fila("Precisión", pct(v.precision), pct(k.precision), v.precision, k.precision)}
        ${fila("&nbsp;&nbsp;falsas alarmas en noches tranquilas", v.FP + " de " + (v.FP + v.TN), k.FP + " de " + (k.FP + k.TN))}
        ${fila("Protegidas (1 MW o más) perdidas", v.protegidas_perdidas + " de " + v.protegidas, k.protegidas_perdidas + " de " + k.protegidas, -v.protegidas_perdidas, -k.protegidas_perdidas)}
        ${fila("VRP nuestro / MIROVA (mediana; 1 = igual)", num(v.mediana_cociente), num(k.mediana_cociente), lejania(v.mediana_cociente), lejania(k.mediana_cociente))}
        </table>${r.sin_par_via.pos || r.sin_par_k.pos ? `<div class="vk-n">Fuera de la cuenta, alertas de MIROVA en pasadas
        que sólo un detector tiene: ${r.sin_par_via.pos} sólo en la vía (publica ${r.sin_par_via.pos_publica}),
        ${r.sin_par_k.pos} sólo en K (publica ${r.sin_par_k.pos_publica}).</div>` : ""}</div>`);
    });
  }

  function pintarGrilla() {
    let h = "<tr><th>Volcán</th>" + SENS.map(([, n]) => `<th>${n}</th>`).join("") + "</tr>";
    VOLS.forEach(([vol, nom]) => {
      h += `<tr><th class="vk-izq">${nom}</th>`;
      SENS.forEach(([b]) => {
        const r = st.d.resultados[`${st.ref}|${st.vent}|${b}`];
        const p = r && r.por_volcan && r.por_volcan[vol];
        if (!p) { h += "<td class='vk-n'>sin pasadas</td>"; return; }
        const c = m => `${m.TP} de ${m.TP + m.FN} · ${m.FP}`;
        h += `<td><span style="color:${COLOR.via}">${c(p.via)}</span><br><span style="color:${COLOR.k}">${c(p.k)}</span></td>`;
      });
      h += "</tr>";
    });
    $("vk-grid").innerHTML = h;
  }

  // Franja por noche: tres filas (MIROVA, vía, K), un punto por noche-satélite con algo que mirar.
  function pintarFranja() {
    const rg = rango(st.sens);
    const svg = $("vk-franja");
    if (!rg) { svg.innerHTML = ""; $("vk-franja-nota").textContent = "Esta ventana no tiene ese sensor."; return; }
    const t0 = Date.parse(rg[0] + "T00:00:00Z"), t1 = Date.parse(rg[1] + "T00:00:00Z") + 86400000;
    const W = 900, H = 160, x0 = 70, x1 = W - 10, filas = [["MIROVA", 34], ["vía", 82], ["K", 130]];
    const X = d => x0 + (x1 - x0) * (Date.parse(d + "T12:00:00Z") - t0) / (t1 - t0);
    let g = filas.map(([n, y]) => `<text x="4" y="${y + 4}" class="vk-et">${n}</text><line x1="${x0}" x2="${x1}" y1="${y}" y2="${y}" class="vk-eje"/>`).join("");
    const meses = [];
    for (let d = new Date(t0); d.getTime() < t1; d.setUTCDate(d.getUTCDate() + 1)) {
      if (d.getUTCDate() === 1 || d.getTime() === t0) meses.push(d.toISOString().slice(0, 10));
    }
    g += meses.map(m => `<line x1="${X(m)}" x2="${X(m)}" y1="14" y2="${H - 6}" class="vk-mes"/><text x="${X(m) + 2}" y="10" class="vk-et">${m.slice(0, 7)}</text>`).join("");
    g += `<text x="${x1}" y="${H - 2}" text-anchor="end" class="vk-et">${rg[0]} a ${rg[1]}</text>`;
    const sel = NOCHES.filter(n => n.vol === st.vol && n.b === st.sens && n.noche >= rg[0] && n.noche <= rg[1]);
    // Dos satélites pueden pasar la misma noche: un renglón por satélite dentro de cada fila, para que un punto y una
    // cruz de la misma noche no queden encima.
    const sats = [...new Set(sel.map(n => n.sat))].sort();
    const dy = n => (sats.indexOf(n.sat) - (sats.length - 1) / 2) * 9;
    let nAl = 0, nSilV = 0, nSilK = 0;
    sel.forEach(n => {
      const x = X(n.noche).toFixed(1), l = lab(n), pr = prot(n);
      const tip = `${n.noche} ${n.sat}: MIROVA ${l === "pos" ? "alerta " + num(n.vrp_mirova) + " MW" : l === "neg" ? "miró y no vio nada" : "sin juicio"}; `
        + `vía ${n.via_pub == null ? "sin record" : n.via_pub ? "publica " + num(n.via_vrp) + " MW" : "calla"} (${lugar(n.via_dc, n.via_dmc)}); `
        + `K ${n.k_pub == null ? "sin record" : n.k_pub ? "publica " + num(n.k_vrp) + " MW" : "calla"} (${lugar(n.k_dc, n.k_dmc)}${n.k_fuente ? ", " + n.k_fuente : ""})`;
      const ym = 34 + dy(n);
      if (l === "pos") { nAl++; g += `<circle cx="${x}" cy="${ym}" r="${pr ? 5 : 3}" fill="${COLOR.mir}"><title>${esc(tip)}</title></circle>`; }
      else if (l === "neg") g += `<circle cx="${x}" cy="${ym}" r="2.5" fill="none" stroke="${COLOR.gris}"><title>${esc(tip)}</title></circle>`;
      [["via_pub", 82 + dy(n), COLOR.via], ["k_pub", 130 + dy(n), COLOR.k]].forEach(([c, y, col]) => {
        if (n[c] === 1) g += `<circle cx="${x}" cy="${y}" r="3.5" fill="${col}"><title>${esc(tip)}</title></circle>`;
        else if (n[c] === 0 && l === "pos") {
          if (c === "via_pub") nSilV++; else nSilK++;
          g += `<path d="M${x - 4},${y - 4}L${+x + 4},${y + 4}M${x - 4},${y + 4}L${+x + 4},${y - 4}" stroke="${COLOR.mir}" stroke-width="1.6"><title>${esc(tip)}</title></path>`;
        }
      });
    });
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.innerHTML = g;
    $("vk-franja-nota").textContent = sel.length
      ? `${nAl} noches-satélite con alerta de MIROVA; silencios: vía ${nSilV}, K ${nSilK}. Dentro de cada fila, un renglón por satélite (de arriba abajo: ${sats.join(", ")}). Pasa el puntero sobre un punto para ver el detalle.`
      : "Sin noches con alerta de MIROVA ni publicaciones en esta ventana.";
  }

  function pintarDesacuerdos() {
    const filas = [];
    SENS.forEach(([b, nom]) => {
      const rg = rango(b); if (!rg) return;
      NOCHES.forEach(n => {
        if (n.b !== b || n.noche < rg[0] || n.noche > rg[1] || n.via_pub == null || n.k_pub == null || n.via_pub === n.k_pub) return;
        const l = lab(n); if (l !== "pos" && l !== "neg") return;
        if (st.soloProt && !prot(n)) return;
        filas.push([nom, n, l]);
      });
    });
    filas.sort((a, b) => a[1].noche < b[1].noche ? 1 : a[1].noche > b[1].noche ? -1 : 0);
    const MAX = 300;
    $("vk-disc-nota").textContent = `${filas.length} noches-satélite en que la vía y K no coinciden` + (filas.length > MAX ? ` (se muestran las ${MAX} más recientes).` : ".");
    $("vk-disc").innerHTML = filas.length ? "<tr><th>Noche</th><th>Volcán</th><th>Satélite</th><th>MIROVA</th><th>vía</th><th>K</th><th>¿Quién coincide?</th></tr>" +
      filas.slice(0, MAX).map(([nom, n, l]) => {
        const acierta = l === "pos" ? (n.via_pub ? "vía" : "K") : (n.via_pub ? "K" : "vía");
        return `<tr><td>${n.noche}</td><td>${esc(NOMBRE_VOL[n.vol] || n.vol)}</td><td>${esc(n.sat)}</td>
        <td>${l === "pos" ? "alerta " + num(n.vrp_mirova) + " MW" + (prot(n) ? " (protegida)" : "") : "miró y no vio nada"}</td>
        <td class="${n.via_pub ? "vk-si" : "vk-no"}">${n.via_pub ? "publica " + num(n.via_vrp) + " MW" : "calla"} · ${lugar(n.via_dc, n.via_dmc)}</td>
        <td class="${n.k_pub ? "vk-si" : "vk-no"}">${n.k_pub ? "publica " + num(n.k_vrp) + " MW" : "calla"} · ${lugar(n.k_dc, n.k_dmc)}</td>
        <td style="color:${acierta === "vía" ? COLOR.via : COLOR.k}">${acierta}</td></tr>`;
      }).join("") : "<tr><td class='vk-n'>Ninguna en esta ventana y referencia.</td></tr>";
  }

  function pintarEstado() {
    const m = st.d.meta;
    const edadH = (Date.now() - Date.parse(m.generado_utc)) / 3600000;
    const avisos = (m.avisos || []).slice();
    if (edadH > 48) avisos.push(`Este cálculo tiene ${Math.round(edadH / 24)} días: el refresco diario no está corriendo (workflow «Comparacion via, K y MIROVA»).`);
    $("vk-avisos").innerHTML = avisos.map(a => `<div class="vk-aviso">⚠️ ${esc(a)}</div>`).join("");
    $("vk-estado").textContent = `Calculado el ${m.generado_utc.slice(0, 16).replace("T", " ")} UTC · última pasada en la tabla de MIROVA: ${(m.ultima_fila_tabla_mirova || "sin dato").slice(0, 16)} · guardia K hasta: ${m.guardia_hasta || "sin dato"} · adopción de la vía: MODIS ${m.adopcion.MODIS}, VIIRS ${m.adopcion.VIIRS375}.`;
  }

  function pintar() {
    botones("vk-ctl-ref", REFS, "ref"); botones("vk-ctl-vent", VENTS, "vent");
    pintarEstado(); pintarTarjetas(); pintarGrilla(); pintarFranja(); pintarDesacuerdos();
  }

  async function iniciar() {
    const sv = $("vk-vol"), ss = $("vk-sens");
    VOLS.forEach(([v, n]) => sv.insertAdjacentHTML("beforeend", `<option value="${v}">${n}</option>`));
    SENS.forEach(([b, n]) => ss.insertAdjacentHTML("beforeend", `<option value="${b}">${n}</option>`));
    sv.value = st.vol; ss.value = st.sens;
    sv.addEventListener("change", () => { st.vol = sv.value; pintarFranja(); });
    ss.addEventListener("change", () => { st.sens = ss.value; pintarFranja(); });
    $("vk-solo-prot").addEventListener("change", e => { st.soloProt = e.target.checked; pintarDesacuerdos(); });
    try {
      const r = await fetch(URL_JSON, { cache: "no-cache" });
      if (!r.ok) throw new Error("HTTP " + r.status);
      st.d = await r.json();
    } catch (e) {
      $("vk-avisos").innerHTML = `<div class="vk-aviso">⚠️ No pude leer ${esc(URL_JSON)} (${esc(e.message)}).</div>`;
      return;
    }
    prepararNoches(st.d);
    pintar();
  }
  iniciar();
})();
