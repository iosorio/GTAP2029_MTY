#!/usr/bin/env python3
"""
Procesa la captura de Publish or Perish y calcula el factor de cobertura
Google Scholar / OpenAlex, obra por obra.

Lee las DOS vias en las que puede llegar la captura, sin que haya que elegir:

  * `scholar/*.json`  — consultas guardadas de PoP, copiadas de la MacPro desde
                        ~/Library/Application Support/Publish or Perish/Results6/
  * `pop_csv/*.csv`   — exportaciones manuales (File > Export Results > CSV)

Los denominadores de OpenAlex NO se escriben a mano: se derivan de
`resultados_openalex.json`, sumando los registros que OpenAlex parte en dos.
La version previa los llevaba escritos y dos estaban mal --- GTAP-E con 417 en
vez de 746 y GTAP-AGR con 30 en vez de 179, ambos declarando `registros=2`---,
lo que habria inflado sus razones 1.79x y 5.97x sobre el unico numero que esta
ruta existe para medir.

Descarta los registros `CITATION` de Scholar: son entradas que Scholar fabrica a
partir de referencias sueltas que no logro vincular al documento real, y sus
conteos son basura. Tomarlos por buenos fue lo que hundio el intento del 25 de
agosto de 2026, donde "The Standard GTAP Model, Version 7" salio con 2 citas en
Scholar contra 293 en OpenAlex --- la brecha al reves de la realidad.

Uso:
    python3 09_procesar_pop.py                  # lee scholar/ y pop_csv/
    python3 09_procesar_pop.py --desde-macpro   # copia Results6/ de la MacPro y procesa
    python3 09_procesar_pop.py --json           # vuelca el JSON a stdout

Escribe resultados_pop.json y comparacion_scholar_openalex.csv.
Ver 08_protocolo_scholar.md.
"""
import argparse
import csv
import glob
import json
import os
import re
import subprocess
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
OPENALEX_JSON = os.path.join(AQUI, "resultados_openalex.json")
CRUDOS = os.path.join(AQUI, "scholar")
CSVS = os.path.join(AQUI, "pop_csv")
SALIDA_JSON = os.path.join(AQUI, "resultados_pop.json")
SALIDA_CSV = os.path.join(AQUI, "comparacion_scholar_openalex.csv")

MACPRO = "macpro"
LLAVE = os.path.expanduser("~/.ssh/id_ed25519_ior_macpro")
REMOTO = "/Users/Israel/Library/Application Support/Publish or Perish/Results6/"

# Fichas que Scholar conoce solo por bibliografias ajenas. Nunca son la obra.
TIPO_FANTASMA = "CITATION"

# Por debajo de esto una fila no puede ser la obra canonica, salvo donde la
# tabla declara que un numero chico es correcto (gtap12).
MINIMO_PLAUSIBLE = 10

# El registro de obras. `oa` selecciona los registros de resultados_openalex.json
# cuya suma es el denominador --- por eso GTAP-E, GTAP-AGR y Standard v7 quedan
# fusionadas sin que nadie sume a mano. `gs` empareja las filas de Scholar.
OBRAS = [
    dict(clave="gtap5", titulo="Global Trade, Assistance, and Production: The GTAP 5 Data Base",
         oa=r"gtap 5 data", gs=r"gtap\s?5\s?data\s?base", anios={2002}, libro=True),
    dict(clave="hertel1997", titulo="Global Trade Analysis: Modeling and Applications",
         oa=r"global trade analysis", gs=r"global trade analysis:? modeling and applications",
         anios={1997}, libro=True, suma_capitulo="structure",
         nota="Scholar agrega ediciones, reimpresiones y capitulos bajo el registro "
              "del libro; OpenAlex lista 'Structure of GTAP' (cap. 2) aparte. La "
              "razon de un libro es el techo del factor de cobertura, no su valor tipico."),
    dict(clave="gtape", titulo="GTAP-E: An Energy-Environmental Version of the GTAP Model",
         oa=r"gtap-?e\b", gs=r"gtap-?e\b.*energy.?environmental", anios={2001, 2002},
         nota="Scholar tambien lista una revision de 2007 (Truong, Kemfert, Burniaux) que "
              "OpenAlex no separa; queda excluida por anio. Es la obra con el "
              "emparejamiento mas sucio de las once."),
    dict(clave="gtap9", titulo="An Overview of the GTAP 9 Data Base",
         oa=r"gtap 9 data", gs=r"overview of the gtap\s?9\s?data\s?base", anios={2016}),
    dict(clave="gtap10", titulo="The GTAP Data Base: Version 10",
         oa=r"gtap data ?base:? ?version 10", gs=r"gtap data\s?base:? ?version 10",
         anios={2019}, excluir=r"pakistan"),
    dict(clave="standard7", titulo="The Standard GTAP Model, Version 7",
         oa=r"standard gtap model", gs=r"standard gtap model,? version 7", anios={2017}),
    dict(clave="structure", titulo="Structure of GTAP",
         oa=r"structure of gtap", gs=r"structure of gtap", anios={1996, 1997, 1999, 2013},
         excluir=r"theoretical structure|dynamic gtap", libro=True,
         nota="Scholar devuelve tambien 'Theoretical structure of Dynamic GTAP' "
              "(Ianchovichina y McDougall, 377 citas), que es otra obra y queda excluida."),
    dict(clave="gtapagr", titulo="GTAP-AGR: A Framework for Assessing the Implications "
                                 "of Multilateral Changes in Agricultural Policies",
         oa=r"gtap-?agr", gs=r"gtap-?agr", anios={2005}),
    dict(clave="gtap11", titulo="The GTAP Data Base: Version 11",
         oa=r"gtap data ?base:? ?version 11", gs=r"data\s?base:? ?version 11", anios={2022}),
    dict(clave="dynamic", titulo="Dynamic Modeling and Applications for Global Economic Analysis",
         oa=r"dynamic modeling and applications", gs=r"dynamic modeling and applications",
         anios={2012}, libro=True),
    dict(clave="gtap12", titulo="The GTAP Data Base: Version 12",
         oa=r"gtap data ?base:? ?version 12", gs=r"data\s?base:? ?version 12", anios={2025},
         excluir_de_razon=True,
         nota="1 cita en OpenAlex y 0 resultados en Scholar: demasiado reciente para "
              "sostener un cociente. Se reporta pero no entra en la mediana."),
    # Bloque B: OpenAlex no los indexa como obras. Sin denominador no hay razon;
    # el valor de Scholar dimensiona el hueco en terminos absolutos.
    dict(clave="gtap8", titulo="Global Trade, Assistance, and Production: The GTAP 8 Data Base",
         oa=None, gs=r"gtap\s?8\s?data\s?base", anios={2012}, hueco=True),
    dict(clave="gtap7", titulo="Global Trade, Assistance, and Production: The GTAP 7 Data Base",
         oa=None, gs=r"gtap\s?7\s?data\s?base", anios={2008}, hueco=True),
    dict(clave="gtap6", titulo="Global Trade, Assistance, and Production: The GTAP 6 Data Base",
         oa=None, gs=r"gtap\s?6\s?data\s?base", anios={2006}, hueco=True),
]


def entero(v):
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return None


def denominadores():
    """Suma, por obra, los registros de OpenAlex que le pertenecen."""
    with open(OPENALEX_JSON, encoding="utf-8") as fh:
        canonicas = json.load(fh)["openalex"]["obras_canonicas"]
    for obra in OBRAS:
        if not obra["oa"]:
            obra["openalex"], obra["openalex_registros"], obra["openalex_ids"] = None, 0, []
            continue
        hits = [o for o in canonicas if re.search(obra["oa"], o["titulo"], re.I)]
        obra["openalex"] = sum(o["cited_by_count"] for o in hits)
        obra["openalex_registros"] = len(hits)
        obra["openalex_ids"] = [o["openalex_id"] for o in hits]
    por_clave = {o["clave"]: o for o in OBRAS}
    for obra in OBRAS:
        otra = obra.get("suma_capitulo")
        if otra and por_clave.get(otra, {}).get("openalex"):
            obra["openalex_con_capitulo"] = obra["openalex"] + por_clave[otra]["openalex"]


def traer_de_macpro():
    os.makedirs(CRUDOS, exist_ok=True)
    orden = ["scp", "-q", "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes",
             "-i", LLAVE, "%s:%s*.json" % (MACPRO, REMOTO), CRUDOS + "/"]
    hecho = subprocess.run(orden, capture_output=True, text=True)
    if hecho.returncode != 0:
        sys.exit("no se pudo copiar de la MacPro:\n" + hecho.stderr.strip())
    n = len([x for x in os.listdir(CRUDOS) if x.endswith(".json")])
    print("copiadas %d consultas a scholar/" % n, file=sys.stderr)


def filas_de_json():
    """Consultas guardadas de PoP (Results6)."""
    salida = []
    for ruta in sorted(glob.glob(os.path.join(CRUDOS, "*.json"))):
        with open(ruta, encoding="utf-8-sig") as fh:
            d = json.load(fh)
        consulta = d.get("$query", {})
        etiqueta = consulta.get("Name") or consulta.get("Title") or ""
        for r in d.get("$results", []):
            autores = r.get("authors") or []
            salida.append(dict(
                titulo=(r.get("title") or "").strip(),
                tipo=(r.get("type") or "").strip().upper() or None,
                cites=entero(r.get("cites")),
                anio=str(r.get("year") or "") or None,
                autores=", ".join(autores) if isinstance(autores, list) else str(autores),
                origen=os.path.basename(ruta), via="consulta guardada",
                consulta=etiqueta, cites_url=r.get("cites_url") or None))
    return salida


def filas_de_csv():
    """Exportaciones manuales a CSV."""
    salida = []
    for ruta in sorted(glob.glob(os.path.join(CSVS, "*.csv"))):
        with open(ruta, encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                salida.append(dict(
                    titulo=(r.get("Title") or "").strip(),
                    tipo=(r.get("Type") or "").strip().upper() or None,
                    cites=entero(r.get("Cites")),
                    anio=(r.get("Year") or "").strip() or None,
                    autores=r.get("Authors") or None,
                    origen=os.path.basename(ruta), via="csv exportado",
                    consulta=None, cites_url=r.get("CitesURL") or None))
    return salida


def identidad(f):
    """Identificador estable del registro de Scholar.

    `cites_url` trae el id del cluster (`?cites=6913937926432472332`), que no
    cambia aunque el conteo suba entre capturas. Deduplicar por (titulo, citas)
    no bastaba: el libro de Hertel llego por CSV en agosto con 5,742 y por
    consulta guardada hoy con 5,749, y al ser cifras distintas se colaban las
    dos filas y la suma lo contaba dos veces.
    """
    m = re.search(r"[?&]cites=(\d+)", f["cites_url"] or "")
    return m.group(1) if m else "t:" + re.sub(r"\W+", " ", f["titulo"].lower()).strip()


def deduplica(filas):
    """Una fila por registro de Scholar, quedandose con la captura mas alta."""
    mejor, duplicadas = {}, 0
    for f in filas:
        k = identidad(f)
        previa = mejor.get(k)
        if previa is None:
            mejor[k] = f
            continue
        duplicadas += 1
        if (f["cites"] or 0) > (previa["cites"] or 0):
            mejor[k] = f
    return list(mejor.values()), duplicadas


def mediana(xs):
    if not xs:
        return None
    ys = sorted(xs)
    n = len(ys)
    return ys[n // 2] if n % 2 else round((ys[n // 2 - 1] + ys[n // 2]) / 2, 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde-macpro", action="store_true",
                    help="copia las consultas guardadas de la MacPro antes de procesar")
    ap.add_argument("--json", action="store_true", help="vuelca el JSON a stdout")
    args = ap.parse_args()

    if args.desde_macpro:
        traer_de_macpro()

    denominadores()
    crudas = filas_de_json() + filas_de_csv()
    filas, duplicadas = deduplica(crudas)

    descartadas, por_obra, sin_clasificar = [], {}, []
    for f in filas:
        # Emparejar PRIMERO, decidir despues. Un registro CITATION no es basura por
        # definicion: cuando Scholar no tiene el documento indexado --documentacion
        # de Purdue sin DOI ni PDF-- el cluster de referencias es el unico registro
        # de la obra, y su conteo es el bueno. Lo que no sirve es un fragmento
        # suelto de dos o tres citas. Descartar por tipo tiraba el volumen GTAP 5
        # (1,618 citas) y los tres volumenes del Bloque B.
        for obra in OBRAS:
            if not re.search(obra["gs"], f["titulo"], re.I):
                continue
            if obra.get("excluir") and re.search(obra["excluir"], f["titulo"], re.I):
                continue
            # el anio separa obras distintas que comparten titulo (la revision de
            # GTAP-E de 2007) y registros arrastrados de otra obra (el volumen 5
            # aparece en la busqueda del 6). Las filas sin anio se admiten.
            anio = entero(f["anio"])
            if obra.get("anios") and anio and anio not in obra["anios"]:
                continue
            por_obra.setdefault(obra["clave"], []).append(f)
            break
        else:
            if f["tipo"] == TIPO_FANTASMA:
                descartadas.append(dict(f, motivo="ficha CITATION que no corresponde "
                                                  "a ninguna obra de la tabla"))
            else:
                sin_clasificar.append(f)

    resultados, razones, razones_sin_libro, huecos = [], [], [], []
    for obra in OBRAS:
        regs = por_obra.get(obra["clave"], [])
        validos = [r for r in regs if r["cites"] is not None]
        indexados = [r for r in validos if r["tipo"] != TIPO_FANTASMA]
        clusters = [r for r in validos if r["tipo"] == TIPO_FANTASMA]

        # El numero de cabecera es el del registro indexado si existe; si Scholar
        # solo tiene clusters de referencias, el mayor de esos. Se anota de cual.
        if indexados:
            mayor, origen = max(r["cites"] for r in indexados), "registro indexado"
        elif clusters:
            mayor, origen = (max(r["cites"] for r in clusters),
                             "cluster CITATION: Scholar no tiene el documento indexado")
        else:
            mayor, origen = None, None

        # La suma no duplica: cada cluster cuenta documentos citantes distintos,
        # y un citante cae en un solo cluster segun como escribio la referencia.
        suma = sum(r["cites"] for r in validos) if validos else None

        fila = dict(obra=obra["clave"], titulo=obra["titulo"],
                    openalex=obra["openalex"],
                    openalex_registros=obra["openalex_registros"],
                    openalex_ids=obra["openalex_ids"],
                    scholar_mayor=mayor, scholar_suma=suma,
                    scholar_origen=origen,
                    scholar_registros_indexados=len(indexados),
                    scholar_clusters_citation=len(clusters),
                    scholar_filas=len(regs), capturada=bool(regs),
                    es_libro=bool(obra.get("libro")), registros=regs)

        if obra.get("hueco"):
            fila["razon_scholar_sobre_openalex"] = None
            fila["nota_hueco"] = ("OpenAlex no indexa esta obra. Sin denominador no hay "
                                  "razon: el valor de Scholar mide el tamano del hueco "
                                  "de indexacion en terminos absolutos.")
            if mayor:
                huecos.append(mayor)
        elif mayor and obra["openalex"]:
            razon = round(mayor / obra["openalex"], 2)
            fila["razon_scholar_sobre_openalex"] = razon
            if suma and suma != mayor:
                fila["razon_sobre_suma_fusionada"] = round(suma / obra["openalex"], 2)
            if obra.get("openalex_con_capitulo"):
                fila["openalex_con_capitulo"] = obra["openalex_con_capitulo"]
                fila["razon_alterna_con_capitulo"] = round(
                    mayor / obra["openalex_con_capitulo"], 2)
            if obra.get("excluir_de_razon"):
                fila["excluida_de_la_mediana"] = True
            else:
                razones.append(razon)
                if not obra.get("libro"):
                    razones_sin_libro.append(razon)
            if mayor < MINIMO_PLAUSIBLE and not obra.get("excluir_de_razon"):
                fila["revisar"] = "solo %d citas en Scholar: revisar la consulta a mano" % mayor
        if obra.get("nota"):
            fila["advertencia"] = obra["nota"]
        resultados.append(fila)

    pendientes = [o["clave"] for o in OBRAS
                  if not por_obra.get(o["clave"]) and not o.get("hueco")]
    pendientes_hueco = [o["clave"] for o in OBRAS
                        if not por_obra.get(o["clave"]) and o.get("hueco")]

    resumen = dict(
        obras_con_razon=len(razones),
        obras_pendientes=len(pendientes),
        pendientes=pendientes,
        huecos_pendientes=pendientes_hueco,
        filas_duplicadas_entre_vias=duplicadas,
    )
    if razones:
        resumen.update(razon_mediana=mediana(razones),
                       razon_minima=min(razones), razon_maxima=max(razones))
    if razones_sin_libro:
        resumen.update(razon_mediana_sin_libros=mediana(razones_sin_libro),
                       obras_sin_libro=len(razones_sin_libro))
    if huecos:
        resumen["citas_scholar_en_los_huecos"] = sum(huecos)
    if len(razones) < 3:
        resumen["advertencia"] = (
            "Con menos de tres obras medidas la mediana no significa nada. El factor "
            "de cobertura sigue SIN verificar: lo que hay es un dato suelto, no una "
            "distribucion. Ver 08_protocolo_scholar.md.")
    resumen["factor_deducido_a_verificar"] = 5.0

    salida = dict(
        fecha_proceso=time.strftime("%Y-%m-%d"),
        fuentes=dict(consultas_guardadas=len(glob.glob(os.path.join(CRUDOS, "*.json"))),
                     csv_exportados=len(glob.glob(os.path.join(CSVS, "*.csv"))),
                     filas_leidas=len(crudas), filas_unicas=len(filas)),
        denominadores="derivados de resultados_openalex.json, fusionando los registros "
                      "que OpenAlex parte en dos",
        resumen=resumen, por_obra=resultados,
        descartadas_por_tipo_citation=descartadas, sin_clasificar=sin_clasificar)

    with open(SALIDA_JSON, "w", encoding="utf-8") as fh:
        json.dump(salida, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    if args.json:
        json.dump(salida, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")

    campos = ["obra", "openalex_ids", "openalex_registros", "openalex_citas",
              "scholar_citas", "razon_scholar_openalex", "nota"]
    with open(SALIDA_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        for f in resultados:
            w.writerow({
                "obra": f["titulo"],
                "openalex_ids": " + ".join(f["openalex_ids"]),
                "openalex_registros": f["openalex_registros"],
                "openalex_citas": "" if f["openalex"] is None else f["openalex"],
                "scholar_citas": "" if f["scholar_mayor"] is None else f["scholar_mayor"],
                "razon_scholar_openalex": (
                    "no calculable (OpenAlex no lo indexa)" if f.get("nota_hueco")
                    else f.get("razon_scholar_sobre_openalex", "")),
                "nota": f.get("nota_hueco") or f.get("advertencia") or
                        ("" if f["capturada"] else "pendiente de captura")})

    e = sys.stderr
    e.write("filas %d (unicas %d) | obras con razon %d | pendientes %d | "
            "CITATION descartadas %d | sin clasificar %d\n"
            % (len(crudas), len(filas), len(razones), len(pendientes),
               len(descartadas), len(sin_clasificar)))
    e.write("%-52s %9s %9s %7s\n" % ("obra", "OpenAlex", "Scholar", "razon"))
    e.write("-" * 82 + "\n")
    for f in resultados:
        e.write("%-52s %9s %9s %7s\n" % (
            f["titulo"][:52],
            "-" if f["openalex"] is None else "{:,}".format(f["openalex"]),
            "-" if f["scholar_mayor"] is None else "{:,}".format(f["scholar_mayor"]),
            f.get("razon_scholar_sobre_openalex") or "-"))
    e.write("-" * 82 + "\n")
    if razones:
        e.write("razon Scholar/OpenAlex sobre %d obras: mediana %s, rango %s-%s\n"
                % (len(razones), mediana(razones), min(razones), max(razones)))
        if razones_sin_libro:
            e.write("  sin libros (%d obras): mediana %s\n"
                    % (len(razones_sin_libro), mediana(razones_sin_libro)))
        e.write("  el 5.00x que se deducia por residuo queda refutado; ver\n"
                "  07_reconciliacion_2017.py y 08_protocolo_scholar.md\n")
    else:
        e.write("todavia no hay ninguna razon calculable\n")
    if huecos:
        e.write("huecos de indexacion (Bloque B): %s citas en Scholar, sin denominador\n"
                % "{:,}".format(sum(huecos)))
    e.write("\n%s\n%s\n" % (SALIDA_JSON, SALIDA_CSV))


if __name__ == "__main__":
    main()
