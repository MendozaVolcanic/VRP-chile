# Plan de relleno del historico con K (S157)

Generado por `armar_relleno.py`; CMR y LAADS consultados el 2026-10-21T02:11:01Z (APIs publicas, sin credenciales).
NO despachado: lo lanza la sesion duena del loop.

## Antes de despachar

1. **El PR del merge que conserva la base tiene que estar mergeado.** Con el merge anterior, relanzar
   unos pocos dias de un volcan escribe su JSON SOLO con esos dias y borra el resto del historico en main.
2. **En serie, uno a la vez**, esperando que termine cada run (incluido su job `merge`): todos usan el
   perfil `_s154_reproc_k_historico`, que es el grupo de concurrencia `reproc-chunked-_s154_reproc_k_historico`, el mismo de los
   relanzamientos de NevadosDeChillan. GitHub guarda UN solo run pendiente por grupo: un tercero
   despachado mientras otro espera lo EXPULSA.
3. Despues de cada run, contar las pasadas del volcan en la ventana contra la serie operacional (A108):
   un run verde con un corte de CMR puede volver a no traerlas.

## Resumen por version del record operacional

Decision por pasada: CMR si respondio (es donde busca `fetch.py`); si CMR no dio dato, el listado
publico del archivo LAADS DAAC (donde se baja el estandar). `existe` exige L1B **y** geolocalizacion.

| product_version | decision (fuente) | pasadas |
|---|---|---|
| `nrt` | no_existe (CMR) | 58 |
| `standard` | existe (CMR) | 31 |

## Despachos (en este orden, uno a la vez)

1. PlanchonPeteroa, 2025-04-09 a 2025-04-09 (1 dias)

```bash
gh workflow run reproc-chunked.yml --repo MendozaVolcanic/VRP-chile --ref main -f profile=_s154_reproc_k_historico -f volcanoes=PlanchonPeteroa -f start=2025-04-09 -f end=2025-04-09 -f max_days=1
```

2. PlanchonPeteroa, 2025-10-01 a 2025-10-01 (1 dias)

```bash
gh workflow run reproc-chunked.yml --repo MendozaVolcanic/VRP-chile --ref main -f profile=_s154_reproc_k_historico -f volcanoes=PlanchonPeteroa -f start=2025-10-01 -f end=2025-10-01 -f max_days=1
```

3. Chaiten, 2025-10-18 a 2025-10-18 (1 dias)

```bash
gh workflow run reproc-chunked.yml --repo MendozaVolcanic/VRP-chile --ref main -f profile=_s154_reproc_k_historico -f volcanoes=Chaiten -f start=2025-10-18 -f end=2025-10-18 -f max_days=1
```

4. Copahue, 2026-03-07 a 2026-03-07 (1 dias)

```bash
gh workflow run reproc-chunked.yml --repo MendozaVolcanic/VRP-chile --ref main -f profile=_s154_reproc_k_historico -f volcanoes=Copahue -f start=2026-03-07 -f end=2026-03-07 -f max_days=1
```

5. PuyehueCordonCaulle, 2026-04-25 a 2026-04-25 (1 dias)

```bash
gh workflow run reproc-chunked.yml --repo MendozaVolcanic/VRP-chile --ref main -f profile=_s154_reproc_k_historico -f volcanoes=PuyehueCordonCaulle -f start=2026-04-25 -f end=2026-04-25 -f max_days=1
```

6. Copahue, 2026-07-02 a 2026-07-02 (1 dias)

```bash
gh workflow run reproc-chunked.yml --repo MendozaVolcanic/VRP-chile --ref main -f profile=_s154_reproc_k_historico -f volcanoes=Copahue -f start=2026-07-02 -f end=2026-07-02 -f max_days=1
```

7. Copahue, 2026-07-05 a 2026-07-05 (1 dias)

```bash
gh workflow run reproc-chunked.yml --repo MendozaVolcanic/VRP-chile --ref main -f profile=_s154_reproc_k_historico -f volcanoes=Copahue -f start=2026-07-05 -f end=2026-07-05 -f max_days=1
```

8. PuyehueCordonCaulle, 2026-07-13 a 2026-07-13 (1 dias)

```bash
gh workflow run reproc-chunked.yml --repo MendozaVolcanic/VRP-chile --ref main -f profile=_s154_reproc_k_historico -f volcanoes=PuyehueCordonCaulle -f start=2026-07-13 -f end=2026-07-13 -f max_days=1
```

9. PlanchonPeteroa, 2026-07-27 a 2026-07-27 (1 dias)

```bash
gh workflow run reproc-chunked.yml --repo MendozaVolcanic/VRP-chile --ref main -f profile=_s154_reproc_k_historico -f volcanoes=PlanchonPeteroa -f start=2026-07-27 -f end=2026-07-27 -f max_days=1
```

10. PuyehueCordonCaulle, 2026-09-11 a 2026-09-11 (1 dias)

```bash
gh workflow run reproc-chunked.yml --repo MendozaVolcanic/VRP-chile --ref main -f profile=_s154_reproc_k_historico -f volcanoes=PuyehueCordonCaulle -f start=2026-09-11 -f end=2026-09-11 -f max_days=1
```

## Pasadas sin producto estandar (repetir el trozo no las traeria)

- Chaiten 2026-08-05 05:30 VIIRS_SNPP (record `nrt`, CMR)
- Chaiten 2026-08-05 05:30 VIIRS_SNPP_750 (record `nrt`, CMR)
- Chaiten 2026-08-06 05:12 VIIRS_SNPP (record `nrt`, CMR)
- Chaiten 2026-08-06 05:12 VIIRS_SNPP_750 (record `nrt`, CMR)
- Chaiten 2026-08-06 06:54 VIIRS_SNPP (record `nrt`, CMR)
- Chaiten 2026-08-06 06:54 VIIRS_SNPP_750 (record `nrt`, CMR)
- Copahue 2026-08-05 05:30 VIIRS_SNPP (record `nrt`, CMR)
- Copahue 2026-08-05 05:30 VIIRS_SNPP_750 (record `nrt`, CMR)
- Copahue 2026-08-06 05:12 VIIRS_SNPP (record `nrt`, CMR)
- Copahue 2026-08-06 05:12 VIIRS_SNPP_750 (record `nrt`, CMR)
- Copahue 2026-08-06 06:48 VIIRS_SNPP (record `nrt`, CMR)
- Copahue 2026-08-06 06:48 VIIRS_SNPP_750 (record `nrt`, CMR)
- Isluga 2026-08-05 05:24 VIIRS_SNPP (record `nrt`, CMR)
- Isluga 2026-08-05 05:24 VIIRS_SNPP_750 (record `nrt`, CMR)
- Isluga 2026-08-06 05:06 VIIRS_SNPP (record `nrt`, CMR)
- Isluga 2026-08-06 05:06 VIIRS_SNPP_750 (record `nrt`, CMR)
- Isluga 2026-08-06 06:42 VIIRS_SNPP (record `nrt`, CMR)
- Isluga 2026-08-06 06:42 VIIRS_SNPP_750 (record `nrt`, CMR)
- Lascar 2026-08-05 05:24 VIIRS_SNPP (record `nrt`, CMR)
- Lascar 2026-08-05 05:24 VIIRS_SNPP_750 (record `nrt`, CMR)
- Lascar 2026-08-06 05:06 VIIRS_SNPP (record `nrt`, CMR)
- Lascar 2026-08-06 05:06 VIIRS_SNPP_750 (record `nrt`, CMR)
- Lascar 2026-08-06 06:48 VIIRS_SNPP (record `nrt`, CMR)
- Lascar 2026-08-06 06:48 VIIRS_SNPP_750 (record `nrt`, CMR)
- Lastarria 2026-08-05 05:24 VIIRS_SNPP (record `nrt`, CMR)
- Lastarria 2026-08-05 05:24 VIIRS_SNPP_750 (record `nrt`, CMR)
- Lastarria 2026-08-06 05:06 VIIRS_SNPP (record `nrt`, CMR)
- Lastarria 2026-08-06 05:06 VIIRS_SNPP_750 (record `nrt`, CMR)
- Lastarria 2026-08-06 06:48 VIIRS_SNPP (record `nrt`, CMR)
- Lastarria 2026-08-06 06:48 VIIRS_SNPP_750 (record `nrt`, CMR)
- Llaima 2026-08-05 05:30 VIIRS_SNPP (record `nrt`, CMR)
- Llaima 2026-08-05 05:30 VIIRS_SNPP_750 (record `nrt`, CMR)
- Llaima 2026-08-06 05:12 VIIRS_SNPP (record `nrt`, CMR)
- Llaima 2026-08-06 05:12 VIIRS_SNPP_750 (record `nrt`, CMR)
- Llaima 2026-08-06 06:48 VIIRS_SNPP (record `nrt`, CMR)
- Llaima 2026-08-06 06:48 VIIRS_SNPP_750 (record `nrt`, CMR)
- PlanchonPeteroa 2026-08-05 05:30 VIIRS_SNPP (record `nrt`, CMR)
- PlanchonPeteroa 2026-08-05 05:30 VIIRS_SNPP_750 (record `nrt`, CMR)
- PlanchonPeteroa 2026-08-06 05:06 VIIRS_SNPP (record `nrt`, CMR)
- PlanchonPeteroa 2026-08-06 05:06 VIIRS_SNPP_750 (record `nrt`, CMR)
- PlanchonPeteroa 2026-08-06 06:48 VIIRS_SNPP (record `nrt`, CMR)
- PlanchonPeteroa 2026-08-06 06:48 VIIRS_SNPP_750 (record `nrt`, CMR)
- PuyehueCordonCaulle 2026-08-05 05:30 VIIRS_SNPP (record `nrt`, CMR)
- PuyehueCordonCaulle 2026-08-05 05:30 VIIRS_SNPP_750 (record `nrt`, CMR)
- PuyehueCordonCaulle 2026-08-06 05:12 VIIRS_SNPP (record `nrt`, CMR)
- PuyehueCordonCaulle 2026-08-06 05:12 VIIRS_SNPP_750 (record `nrt`, CMR)
- PuyehueCordonCaulle 2026-08-06 06:48 VIIRS_SNPP (record `nrt`, CMR)
- PuyehueCordonCaulle 2026-08-06 06:48 VIIRS_SNPP_750 (record `nrt`, CMR)
- PuyehueCordonCaulle 2026-08-06 06:54 VIIRS_SNPP (record `nrt`, CMR)
- PuyehueCordonCaulle 2026-08-06 06:54 VIIRS_SNPP_750 (record `nrt`, CMR)
- Tupungatito 2026-08-05 05:24 VIIRS_SNPP (record `nrt`, CMR)
- Tupungatito 2026-08-05 05:24 VIIRS_SNPP_750 (record `nrt`, CMR)
- Tupungatito 2026-08-05 05:30 VIIRS_SNPP (record `nrt`, CMR)
- Tupungatito 2026-08-05 05:30 VIIRS_SNPP_750 (record `nrt`, CMR)
- Tupungatito 2026-08-06 05:06 VIIRS_SNPP (record `nrt`, CMR)
- Tupungatito 2026-08-06 05:06 VIIRS_SNPP_750 (record `nrt`, CMR)
- Tupungatito 2026-08-06 06:48 VIIRS_SNPP (record `nrt`, CMR)
- Tupungatito 2026-08-06 06:48 VIIRS_SNPP_750 (record `nrt`, CMR)

## Pasadas faltantes

| Volcan | Pasada | Sensor | Trozo | Record | Decision | CMR L1B / GEO | LAADS L1B / GEO | CMR NRT L1B |
|---|---|---|---|---|---|---|---|---|
| Chaiten | 2025-10-18 05:00 | VIIRS_NOAA20 | 7 | `standard` | existe (CMR) | VJ102IMG.A2025291.0500.021.2025291112216.nc / VJ103IMG.A2025291.0500.021.2025291100424.nc | VJ102IMG.A2025291.0500.021.2025291112216.nc / VJ103IMG.A2025291.0500.021.2025291100424.nc | no |
| Chaiten | 2025-10-18 06:36 | VIIRS_NOAA20 | 7 | `standard` | existe (CMR) | VJ102IMG.A2025291.0636.021.2025291135439.nc / VJ103IMG.A2025291.0636.021.2025291122227.nc | VJ102IMG.A2025291.0636.021.2025291135439.nc / VJ103IMG.A2025291.0636.021.2025291122227.nc | no |
| Chaiten | 2025-10-18 06:42 | VIIRS_NOAA20 | 7 | `standard` | existe (CMR) | VJ102IMG.A2025291.0642.021.2025291133011.nc / VJ103IMG.A2025291.0642.021.2025291122250.nc | VJ102IMG.A2025291.0642.021.2025291133011.nc / VJ103IMG.A2025291.0642.021.2025291122250.nc | no |
| Chaiten | 2026-08-05 05:30 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Chaiten | 2026-08-05 05:30 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Chaiten | 2026-08-06 05:12 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Chaiten | 2026-08-06 05:12 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Chaiten | 2026-08-06 06:54 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Chaiten | 2026-08-06 06:54 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Copahue | 2026-03-07 07:35 | MODIS_AQUA | 11 | `standard` | existe (CMR) | MYD021KM.A2026066.0735.061.2026066191026.hdf / MYD03.A2026066.0735.061.2026066153019.hdf | MYD021KM.A2026066.0735.061.2026066191026.hdf / MYD03.A2026066.0735.061.2026066153019.hdf | no |
| Copahue | 2026-07-02 04:42 | VIIRS_NOAA20_750 | 14 | `standard` | existe (CMR) | VJ102MOD.A2026183.0442.021.2026183114516.nc / VJ103MOD.A2026183.0442.021.2026183103325.nc | VJ102MOD.A2026183.0442.021.2026183114516.nc / VJ103MOD.A2026183.0442.021.2026183103325.nc | no |
| Copahue | 2026-07-02 06:24 | VIIRS_NOAA20_750 | 14 | `standard` | existe (CMR) | VJ102MOD.A2026183.0624.021.2026183130544.nc / VJ103MOD.A2026183.0624.021.2026183121825.nc | VJ102MOD.A2026183.0624.021.2026183130544.nc / VJ103MOD.A2026183.0624.021.2026183121825.nc | no |
| Copahue | 2026-07-05 05:06 | VIIRS_SNPP | 14 | `standard` | existe (CMR) | VNP02IMG.A2026186.0506.002.2026186131009.nc / VNP03IMG.A2026186.0506.002.2026186125120.nc | VNP02IMG.A2026186.0506.002.2026186131009.nc / VNP03IMG.A2026186.0506.002.2026186125120.nc | no |
| Copahue | 2026-07-05 06:48 | VIIRS_SNPP | 14 | `standard` | existe (CMR) | VNP02IMG.A2026186.0648.002.2026186151805.nc / VNP03IMG.A2026186.0648.002.2026186145731.nc | VNP02IMG.A2026186.0648.002.2026186151805.nc / VNP03IMG.A2026186.0648.002.2026186145731.nc | no |
| Copahue | 2026-08-05 05:30 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Copahue | 2026-08-05 05:30 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Copahue | 2026-08-06 05:12 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Copahue | 2026-08-06 05:12 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Copahue | 2026-08-06 06:48 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Copahue | 2026-08-06 06:48 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Isluga | 2026-08-05 05:24 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Isluga | 2026-08-05 05:24 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Isluga | 2026-08-06 05:06 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Isluga | 2026-08-06 05:06 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Isluga | 2026-08-06 06:42 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Isluga | 2026-08-06 06:42 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Lascar | 2026-08-05 05:24 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Lascar | 2026-08-05 05:24 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Lascar | 2026-08-06 05:06 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Lascar | 2026-08-06 05:06 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Lascar | 2026-08-06 06:48 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Lascar | 2026-08-06 06:48 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Lastarria | 2026-08-05 05:24 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Lastarria | 2026-08-05 05:24 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Lastarria | 2026-08-06 05:06 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Lastarria | 2026-08-06 05:06 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Lastarria | 2026-08-06 06:48 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Lastarria | 2026-08-06 06:48 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Llaima | 2026-08-05 05:30 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Llaima | 2026-08-05 05:30 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Llaima | 2026-08-06 05:12 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Llaima | 2026-08-06 05:12 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Llaima | 2026-08-06 06:48 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Llaima | 2026-08-06 06:48 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| PlanchonPeteroa | 2025-04-09 04:30 | VIIRS_SNPP_750 | 2 | `standard` | existe (CMR) | VNP02MOD.A2025099.0430.002.2025099124749.nc / VNP03MOD.A2025099.0430.002.2025099122620.nc | VNP02MOD.A2025099.0430.002.2025099124749.nc / VNP03MOD.A2025099.0430.002.2025099122620.nc | no |
| PlanchonPeteroa | 2025-04-09 04:36 | VIIRS_SNPP_750 | 2 | `standard` | existe (CMR) | VNP02MOD.A2025099.0436.002.2025099124758.nc / VNP03MOD.A2025099.0436.002.2025099122622.nc | VNP02MOD.A2025099.0436.002.2025099124758.nc / VNP03MOD.A2025099.0436.002.2025099122622.nc | no |
| PlanchonPeteroa | 2025-04-09 04:54 | VIIRS_NOAA20 | 2 | `standard` | existe (CMR) | VJ102IMG.A2025099.0454.021.2025099111108.nc / VJ103IMG.A2025099.0454.021.2025099100039.nc | VJ102IMG.A2025099.0454.021.2025099111108.nc / VJ103IMG.A2025099.0454.021.2025099100039.nc | no |
| PlanchonPeteroa | 2025-04-09 04:54 | VIIRS_NOAA20_750 | 2 | `standard` | existe (CMR) | VJ102MOD.A2025099.0454.021.2025099111108.nc / VJ103MOD.A2025099.0454.021.2025099100039.nc | VJ102MOD.A2025099.0454.021.2025099111108.nc / VJ103MOD.A2025099.0454.021.2025099100039.nc | no |
| PlanchonPeteroa | 2025-04-09 05:48 | VIIRS_NOAA21 | 2 | `standard` | existe (CMR) | VJ202IMG.A2025099.0548.021.2025099124726.nc / VJ203IMG.A2025099.0548.021.2025099100853.nc | VJ202IMG.A2025099.0548.021.2025099124726.nc / VJ203IMG.A2025099.0548.021.2025099100853.nc | no |
| PlanchonPeteroa | 2025-04-09 05:48 | VIIRS_NOAA21_750 | 2 | `standard` | existe (CMR) | VJ202MOD.A2025099.0548.021.2025099124726.nc / VJ203MOD.A2025099.0548.021.2025099100853.nc | VJ202MOD.A2025099.0548.021.2025099124726.nc / VJ203MOD.A2025099.0548.021.2025099100853.nc | no |
| PlanchonPeteroa | 2025-04-09 06:12 | VIIRS_SNPP_750 | 2 | `standard` | existe (CMR) | VNP02MOD.A2025099.0612.002.2025099145555.nc / VNP03MOD.A2025099.0612.002.2025099143424.nc | VNP02MOD.A2025099.0612.002.2025099145555.nc / VNP03MOD.A2025099.0612.002.2025099143424.nc | no |
| PlanchonPeteroa | 2025-04-09 06:36 | VIIRS_NOAA20 | 2 | `standard` | existe (CMR) | VJ102IMG.A2025099.0636.021.2025099130221.nc / VJ103IMG.A2025099.0636.021.2025099122646.nc | VJ102IMG.A2025099.0636.021.2025099130221.nc / VJ103IMG.A2025099.0636.021.2025099122646.nc | no |
| PlanchonPeteroa | 2025-04-09 06:36 | VIIRS_NOAA20_750 | 2 | `standard` | existe (CMR) | VJ102MOD.A2025099.0636.021.2025099130221.nc / VJ103MOD.A2025099.0636.021.2025099122646.nc | VJ102MOD.A2025099.0636.021.2025099130221.nc / VJ103MOD.A2025099.0636.021.2025099122646.nc | no |
| PlanchonPeteroa | 2025-10-01 04:54 | VIIRS_SNPP_750 | 7 | `standard` | existe (CMR) | VNP02MOD.A2025274.0454.002.2025274131217.nc / VNP03MOD.A2025274.0454.002.2025274123629.nc | VNP02MOD.A2025274.0454.002.2025274131217.nc / VNP03MOD.A2025274.0454.002.2025274123629.nc | no |
| PlanchonPeteroa | 2025-10-01 05:18 | VIIRS_NOAA20_750 | 7 | `standard` | existe (CMR) | VJ102MOD.A2025274.0518.021.2025274111444.nc / VJ103MOD.A2025274.0518.021.2025274101037.nc | VJ102MOD.A2025274.0518.021.2025274111444.nc / VJ103MOD.A2025274.0518.021.2025274101037.nc | no |
| PlanchonPeteroa | 2025-10-01 06:06 | VIIRS_NOAA21_750 | 7 | `standard` | existe (CMR) | VJ202MOD.A2025274.0606.021.2025274121346.nc / VJ203MOD.A2025274.0606.021.2025274115500.nc | VJ202MOD.A2025274.0606.021.2025274121346.nc / VJ203MOD.A2025274.0606.021.2025274115500.nc | no |
| PlanchonPeteroa | 2025-10-01 06:36 | VIIRS_SNPP_750 | 7 | `standard` | existe (CMR) | VNP02MOD.A2025274.0636.002.2025274150833.nc / VNP03MOD.A2025274.0636.002.2025274144505.nc | VNP02MOD.A2025274.0636.002.2025274150833.nc / VNP03MOD.A2025274.0636.002.2025274144505.nc | no |
| PlanchonPeteroa | 2026-07-27 05:18 | VIIRS_NOAA20_750 | 15 | `standard` | existe (CMR) | VJ102MOD.A2026208.0518.021.2026208111143.nc / VJ103MOD.A2026208.0518.021.2026208101657.nc | VJ102MOD.A2026208.0518.021.2026208111143.nc / VJ103MOD.A2026208.0518.021.2026208101657.nc | no |
| PlanchonPeteroa | 2026-08-05 05:30 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| PlanchonPeteroa | 2026-08-05 05:30 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| PlanchonPeteroa | 2026-08-06 05:06 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| PlanchonPeteroa | 2026-08-06 05:06 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| PlanchonPeteroa | 2026-08-06 06:48 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| PlanchonPeteroa | 2026-08-06 06:48 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| PuyehueCordonCaulle | 2026-04-25 05:06 | VIIRS_NOAA21 | 12 | `standard` | existe (CMR) | VJ202IMG.A2026115.0506.021.2026115103004.nc / VJ203IMG.A2026115.0506.021.2026115101102.nc | VJ202IMG.A2026115.0506.021.2026115103004.nc / VJ203IMG.A2026115.0506.021.2026115101102.nc | no |
| PuyehueCordonCaulle | 2026-04-25 06:00 | VIIRS_NOAA20_750 | 12 | `standard` | existe (CMR) | VJ102MOD.A2026115.0600.021.2026115122752.nc / VJ103MOD.A2026115.0600.021.2026115114402.nc | VJ102MOD.A2026115.0600.021.2026115122752.nc / VJ103MOD.A2026115.0600.021.2026115114402.nc | no |
| PuyehueCordonCaulle | 2026-04-25 06:48 | VIIRS_NOAA21 | 12 | `standard` | existe (CMR) | VJ202IMG.A2026115.0648.021.2026115120003.nc / VJ203IMG.A2026115.0648.021.2026115115031.nc | VJ202IMG.A2026115.0648.021.2026115120003.nc / VJ203IMG.A2026115.0648.021.2026115115031.nc | no |
| PuyehueCordonCaulle | 2026-07-13 02:05 | MODIS_TERRA | 14 | `standard` | existe (CMR) | MOD021KM.A2026194.0205.061.2026194131825.hdf / MOD03.A2026194.0205.061.2026194093425.hdf | MOD021KM.A2026194.0205.061.2026194131825.hdf / MOD03.A2026194.0205.061.2026194093425.hdf | no |
| PuyehueCordonCaulle | 2026-07-13 07:00 | MODIS_AQUA | 14 | `standard` | existe (CMR) | MYD021KM.A2026194.0700.061.2026194193117.hdf / MYD03.A2026194.0700.061.2026194152315.hdf | MYD021KM.A2026194.0700.061.2026194193117.hdf / MYD03.A2026194.0700.061.2026194152315.hdf | no |
| PuyehueCordonCaulle | 2026-07-13 08:40 | MODIS_AQUA | 14 | `standard` | existe (CMR) | MYD021KM.A2026194.0840.061.2026194191852.hdf / MYD03.A2026194.0840.061.2026194164612.hdf | MYD021KM.A2026194.0840.061.2026194191852.hdf / MYD03.A2026194.0840.061.2026194164612.hdf | no |
| PuyehueCordonCaulle | 2026-08-05 05:30 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| PuyehueCordonCaulle | 2026-08-05 05:30 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| PuyehueCordonCaulle | 2026-08-06 05:12 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| PuyehueCordonCaulle | 2026-08-06 05:12 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| PuyehueCordonCaulle | 2026-08-06 06:48 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| PuyehueCordonCaulle | 2026-08-06 06:48 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| PuyehueCordonCaulle | 2026-08-06 06:54 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| PuyehueCordonCaulle | 2026-08-06 06:54 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| PuyehueCordonCaulle | 2026-09-11 05:36 | VIIRS_SNPP | 16 | `standard` | existe (CMR) | VNP02IMG.A2026254.0536.002.2026254120727.nc / VNP03IMG.A2026254.0536.002.2026254114313.nc | VNP02IMG.A2026254.0536.002.2026254120727.nc / VNP03IMG.A2026254.0536.002.2026254114313.nc | no |
| PuyehueCordonCaulle | 2026-09-11 05:54 | VIIRS_NOAA20 | 16 | `standard` | existe (CMR) | VJ102IMG.A2026254.0554.021.2026254132052.nc / VJ103IMG.A2026254.0554.021.2026254123047.nc | VJ102IMG.A2026254.0554.021.2026254132052.nc / VJ103IMG.A2026254.0554.021.2026254123047.nc | no |
| PuyehueCordonCaulle | 2026-09-11 07:25 | MODIS_AQUA | 16 | `standard` | existe (CMR) | MYD021KM.A2026254.0725.061.2026254194954.hdf / MYD03.A2026254.0725.061.2026254152820.hdf | MYD021KM.A2026254.0725.061.2026254194954.hdf / MYD03.A2026254.0725.061.2026254152820.hdf | no |
| Tupungatito | 2026-08-05 05:24 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Tupungatito | 2026-08-05 05:24 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Tupungatito | 2026-08-05 05:30 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Tupungatito | 2026-08-05 05:30 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Tupungatito | 2026-08-06 05:06 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Tupungatito | 2026-08-06 05:06 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Tupungatito | 2026-08-06 06:48 | VIIRS_SNPP | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
| Tupungatito | 2026-08-06 06:48 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (CMR) | no / no | no / no | no |
