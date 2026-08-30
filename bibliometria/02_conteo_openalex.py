#!/usr/bin/env python3
"""
Conteo bibliometrico de GTAP en OpenAlex.

Mide cuantos TRABAJOS DISTINTOS citan al menos una de las obras canonicas
del Global Trade Analysis Project. Usa el filtro `cites:` de OpenAlex con
OR (barra vertical), de modo que la union se calcula del lado del servidor
y no hay doble conteo.

Los IDs de OpenAlex fueron resueltos y verificados manualmente por titulo,
autor y anio a partir de 01_resolver_ids.py. Estan fijados aqui para que la
corrida sea reproducible: un tercero que ejecute este script debe obtener
exactamente las mismas cifras (salvo crecimiento natural del indice).

Uso:  python3 02_conteo_openalex.py > resultados_openalex.json
"""
import json
import sys
import time
import urllib.parse
import urllib.request

MAILTO = "osorio.israel@gmail.com"
BASE = "https://api.openalex.org/works"

# ---------------------------------------------------------------------------
# Obras canonicas verificadas.
#   incluir_en:  "estricto" = obra listada en la mision, registro principal
#                "duplicado" = mismo trabajo, segundo registro en OpenAlex
#                "extendido" = obra canonica adicional no listada en la mision
# ---------------------------------------------------------------------------
OBRAS = [
    dict(etiqueta="hertel1997", openalex_id="W1485558032",
         titulo="Global Trade Analysis: Modeling and Applications",
         autor="Hertel, T. (ed.)", anio=1997, incluir_en="estricto"),
    dict(etiqueta="structure", openalex_id="W2497463976",
         titulo="Structure of GTAP",
         autor="Hertel, T. & Tsigas, M.", anio=1997, incluir_en="estricto",
         nota="OpenAlex fecha el capitulo en 1996; es el cap. 2 del libro de 1997"),
    dict(etiqueta="gtap9", openalex_id="W2413227257",
         titulo="An Overview of the GTAP 9 Data Base",
         autor="Aguiar, A. et al.", anio=2016, incluir_en="estricto"),
    dict(etiqueta="gtap10", openalex_id="W2955545697",
         titulo="The GTAP Data Base: Version 10",
         autor="Aguiar, A. et al.", anio=2019, incluir_en="estricto"),
    dict(etiqueta="standard7", openalex_id="W2633769093",
         titulo="The Standard GTAP Model, Version 7",
         autor="Corong, E. et al.", anio=2017, incluir_en="estricto"),
    dict(etiqueta="standard7_dup", openalex_id="W4242531241",
         titulo="The Standard GTAP Model: Version 7 (registro duplicado)",
         autor="Corong, E.", anio=2017, incluir_en="duplicado"),
    dict(etiqueta="gtap11", openalex_id="W4320021891",
         titulo="The GTAP Data Base: Version 11",
         autor="Aguiar, A. et al.", anio=2022, incluir_en="estricto"),
    dict(etiqueta="gtap12", openalex_id="W7117369847",
         titulo="The GTAP Data Base: Version 12",
         autor="Aguiar, A. et al.", anio=2025, incluir_en="estricto"),
    dict(etiqueta="gtape", openalex_id="W2141229371",
         titulo="GTAP-E: An Energy-Environmental Version of the GTAP Model",
         autor="Burniaux, J-M. & Truong, T.", anio=2002, incluir_en="estricto"),
    dict(etiqueta="gtape_dup", openalex_id="W3123830708",
         titulo="GTAP-E (registro duplicado, GTAP Technical Paper 16)",
         autor="Burniaux, J-M. & Truong, T.", anio=2002, incluir_en="duplicado"),
    dict(etiqueta="dynamic", openalex_id="W1574368972",
         titulo="Dynamic Modeling and Applications for Global Economic Analysis",
         autor="Ianchovichina, E. & Walmsley, T.", anio=2012, incluir_en="estricto"),
    dict(etiqueta="gtapagr", openalex_id="W3121700781",
         titulo="GTAP-AGR: A Framework for Assessing the Implications of "
                "Multilateral Changes in Agricultural Policies",
         autor="Keeney, R. & Hertel, T.", anio=2005, incluir_en="estricto"),
    dict(etiqueta="gtapagr_dup", openalex_id="W1525723848",
         titulo="GTAP-AGR (registro duplicado)",
         autor="Keeney, R. & Hertel, T.", anio=2005, incluir_en="duplicado"),
    dict(etiqueta="gtap5", openalex_id="W2403987006",
         titulo="Global Trade, Assistance, and Production: The GTAP 5 Data Base",
         autor="Dimaranan, B. & McDougall, R.", anio=2002, incluir_en="extendido",
         nota="No listada en la mision. Se agrega porque es el unico volumen de "
              "la serie 'Global Trade, Assistance, and Production' que OpenAlex "
              "indexa como obra; los volumenes 6, 7 y 8 no existen en el indice."),
]

# Volumenes solicitados por la mision que NO pudieron resolverse.
NO_RESUELTAS = [
    dict(titulo="Global Trade Assistance and Production: The GTAP 8 Data Base",
         autor="Narayanan, B., Aguiar, A. & McDougall, R. (eds.)", anio=2012),
    dict(titulo="Global Trade Assistance and Production: The GTAP 7 Data Base",
         autor="Narayanan, B. & Walmsley, T. (eds.)", anio=2008),
    dict(titulo="Global Trade Assistance and Production: The GTAP 6 Data Base",
         autor="Dimaranan, B. (ed.)", anio=2006),
]


def get(url, reintentos=4):
    """GET con reintento exponencial ante 429/5xx."""
    espera = 2.0
    for intento in range(reintentos):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "gtap-bibliometria (%s)" % MAILTO})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and intento < reintentos - 1:
                sys.stderr.write("  HTTP %s, reintento en %.0fs\n" % (e.code, espera))
                time.sleep(espera)
                espera *= 2
                continue
            raise
    raise RuntimeError("agotados los reintentos")


def q(**kwargs):
    kwargs["mailto"] = MAILTO
    return "%s?%s" % (BASE, urllib.parse.urlencode(kwargs))


def cited_by_count(wid):
    """Paso 4: citas que OpenAlex atribuye a la obra."""
    d = get("https://api.openalex.org/works/%s?mailto=%s&select=id,display_name,"
            "publication_year,cited_by_count,type" % (wid, MAILTO))
    return d


def contar_union(ids):
    """meta.count = trabajos distintos que citan al menos una de las obras."""
    d = get(q(filter="cites:%s" % "|".join(ids), per_page=1))
    return d["meta"]["count"]


def agrupar(ids, campo):
    """group_by de OpenAlex. Las llaves vienen como URL; se normalizan al codigo."""
    d = get(q(filter="cites:%s" % "|".join(ids), group_by=campo, per_page=200))
    out = {}
    for g in d["group_by"]:
        k = g["key"]
        if isinstance(k, str) and k.startswith("http"):
            k = k.rsplit("/", 1)[-1]
        out[str(k)] = g["count"]
    return out


# Paises de America Latina y el Caribe hispano/luso-parlante, para el corte
# regional de la ficha. Se cuenta con una sola consulta (no sumando paises),
# porque un trabajo con coautoria en dos paises se contaria dos veces.
LATAM = ["mx", "br", "ar", "cl", "co", "pe", "uy", "cr", "ec", "bo", "py",
         "ve", "gt", "pa", "do", "hn", "ni", "sv", "cu"]


def contar_filtrado(ids, filtro_extra):
    """Trabajos distintos de la union que ademas cumplen filtro_extra."""
    d = get(q(filter="cites:%s,%s" % ("|".join(ids), filtro_extra), per_page=1))
    return d["meta"]["count"]


def main():
    incidencias = []
    obras_salida = []

    sys.stderr.write("Paso 4: leyendo cited_by_count de cada obra canonica...\n")
    for o in OBRAS:
        try:
            d = cited_by_count(o["openalex_id"])
            o_out = dict(titulo=o["titulo"], anio=o["anio"], autor=o["autor"],
                         openalex_id=o["openalex_id"],
                         openalex_titulo=d.get("display_name"),
                         openalex_anio=d.get("publication_year"),
                         openalex_tipo=d.get("type"),
                         cited_by_count=d.get("cited_by_count"),
                         rol=o["incluir_en"])
            if o.get("nota"):
                o_out["nota"] = o["nota"]
            obras_salida.append(o_out)
            sys.stderr.write("  %-14s %-12s cb=%s\n" % (o["etiqueta"], o["openalex_id"],
                                                       d.get("cited_by_count")))
        except Exception as e:
            incidencias.append("No se pudo leer cited_by_count de %s (%s): %s"
                               % (o["titulo"], o["openalex_id"], e))
            sys.stderr.write("  FALLO %s: %s\n" % (o["etiqueta"], e))
        time.sleep(0.3)

    for nr in NO_RESUELTAS:
        incidencias.append(
            "OpenAlex no indexa como obra el volumen '%s' (%s, %s). Solo contiene "
            "capitulos sueltos de su documentacion, que se citan de forma marginal. "
            "Las citas a este volumen NO estan en la union; el conteo es un piso."
            % (nr["titulo"], nr["autor"], nr["anio"]))

    ids_estricto = [o["openalex_id"] for o in OBRAS if o["incluir_en"] == "estricto"]
    ids_ampliado = [o["openalex_id"] for o in OBRAS]

    sys.stderr.write("\nPaso 2: contando la union...\n")
    union_estricto = contar_union(ids_estricto)
    time.sleep(0.4)
    union_ampliado = contar_union(ids_ampliado)
    sys.stderr.write("  estricto (%d obras): %d\n" % (len(ids_estricto), union_estricto))
    sys.stderr.write("  ampliado (%d registros): %d\n" % (len(ids_ampliado), union_ampliado))

    sys.stderr.write("\nPaso 3: desgloses sobre el conjunto ampliado...\n")
    time.sleep(0.4)
    por_anio = agrupar(ids_ampliado, "publication_year")
    time.sleep(0.4)
    por_tipo = agrupar(ids_ampliado, "type")
    time.sleep(0.4)
    por_pais = agrupar(ids_ampliado, "institutions.country_code")

    sys.stderr.write("\nCortes regionales (consulta unica, sin doble conteo)...\n")
    time.sleep(0.4)
    n_mexico = contar_filtrado(ids_ampliado, "institutions.country_code:mx")
    time.sleep(0.4)
    n_latam = contar_filtrado(ids_ampliado, "institutions.country_code:%s" % "|".join(LATAM))
    sys.stderr.write("  Mexico: %s   America Latina: %s\n" % (n_mexico, n_latam))

    suma_citas = sum(o["cited_by_count"] for o in obras_salida
                     if o["cited_by_count"] is not None)

    salida = {
        "openalex": {
            "endpoint": BASE,
            "obras_canonicas": obras_salida,
            "obras_no_resueltas": NO_RESUELTAS,
            "suma_cited_by_count_con_traslape": suma_citas,
            "union_trabajos_citantes": union_ampliado,
            "union_trabajos_citantes_solo_obras_de_la_mision": union_estricto,
            "ids_union_ampliada": ids_ampliado,
            "ids_union_estricta": ids_estricto,
            "por_anio": dict(sorted((k, v) for k, v in por_anio.items() if k)),
            "por_tipo": dict(sorted(por_tipo.items(), key=lambda kv: -kv[1])),
            "por_pais": dict(sorted(por_pais.items(), key=lambda kv: -kv[1])),
            "trabajos_con_afiliacion_mexico": n_mexico,
            "trabajos_con_afiliacion_america_latina": n_latam,
            "paises_latam_incluidos": [c.upper() for c in LATAM],
        },
        "incidencias": incidencias,
    }
    print(json.dumps(salida, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
