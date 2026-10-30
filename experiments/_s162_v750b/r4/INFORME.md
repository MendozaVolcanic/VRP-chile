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
    unset VRP_PROFILE; echo "VRP_PROFILE=[${VRP_PROFILE-}]"     # P1-03: tiene que imprimir [] (vacío)
    python experiments/_s162_v750b/r4/control_previo_v750b.py datos --data data/mirova_equivalent --hasta 2026-11-02 | tee $R4/datos_salida.txt   # P1-04: OK o no se genera
    python experiments/_s162_v750b/objetivos_v750b.py --data data/mirova_equivalent --ref-dest $R4/ref --hasta 2026-11-02 > $R4/gen1_salida.txt 2>&1; echo rc=$?
    python experiments/_s162_v750b/adenda2/objetivos_supl_v750b.py --data data/mirova_equivalent --ref-dest $R4/ref --hasta 2026-11-02 --sellado experiments/_s162_v750b/objetivos_v750b.json > $R4/gen2_salida.txt 2>&1; echo rc=$?
    python experiments/_s162_v750b/r4/contar_n3_v750b.py --objetivos experiments/_s162_v750b/objetivos_v750b.json > $R4/n3_salida.txt 2>&1; echo rc=$?
    tail -5 $R4/gen1_salida.txt; tail -6 $R4/gen2_salida.txt; cat $R4/n3_salida.txt

**Reglas del día antes de generar** (auditoría de patrones S169, f1, con su verificador; se cumplen antes de mirar
ninguna salida): (P1-03) `VRP_PROFILE` vacío: con un perfil diurno en el shell, como `_s154_ab_diurno_k_on`, la pasada
diurna V750 de Láscar del 2026-10-15 17:00 UTC no se descarta (medido sobre `main` `443da8649`); (P1-04) la fecha máxima
de los records VIIRS 750 de `data/` de `main` del día es mayor o igual que `--hasta`, impresa en `datos_salida.txt`.

Antes de seguir: las dos primeras salen 0, el control dice IGUALES, 0 sin gránulo (o declarados), y la cuenta de N-3
se le informa a la coordinadora. Luego, la rama y el tag (sin push de la rama de disparo: ese push lanza el run):

    cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/.claude/worktrees/s162-viirs750-2-918174"
    tr -d '\r' < experiments/_s162_v750b/r4/armar_rama_disparo.sh > $R4/armar.sh   # el checkout de Windows puede traer CRLF
    bash $R4/armar.sh $R4/arbol $M s167-v750b-adenda3-sellada s169-v750b-objetivos-20261103
    git tag -a s169-v750b-objetivos-20261103 s169-v750b-objetivos-20261103 -m "V750-B: objetivos al 2026-11-02 (main $M, carpeta de V750-B de s167-v750b-adenda3-sellada), sha256 en el mensaje del pedido"
    git push origin refs/heads/s169-v750b-objetivos-20261103 refs/tags/s169-v750b-objetivos-20261103

Pedido a la coordinadora: el tag, los sha256 que imprime el armado, la cuenta de N-3, 32 trozos (`NCHUNKS`), timeout
120 min, y el despacho: `git push origin s169-v750b-objetivos-20261103:refs/heads/s162-v750b-disparo` (lo hace ella).

## 4. Lectura (cuando la coordinadora entregue los artefactos)

Todo desde el árbol `$R4/arbol` del día (dependencias de `main` del día, carpeta de V750-B del tag sellado; P1-01), no
desde este worktree:

    cd $R4/arbol; unset VRP_PROFILE; export TEMP=$R4/tmp TMP=$R4/tmp PYTHONIOENCODING=utf-8
    R=experiments/_s162_v750b; EV=D:/vrp-trabajo/temporales/evaluar_d25_s161.py
    CA=D:/vrp-trabajo/temporales/s159_oraculo/censo_39713438252
    git -C "<worktree>" show origin/main:experiments/_s159/oraculo_censo/objetivos.json > $R4/objetivos_censo_s159.json
    python $R/adenda2/separar_resultados_v750b.py --art <artefactos> [<relanzamiento>] --dest $R4/sep
    python $R/r4/control_previo_v750b.py lectura --art $R4/sep/sellado/* --objetivos $R/objetivos_v750b.json \
      --censo-art $CA --manifiesto $R4/lectura/manifiesto.json --insumo $R/sin_granulo_v750b.json $EV \
      $R4/objetivos_censo_s159.json --argumentos "<línea exacta del lector>"      # tiene que decir OK
    [ -e $R4/lectura/veredicto_v750b.txt ] && echo "YA EXISTE: no se pisa" || \
    python $R/adenda3/leer_n3_v750b.py --art $R4/sep/sellado/* --objetivos $R/objetivos_v750b.json \
      --sin-granulo $R/sin_granulo_v750b.json --evaluador $EV --censo-art $CA \
      --censo-objetivos $R4/objetivos_censo_s159.json --salida $R4/lectura/veredicto_v750b.txt
    python $R/adenda1/leer_v750b.py <los mismos argumentos> --salida $R4/lectura/sin_n3_solo_informa.txt
    python $R/adenda2/leer_posicion_v750b.py --art <artefactos> --objetivos $R/objetivos_v750b.json \
      --objetivos-supl $R/adenda2/objetivos_supl_v750b.json --sin-granulo-supl $R/adenda2/sin_granulo_supl_v750b.json \
      --evaluador $EV > $R4/lectura/posicion_solo_informa.txt

El veredicto de V750-B es el del lector de la adenda 3 (adenda 3 §3). Los otros dos informan. Antes de que Nicolás
confirme la ROI (§6.5), se miran juntas la lista aparte de N-3 y la ROI sin N-3 (VA3-05).

**Reglas del día para leer** (auditoría S169, f1; escritas antes de ver datos):
- (P1-01) el lector corre desde `$R4/arbol`, no desde este worktree, aunque hoy dé lo mismo.
- (VF1-01) el control previo comprueba que `--censo-art` exista y traiga resultados: con una ruta errada el analizador
  imprime «{} FALLA», igual que un censo distinto. Si falla por la ruta, se corrige y se relee.
- (VF1-03) el control previo coteja volcán y hora de cada resultado con el objetivo de su id; el analizador sellado
  empareja sólo por id. Además, el sha256 de `objetivos_v750b.json` del tag de disparo tiene que ser el que se pasa.
- (P1-02) **nunca** se pasa `--leer-con-faltantes` si la línea «== control B0 y B1 = censo S159» dice FALLA con alguna
  clave `*_DISTINTO`: el texto sellado (pre-registro l. 211 a 214) sólo permite la bandera cuando el censo «no se puede
  correr», y el código la acepta también para uno que corrió y salió distinto. Si dice FALLA con `{}`, es la ruta
  (VF1-01). Si dice OK, la bandera cubre sólo la cobertura, y sólo con la decisión de la coordinadora con Nicolás.
- (P1-05) el manifiesto guarda los sha256 de objetivos, resultados, censo, evaluador y la línea de argumentos; el
  veredicto va a un archivo nuevo (no se pisa ninguno), y la carpeta `lectura/` se commitea en esta rama ANTES de
  mostrarle el resultado a nadie.

## 5. La ROI elegida, hacia la vía (preparado, sin merge)

Rama `s169-roi-v750` (`3c5c494b9`; con las pruebas de `main()` y la doble aplicación de P1-13 y VF1-02 en
`cd5aa300c`: 32 de 32, 70 con la de la vía, nulo 9 de 9 atrapadas por aserción), sobre el tag defensivo `pre-s169-roi-v750` (= `main` `443da8649`, A45): el script
`scripts/roi_v750b_a_grillas.py --brazo <B0..B5> [--escribir]` reescribe sólo `roi_v750` de los 11 volcanes en
`pipeline/grillas_mirova.yaml` (B0 def, B1 sens, B2 crater, B3 inner, B4 sens en Cordón Caulle y Tupungatito y def en
el resto, B5 corona) y el comentario que dice qué ROI rige; la rama no cambia el YAML. Prueba
`tests/test_roi_v750b_variantes_s169.py`: 21 de 21 (59 con la de la vía), 4 mutaciones del script atrapadas por
aserción. El día de la lectura: en esa rama, `python scripts/roi_v750b_a_grillas.py --brazo <elegido> --escribir`,
la prueba, commit y PR; el merge y el encendido van con la frase de Nicolás.
