# Bloque común de la segunda ronda S158 (se pega entero en cada prompt, después del preámbulo canónico)

```text
Segunda ronda de la auditoría S158. La primera ronda (seis auditores y tres verificadores) usó el código operacional
de VIIRS 750 que MIROVA publicó el 2026-07-24 (OSF zm62w, MIT; copia verificada en
experiments/_s158_d17_diseno/osf_codigo_mirova/) como vara, y sacó conclusiones que van a decidir cambios en el
pipeline de producción. En este proyecto los agentes ya se han equivocado antes con confianza (auditorías S138, S146,
S150 y S155 lo registran). Esta ronda existe para cambiar el método, no para repetir a los mismos agentes: tu trabajo
vale por ser INDEPENDIENTE.

Reglas de independencia (obligatorias):
- No leas docs/AUDIT_S158.md, ni nada bajo experiments/_s158_audit/ (informes f1 a f6 y v1 a v3), ni
  experiments/_s158_oraculo_mirova/, ni tests/test_oraculo_mirova_v750_s158.py, ni
  docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md, salvo que tu alcance diga explícitamente lo contrario. Tampoco las ramas
  s158-tupungatito ni s158-v750-recall. Si CLAUDE.md o la memoria te muestran una conclusión de la primera ronda
  (marcas «S158»), trátala como una afirmación a verificar, nunca como un dato.
- Escribe tus scripts desde cero. Puedes leer el código del pipeline (pipeline/, scripts/), los datos (data/), el
  código de MIROVA (los dos .m y su README) y la referencia de MIROVA.
- No leas el veredicto del A/B de D25 (no corras su evaluador sobre los datos del A/B ni abras salidas que lo
  contengan).

La vara. Para VIIRS 750, lo que dice el código de MIROVA vale más que cualquier documento, paper o memoria (decisión de
Nicolás, 2026-10-21). Lee los dos .m antes de afirmar qué hace MIROVA. Ojo: la versión publicada se declara compacta,
no completa (README.txt, «Scope»), y sus comentarios pueden rotular al revés el ROI de cumbre: comprueba contra la
matriz de ejemplo (experiments/_s158_d17_diseno/osf_codigo_mirova/Example/VIIRS750_example.mat, legible con
scipy.io.loadmat) en vez de creerle al comentario. Para MODIS y VIIRS 375 no hay código: ahí manda el paper, y una
afirmación trasladada desde VIIRS 750 se marca TRASLADADA, no CONFIRMADA.

Datos. Records: data/mirova_equivalent/<volcán>.json. Referencia NRT de MIROVA: latest_consolidado.csv (raíz del
worktree) y data/mirova_reference/mirova_v1_snapshot/; antes de usar una ventana corre
`python scripts/calidad_referencia_mirova.py` o llama a calidad_referencia_mirova.avisar(desde, hasta) (regla A119: la
tabla sirve desde marzo de 2026, el OCR está mal calibrado hasta el 2026-06-11). OSF v2.5 de MIROVA (2025, global,
por pasada: Npix, Tot_Lmir_hot, Tot_Lmir_bk, VRP, sensor, ángulos): C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv
(98 MB, está fuera del worktree, sólo lectura). Convención de sensores en nuestros records: VIIRS_SNPP, VIIRS_NOAA20,
VIIRS_NOAA21 sin sufijo = VIIRS 375 (I-band); con sufijo _750 = VIIRS 750 (M-band); MODIS_* = MODIS (regla A48:
compruébalo con un Counter antes de clasificar). Los flags efectivos se leen de pipeline.profile con
VRP_PROFILE=mirova_equivalent, nunca del YAML (regla A89). Los PDF están en
C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\documentacion\ ; una cita de paper se lee
renderizando la página a imagen con PyMuPDF (regla A95), nunca de la capa de texto.

Trabajas solo y en segundo plano. Nadie va a contestar preguntas a mitad de camino: no preguntes «¿sigo?», haz el
trabajo del alcance hasta el final. Antes de terminar, mira tu último párrafo: si es un plan o una promesa («después
haré...»), hazlo ahora. Detente sólo si algo te lo impide de verdad, y dilo. Escribe tu informe en tu carpeta a medida
que avanzas (la sesión puede cortarse): INFORME.md con, para cada afirmación de tu alcance, un VEREDICTO propio
(CONFIRMADA, CON MATIZ, REFUTADA, SIN DATO) y su evidencia; los hallazgos nuevos en el formato del preámbulo; la sección
VERIFICADO LIMPIO; y al final «Lo que no pude medir» con la razón. Un informe sin esa última sección se considera
cortado.

Límites: no edites nada fuera de tu carpeta (salvo que tu alcance lo diga); no toques pipeline/, data/ ni frontend/;
no despaches workflows; no uses credenciales de Earthdata ni descargues gránulos; no hagas git commit ni push (lo hace
quien orquesta). Scripts y salidas crudas van a tu carpeta (guarda la salida de cada script en un .txt al lado). Si
encuentras un defecto fuera de tu alcance, anótalo en «Fuera de alcance» y sigue. Disco: C: tiene unos 30 GB libres;
no escribas temporales de más de 2 GB.

Escribe en español de Chile, sin voseo, sin guiones largos ni medios (usa coma, dos puntos o paréntesis), frases
directas, sin metáforas: di lo que quieres decir. El porqué físico antes que el código. Todo número lleva script,
salida cruda, numerador, denominador y ventana temporal. Presupuesto: unas dos horas.
```
