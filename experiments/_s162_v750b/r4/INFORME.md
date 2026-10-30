# V750-B, R4: ensayo de plomería y comandos del 2026-11-03

Pedido por la coordinadora S169 (2026-10-30, «acelerar las pruebas»): dejar mecánico el día del despacho, sin abrir la
referencia de la ventana nueva y sin leer resultados. Nada de este ensayo se usa el 2026-11-03.

## 1. Ensayo del generador (2026-10-30, `--hasta 2026-10-29`)

Árbol aparte en `D:/vrp-trabajo/temporales/v750b_r4_ensayo/arbol`, armado con `git archive` (sin checkout): las
dependencias de `main` `443da8649` (`experiments/_s159/n`, `_s157_prereg_d25`, `_s158_audit_r2`, `_s158_d17_diseno`,
`scripts`, `pipeline`, `volcanoes.yaml`, `frontend/index.html`, `data/mirova_reference`) y, encima, la carpeta
`experiments/_s162_v750b` del tag `s167-v750b-adenda3-sellada`. El generador y el analizador de V750-B son idénticos en
`main` y en el tag. Datos: los `data/mirova_equivalent` de la rama de esta sesión (más viejos que los de `main`; por
eso salen menos objetivos que en el ensayo del 26). Salidas en `ensayo_20261029/`.

| paso | resultado |
|---|---|
| `objetivos_v750b.py` (sellado) | salida 0; 5.654 objetivos, 0 sin gránulo; sha256 `4d1f956d...` |
| `adenda2/objetivos_supl_v750b.py` | salida 0; control pos y neg_limpio contra la sellada **5.654 contra 5.654, IGUALES**; 19 `far_ref` con gránulo, 0 sin; sha256 suplementaria `2e774c41...`, lista del run `b0fc254e...` (5.654 + 19) |
| `r4/contar_n3_v750b.py` | 76 protegidas que deciden; **4 N-3, las 4 en la ventana O** (Láscar 2026-06-27, Nevados de Chillán 2026-10-01 y 2026-10-05, Cordón Caulle 2026-07-03); control: 5 protegidas que deciden sin alerta de la tabla (4 de Suomi NPP, 1 de NOAA), 0 en T |
| `r4/armar_rama_disparo.sh` (rama local de prueba, borrada) | los 7 archivos dentro del commit con los mismos sha256 que imprimió el generador; workflow con `OBJETIVOS` en la lista del run; diff contra `main` fuera de V750-B y del workflow: vacío |

Lo que el ensayo enseñó para el día:
- El generador necesita, además de lo que dice la adenda 2 §7, `data/mirova_reference` y
  `experiments/_s158_d17_diseno` de `main` (lo leen `referencia_mirova_unificada.py` y `02_seleccion.py`).
- `--data` tiene que ser el `data/mirova_equivalent` de `main` de ese día, no el de una rama: con datos viejos la lista
  sale más corta sin aviso.
- Las N-3 son etiquetas de la referencia, así que la cuenta del 2026-11-03 va a incluir casi seguro estas cuatro.

## 2. Ensayo de la lectura (escena sintética N1 de la batería de la adenda 3, no datos de V750-B)

Separador de la adenda 2 sobre los artefactos de la escena: 38 leídas, 38 a la parte sellada, 0 a la suplementaria.
Lector de la adenda 3 sobre la parte sellada, con el control real del censo S159 (`D:/vrp-trabajo/temporales/
s159_oraculo/censo_39713438252` y `experiments/_s159/oraculo_censo/objetivos.json` de `main`, 5.746 pasadas):
control del censo OK, compuerta ABIERTA, «ROI elegida: B4 ... [con la adenda 3, regla N-3]», salida 0, 1 N-3 listada
aparte. El lector de la adenda 1 al lado, sin N-3, deja a B2 fuera de los elegibles (la escena está hecha para eso).
Ninguna de las dos escribe en la carpeta sellada. Salidas en `ensayo_20261029/lectura_*.txt`.

## 3. Comandos del 2026-11-03 (copiar y pegar, en bash, desde este worktree)

    cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/.claude/worktrees/s162-viirs750-2-918174"
    git fetch origin --prune --tags
    M=$(git rev-parse origin/main); echo "main $M"
    R4=D:/vrp-trabajo/temporales/v750b_r4_20261103; mkdir -p $R4/arbol $R4/ref
    git -c core.autocrlf=false archive $M experiments/_s159/n experiments/_s157_prereg_d25 experiments/_s158_audit_r2 \
      experiments/_s158_d17_diseno scripts pipeline volcanoes.yaml frontend/index.html data/mirova_reference \
      data/mirova_equivalent | tar -x -C $R4/arbol
    git -c core.autocrlf=false archive s167-v750b-adenda3-sellada experiments/_s162_v750b | tar -x -C $R4/arbol
    git -c core.autocrlf=false archive claude/s162-viirs750-2-918174 experiments/_s162_v750b/r4 | tar -x -C $R4/arbol
    export TEMP=$R4/tmp TMP=$R4/tmp PYTHONIOENCODING=utf-8; mkdir -p $R4/tmp
    cd $R4/arbol
    python experiments/_s162_v750b/objetivos_v750b.py --data data/mirova_equivalent --ref-dest $R4/ref --hasta 2026-11-02 > $R4/gen1_salida.txt 2>&1; echo rc=$?
    python experiments/_s162_v750b/adenda2/objetivos_supl_v750b.py --data data/mirova_equivalent --ref-dest $R4/ref --hasta 2026-11-02 --sellado experiments/_s162_v750b/objetivos_v750b.json > $R4/gen2_salida.txt 2>&1; echo rc=$?
    python experiments/_s162_v750b/r4/contar_n3_v750b.py --objetivos experiments/_s162_v750b/objetivos_v750b.json > $R4/n3_salida.txt 2>&1; echo rc=$?
    tail -5 $R4/gen1_salida.txt; tail -6 $R4/gen2_salida.txt; cat $R4/n3_salida.txt

Antes de seguir: las dos primeras salen 0, el control dice IGUALES, 0 sin gránulo (o declarados), y la cuenta de N-3
se le informa a la coordinadora. Luego, la rama y el tag (sin push de la rama de disparo: ese push lanza el run):

    cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/.claude/worktrees/s162-viirs750-2-918174"
    tr -d '' < experiments/_s162_v750b/r4/armar_rama_disparo.sh > $R4/armar.sh   # el checkout de Windows puede traer CRLF
    bash $R4/armar.sh $R4/arbol $M s167-v750b-adenda3-sellada s169-v750b-objetivos-20261103
    git tag -a s169-v750b-objetivos-20261103 s169-v750b-objetivos-20261103 -m "V750-B: objetivos al 2026-11-02 (main $M, carpeta de V750-B de s167-v750b-adenda3-sellada), sha256 en el mensaje del pedido"
    git push origin refs/heads/s169-v750b-objetivos-20261103 refs/tags/s169-v750b-objetivos-20261103

Pedido a la coordinadora: el tag, los sha256 que imprime el armado, la cuenta de N-3, 32 trozos (`NCHUNKS`), timeout
120 min, y el despacho: `git push origin s169-v750b-objetivos-20261103:refs/heads/s162-v750b-disparo` (lo hace ella).

## 4. Lectura (cuando la coordinadora entregue los artefactos)

    R=<raíz del worktree>/experiments/_s162_v750b; EV=D:/vrp-trabajo/temporales/evaluar_d25_s161.py
    O=<árbol de $R4>/experiments/_s162_v750b
    python $R/adenda2/separar_resultados_v750b.py --art <artefactos> [<relanzamiento>] --dest $R4/sep
    python $R/adenda3/leer_n3_v750b.py --art $R4/sep/sellado/<carpetas> --objetivos $O/objetivos_v750b.json \
      --sin-granulo $O/sin_granulo_v750b.json --evaluador $EV \
      --censo-art D:/vrp-trabajo/temporales/s159_oraculo/censo_39713438252 \
      --censo-objetivos <objetivos.json del censo S159: experiments/_s159/oraculo_censo/objetivos.json de main> \
      --salida $R4/veredicto_v750b.txt
    python $R/adenda1/leer_v750b.py <los mismos argumentos> --salida $R4/sin_n3_solo_informa.txt
    python $R/adenda2/leer_posicion_v750b.py --art <artefactos> --objetivos $O/objetivos_v750b.json \
      --objetivos-supl $O/adenda2/objetivos_supl_v750b.json --sin-granulo-supl $O/adenda2/sin_granulo_supl_v750b.json \
      --evaluador $EV

El veredicto de V750-B es el del segundo comando (adenda 3 §3). El tercero y el cuarto informan. Antes de que Nicolás
confirme la ROI (§6.5), se miran juntas la lista aparte de N-3 y la ROI sin N-3 (VA3-05).

## 5. La ROI elegida, hacia la vía (preparado, sin merge)

Rama `s169-roi-v750` (`3c5c494b9`), sobre el tag defensivo `pre-s169-roi-v750` (= `main` `443da8649`, A45): el script
`scripts/roi_v750b_a_grillas.py --brazo <B0..B5> [--escribir]` reescribe sólo `roi_v750` de los 11 volcanes en
`pipeline/grillas_mirova.yaml` (B0 def, B1 sens, B2 crater, B3 inner, B4 sens en Cordón Caulle y Tupungatito y def en
el resto, B5 corona) y el comentario que dice qué ROI rige; la rama no cambia el YAML. Prueba
`tests/test_roi_v750b_variantes_s169.py`: 21 de 21 (59 con la de la vía), 4 mutaciones del script atrapadas por
aserción. El día de la lectura: en esa rama, `python scripts/roi_v750b_a_grillas.py --brazo <elegido> --escribir`,
la prueba, commit y PR; el merge y el encendido van con la frase de Nicolás.
