# S133 · Veredicto del A/B de B22: NO ADOPTAR, y por una razón que no esperaba

**Los dos criterios que importaban fallaron, y fallaron al revés de mi predicción.** Yo había
escrito, antes de correrlo, que el efecto sobre el fondo sería de 0,0036 K — invisible. El
dato da **−1,2 K**, trescientas veces más. El A/B refutó a quien lo diseñó, que es
exactamente para lo que sirve pre-registrar un criterio.

Todos los números salen de `experiments/_s133/resultado_ab_b22.json` (regla S91). Dos
volcanes de régimen opuesto, pareados **por granule** y no por fecha: Láscar n=61, Villarrica
n=70, ventana 2026-08-01 a 2026-08-31.

## El resultado, contra el criterio congelado

| | criterio | Láscar | Villarrica | |
|---|---|---|---|---|
| **C1** | fondo: \|mediana Δσ\| ≤ 0,05 K | **−1,221 K** | **−1,181 K** | ❌ |
| **C2** | detección: 0 pasadas de MIROVA perdidas | 0 perdidas | 0 perdidas | ✅ |
| **C3** | magnitud: razón ON/OFF en 0,95-1,05 | **0,107** | **0,256** | ❌ |
| **C4** | control: 0 píxeles con B22 saturada | 0 de 3.829 | 0 de 4.554 | ✅ |

El sigma del fondo cae de 6,38 a 4,90 K en Láscar y de 7,36 a 4,21 K en Villarrica: entre un
23 % y un 43 % menos. Y la magnitud cae a una décima parte en Láscar y a una cuarta en
Villarrica.

## Por qué mi predicción estaba mal

Razoné que `diag_sigma_bg_k` mide la heterogeneidad del terreno del anillo —nieve parcial,
roca, hielo— y no el ruido del sensor, y que siendo su mínimo histórico 5,4 veces el NEΔT de
B21, restar en cuadratura daría un cambio invisible.

El error está en tratar el ruido de B21 como una constante. **No lo es.** B21 es la banda de
ganancia baja: su rango llega hasta los 500 K, y eso significa que sobre un fondo frío de
265 K está trabajando en el fondo de su escala, donde su paso de cuantización es grueso.
Ahí B21 no aporta 0,183 K de ruido, aporta bastante más. B22, de ganancia alta, tiene su
resolución fina justamente en ese rango.

Por eso el sigma cae tanto: no estamos restando en cuadratura un ruido pequeño, estamos
cambiando de instrumento en el régimen donde el instrumento viejo es peor.

## Lo que eso implica para la magnitud, y por qué NO se adopta igual

El VRP se calcula de cuánto sobresale el píxel por encima de su fondo. Si parte de ese
"sobresalir" era ruido de B21 en el extremo frío de su escala, entonces con B22 desaparece —
y la magnitud cae. Es decir: **la lectura más plausible es que las magnitudes de B22 son las
honestas y las nuestras de hoy vienen infladas por el ruido de la propia banda.**

Eso apunta a adoptar, no a rechazar. Pero el criterio se pre-registró y falló, y **el criterio
no se mueve después de ver el dato**. Además hay dos razones sustantivas para no adoptar hoy:

**Primera, este A/B no puede medir la paridad.** El punto de comparación es MIROVA, y en esta
ventana quedaron 2 pares en Láscar y 0 en Villarrica para el brazo de control, y 0 en ambos
para el encendido. Con ese n no se decide nada. Un cambio que divide la magnitud por 4 o por
10 hay que juzgarlo contra MIROVA con decenas de pares, no con dos.

**Segunda, la detección casi no se movió y eso es sospechoso.** C2 pasó holgado: 4 pasadas
cambian en Láscar y 3 en Villarrica, sin perder ninguna que MIROVA publicara. Si el sigma
baja un 30 %, los umbrales contextuales N·σ deberían bajar con él y la detección debería
volverse **más** sensible. Que no se mueva merece entenderse antes de tocar producción.

## Lo que sí quedó establecido

- **La saturación de B22 no es el problema.** C4 midió 0 píxeles sobre los 331 K en 8.383
  píxeles de anomalía; el `t_max` de la muestra llega a 286 K. La comparación aísla
  limpiamente la diferencia entre bandas, sin que la saturación la contamine. El caso en que
  el paper y el repo coinciden sigue sin ocurrir.
- **Seguimos divergiendo del paper en prácticamente todos los records**, y ahora sabemos que
  esa divergencia no es inocua: cuesta un 30 % de ruido en el fondo.

## Lo que corresponde hacer

No adoptar por ahora, y **no archivar el frente**. Lo que hace falta es un A/B con
suficientes pares contra MIROVA para decidir si la magnitud de B22 acerca o aleja la paridad
— la pregunta que este no pudo responder. Con la ventana de agosto no alcanza; hay que
ampliarla a los meses donde MIROVA publicó más, y sobre los volcanes con más alertas
(Isluga y Láscar tienen 62 y 66 en la ventana del auto-audit, contra las 15 de Villarrica).

El flag `ENABLE_MODIS_B22_PRIMARY` queda **implementado, cableado y apagado**.
