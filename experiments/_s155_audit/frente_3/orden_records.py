"""F3: ¿records[-1] es el más reciente? nrt-healthcheck.yml lo supone (l. 72).
P1: si la lista estuviera desordenada, esto contaría inversiones > 0. P2: imprime n por volcán (0 = SIN DATO)."""
import json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
for v in ["Lascar","Lastarria","Isluga","Llaima","Villarrica","Chaiten","Tupungatito","Copahue","PlanchonPeteroa","PuyehueCordonCaulle","NevadosDeChillan"]:
    rs = json.load(open(os.path.join(ROOT,"data","mirova_equivalent",v+".json"),encoding="utf-8"))["records"]
    dts = [r.get("datetime_utc") or "" for r in rs]
    inv = sum(1 for a,b in zip(dts,dts[1:]) if b < a)
    print(v, "n", len(rs), "inversiones", inv, "ultimo", dts[-1], "max", max(dts), "igual", dts[-1]==max(dts))
