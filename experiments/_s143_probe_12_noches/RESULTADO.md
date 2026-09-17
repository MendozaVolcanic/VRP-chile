# Resultado del probe S143 de las 12 noches

Generado por `analizar.py` desde `resultado.json` (2026-09-17T19:19:49+00:00). Ningún número escrito a mano.

**Lectura pre-registrada:** ambas recuperan: comparar costo en negativos; la de menor costo al A/B, la otra como ablacion

## Control de instrumento

- 1_todas_ok: cumple
- 2a_control_recupera_11: cumple
- 2b_s135_d_recupera_max_1: cumple
- 3_envoltorio_coherente: cumple
- 4_control_publica_11_neg_artefacto: cumple

## Por variante

| variante | pasadas ok | noches recuperadas (con cota) | sin cota | neg_artefacto publicadas | neg_quieta publicadas | pasadas con filtro del Test 1 |
|---|---|---|---|---|---|---|
| control | 61 de 61 | 12 de 12 | 12 | 12 de 12 | 0 de 8 | 50 |
| s135_d | 61 de 61 | 0 de 12 | 0 | 0 de 12 | 0 de 8 | 53 |
| s135_d_sin_compuerta_ctx | 61 de 61 | 11 de 12 | 12 | 7 de 12 | 0 de 8 | 53 |
| literal | 61 de 61 | 10 de 12 | 12 | 6 de 12 | 1 de 8 | 47 |
| literal_sin_compuerta_ctx | 61 de 61 | 11 de 12 | 12 | 9 de 12 | 1 de 8 | 32 |
| literal_t1_sin_filtro | 61 de 61 | 12 de 12 | 12 | 12 de 12 | 1 de 8 | 0 |

## Noche por noche (con cota)

| noche | control | s135_d | s135_d_sin_compuerta_ctx | literal | literal_sin_compuerta_ctx | literal_t1_sin_filtro |
|---|---|---|---|---|---|---|
| Isluga|2026-07-01 | sí | no | sí | sí | sí | sí |
| Isluga|2026-07-16 | sí | no | sí | sí | sí | sí |
| Isluga|2026-08-19 | sí | no | sí | sí | sí | sí |
| Lastarria|2026-07-02 | sí | no | sí | sí | sí | sí |
| Lastarria|2026-08-28 | sí | no | sí | sí | sí | sí |
| PlanchonPeteroa|2026-06-22 | sí | no | sí | sí | sí | sí |
| PlanchonPeteroa|2026-06-26 | sí | no | sí | sí | sí | sí |
| PlanchonPeteroa|2026-07-24 | sí | no | no | no | no | sí |
| PlanchonPeteroa|2026-08-09 | sí | no | sí | sí | sí | sí |
| PlanchonPeteroa|2026-08-24 | sí | no | sí | no | sí | sí |
| Tupungatito|2026-07-07 | sí | no | sí | sí | sí | sí |
| Tupungatito|2026-08-01 | sí | no | sí | sí | sí | sí |

## Matices del verificador con contexto limpio (leer junto con la tabla)

`VERIFICADOR_POST_CORRIDA.md`, veredicto SE SOSTIENE CON MATICES. Recontó cada número con su propio
cargador, su propio corredor de node y su propia haversine, y no encontró ninguna discrepancia.

**Lo que queda habilitado:**

- El código de hoy reproduce los brazos A y D de S135 exactamente, y el mecanismo es el declarado: el
  filtro contextual vacía la máscara del Test 1 en 53 de 53 pasadas del brazo D.
- **D22 y D25 solos (el brazo `literal`, que ya estaba pre-registrado) recuperan 10 de las 12 noches**,
  y ese 10 no cambia con ningún campo de posición. Es el resultado firme del probe.
- Las 9 ganancias de `literal_sin_compuerta_ctx` vienen de la máscara, con el filtro corriendo, y sin
  pérdidas; su costo es menor que el de apagar el filtro entero.

**Lo que NO queda habilitado:**

- **Cambiar los brazos por la diferencia 11 contra 10.** La cota se mide sobre el centroide del
  cúmulo, y para records `test1_roi` la regla del proyecto (S106, A84) dice que la posición es
  `final_hotspot`; los dos campos separan 1,06 km de mediana en esos records. Con `final_hotspot` las
  tres variantes literales empatan en 10 y el propio control cae a 10. El orden 10 / 11 / 12 no
  sobrevive al cambio de campo.
- Cualquier tasa: 61 pasadas de cuatro volcanes, en muestra, un solo sensor.
- "Nadie pierde nada": no hay pasadas donde el brazo D publique y el control no.

**Dos notas de honestidad del titular:** el brazo `literal` se queda en 10 de 12, y la métrica "noches
recuperadas" crece con cualquier publicación (`literal_t1_sin_filtro` llega a 12 publicando 54 de 61
pasadas, con cúmulos de hasta 75 píxeles y 1,37 MW contra 1 píxel del resto). Las dos noches de
Planchón-Peteroa que el `literal` no recupera **no son pérdidas de publicación**: publica a 0,25 y
0,52 km del cráter, y lo que falla es la cota contra la distancia que informa MIROVA.
