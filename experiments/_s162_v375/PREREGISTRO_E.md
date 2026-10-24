# Pre-registro V375-E (S162): el paquete del código de MIROVA en VIIRS 375 contra producción (K)

> Escrito antes de que exista el paquete en `pipeline/` y antes de ver ningún resultado suyo. Lo que cambie después del
> sello va en una adenda fechada al final. Es el pre-registro de una ADOPCIÓN posible: la implementación, el sello, el
> tag defensivo y el despacho pasan por A45 (el sí de Nicolás, cada uno). Estado: **BORRADOR, sin sellar**; depende de
> PD1 (la ROI, V375-C), de PD3 (la vía de proceso en `pipeline/` detrás de flag) y del evaluador común de la sesión del
> instrumento (programa §8.3: placebo y comparador d′ fuera de `evaluar_d25.py`).

## 1. Pregunta

Si VIIRS 375 pasa a calcularse con el código de MIROVA (el mismo que en 750, con bandas I, la grilla de 134 x 134 y la
caja que salga de PD1), ¿el tablero se parece más a MIROVA que hoy, en las dos direcciones, sin perder ninguna alerta
protegida?

**Por qué.** Producción ve casi todo lo que MIROVA ve en 375 (recall 96,8 %), pero muestra la magnitud a dos tercios
(0,651 [0,436; 0,848] en la muestra de S159) y publica en 3,85 % de las noches limpias. El port, sobre las mismas
pasadas, dio la magnitud al centésimo (1,000 [0,966; 1,019], n 61) y apagó dos de cada tres puntos de cumbre en noches
sin nada. Y en las pasadas oblicuas el problema es doble: MIROVA también pierde magnitud cuando mira de lado, pero K
pierde más. Medido de antemano sobre la población congelada de S159 (`linea_base_curva_salida.txt`, pares de la misma
noche y volcán con 15° o más de diferencia de cenit, las dos pasadas publicadas): la pasada más oblicua sobre la menos
oblicua da **0,778** en MIROVA y **0,573** en K; la razón doble K / MIROVA es **0,766 [0,722; 0,861]** (215 noches), y
sobre 50° de cenit **0,733 [0,608; 0,861]** (153). La meta del paquete no es aplanar la curva (MIROVA no es plana) sino
**caer igual que MIROVA**: razón doble 1.

## 2. Brazos

| brazo | qué es |
|---|---|
| **K** | producción (detector K, #850), lo publicado; control |
| **P** | el paquete: vía de proceso «código MIROVA» de VIIRS 375 con la caja de PD1, el predicado de cumbre del tablero |
| P-def | el paquete con la caja M14 (la de S159), para separar el efecto de la ROI |
| P-sinfiltro | el paquete publicando todo lo que detecta (decisión 5 del programa: medir sin el predicado de cumbre) |
| PLACEBO | K con el VRP x 1,2 (programa §2, obligatorio): tiene que dar 0 discordantes en P1 y P2, y d′ = 0 |

Lo que el paquete acopla y se prueba junto (programa §7): remuestreo a la grilla fija (D17), Test 1 como alerta, ventana
de 3 x 3 con la celda central, umbrales del `.m`, sin compuerta de 3 K, segundo pase con la regresión recalculada,
fondo por `fillmissing2` bajo el halo, sin recorte, suma de todos los alertados, sin modo de un píxel ni tope D9.
La atribución pieza a pieza no es de aquí: va en ablaciones locales sobre las grillas guardadas.

## 3. Tres pasos, en orden (decisión 3 del programa)

1. **Equivalencia (PD3)**. La vía de `pipeline/`, corrida sobre los gránulos del lote de B y C (859 pasadas con grilla
   guardada), reproduce al port de `brazos.py` pasada por pasada: misma cantidad de alertados y VRP a 1e-3 MW en el
   99 % o más, y **las 80 protegidas idénticas**. Si no, el paquete no es el código y no se sigue.
2. **Lectura retrospectiva** sobre la unión de B y C (marco de S159, del 2026-04-01 al 2026-10-21, sin el 12, 13 y 17 a
   20 de octubre), con los pesos de `PREREGISTRO_B.md` §3. Ventanas T y O por separado, O1 y O2 (#535) por separado.
3. **Sombra prospectiva confirmatoria** desde el **2026-11-03** (ventana P del programa, sin Suomi NPP: otro régimen),
   como perfil aparte con su `data_subdir`, sin tocar la vista operacional, hasta 30 noches o 40 alertas de MIROVA que
   decidan, lo que llegue último. La referencia se congela por hash en cada corte de lectura.

## 4. Controles (antes de leer)

Los de `PREREGISTRO_B.md` §4 (cobertura contra la referencia de MIROVA del instrumento, SIN DATO fuera del
denominador, K re-corrido, control positivo, nulo, NUNCA, PLACEBO), y para la curva de cenit (`curva_cenit.py`,
probados sobre K en `linea_base_curva_salida.txt`):

- **Nulo de cenit parecido**: en la misma noche y volcán, el par de pasadas con alerta de MIROVA que difieren en menos
  de 5° de cenit, en orden al azar. La razón doble de ese nulo tiene que contener 1 (en K: 1,035 [0,784; 1,182], 37
  noches); si no, NULO SESGADO y la curva no se lee. El nulo de 750 (los mismos pares ordenados por hora) **no sirve en
  375**: el VRP de MIROVA baja de una pasada a la siguiente de la misma noche (mediana 0,818, n 365), y el orden por
  hora cae casi igual que el orden por cenit (0,786 contra 0,778).
- **Ganancia pareja** (x 1,2 a todas las pasadas): la razón doble no se mueve (en K: 0,766 → 0,766).
- **Ganancia que crece con el cenit** (1 + 0,01 por grado sobre 20°): la razón doble tiene que subir (en K: 0,766 →
  0,988). Si no se mueve, el instrumento no ve el cenit.

## 5. Lecturas y regla de adopción

### 5.1 Detección (P1, P1b, P2, silencio, MISSION)

Las de `PREREGISTRO_C.md` §5 y `PREREGISTRO_B.md` §5, de P contra K: P1 veto (ninguna protegida que K publica puede
perderse; lectura A, regla SN; la protegida de cráter de V375-A al lado), P1b en las dos direcciones, P2 por la prueba
de signos por bloque noche-volcán (D-45), silencio en negativos limpios con la cota de Wilson sobre n efectivo, MISSION
con la cota honesta del estrato de cero eventos.

### 5.2 Magnitud (M)

La regla sellada de D-27 sobre d = |log10(P / MIROVA)| − |log10(K / MIROVA)| y el comparador de ganancia pareja de
D-28 (d′ con ĝ = mediana de log10(P / K)), con la calibración de D-30 y D-32, **tomados del evaluador común de la
sesión del instrumento** (no se reimplementan aquí). Por tramo de 10° de cenit, por volcán y por canal. El placebo da
d′ = 0 por construcción; si no, el instrumento está roto.

### 5.3 La curva de cenit

Razón doble D por noche (`curva_cenit.py`), condicionada (las dos pasadas publicadas, DECIDE) y sin condicionar (no
publicar = 0, informa). Veredicto: SIN SUSTRATO con menos de 8 noches en la lectura o en el nulo; NULO SESGADO si el
nulo no contiene 1; **CAE MAS QUE MIROVA** si el IC de la mediana de D queda entero bajo 1; CAE MENOS QUE MIROVA si
queda entero sobre 1; **REPRODUCE LA CURVA** si lo contiene y la mediana está en [0,8; 1,25]; NO RESUELTO en otro caso.
Se informa al lado si la curva de MIROVA misma se separa del nulo (en la ventana O no se separa: 0,857 [0,707; 1,077]
contra un nulo de 1,074); esa marca no bloquea, porque D compara las dos caídas en los mismos pares. Por tramo de la
pasada oblicua (menos de 50°, 50° o más) y por volcán (Chillán aparte, V375-F).
Vara de K, medida antes: **CAE MAS QUE MIROVA**, 0,766 [0,722; 0,861].

### 5.4 Regla de adopción del paquete (para PD4, decide Nicolás con A45)

El paquete P **cumple** si, en la lectura retrospectiva Y en la sombra prospectiva: (a) P1 no pierde ninguna protegida
que K publica; (b) P2 contra K da GANA o EMPATE (no PIERDE ni BLOQUEA) y el silencio no da ENCIENDE DE MAS; (c) M da
MEJORA con d′ dando MEJORA (no sólo una ganancia) o, si d no mejora, no EMPEORA; (d) la curva da REPRODUCE LA CURVA,
o al menos el IC de D del paquete queda entero sobre el de K. Si (a) falla en cualquiera de las dos, **no cumple**.
Si la retrospectiva cumple y la sombra no tiene sustrato a las 30 noches, la decisión es de Nicolás con lo que haya.

## 6. Lo que este pre-registro no hace

No implementa nada (PD3 es otra tarea con su propio pre-registro de implementación y A45). No mide el día. No mide
Chillán sobre 3 MW como pregunta propia (V375-F, después de esto). No mezcla la ventana P con la O: son regímenes
distintos (cese de Suomi NPP).
