#!/usr/bin/env python3
"""
Universo semilla ampliado de GTAP en OpenAlex.

El conteo de la Ruta A (02_conteo_openalex.py) parte de 14 obras metodologicas.
La cifra de 2017 del boletin de GTAP -- "24,400+ citations attributed to GTAP
research globally" -- no se refiere a esas 14 obras sino al corpus completo de
publicaciones del proyecto. Este script mide ese corpus.

Semilla ampliada = las cuatro series que OpenAlex indexa como fuentes propias
del proyecto (GTAP Working Papers, GTAP Technical Papers, GTAP Research
Memoranda y el Journal of Global Economic Analysis) mas las obras canonicas de
la Ruta A que viven fuera de esas series (libros y volumenes de base de datos).

Produce tres cantidades, que NO deben confundirse entre si:

  A) CITAS a la semilla (eventos de citacion, con traslape entre obras).
     Es la unica comparable con el "24,400+" de Scholar.
  B) TRABAJOS DISTINTOS que citan a la semilla (union deduplicada).
     Es la cantidad sobre la que se calculan los porcentajes por pais.
  C) Desglose por pais de (B), calculado sobre la union, no sobre la suma.

Uso:  python3 05_universo_ampliado.py > resultados_universo_ampliado.json
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
BASE = "https://api.openalex.org"

# Series que OpenAlex indexa como fuentes propias del proyecto GTAP.
SERIES = [
    ("S4393920178", "GTAP Working Paper Series"),
    ("S4393920177", "GTAP Technical Paper Series"),
    ("S4393920179", "GTAP Research Memoranda Series"),
    ("S4210214325", "Journal of Global Economic Analysis"),
]

# Obras canonicas de la Ruta A. Las que viven fuera de las series de arriba
# (libros y volumenes de base de datos) se agregan a la semilla; las que ya
# pertenecen a una serie entran por la serie y aqui solo sirven de control.
CANONICAS = [
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

LOTE_OR = 50          # valores por filtro OR; 50 es conservador
PAUSA = 0.15          # cortesia entre peticiones


def get(url, reintentos=5):
    """GET con reintento exponencial ante 429/5xx."""
    espera = 2.0
    for intento in range(reintentos):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "gtap-bibliometria (%s)" % MAILTO})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and intento < reintentos - 1:
                sys.stderr.write("  HTTP %s, reintento en %.0fs\n" % (e.code, espera))
                time.sleep(espera)
                espera *= 2
                continue
            raise
    raise RuntimeError("agotados los reintentos")


def paginar(filtro, select, etiqueta):
    """Recorre un filtro completo con cursor. Devuelve la lista de registros."""
    out, cursor, pag = [], "*", 0
    while cursor:
        url = "%s/works?%s" % (BASE, urllib.parse.urlencode(
            dict(filter=filtro, select=select, per_page=200,
                 cursor=cursor, mailto=MAILTO)))
        d = get(url)
        out.extend(d["results"])
        cursor = d["meta"].get("next_cursor")
        pag += 1
        if pag % 10 == 0:
            sys.stderr.write("    %s: %d registros\n" % (etiqueta, len(out)))
        if not d["results"]:
            break
        time.sleep(PAUSA)
    return out


def main():
    sys.stderr.write("== 1. Semilla: series propias de GTAP ==\n")
    semilla = {}          # id -> dict(titulo, anio, citas, serie)
    por_serie = {}
    for sid, nombre in SERIES:
        regs = paginar("primary_location.source.id:%s" % sid,
                       "id,display_name,publication_year,cited_by_count", nombre)
        citas = sum(r["cited_by_count"] for r in regs)
        por_serie[nombre] = dict(obras=len(regs), citas=citas, source_id=sid)
        for r in regs:
            wid = r["id"].rsplit("/", 1)[-1]
            semilla[wid] = dict(titulo=r["display_name"],
                                anio=r["publication_year"],
                                citas=r["cited_by_count"], origen=nombre)
        sys.stderr.write("  %-42s %3d obras, %5d citas\n" % (nombre, len(regs), citas))

    sys.stderr.write("== 2. Semilla: obras canonicas fuera de serie ==\n")
    canon_fuera = []
    for wid, titulo, anio in CANONICAS:
        if wid in semilla:
            continue
        d = get("%s/works/%s?mailto=%s&select=id,display_name,publication_year,"
                "cited_by_count,type" % (BASE, wid, MAILTO))
        semilla[wid] = dict(titulo=d["display_name"], anio=d["publication_year"],
                            citas=d["cited_by_count"], origen="obra canonica")
        canon_fuera.append(dict(id=wid, titulo=d["display_name"],
                                anio=d["publication_year"],
                                citas=d["cited_by_count"], tipo=d["type"]))
        sys.stderr.write("  + %-52s %5d citas\n" % (d["display_name"][:52],
                                                    d["cited_by_count"]))
        time.sleep(PAUSA)

    ids = sorted(semilla)
    suma_citas = sum(v["citas"] for v in semilla.values())
    sys.stderr.write("  SEMILLA: %d obras, %d citas sumadas (con traslape)\n"
                     % (len(ids), suma_citas))

    sys.stderr.write("== 3. Union de trabajos citantes ==\n")
    union = {}            # id citante -> set de paises
    anios = {}
    for i in range(0, len(ids), LOTE_OR):
        lote = ids[i:i + LOTE_OR]
        regs = paginar("cites:%s" % "|".join(lote),
                       "id,authorships,publication_year",
                       "lote %d/%d" % (i // LOTE_OR + 1,
                                       (len(ids) + LOTE_OR - 1) // LOTE_OR))
        for r in regs:
            wid = r["id"].rsplit("/", 1)[-1]
            if wid not in union:
                paises = set()
                for a in r.get("authorships") or []:
                    for c in a.get("countries") or []:
                        paises.add(c)
                union[wid] = paises
                anios[wid] = r.get("publication_year")
        sys.stderr.write("  lote %d: union acumulada = %d\n"
                         % (i // LOTE_OR + 1, len(union)))

    n_union = len(union)

    sys.stderr.write("== 4. Desglose por pais ==\n")
    por_pais = {}
    con_afiliacion = 0
    for wid, paises in union.items():
        if paises:
            con_afiliacion += 1
        for c in paises:
            por_pais[c] = por_pais.get(c, 0) + 1
    por_pais = dict(sorted(por_pais.items(), key=lambda kv: -kv[1]))

    serie_anual = {}
    for wid, a in anios.items():
        if a:
            serie_anual[a] = serie_anual.get(a, 0) + 1
    serie_anual = dict(sorted(serie_anual.items()))

    salida = dict(
        fecha_consulta=time.strftime("%Y-%m-%d"),
        fuente="OpenAlex",
        metodo=dict(
            semilla="4 series propias de GTAP indexadas por OpenAlex "
                    "(Working Papers, Technical Papers, Research Memoranda, JGEA) "
                    "mas las obras canonicas que viven fuera de esas series",
            union="filtro cites: en lotes de %d, IDs citantes deduplicados "
                  "del lado cliente" % LOTE_OR,
            advertencia_unidades=(
                "citas_a_la_semilla son eventos de citacion (comparable con el "
                "'24,400+' de Google Scholar); trabajos_citantes_distintos es la "
                "union deduplicada (base de los porcentajes por pais). No son la "
                "misma cantidad y no deben intercambiarse."),
        ),
        semilla=dict(
            obras_totales=len(ids),
            citas_a_la_semilla=suma_citas,
            por_serie=por_serie,
            canonicas_fuera_de_serie=canon_fuera,
        ),
        citantes=dict(
            trabajos_citantes_distintos=n_union,
            traslape_absorbido=suma_citas - n_union,
            con_afiliacion_resuelta=con_afiliacion,
            paises_representados=len(por_pais),
            por_pais=por_pais,
            serie_anual=serie_anual,
        ),
    )
    json.dump(salida, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    sys.stderr.write("\nLISTO: semilla %d obras | %d citas | union %d trabajos | %d paises\n"
                     % (len(ids), suma_citas, n_union, len(por_pais)))


if __name__ == "__main__":
    main()
