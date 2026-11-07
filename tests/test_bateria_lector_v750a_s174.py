# -*- coding: utf-8 -*-
"""S174 (VPR953-04): la batería del lector de la sombra de V750-A corre en el CI.

POR QUÉ. `experiments/_s162_v750a/evaluar_v750a.py --fase sombra` decide si VIIRS 750 de producción cambia de detector
en los once volcanes. Su batería (`probar_evaluar_v750a.py`) y su medidor de mutaciones (`mutar_evaluar_v750a.py`) sólo
los corría alguien a mano: nada en `tests/` ni en `.github/` los ejecutaba, así que un cambio que rompiera el lector
pasaba con el CI en verde (verificador de #953). Esta prueba corre la batería ENTERA en el CI y exige que cada escenario
salga OK, y un subconjunto barato del medidor muestra, en la misma máquina del CI, que la batería puede ponerse roja.

Lo que la batería necesita y el checkout de profundidad 1 no trae:
- los commits reales con que los escenarios de sombra cortan la lectura (`git merge-base --is-ancestor`): el paso
  «Historia de commits de main» de `.github/workflows/tests.yml` baja la historia de main sin árboles ni blobs (unos 4 MB);
- el evaluador `experiments/_s157_prereg_d25/evaluar_d25.py` del tag `s161-d25-lectura`: su blob en main es el mismo
  (S174, `git diff --stat s161-d25-lectura origin/main -- <archivo>` vacío), así que se usa el del árbol;
- node (el predicado del tablero), que el runner trae;
- que `TZ=XXX-12` ponga el proceso en UTC+12 (ER45 y ER47): si la plataforma ignorara TZ, ER45 dejaría de ver la
  conversión a la zona local (MR75) en una máquina en UTC y la batería seguiría en verde sin vigilarla.

Control de que esta prueba puede fallar: con `V750A_LECTOR_MODULO` apuntando a una copia mutada del lector (en la misma
carpeta, para que resuelva las mismas rutas), `test_la_bateria_entera_sale_ok` tiene que fallar por aserción.

Segunda vuelta (verificador de #954). El juez de la batería es la batería misma: vaciar las aserciones de un escenario
(ER54 sin `tiene` ni `no_tiene`) dejaba las cuatro pruebas en verde (VPR954-01). Por eso
`test_la_bateria_y_su_medidor_tienen_la_huella_fijada` fija el sha256 de `probar_evaluar_v750a.py` y
`mutar_evaluar_v750a.py` (fines de línea normalizados a LF, así da lo mismo en Windows con autocrlf y en Linux): todo
cambio a los escenarios, a su juez (`correr`) o al medidor tiene que venir con la huella nueva en este archivo, y eso se
ve en el diff. Y el medidor reconoce una atrapada «sólo por la bandera "no se cae"» por un texto (`BANDERA`) copiado de
`probar_evaluar_v750a.py`; si ese texto cambia, el rótulo vuelve a decir «por aserción» en silencio (VPR954-02):
`test_la_bandera_del_medidor_es_el_texto_que_emite_la_bateria` lo compara con lo que la batería emite de verdad.
"""
import datetime
import hashlib
import importlib.util
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "_s162_v750a"
PRUEBAS = EXP / "probar_evaluar_v750a.py"
MEDIDOR = EXP / "mutar_evaluar_v750a.py"
LECTOR = Path(os.environ.get("V750A_LECTOR_MODULO") or EXP / "evaluar_v750a.py")
EVALUADOR_RUTA = "experiments/_s157_prereg_d25/evaluar_d25.py"
# Conteo fijo a propósito: un escenario que desaparece (o uno nuevo que no se anota aquí) pone la prueba en rojo.
N_ESCENARIOS = 105
# Los escenarios son independientes (cada uno en su carpeta); en grupos paralelos la batería cabe holgada en el job
# `bateria-v750a` de 40 min (158 s en el CI de #954).
GRUPOS = 4
# VPR954-01: sha256 de probar_evaluar_v750a.py y mutar_evaluar_v750a.py con fines de línea LF (ver _huella_bateria).
# Se actualiza A PROPÓSITO, con el valor que imprime la prueba cuando falla, después de correr el medidor sobre los
# escenarios tocados.
HUELLA_BATERIA = "b5222101be801e2039ebdd89fab2409bd17b8721e1d3a72a3b24abf8b8c69335"


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


P = _cargar("probar_evaluar_v750a_t", PRUEBAS)
M = _cargar("mutar_evaluar_v750a_t", MEDIDOR)


def _huella_bateria():
    """sha256 de los dos archivos leídos del disco (así ve también un cambio sin commitear) con CRLF pasado a LF."""
    h = hashlib.sha256()
    for ruta in (PRUEBAS, MEDIDOR):
        h.update(ruta.name.encode("utf-8") + b"\0" + ruta.read_bytes().replace(b"\r\n", b"\n") + b"\0")
    return h.hexdigest()


def test_la_bateria_y_su_medidor_tienen_la_huella_fijada():
    """VPR954-01: un escenario con las aserciones vaciadas sigue saliendo OK, así que la corrida no lo ve; la huella sí."""
    h = _huella_bateria()
    assert h == HUELLA_BATERIA, (
        f"la huella de {PRUEBAS.name} y {MEDIDOR.name} (sha256, fines de línea LF) es {h} y esta prueba fija "
        f"{HUELLA_BATERIA}. Cambió la batería del lector de V750-A, su juez o su medidor. Si es a propósito: corre el "
        f"medidor (python {MEDIDOR.name} --dest <tmp> --evaluador <evaluar_d25.py del blob de git> --solo <MR> "
        f"--escenarios <los tocados>), confirma que ningún escenario perdió aserciones, anota el resultado en el PR y "
        f"copia {h} en HUELLA_BATERIA de {Path(__file__).name}.")


def _evaluador(tmp):
    """El blob de git, no el archivo del disco: el lector fija el sha256 de los bytes y con autocrlf (Windows) el disco
    trae CRLF. El lector mismo rechaza un contenido distinto del del tag s161-d25-lectura."""
    ruta = tmp / "evaluar_d25.py"
    ruta.write_bytes(subprocess.run(["git", "cat-file", "blob", f"HEAD:{EVALUADOR_RUTA}"], cwd=ROOT,
                                    capture_output=True, check=True).stdout)
    return ruta


def _env(tmp):
    t = str(tmp)
    return dict(os.environ, TEMP=t, TMP=t, TMPDIR=t, PYTHONIOENCODING="utf-8")


def test_los_commits_reales_de_la_bateria_estan_en_el_clon():
    """Sin estos commits los escenarios de sombra no pueden dar lo esperado; en el CI los trae el paso de tests.yml."""
    faltan = [s for s in (P.SHA_REAL_B0, P.SHA_REAL_B4, P.SHA_CORTE_PRUEBA)
              if subprocess.run(["git", "cat-file", "-e", f"{s}^{{commit}}"], cwd=ROOT,
                                capture_output=True).returncode != 0]
    assert not faltan, (f"faltan commits {faltan}: el clon es superficial; en el CI los baja el paso «Historia de "
                        "commits de main» de .github/workflows/tests.yml")
    o = subprocess.run(["git", "merge-base", "--is-ancestor", P.SHA_CORTE_PRUEBA, P.SHA_REAL_B4], cwd=ROOT,
                       capture_output=True)
    assert o.returncode == 0, "SHA_CORTE_PRUEBA tiene que ser ancestro de SHA_REAL_B4 (la historia está cortada)"


def test_tz_de_er45_y_er47_pone_el_proceso_en_utc_mas_12(tmp_path):
    """ER45 y ER47 sólo vigilan la zona si TZ surte efecto en esta plataforma (Windows lo medía; Linux era SIN DATO)."""
    zonas = {P.ESCENARIOS[n]["env"]["TZ"] for n in ("ER45", "ER47")}
    assert zonas == {"XXX-12"}, zonas
    cod = ("import datetime; print(datetime.datetime(2026, 11, 7, 12, 0, tzinfo=datetime.timezone.utc)"
           ".astimezone().utcoffset().total_seconds())")
    o = subprocess.run([sys.executable, "-c", cod], capture_output=True, text=True,
                       env=dict(_env(tmp_path), TZ="XXX-12"))
    assert o.returncode == 0, o.stderr
    assert float(o.stdout.strip()) == 12 * 3600, f"con TZ=XXX-12 el desfase local es {o.stdout.strip()} s, no 43200"


def test_la_bandera_del_medidor_es_el_texto_que_emite_la_bateria(tmp_path):
    """VPR954-02: el medidor rotula «sólo por la bandera "no se cae"» buscando BANDERA en la línea de la falla. Aquí la
    batería corre ER53 (no_traceback=True) contra un lector falso que sólo lanza una excepción, y la falla que emite
    tiene que contener BANDERA; si alguien cambia uno de los dos textos, el rótulo de MR74 volvería a decir «por
    aserción» sin que nada se pusiera rojo."""
    falso = tmp_path / "lector_que_se_cae.py"
    falso.write_text("raise RuntimeError('lector falso: se cae a propósito')\n", encoding="utf-8")
    est, det = P.correr("ER53", P.ESCENARIOS["ER53"], falso, _evaluador(tmp_path), tmp_path / "dest")
    assert est == "FALLA" and len(det) == 1, (est, det)
    assert M.BANDERA in det[0], (f"BANDERA de {MEDIDOR.name} ({M.BANDERA!r}) no está en la falla que emite "
                                 f"{PRUEBAS.name} para un escenario que afirma que no se cae: {det[0]!r}")


def _correr_grupo(args):
    k, nombres, tmp, evaluador = args
    dest = tmp / f"grupo{k}"
    dest.mkdir()
    o = subprocess.run([sys.executable, str(PRUEBAS), "--dest", str(dest), "--analizador", str(LECTOR),
                        "--evaluador", str(evaluador), "--solo", ",".join(nombres)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(EXP),
                       env=_env(tmp), timeout=1800)
    return nombres, o


def test_la_bateria_entera_sale_ok(tmp_path):
    nombres = sorted(P.ESCENARIOS)
    assert len(nombres) == N_ESCENARIOS, f"la batería tiene {len(nombres)} escenarios; esta prueba fija {N_ESCENARIOS}"
    grupos = [nombres[k::GRUPOS] for k in range(GRUPOS)]
    evaluador = _evaluador(tmp_path)
    t0 = datetime.datetime.now()
    with ThreadPoolExecutor(GRUPOS) as ex:
        res = list(ex.map(_correr_grupo, [(k, g, tmp_path, evaluador) for k, g in enumerate(grupos)]))
    print(f"batería del lector V750-A: {len(nombres)} escenarios en {GRUPOS} grupos, "
          f"{(datetime.datetime.now() - t0).total_seconds():.0f} s")
    estado, malos, resumenes = {}, [], []
    for g, o in res:
        for linea in o.stdout.splitlines():
            if " | " in linea and linea.split(" | ")[0] in g:
                nom, est = linea.split(" | ")[:2]
                estado[nom] = est.strip()
                if estado[nom] != "OK":
                    malos.append(linea[:400])
        resumenes.append((o.returncode, next((x for x in o.stdout.splitlines() if x.startswith("== PRUEBAS")),
                                             "(sin línea de pruebas) " + o.stderr[-300:]), len(g)))
    assert not malos, f"{len(malos)} escenarios no salen OK:\n" + "\n".join(malos)
    assert sorted(estado) == nombres, f"escenarios sin resultado: {sorted(set(nombres) - set(estado))}"
    for rc, linea, n in resumenes:
        assert rc == 0 and linea == f"== PRUEBAS: TODOS LOS ESCENARIOS COMO SE ESPERA ({n})", (rc, linea)
    assert sum(n for _rc, _l, n in resumenes) == N_ESCENARIOS


def test_el_medidor_atrapa_un_subconjunto_barato_en_esta_maquina(tmp_path):
    """La batería puede ponerse roja aquí (A110): IDENTIDAD pasa, CAIDA se cae, y tres mutaciones se atrapan por
    aserción. MR75 (la zona de --ahora a la hora local) sólo se ve si TZ=XXX-12 surte efecto en ER45; MR73 y MR76 rompen
    la regla de 14 noches de los volcanes sin cambio con B0 (ER55 y ER56). VPR954-02: MR74 (el OverflowError de --ahora
    sin capturar) se atrapa en ER53 SÓLO por la bandera «no se cae» y tiene que salir rotulada así; es el control
    positivo del rótulo en el CI. ER53 sale por argparse antes de cargar los objetivos (con él solo, CAIDA daría PASA en
    falso); ER45, ER54, ER55 y ER56 sí los cargan, así que CAIDA significa algo."""
    dest = tmp_path / "medidor"
    o = subprocess.run([sys.executable, str(MEDIDOR), "--dest", str(dest), "--evaluador", str(_evaluador(tmp_path)),
                        "--hilos", "4", "--solo", "MR73,MR74,MR75,MR76", "--escenarios", "ER45,ER53,ER54,ER55,ER56"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(EXP),
                       env=_env(tmp_path), timeout=1800)
    txt = o.stdout + o.stderr
    print(txt)
    lineas = {x.split(" | ")[0]: x.split(" | ")[1] for x in o.stdout.splitlines() if " | " in x}
    assert lineas.get("IDENTIDAD", "").startswith("PASA "), txt
    assert lineas.get("CAIDA", "").startswith("CAÍDA "), txt
    for m in ("MR73", "MR75", "MR76"):
        assert lineas.get(m, "").startswith("ATRAPADA "), (m, txt)
    assert "sólo por la bandera" not in "".join(x for x in o.stdout.splitlines() if x.startswith(("MR73", "MR75",
                                                                                                    "MR76"))), txt
    assert lineas.get("MR74", "").startswith('ATRAPADA sólo por la bandera "no se cae" '), ("MR74", txt)
    resumen = next((x for x in o.stdout.splitlines() if x.startswith("== RESUMEN")), "")
    assert resumen.startswith("== RESUMEN: 4 de 4 mutaciones atrapadas (3 por aserción sobre la salida, 1 sólo por la "
                              'bandera "no se cae")'), txt
    assert o.returncode == 0, txt
