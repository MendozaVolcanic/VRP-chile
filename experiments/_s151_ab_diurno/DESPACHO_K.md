# Despacho del A/B diurno sobre K: procedimiento

Procedimiento operativo de la §4 de `ADENDA_K.md` (sellada por Nicolás; este archivo no cambia el criterio, sólo
escribe los pasos que el verificador del candado pidió dejar por escrito, hallazgo H-5 de
`verificador_candado_k_v2/INFORME.md` en la rama `loop/activo`).

## Antes del primer despacho

1. El reproceso histórico con K (tarea 1.24) terminó y su reemplazo está aplicado: con el NRT y el histórico corriendo a
   la vez no queda margen en el tope de 20 jobs.
2. El candado está verificado: las 42 mutaciones de `candado_k_s155/m1_mutaciones_v2.py` caen todas por una prueba con
   nombre, ninguna por caída, y un verificador con contexto limpio lo confirmó.
3. Se pone el tag sobre `main` y se lee su commit **completo**:

   ```bash
   git tag -a s154-diurno-k-codigo -m "codigo del A/B diurno sobre K" origin/main
   git push origin s154-diurno-k-codigo
   git rev-parse s154-diurno-k-codigo^{commit}
   ```

   `^{commit}` importa: sobre un tag anotado, `git rev-parse <tag>` devuelve el sha del objeto tag, no el del commit, y
   los records traen el del commit. El evaluador exige los 40 caracteres y se niega con un sha abreviado.

## Cada despacho

- Desde el tag, nunca desde `main` a secas (A108; S152, desempates que dependen de la CPU).
- Brazos `_s154_ab_diurno_k_control` y `_s154_ab_diurno_k_on`; las diez medias ventanas de la corrida sobre C0, una
  por despacho, y la siguiente recién cuando la anterior empezó (grupo `s151-ab-diurno`, un solo pendiente).

## Evaluación

```bash
python -I experiments/_s151_ab_diurno/evaluar_diurno.py --raiz <W2a> ... --raiz <W6b> \
  --brazos _s154_ab_diurno_k_control,_s154_ab_diurno_k_on --base k \
  --sha-codigo <los 40 caracteres de git rev-parse s154-diurno-k-codigo^{commit}>
```

Lo que tiene que verse en la salida antes de leer el veredicto: la línea `[brazos]` con «regla G1: cola exacta», la
línea `H2a: N records del control y M del diurno leídos` con N y M mayores que cero, y la línea final
`VEREDICTO (§6 con la adenda K)`.
