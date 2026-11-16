# Cotas de VIIRS 375 de la regla de reversión, con los casos de la retrospectiva (S178, P10)

Rama `claude/s178-cotas-v375`, desde `origin/loop/activo` `12409d1fd`. Nada sellado cambia: ni la regla en borrador
(`experiments/_s176_v375e_adopcion/REGLA_REVERSION_V375E_BORRADOR.md`), ni el script de S176, ni el lector.
Todo número de abajo sale de `cotas_v375_con_retro_salida.txt` (misma carpeta), producido por
`cotas_v375_con_retro.py`.

## 1. El fenómeno

Con la vía «código MIROVA» encendida en VIIRS 375, el costo aceptado es que calle algunas alertas débiles que K
publica (un foco sub-píxel de 0,05 a 1 MW, la clase Muy Bajo de MIROVA) y que publique en algún negativo limpio que K
callaba. La regla no revierte por eso: investiga cuando en 120 días se junta más de lo esperable. Lo esperable sale de
cuántas veces pasó en datos anteriores. Hasta hoy, esos datos eran sólo el A/B de V375-B y C (junio a octubre de 2026,
con el port y no con la vía real). La retrospectiva trae la vía real contra K en otro verano (febrero y marzo de 2026,
F26-V), en 2025 (R25) y en la primera quincena de octubre (DM).

## 2. Dónde estaban las cotas y su método

- Regla: §4.4 y decisión D1 del borrador; cotas **más de 14** (i, Muy Bajo perdidas) y **más de 15** (ii,
  sobre-publicación diferencial), sin sellar (`COTAS` en `scripts/vigilancia_guardia_viirs.py` vale `None`).
- Script: `experiments/_s176_v375e_adopcion/cotas_retrospectiva_v375.py`, sobre la caché de filas del evaluador
  sellado `experiments/_s162_v375/evaluar.py` (runs 40116289866, 40131572769 y S159), ventana O (125 días), brazo C13
  «cercano», sólo NOAA-20 y NOAA-21. Método escrito: conteo ponderado por día, llevado a 120 días, cota = primer
  entero con falsa alarma Poisson de 8 % o menos.
- Este script importa ese módulo sin tocarlo y repite su cuenta: da otra vez 14 y 15 (sección 1 de la salida).

## 3. Los casos nuevos, con el mismo predicado

Filas armadas con las funciones del lector del tag `s178-retro-lectura` (candado: 16 de 16 sha256 del manifiesto;
control de identidad: la regla de VIIRS 375 en F26-V da lo mismo que `lectura.json`; control del instrumento: K
contra K da 0, un brazo mudo pierde 151). Brazo V-cercano (el que decide), régimen NOAA-20 y NOAA-21:

| tramo | días | (i) Muy Bajo que K publica y la vía calla | (ii) neg_resto que la vía publica | cota sola (i) / (ii) |
|---|---|---|---|---|
| O (vigente, ponderado) | 125 | 2 de 97 crudo, 9,8 ponderado | 5 de 993 crudo, 10,5 ponderado | 14 / 15 |
| F26-V (censo) | 59 | 1 de 139 | 5 de 528 | 4 / 15 |
| DM (censo) | 14 | 1 de 51 | 1 de 216 | 13 / 13 |
| R25, sólo (i), lectura no escrita del OSF | 320 | 12 de 1.354 (3 de NOAA-20) | no existe | 8 (todas las plataformas) |

En F26-V las 5 de (ii) son NOAA-20; la NOAA-21 de febrero y marzo queda `sin_info` (la tabla no la cubre).

## 4. Cómo sumar: lo decide Nicolás

El método escrito no dice cómo juntar una ventana nueva con la vieja. Opciones calculadas (sección 4 de la salida):

| opción | (i) | (ii) | qué supone |
|---|---|---|---|
| A. vigente | 14 | 15 | no suma nada |
| B. O + F26-V por día | 11 | 15 | suma conteos y días; F26-V tiene menos pasadas VIIRS por noche en la tabla (A119 b), lo que baja la tasa por día |
| B-rad. como B, F26-V con el brazo radiante | 13 | 15 | el record de la vía publica hoy con radiante; O no tiene ese brazo |
| C. O + F26-V por pasada de la clase | 12 | 17 | tasa por pasada, llevada a las pasadas de cada clase que O ve en 125 días; no depende de la exposición de la tabla |
| C-rad. como C, F26-V con el brazo radiante | 14 | 17 | C con el brazo que la vigilancia cuenta; F26-V radiante: 3 de 139 Muy Bajo, 5 de 528 de más |
| D. O + DM | 14 | 14 | cuenta dos veces del 1 al 16 de octubre (DM está dentro de O; Planchón-Peteroa 2026-10-15 05:18 sale en las dos) y el pre-registro dice que DM es control de montaje, no evidencia (§3.2) |
| E. B + R25 en (i) | 6 | 15 | define «Muy Bajo OSF» sin texto que lo escriba; el OSF está filtrado y reprocesado (A105) |

Lo que cambia de verdad: (ii) es estable (15 en A, B y B-rad; 17 en C). (i) baja en todas las que suman F26-V,
porque en febrero y marzo la vía calló una sola Muy Bajo de 139 contra 2 de 97 en O.

## 5. Recomendación y lo no verificado

- Hecho que pesa en la elección: la vigilancia cuenta lo que publica el record de producción tal como está
  (`scripts/vigilancia_guardia_viirs.py`, `cargar_insumos`: `bp.cargar_nuestros` con el predicado del tablero, sin
  variante de posición), o sea el brazo **radiante**, no el cercano con que se midieron O y la columna principal de
  arriba. En F26-V el radiante calla 3 Muy Bajo y el cercano 1; en (ii) dan lo mismo.
- Sin recomendación firme: la elección es de Nicolás. Dos preguntas: (1) ¿cómo se suma (A, B, C)? (2) ¿con qué brazo
  se mide F26-V, el que decide (cercano) o el que la vigilancia cuenta (radiante)? Con radiante, las cotas quedan
  más cerca de las vigentes (B-rad: 13 y 15; C-rad: 14 y 17).
- Matiz del verificador limpio (S178, que confirmó las cotas): B compara tasas por día con exposiciones distintas.
  En F26-V sólo NOAA-20 es evaluable, porque la tabla no trae NOAA-21 antes del 2026-04-09, y además expone menos
  pasadas VIIRS por noche; O tiene NOAA-20 y NOAA-21. Sumar días mezcla esas dos exposiciones y baja la tasa. C lo
  corrige por construcción: suma por pasada de la clase y lleva la tasa a la exposición de O. Como la vigilancia
  cuenta el radiante (`scripts/vigilancia_guardia_viirs.py:149`, `bp.cargar_nuestros` sobre el record de
  producción), la variante que junta las dos correcciones es **C-rad: 14 y 17**.
- D y E no deberían usarse sin decisión expresa (doble conteo; definición inventada).
- No verificado: verificador limpio de C-rad (se agregó después del verificador); los números crudos
  son chicos (1, 2, 3, 5) y el Poisson no incluye la incertidumbre de la tasa.
