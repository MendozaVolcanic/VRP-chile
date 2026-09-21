# A/B de la conectiva (brazo F): resultado sobre la ventana completa (S148)

> Pre-registro: `experiments/_s147_ab_conectiva/PREREGISTRO.md`, commiteado antes de correr.
> Runs: 35548121381 (brazos B y F) y 35558196104 (reparación del control B en Chaitén,
> Tupungatito y Villarrica, mismo código). Ventana 2026-09-01 a 2026-09-20, toda posterior a #535.
> Salidas crudas: `experiments/_s148_veredicto_conectiva/`. Ningún número de este documento está
> transcrito de memoria: todos salen de esos archivos.
>
> **Esto NO autoriza ningún cambio en producción** (pre-registro §5). Decide si la hipótesis merece
> el gate completo del proyecto: brainstorming, verificación a nivel de píxel, tag defensivo y
> confirmación de Nicolás (A45).

## 0. Lo que agregó el verificador con contexto limpio (leer antes que el resto)

Informe: `docs/audit_s148/VERIFICADOR_RESULTADO_CONECTIVA.md`, scripts en
`experiments/_s148_verificador_resultado/`. **No logró romper el resultado central** (P1 a P4,
magnitud pareada, cúmulos movidos y pasadas perdidas le salen iguales con cálculo propio, y el
reemplazo de los tres volcanes reparados está limpio: 0 gránulos y 0 `product_version` distintos
entre brazos en las 2386 pasadas). Sin hallazgos de gravedad 4 ni 5. Pero corrige cuatro cosas de
este documento:

1. **El costo del §4 está SUBCONTADO.** Fuera de las 143 pasadas positivas, el brazo apaga **50
   publicaciones de VIIRS 375 en noches en que MIROVA sí alertó en ese volcán** por otra pasada
   (el control publica 84 de 171 y el brazo 34), y 7 de 15 en pasadas con referencia lejana. El
   evaluador no mira ese estrato. No está verificado a nivel de píxel que sean calor real, pero
   son las candidatas más serias a señal verdadera que `max` apaga: en una noche con actividad,
   el operador vería menos pasadas confirmándola. **Este es el costo que hay que medir antes de
   cualquier adopción.**
2. **C8 (nulo barajado) no sirve como prueba de selectividad**: un apagador al azar lo cumple en
   200 de 200 semillas. La selectividad del brazo F se sostiene por otra vía (Fisher p = 0,003
   sobre las zonas, P3, y el contraste queda del lado opuesto al de un corte parejo de magnitud).
   La fila de C8 de la tabla del §2 no debe citarse como evidencia.
3. **P2 con 10 sobrevivientes se cumple por azar en 24 % de los sorteos.** P2 "decide" en el
   pre-registro, pero con esta muestra tiene poco poder; lo que carga el peso es P3 y Fisher.
4. **Números que quedaron del tramo de 17 días**: en el §6 "30 de 124" es **34 de 135** sobre la
   ventana completa, y "Nevados de Chillán aporta 1" son **4** positivas. Las noches afectadas son
   dos según la definición: Lastarria 2026-09-04 además de Isluga 2026-09-19. Y la banda del
   control que hace imprimir INDECIDIBLE falla también en VIIRS 750, no sólo en VIIRS 375.

Lo que el verificador no pudo comprobar: el control positivo contra el run 35521542153 (ese
brazo no estaba en su copia); eso lo corrí yo y está en `evaluar_salida.txt`.

## 1. El fenómeno

De noche, cada píxel se compara con sus vecinos en un índice que cruza el infrarrojo medio con el
térmico. El paper de MIROVA da dos umbrales para decidir si el píxel se despega: un piso fijo y
uno que se adapta al ruido de la escena (la media más unos cuantos sigmas). La fórmula del paper
toma el **menor** de los dos (`min`); la prosa del mismo paper, y su antecesor de 2014, exigen
superar **los dos** (`max`). En el borde del barrido los píxeles son más grandes y más ruidosos, y
con fondo frío (nube alta, nieve) el índice se vuelve inestable. Si manda el menor, ese ruido
cruza el piso fijo y se publica. Si mandan los dos, el propio ruido sube el umbral y se calla solo.
Eso es lo que la hipótesis predecía, y lo que MIROVA muestra: su eficiencia cae hacia el borde.

## 2. Controles, antes de mirar nada

| control | resultado |
|---|---|
| Cobertura pareja y simétrica | **2386 contra 2386**, faltan 0 y sobran 0 (tras la reparación; antes al control le faltaban 71) |
| Control positivo del pre-registro: el B de este run reproduce al B del run 35521542153 en la decisión de publicar | **2362 de 2362 idénticas**, cero diferencias en ningún campo |
| Nulo estructural | 0 publicadas de 1142 pasadas sin ningún píxel anómalo |
| Nulo por etiquetas barajadas (que la caída sea selectiva y no un endurecimiento parejo) | observado -0,108, nulo entre 0,050 y 0,146: **fuera del nulo** |
| Verificador con contexto limpio sobre el tramo de 17 días | no logró romperla (`docs/audit_s148/VERIFICADOR_LECTURA_CONECTIVA.md`) |

⚠️ **El evaluador imprime INDECIDIBLE, y hay que decir por qué.** Su control positivo incluye
una banda para la tasa de publicación del control (80 a 92 % en VIIRS 375) que está calibrada
para el control de **producción**, con el Test 1 encendido. Acá el control es el brazo B, sin
Test 1, que publica 29,8 %: queda fuera de esa banda por construcción. El resto de ese control
(identidad 1,0 y cobertura 1,0) se cumple. No toqué el parámetro para cambiar el rótulo: lo dejo
escrito y el veredicto de abajo se apoya en el control que el pre-registro de este A/B define.
Arreglar el evaluador para que la banda dependa del control es trabajo pendiente.

## 3. Las cuatro predicciones, VIIRS 375

| | qué decía | control B (`min`) | brazo F (`max`) | ¿se cumple? |
|---|---|---|---|---|
| **P1** publicación en negativos limpios | 18 % o menos | 29,8 % (111 de 372) | **2,7 %** (10 de 372) | sí |
| **P2** razón borde sobre nadir (**la que decide**) | 1,3 o menos | 2,15 | **0,25** | sí |
| **P3** borde con fondo frío | 30 % o menos | 58,4 % (45 de 77) | **2,6 %** (2 de 77) | sí |
| **P4** recall por pasada | 118 o más, ninguna pérdida de 0,5 MW o más | 137 de 143 | **135 de 143**, ninguna grande | sí |

Por zona: nadir de 18,6 a 4,7 % (6 de 129), zona media de 25,0 a 2,9 %, borde de 40,0 a 1,1 %
(2 de 175).

Salvedad del verificador que sigue valiendo: el valor 0,25 de P2 sale de 2 publicaciones contra
6. Que P2 quede en 1,3 o menos es robusto; que "se invierta" no se puede afirmar con esa muestra.

**Hipótesis CONFIRMADA en VIIRS 375**: la conectiva apaga selectivamente lo del borde con fondo
frío, que es donde vivía el residual.

## 4. Lo que cuesta

- **Dos pasadas positivas, las dos bajo 0,5 MW**: Lastarria 2026-09-04 06:24 (MIROVA 0,14 MW) y
  Tupungatito 2026-09-19 05:06 (MIROVA 0,05 MW).
- **Una noche de volcán**: Isluga 2026-09-19 (MIROVA 0,06 MW). El evaluador marca que esa vara no
  tiene poder estadístico, así que se informa y no decide.
- **La magnitud publicada baja.** Razón contra MIROVA, mediana pareada en VIIRS 375: de **0,79 a
  0,71** (n = 135). No es parejo: baja en Puyehue Cordón Caulle (1,06 a 0,92), Tupungatito (0,44
  a 0,38) y Chaitén (1,31 a 1,25); no cambia en Láscar, Isluga, Planchón Peteroa, Villarrica ni
  Lastarria. Mecanismo medido en `docs/audit_s148/MEDICION_H2_H3_CONECTIVA.md`: se pierde el
  vecino tibio del cúmulo. Es el mismo déficit de A99, agravado. C4 del evaluador igual se cumple.
- **El cúmulo se mueve más de 500 m en 13 de 228 pares**, 10 de ellos en Lastarria (0,8 a 1,8
  km), más Tupungatito (3,1 km), Puyehue Cordón Caulle (3,9 km) y un MODIS de Villarrica. C7 es
  informativo desde #729 porque MIROVA no puede arbitrarlo, pero en Lastarria el desplazamiento
  puede estar tocando el campo fumarólico real (A84): hay que mirarlo con dirección antes de
  cualquier adopción.

## 5. Los otros sensores

- **VIIRS 750**: negativos limpios de 5,9 % (37 de 622) a 0,6 % (4 de 622); positivos 13 de 18 en
  los dos brazos.
- **MODIS: el cero NO es fidelidad.** Pasa de 8,9 % (39 de 440) a 0 de 440, pero con `max` y la
  banda 21 el camino contextual deja de existir (medido en la lectura preliminar: 1 de 399
  pasadas con píxeles del primer pase, contra 397 de 399). Y hay una sola pasada positiva de
  MODIS en la ventana. **En MODIS la conectiva no se juzga sola: va junto con la banda 22 (D21).**

## 6. Dependencias que la propuesta tiene que declarar

1. **D22 y el segundo pase se compensan.** 30 de 124 positivas de VIIRS 375 publican sin ningún
   píxel del primer pase: la compuerta `bt > t_bg + 3 K` las rechaza y el segundo pase, que corre
   sin condicionar, las recupera. Se tocan juntas o no se tocan.
2. **La caja (D18) sigue sin medirse**: el flag sólo llega al primer pase
   (`docs/audit_s148/POR_QUE_LA_CAJA_NO_APAGA.md`). Los brazos G y H no responden esa pregunta.
3. **La ventana es de 20 días de septiembre**, con 143 pasadas positivas dominadas por Isluga,
   Puyehue Cordón Caulle, Tupungatito y Láscar. Villarrica aporta 5 y Nevados de Chillán 1. No
   dice qué pasa con un lago de lava débil en pleno invierno.

## 7. Qué sigue, y qué le toca decidir a Nicolás

La hipótesis merece el gate completo. Propuesta de orden: (a) verificación a nivel de píxel
contra los TIF de MIROVA en las 10 negativas que sobreviven y en las 13 pasadas donde el cúmulo
se mueve; (b) un A/B sobre meses de invierno (junio a agosto), reprocesados en los dos brazos con el
código de hoy, que es donde el lago de lava débil y el fondo frío pesan más; (c) en MODIS, el brazo
conjunto banda 22 con `max`; (d) arreglar el cableado de la caja y repetir G y H. Ninguno de
esos pasos lo despacho sin el visto bueno de Nicolás.
