#!/usr/bin/env python3
"""
Cobertura comparada por obra: OpenAlex vs Crossref vs Semantic Scholar.

Objetivo: acotar cuanto de la brecha entre el conteo propio y el "24,400+"
del boletin de GTAP de 2017 se debe a COBERTURA DEL INDICE y no al universo
semilla.

Que mide y que NO mide
----------------------
Estas tres fuentes son indices academicos que emparejan referencias contra un
catalogo. Su dispersion mide el componente de EMPAREJAMIENTO: cuantas citas
pierde un indice porque no logra resolver la referencia. NO mide el componente
de LITERATURA GRIS -- tesis, working papers, informes de organismos y versiones
duplicadas que Google Scholar indexa y estas tres no. Ese segundo componente
solo lo mide Google Scholar, y solo con Publish or Perish operado a mano
(ver 08_protocolo_scholar.md).

Por eso el resultado de este script es un PISO del factor de cobertura, no el
factor completo.

Uso:  python3 06_cobertura_fuentes.py > resultados_cobertura.json
"""
import os
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# Contacto para el "polite pool" de OpenAlex y Crossref. Las APIs son abiertas
# y no piden llave; el correo solo da prioridad de cola. Se toma del entorno
# para no publicarlo:  export OPENALEX_MAILTO="tu-correo@institucion.edu"
MAILTO = os.environ.get("OPENALEX_MAILTO", "gtap-bibliometria@example.org")

OBRAS = [
    ("W1485558032", "Global Trade Analysis: Modeling and Applications", 1997),
    ("W2497463976", "Structure of GTAP", 1997),
    ("W2413227257", "An Overview of the GTAP 9 Data Base", 2016),
    ("W2955545697", "The GTAP Data Base: Version 10", 2019),
    ("W2633769093", "The Standard GTAP Model, Version 7", 2017),
    ("W4242531241", "The Standard GTAP Model: Version 7 (duplicado)", 2017),
    ("W4320021891", "The GTAP Data Base: Version 11", 2022),
    ("W7117369847", "The GTAP Data Base: Version 12", 2025),
    ("W2141229371", "GTAP-E: An Energy-Environmental Version", 2002),
    ("W3123830708", "GTAP-E (duplicado, Technical Paper 16)", 2002),
    ("W1574368972", "Dynamic Modeling and Applications", 2012),
    ("W3121700781", "GTAP-AGR", 2005),
    ("W1525723848", "GTAP-AGR (duplicado)", 2005),
    ("W2403987006", "GTAP 5 Data Base", 2002),
]


def get(url, headers=None, reintentos=4, espera_inicial=3.0):
    espera = espera_inicial
    for intento in range(reintentos):
        try:
            req = urllib.request.Request(
                url, headers=headers or {"User-Agent": "gtap-bibliometria (%s)" % MAILTO})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and intento < reintentos - 1:
                sys.stderr.write("    HTTP %s, espero %.0fs\n" % (e.code, espera))
                time.sleep(espera)
                espera *= 2
                continue
            return None
        except Exception:
            return None
    return None


def openalex(wid):
    d = get("https://api.openalex.org/works/%s?mailto=%s&select=id,display_name,"
            "doi,publication_year,cited_by_count,type" % (wid, MAILTO))
    if not d:
        return None
    doi = (d.get("doi") or "").replace("https://doi.org/", "") or None
    return dict(citas=d["cited_by_count"], doi=doi, titulo=d["display_name"],
                anio=d["publication_year"], tipo=d["type"])


def crossref(doi):
    if not doi:
        return None
    d = get("https://api.crossref.org/works/%s?mailto=%s"
            % (urllib.parse.quote(doi, safe=""), MAILTO))
    if not d or d.get("status") != "ok":
        return None
    return d["message"].get("is-referenced-by-count")


def semantic_scholar(doi, titulo):
    if doi:
        d = get("https://api.semanticscholar.org/graph/v1/paper/DOI:%s?fields=citationCount"
                % urllib.parse.quote(doi, safe=""))
        if d and "citationCount" in d:
            return d["citationCount"]
    d = get("https://api.semanticscholar.org/graph/v1/paper/search?query=%s&limit=1"
            "&fields=citationCount,title" % urllib.parse.quote(titulo))
    if d and d.get("data"):
        return d["data"][0].get("citationCount")
    return None


def main():
    filas = []
    for wid, etiqueta, anio in OBRAS:
        sys.stderr.write("%s ...\n" % etiqueta[:55])
        oa = openalex(wid)
        if not oa:
            sys.stderr.write("  sin registro en OpenAlex\n")
            continue
        time.sleep(0.3)
        cr = crossref(oa["doi"])
        time.sleep(0.3)
        s2 = semantic_scholar(oa["doi"], oa["titulo"])
        time.sleep(3.0)          # Semantic Scholar limita la tasa

        fila = dict(etiqueta=etiqueta, openalex_id=wid, doi=oa["doi"],
                    anio=oa["anio"], tipo=oa["tipo"],
                    openalex=oa["citas"], crossref=cr, semantic_scholar=s2)
        for nombre, v in (("crossref", cr), ("semantic_scholar", s2)):
            fila["razon_openalex_sobre_%s" % nombre] = (
                round(oa["citas"] / v, 2) if v else None)
        filas.append(fila)
        sys.stderr.write("  OA %-6s CR %-6s S2 %-6s\n"
                         % (oa["citas"], cr, s2))

    def suma(k, solo_con=None):
        """Suma la columna k. Si solo_con se indica, restringe a las obras que
        tienen dato en AMBAS columnas: comparar la suma completa de OpenAlex
        contra una suma parcial de otra fuente infla la razon artificialmente."""
        return sum(f[k] for f in filas
                   if isinstance(f.get(k), int)
                   and (solo_con is None or isinstance(f.get(solo_con), int)))

    tot = dict(openalex=suma("openalex"), crossref=suma("crossref"),
               semantic_scholar=suma("semantic_scholar"))

    # Razones sobre pares completos, con el numero de obras que las sostiene.
    pares = {}
    for fuente in ("crossref", "semantic_scholar"):
        oa = suma("openalex", solo_con=fuente)
        ot = suma(fuente, solo_con="openalex")
        n = sum(1 for f in filas if isinstance(f.get(fuente), int)
                and isinstance(f.get("openalex"), int))
        pares[fuente] = dict(obras_comparables=n, openalex=oa, fuente=ot,
                             razon_openalex_sobre_fuente=(round(oa / ot, 2)
                                                          if ot else None))

    salida = dict(
        fecha_consulta=time.strftime("%Y-%m-%d"),
        advertencia=(
            "Estas tres fuentes son indices academicos con emparejamiento de "
            "referencias. Su dispersion acota el componente de emparejamiento de "
            "la brecha, NO el componente de literatura gris que Google Scholar "
            "indexa y ellas no. El factor de cobertura que sale de aqui es un "
            "piso del factor real frente a Scholar."),
        por_obra=filas,
        totales_columna_completa=dict(
            valores=tot,
            advertencia=("estas sumas cubren distinto numero de obras en cada "
                         "columna y NO deben dividirse entre si; usar "
                         "razones_sobre_pares_completos"),
        ),
        razones_sobre_pares_completos=pares,
    )
    json.dump(salida, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
