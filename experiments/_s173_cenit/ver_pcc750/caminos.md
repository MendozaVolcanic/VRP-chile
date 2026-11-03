# caminos.md: por donde podria estar mal cada afirmacion del auditor de pcc750

Escrito ANTES de abrir ningun archivo citado (solo se listo el directorio pcc750/ y se leyo
el prompt de la tarea y el CLAUDE.md del proyecto). No se edita despues; lo que se aprenda va al
INFORME.md.

Verificador: Claude Fable 5.1 (claude-fable-5-1), esfuerzo del agente: el que fijo el orquestador
(no lo puedo leer desde adentro; lo declaro como SIN DATO y lo repito en el informe).

Afirmaciones recibidas (titulo + numero + gravedad cuando la dio la tarea):

A1. K por pasada, abril a noviembre, 53 alertas: 0,571 bajo 30 y 0,117 sobre 30 con ceros;
    Spearman -0,508 fuera del barajado; en la ventana del auto-audit (22) la pendiente no es
    significativa.
A2. El anillo de K es 3,6 K mas tibio que el fondo local de MIROVA y el lacolito sobresale solo
    4,7 K; en la grilla, poner ese fondo baja el codigo de MIROVA de 1,00 a 0,18; en el granulo
    nativo K 0,425 y F 1,128.
A3. La pendiente sale de fracasos de K (6 de 18 contra 8 de 11).
A4. Ni posicion ni suma (explican la caida).
A5. La caja 7 x 7 del ejemplo no alerta en ninguna de 72 pasadas de PCC (gravedad 3); por eso uso
    cajas B1 y B3 de V750-B.
A6. El anillo de oraculo_ablacion.py va de inner a 25 km, no de 5 a 25 (con inner 20 en PCC).
A7. El codigo de MIROVA en la grilla tampoco es plano en PCC (-0,47); F queda 1,3 sobre MIROVA
    sin ceros.

## Caminos generales (aplican a todas)

G1. Instrumento mide otra cosa: la «razon» debe ser VRP nuestro / VRP MIROVA en la MISMA pasada
    (mismo minuto de Fecha_Satelite_UTC). Si el auditor pareo por noche, por dia o con tolerancia
    de horas, la dependencia del cenit se esconde o se inventa.
G2. Campo equivocado para «VRP nuestro»: en VIIRS 750 el tablero publica pc.vrp_mw (A10), no
    record.vrp_mw ni f5_core_vrp_mw. Si uso record.vrp_mw entra la suma de escena y el tope D9.
G3. Campo equivocado para el cenit: hay que ver que campo del record uso (sensor zenith del
    pixel pico, del centro del volcan, media de la escena). Si lo tomo del granulo y no del
    record, puede ser otra pasada.
G4. La vara: MIROVA = scraper Mirova-v1 (snapshot), con A119 (ventana desde abril para VIIRS por
    pasada) y lectura A + regla SN (alertas de 0,05 MW o menos cuentan como «no vio nada»).
    Posibles fallas: uso del consolidado congelado y no del snapshot vivo; nombre del volcan con
    variantes (A14: «Puyehue-Cordon Caulle» con guion); sensor mal filtrado (VIIRS 750 = sufijo
    _750, A48); alertas de 0,05 o menos contadas como positivas; dia/noche no separado.
G5. Ventana: «abril a noviembre» con 53 alertas. Si la ventana cruza #535 (2026-08-28) o
    #850/#883 (K en el historico) mezcla regimenes (A104); el corpus de main ya es todo K desde
    #883, asi que los records de hoy son K en toda la ventana, pero los del scraper no cambian.
    Tambien: el archivo de datos local puede estar atrasado respecto de origin/main (A52, A25):
    verificar de que commit es repo/data.
G6. n chico: 53 alertas en total, partidas en < 30 y >= 30; con ceros el promedio depende de
    cuantos ceros hay en cada tramo. Una mediana y una media dicen cosas distintas; el auditor
    puede haber reportado media donde la caida es por ceros.
G7. Ceros: un cero puede ser «no detecto» (K fallo) o «no hay record» (no se proceso la pasada,
    cobertura) o «record far» (tablero oculta). Si el auditor mete como 0 las pasadas sin record,
    la razon media baja por cobertura, no por el detector.
G8. Barajado: 200 barajados con semilla 173 del cenit dentro del sensor. Si baraja a traves de
    sensores o baraja la razon en vez del cenit, el control es otro. Si Spearman se calcula con
    ceros empatados, el rho se deforma por empates (y el barajado tambien, asi que el control
    sigue valiendo, pero el valor no se compara con uno sin ceros).
G9. El cenit en el record: puede ser NaN en muchos records (p. ej. los de antes de cierto PR que
    lo agrego). Entonces la ventana efectiva es menor que la declarada.
G10. La copia local de los scripts del auditor (repo/, insumos/n, oraculo_r2) puede ser de otro
    commit que el de origin/main de hoy; comparar COMMIT.txt y REF_SHA.txt con los sha de hoy.
G11. La pieza «anillo»: el pipeline de produccion (process_viirs_mod.py) arma el fondo de K con
    un radio y una exclusion que hay que leer en el codigo y en el perfil, no en el YAML (A89:
    leer pipeline.profile); el caller puede transformar el argumento (A6). Si el auditor reconstruyo
    «el anillo de K» con otro radio, su 3,6 K no es el de produccion.
G12. Esfuerzo bajo del autor: errores tipicos son el campo equivocado, el pareo por noche, y
    copiar numeros de un informe anterior (s162) sin recorrerlos.

## Caminos especificos

### A1 (K por pasada 0,571 / 0,117; Spearman -0,508; 22 del auto-audit sin pendiente)
- A1.a: ¿la razon se calculo con pc.vrp_mw y la alerta de MIROVA a la MISMA hora? (G1, G2).
- A1.b: ¿los 53 incluyen alertas diurnas? MIROVA alerta de dia en VIIRS 750 y K es solo nocturno
  en MIR: si las diurnas entran como ceros, la razon cae por dia/noche, y el cenit diurno puede
  correlacionar con la hora.
- A1.c: ¿los 53 pasan la regla SN (0,05 MW o menos descartados) y la lectura A?
- A1.d: ¿el 0,571 y 0,117 son medias o medianas? ¿con cuantos ceros en cada tramo? Si en el tramo
  >= 30 hay 8 ceros de 11, la media es una fraccion de fracasos, no una razon de magnitud.
- A1.e: ¿la pendiente «no significativa» en la ventana de 22 es por n o porque la relacion no
  existe ahi? Con n = 22 el poder es bajo: SIN DATO, no «no hay».
- A1.f: ¿Spearman se calculo sobre pares con razon 0 incluida? Los ceros empatados a cenit alto
  inflan el rho negativo.
- A1.g: ¿el cenit es el del record o el del granulo? ¿cuantos records tienen cenit nulo?
- A1.h: ¿el barajado es dentro de VIIRS 750 solo o mezcla sensores? Con un solo sensor «dentro
  del sensor» es trivial, bien; pero si mezclo NOAA-20 y SNPP con distintos cenit medios, el
  barajado cruza plataformas; eso esta permitido por la vara, solo hay que decirlo.
- A1.i: la ventana «abril a noviembre» ¿tiene alertas de MIROVA de PCC en VIIRS 750 en los dos
  tramos de cenit? Un tramo con 3 pares no sostiene un 0,117.
- A1.j: ¿la copia local de PuyehueCordonCaulle.json es la de origin/main de hoy (post #883)?

### A2 (anillo de K 3,6 K mas tibio; lacolito 4,7 K; 1,00 a 0,18; nativo K 0,425 / F 1,128)
- A2.a: ¿el «anillo de K» que midio es el que arma process_viirs_mod.py en produccion (radio,
  exclusion del halo, kernel local opt-in por volcan en PCC)? (G11). PCC puede tener
  local_kernel_bg activado (A89 dice que 5 de 11 Tier A lo tienen) y entonces el fondo de K no
  es el anillo global.
- A2.b: ¿el «fondo local de MIROVA» es el de MIROVA_VIIRS750_VRP.m (interpolacion bajo un halo
  dilatado) o una reconstruccion del auditor sobre la grilla? ¿con que dilatacion?
- A2.c: el 1,00 a 0,18 ¿es sobre cuantas pasadas? ¿una sola (un ejemplo) o la mediana? Un numero
  de una pasada se presenta como regla.
- A2.d: «en el granulo nativo K 0,425 y F 1,128»: ¿F que es? (¿la vía «codigo MIROVA» completa
  sobre el granulo nativo?). ¿Que ROI uso F en el nativo? Si uso la caja B1/B3 en vez de la que
  la via usaria de verdad en PCC, el 1,128 es de otra configuracion.
- A2.e: unidades: 3,6 K en temperatura de brillo del M13 o en radiancia? Un delta de 3,6 K en BT
  a 270 K no es lo mismo que a 300 K en radiancia; el VRP usa radiancia.
- A2.f: ¿el lacolito «sobresale 4,7 K» sobre que fondo? Si es sobre el anillo tibio, la
  comparacion contra MIROVA cambia con el fondo elegido: circular.

### A3 (pendiente sale de fracasos de K: 6 de 18 contra 8 de 11)
- A3.a: ¿que es «fracaso»? ¿record sin pc (cero), record far, record ausente? (G7).
- A3.b: ¿6 de 18 y 8 de 11 son los dos tramos de cenit? 18 + 11 = 29, no 53: ¿que paso con los
  otros 24? ¿son la ventana del auto-audit o una sub-ventana?
- A3.c: si saco los ceros, ¿la razon sigue cayendo con el cenit? Si no cae, la afirmacion se
  sostiene; si cae, es parcial.
- A3.d: ¿los fracasos a cenit alto coinciden con pasadas de borde de barrido (D25, bow-tie)? El
  auditor puede confundir «fracaso de K» con «granulo cortado / sin cobertura».

### A4 (ni posicion ni suma)
- A4.a: ¿como midio «posicion»? Si uso pc_lat/pc_lon contra el crater y PCC es difuso (lacolito a
  7 km, A20), la posicion no es el crater; necesita comparar contra la posicion de MIROVA, que el
  CSV no trae con acimut (A93, A107).
- A4.b: «suma»: ¿comparo el numero de pixeles nuestros contra el de MIROVA por pasada (n_pix)?
  ¿con que campo? Si el numero de pixeles de MIROVA viene del OCR, puede ser de otra pasada
  (reference_ocr_imagen_de_otra_pasada).
- A4.c: una negacion («ni ... ni ...») requiere que la medicion pueda ver el efecto: ¿tiene
  control positivo?

### A5 (caja 7 x 7 del ejemplo no alerta en 72 pasadas; uso B1 y B3 de V750-B)
- A5.a: ¿la caja 7 x 7 es la que la via usaria de verdad en PCC? Hay que leer
  pipeline/grillas_mirova.yaml en origin/main y en loop/activo, y el prerregistro de V750-B. Si
  el YAML da a PCC otra ROI (p. ej. una caja mas grande o desplazada al lacolito), el 7 x 7 es
  una ROI que nadie usaria y el «no alerta» es un hallazgo sobre la ROI equivocada.
- A5.b: ¿las 72 pasadas son las de la ventana de alertas de MIROVA o de todas las pasadas? Si
  incluye negativos limpios, «no alerta» en esos es lo correcto.
- A5.c: ¿«no alerta» con que umbrales? Los de MIROVA V750 son 5 sigma dentro de la caja y 10
  fuera, de noche; si uso 15 (diurnos) por un error de bandera dia/noche, no alerta.
- A5.d: ¿B1 y B3 estan definidas en el prerregistro como brazos o como ROI? Si son brazos de un
  A/B (p. ej. B1 = caja centrada en crater, B3 = caja grande) la via de produccion usa uno solo;
  el auditor pudo elegir el que da mejor.
- A5.e: la grilla fija de PCC: ¿centrada donde? Si la grilla de s159_n esta centrada en el
  centro de MIROVA (mirova_center) y la ROI del YAML en el crater, la caja del ejemplo cae fuera
  del lacolito.
- A5.f: ¿se comprobo que la grilla leida de D:/vrp-trabajo/temporales/s159_n es la de PCC (no
  otra) y que tiene pasadas nocturnas?

### A6 (anillo de oraculo_ablacion.py va de inner a 25 km, no de 5 a 25)
- A6.a: leer oraculo_ablacion.py: ¿de donde sale el radio interior? Si es `inner_radius_km` de
  volcanoes.yaml y PCC tiene 20, el anillo es 20 a 25 km. Si es una constante 5, la afirmacion
  es falsa.
- A6.b: ¿eso importa? Si el oraculo es un instrumento de otro (s162) y no la via de produccion,
  es un seguimiento, no un hallazgo de paridad. ¿El pipeline de produccion usa el mismo radio?
- A6.c: ¿el comentario/docstring dice «5 a 25» y el codigo hace otra cosa (texto contra codigo,
  patron S169)?

### A7 (codigo de MIROVA en la grilla tampoco es plano: -0,47; F 1,3 sobre MIROVA sin ceros)
- A7.a: -0,47 ¿es Spearman sobre que n? ¿con ceros? ¿con barajado?
- A7.b: F 1,3 «sin ceros»: si se sacan los ceros de F pero no los de MIROVA, es una comparacion
  entre poblaciones distintas. ¿Cuantos ceros tiene F?
- A7.c: ¿F en la grilla usa la ROI que la via usaria (A5)? Si usa B1/B3, el 1,3 es de otra ROI.
- A7.d: si F tambien cae con el cenit, la conclusion «la pieza es el fondo» pierde fuerza: el
  remuestreo (D17) no se descarta. ¿El auditor separo fondo y remuestreo con un A/B de piezas
  (cambiar una a la vez) o solo comparo K contra F?
- A7.e: el control positivo del instrumento: ¿hay algun brazo donde la pendiente desaparece?
  Si ningun brazo da pendiente cero, el instrumento puede estar midiendo cobertura o nube, no
  la pieza.

## Caminos propios que voy a intentar ademas (medir por otro camino)

P1. Re-correr s01 y s03 en copia dentro de ver_pcc750/ y comparar numero a numero.
P2. Recalcular la razon por pasada con mi propio script, directamente de
    data/mirova_equivalent/PuyehueCordonCaulle.json de origin/main (sha verificado) y del
    snapshot del scraper, con pc.vrp_mw, pareo por minuto, regla SN, solo nocturno, VIIRS 750.
P3. Estratificar por plataforma (SNPP / NOAA-20 / NOAA-21) y por tramo de cenit; reportar
    mediana y media con y sin ceros, y n por celda.
P4. Leer grillas_mirova.yaml (origin/main y loop/activo) y el prerregistro V750-B; comparar la
    ROI de PCC con las cajas B1/B3 del auditor.
P5. Leer en process_viirs_mod.py como arma el fondo de K para PCC (radio, kernel local,
    exclusion) y en pipeline.profile los flags vigentes.
P6. Leer oraculo_ablacion.py para A6.
P7. Pérdida aceptada del 2026-10-10 (#865, #881): tratarla aparte: ver si esas pasadas estan en
    los 53 y que pasa con la razon sin ellas.

---
sha256 (antes de este pie): ab0e8c3846dfd10a50c5e43cbba9a20122b200aeecec6cba281eb59b2b140031
hora del servidor (GitHub, header Date): Date: Tue, 03 Nov 2026 02:48:40 GMT
