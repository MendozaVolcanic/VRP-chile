# Caminos por los que cada afirmacion del borrador podria estar mal (escrito antes de abrir los pre-registros sellados)

Objeto: experiments/_s172_prereg_retro/PREREGISTRO_RETRO_PAQUETE.md, loop/activo 01be21ff5.

## V-1 fuera de muestra
- La ventana que el borrador atribuye a una regla es la del texto del pre-registro, pero el dato efectivamente mirado fue otro (por ejemplo, V750-B "T" abarca desde 04-01, pero un diagnostico previo miro febrero).
- El tag citado no contiene lo que el borrador dice (el pre-registro cambia entre tags, adendas posteriores).
- K (V2) pudo haber mirado febrero y marzo en VIIRS; el borrador dice que VIIRS decide desde 04-01 pero los diagnosticos pudieron incluir febrero.
- Otras fuentes de contaminacion no listadas: auditorias S150/S151/S153 (meses mar-jun), S159 marco, S165 regla de posicion, S172 Chillan (2026-?), probes de caja 5x5, experimentos de la ventana de verano (p. ej. _s130, _s139 usaron toda la data).
- "Febrero de 2026 en MODIS" no miro: la censo D-48 de MOD-D dice 03-01 a 10-16, pero S124-S139 usaron toda la historia 2025+ (OSF) para calibrar WOOSTER y para auditorias R2; 2025 contra OSF fue mirado por A12/A54/A66 etc. (las cuentas de calibracion S14 son OSF 2001-2025).
- Las lineas citadas (l. 90 a 102, etc.) no corresponden a lo que dicen.

## V-2 reglas de adopcion
- La regla "tal como esta sellada" no es la del tag citado sino una adenda posterior.
- "Censo en lugar de muestra con pesos" si cambia lo que puede decidir: potencia, estratos vacios, SIN SUSTRATO, bootstrap pesado vs plano, umbrales por n minimo.
- La regla de MOD-D exige piezas (identidad con grillas, tramo E) cuyo retiro cambia el veredicto.
- V750-A es borrador: sellar "su texto copiado" crea una regla sellada nueva sin pasar por sus verificadores.
- El brazo de posicion que "decide" cambia entre pre-registros y el borrador mezcla.

## V-3 la prueba puede perder
- P1 con 0 perdidas y n pequeno no puede perder (poder bajo, el borrador lo admite) y el veredicto verde igual se llama "SE SOSTIENE".
- Placebo K x1.2 no ejercita P1 (la perdida de una protegida) sino M.
- Nulo: K-gemelo vs K de disco: ambos con el mismo codigo; si K disco fue escrito por #883 el control es tautologico.
- Veredicto 3 depende de "regla da NO ADOPTAR", pero la regla del sensor puede dar NO ADOPTAR por razones que no son de F26 (p. ej. necesidad de tramo O).
- Orden de veredictos: el 4 SIN PODER vs 2: una pierde-protegida SIN DATO.
- Cobertura A108: "SIN DATO sale del denominador de los dos brazos" puede esconder perdidas de la via (el descarte sin record 171-01).
- El nombre "LA ADOPCION SE SOSTIENE" promete mas que un tramo de verano en 11 volcanes casi todos Lascar.

## V-4 referencia
- Conteos propios del borrador (25, 30, 7, 317, 17, 162, 2577, piso 5,05 MW, NOAA-21 2026-04-09) pueden provenir de aproximar noche como 00-11 UTC, de no aplicar TOL_S, de mezclar OCR, de distancia a coordenadas OSF.
- El archivo VRP_GLOBAL_ARCHIVE_2025.csv local pudo cambiar (sha256) o no es el de GitHub.
- El piso de 5,05 MW en 750 puede ser artefacto de una columna (Wooster vs unidad) o de que un VRP minimo se calcula sobre un subconjunto.
- "NOAA-21 sin referencia antes de 2026-04-09" puede ser el hito del OCR y no de la tabla.
- La tabla F26: hitos de calidad (02-14, 02-23, 03-01) leidos de calidad_referencia_mirova.py pueden ser distintos.
- Dayflag 0 = noche no verificado.

## V-5 montaje
- extends resuelve un nivel: puede que resuelva mas (o ninguno) segun el codigo de hoy; main ya cambio desde 14fb62030.
- Los flags que "define los brazos" tienen otros nombres en el codigo de hoy (A89: el nombre en el YAML no es el del parametro).
- Costo: 2,39 min/volcan-dia viene de dividir mal (jobs de 176 vs trozos), p95 de 160 min puede ser de otro run, 6 de 176 fallaron.
- 176 jobs en D4: 11 volcanes x 16 trozos = 176 ok; 320 dias/20 = 16 ok. D2: 59 dias/20 = 3 trozos x 11 = 33 + 11 DM = 44 ok.
- Tope de 256 jobs; el limite real de concurrencia; 20 jobs para plan Free (el repo es publico: 20 concurrentes en Free, pero repo publico no tiene limite de minutos).
- Total de volcan-dia: 825, 235, 3520: aritmetica.
- Token vence 2026-12-07; rotacion 11-27 ok.

## Generales
- La copia local de un archivo del repo esta atrasada respecto del ref citado; leer siempre con git show del ref.
- Mi propio script mide otra cosa que el borrador (noche, pareo): declararlo.

sha256 de este archivo antes de esta linea: 391e868ede5698f74ff059bd2e29b3154fd37df5f78e4011060e31fc44fb75ba ; hora del servidor (date -u): Mon Nov  2 01:44:08 UTC 2026. No se vuelve a editar.
