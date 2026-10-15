# A/B de F y K contra producción en los 11 Tier A (tarea 1.6 del loop)

El documento que manda es `PREREGISTRO.md`. Este README sólo deja escrito qué regla de las alertas mínimas
decide, porque la decisión D-9 llegó después de sellar el pre-registro.

## Qué regla de las alertas mínimas decide (D-9, issue #811)

- **Decide la regla original** (la etiqueta del scraper: toda alerta con VRP mayor que cero es alerta). Es la
  que estaba vigente cuando se escribió y se aprobó el pre-registro, y cambiarla después de despachar sería
  mover la vara de un experimento ya corrido. Las secciones 5 a 8 de `evaluar_fk.py` y `res["global"]`
  usan esa regla, sin ningún cambio.
- **Se informan las otras**, en la sección 10 de `evaluar_fk.py` (`res["reglas_d9"]`) y en `--combinar`:
  SN (la decidida por Nicolás el 2026-10-15), SE (estrato aparte) y las dos con umbral 0,04, que dejan 0,05
  exacto como alerta. Para cada una se recalcula la suma de P2, su veredicto por sensor y el veredicto de la
  ventana, marcado "DISTINTO del que decide" cuando no coincide. P1 no cambia con ninguna regla (las
  protegidas tienen 1 MW o más) y P3 se queda con la etiqueta original.
- **Por qué se informan**: Nicolás aprobó SN con la condición de probar todas las opciones. Si el veredicto
  informado con SN difiere del que decide, eso va escrito en el resultado y la adopción lo tiene que mirar.

**Controles de la sección 10.** La etiqueta original re-calculada tiene que coincidir con la de la tabla
(`control: ... igual a la de la tabla`), y con la regla original la sección 10 tiene que reproducir la suma
y los P2 de la sección 6 (`autocontrol`). En la autoprueba (`probar_evaluar_fk.py`) se agregaron cuatro
comprobaciones a las 37 que había: el autocontrol en el nulo; un caso en que F y K callan justo las alertas de
0,05 MW o menos (33 en V1), donde lo que decide sigue en PIERDE y NO CUMPLE (suma) y la sección 10 informa
SN GANA, SE EMPATE y original PIERDE (dos comprobaciones: prueba que la sección puede dar un veredicto
distinto sin tocar el que decide); y Chillán, donde la sección 10 tiene que dar lo que midió el estudio por
su propio camino (SN 55, 6 y 6; SE 52, 5 y 5). Resultado: **41 de 41** (`probar_salida.txt`); las 37
originales siguen OK.
