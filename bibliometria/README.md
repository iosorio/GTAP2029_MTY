# Conteo bibliométrico de GTAP

**Última medición:** 30 de agosto de 2026
**Host de ejecución:** MacPro (`Israels-Mac-Pro.local`)
**Fuente principal:** API de OpenAlex, sin llave y sin dependencias externas

## La cifra

> **5,878 trabajos académicos distintos citan la producción del Global Trade
> Analysis Project**, procedentes de **129 países**.
> De ellos, **24 tienen afiliación institucional mexicana** — el **0.41%**.

Esa es la cifra de cabecera y la que sostienen todos los entregables.

**Es un piso, y se declara como piso.** Las razones están en *Limitaciones*.

## Por qué el dato mexicano aguanta

El argumento no descansa en el tamaño del conteo sino en su estabilidad. Al
ampliar el universo semilla de 14 obras a 323 —más del doble de trabajos
citantes— la participación mexicana no se movió:

| Universo semilla | Trabajos citantes | México | % | Brasil | % |
|---|---:|---:|---:|---:|---:|
| 14 obras canónicas (25-ago) | 3,947 | 14 | 0.35% | 74 | 1.87% |
| 323 obras del corpus (30-ago) | 5,878 | 24 | 0.41% | 110 | 1.87% |

Casi se duplica el universo y el 0.4% no se mueve. El orden regional tampoco:
Brasil 110 · Argentina 35 · Chile 33 · **México 24** · Colombia 23. México
sigue cuarto en América Latina, con Colombia a un trabajo de distancia.

Esa robustez frente al cambio de definición —y no la magnitud— es lo que hace
defendible la frase de la ficha.

## Dos rutas, dos preguntas

**Ruta A estricta — 14 obras canónicas.** 3,947 trabajos citantes, 111 países,
4,864 citas. Sigue siendo válida y se conserva como **piso conservador
declarado**: mide quién construye sobre las obras metodológicas centrales.

**Universo ampliado — 323 obras.** La semilla ya no son 14 obras sueltas sino
las cuatro series propias de GTAP que OpenAlex indexa como fuentes, más las
obras canónicas que viven fuera de ellas. Es la unidad que GTAP usa cuando habla
de sí mismo.

| Serie | Obras | Citas |
|---|---:|---:|
| GTAP Working Paper Series | 98 | 1,629 |
| GTAP Technical Paper Series | 37 | 1,172 |
| GTAP Research Memoranda Series | 39 | 541 |
| Journal of Global Economic Analysis | 143 | 2,619 |
| Canónicas fuera de serie | 6 | 2,864 |
| **Semilla completa** | **323** | **8,825** |

Las dos rutas no se promedian ni se suman: responden preguntas distintas.

## Tres cantidades que no son la misma

La confusión entre ellas es la fuente de casi todos los errores en este terreno.

| Cantidad | Ampliado | Estricto | Qué es |
|---|---:|---:|---|
| Trabajos citantes distintos | **5,878** | 3,947 | Documentos. Base de los porcentajes por país. |
| Citas a la semilla | **8,825** | 4,864 | Eventos de citación, con traslape. Lo único comparable con el «24,400+» de Scholar. |
| Traslape absorbido | 2,947 | 917 | Trabajos que citan más de una obra de la semilla. |

Una cuarta cantidad circuló en borradores previos y **no pertenece aquí**: las
41,527 citas recibidas *por* la literatura citante, de un conteo en Semantic
Scholar. Es el impacto de quienes usan GTAP, no las citas a GTAP.

La suma por país excede la unión porque un trabajo con coautores de varios
países cuenta en cada uno. **Los porcentajes se calculan sobre la unión.**

## La brecha frente al «24,400+» de 2017

El boletín de GTAP de 2017 reporta «24,400+ citations attributed to GTAP
research globally», medido en Google Scholar. `07_reconciliacion_2017.py`
reconstruye el acervo tal como estaba en 2017 y descompone la brecha:

| | |
|---|---:|
| Ruta A a 2017 | 2,818 citas |
| Semilla ampliada a 2017 | 4,879 citas |
| Factor de universo semilla | **1.73x** ← medido |
| Factor de cobertura implícito | **5.00x** ← deducido por residuo |
| Brecha total | **8.66x** → 2,818 × 8.66 ≈ 24,400 |

**El 1.73x está medido sobre OpenAlex. El 5.00x no:** es lo que Scholar tendría
que estar contando de más para que el 24,400 cuadre. Verificarlo es la Ruta B, y
es lo único que sigue abierto.

## Cobertura entre bases (`06_cobertura_fuentes.py`)

Sobre pares completos, nunca sobre sumas de columnas que cubren distinto número
de obras:

| Par | Obras comparables | Razón |
|---|---:|---:|
| OpenAlex / Crossref | 10 | 1.85x |
| OpenAlex / Semantic Scholar | 7 | 0.80 |

OpenAlex es más ancho que Crossref y algo más angosto que Semantic Scholar.
Las tres son índices académicos con emparejamiento de referencias: su dispersión
acota el componente de **emparejamiento**, no el de literatura gris que Scholar
indexa y ellas no.

## Ruta B — abierta, 1 de 11

Verifica el 5.00x deducido midiendo la razón Scholar/OpenAlex obra por obra, con
Publish or Perish operado a mano. **El protocolo completo, con la hoja de
captura y las trampas del método, está en [`08_protocolo_scholar.md`](08_protocolo_scholar.md).**

Lo único medido hasta hoy: *Global Trade Analysis: Modeling and Applications*
(Hertel, 1997) — OpenAlex 895, Scholar 5,742, razón **6.42x**, o **4.97x** si se
compara contra libro + capítulo. Bordea el 5.00x por arriba, pero **una obra no
es una distribución**: cuando estén las diez se reporta mediana y rango, no
promedio.

Restricción vigente: **Publish or Perish sí, scrapers de Google Scholar no.**
`scholar.google.com/robots.txt` prohíbe el rastreo automatizado; la herramienta
es aceptable porque la opera una persona de forma interactiva.

## Cómo reproducirlo

```bash
python3 01_resolver_ids.py > candidatos.txt     # resuelve IDs y lista candidatos
python3 02_conteo_openalex.py > resultados_openalex.json
python3 03_ensamblar_entregable.py resultados_openalex.json 2026-08-25 > resultados_bibliometria_gtap.json
python3 04_verificar.py                         # pruebas de consistencia

python3 05_universo_ampliado.py   > resultados_universo_ampliado.json  # la cifra de cabecera
python3 06_cobertura_fuentes.py   > resultados_cobertura.json         # OpenAlex/Crossref/S2
python3 07_reconciliacion_2017.py > resultados_reconciliacion.json    # la brecha de 2017
python3 09_procesar_pop.py                                            # Ruta B: Scholar/OpenAlex
```

Solo biblioteca estándar de Python 3. Sin llave de API: OpenAlex es abierto y el
parámetro `mailto` únicamente da entrada al pool cortés.

`09_procesar_pop.py` es el único que escribe sus archivos por su cuenta; los
demás vuelcan JSON a stdout. Lee **las dos vías** en que puede llegar la captura de
Publish or Perish —las consultas guardadas de `Results6/` y los CSV exportados a
mano— y deduplica entre ellas. Sus denominadores de OpenAlex se **derivan** de
`resultados_openalex.json`, fusionando los registros que OpenAlex parte en dos;
no se escriben a mano.

## Verificación

`04_verificar.py` corre tres pruebas:

1. `cites:<id>` contra el `cited_by_count` de la misma obra — coinciden con
   diferencias de 1 a 4 unidades (<1%), el desfase conocido de OpenAlex entre el
   índice en vivo y el campo cacheado.
2. La unión de dos obras queda acotada entre el máximo individual y la suma.
3. La unión total es menor que la suma con traslape, y el conteo es estable
   entre corridas.

## Limitaciones (por qué la cifra es un piso)

- **OpenAlex no indexa los volúmenes GTAP 6, 7 y 8** como obras, solo capítulos
  sueltos que casi no se citan. Son los de mayor uso entre 2006 y 2016 y sus
  citas no están en la unión. El volumen GTAP 5 sí está indexado (1,122 citas) y
  se incluyó. Dimensionar ese hueco es el Bloque B de `08_protocolo_scholar.md`.
- **Referencias no resueltas.** OpenAlex descarta las referencias que no logra
  emparejar con una obra de su índice.
- **Afiliación institucional incompleta.** El desglose por país solo cubre los
  trabajos cuya afiliación OpenAlex resuelve: 4,571 de 5,878. Los cortes
  regionales también son un piso.
- **Cobertura frente a Google Scholar.** Scholar indexa tesis, working papers,
  informes de organismos y literatura gris que OpenAlex no cubre. Por eso la
  Ruta B mide más alto: mide otra cosa, con otra cobertura. Las dos cifras se
  reportan por separado con su fuente.
- **Presupuesto de las APIs.** OpenAlex tiene cuota diaria por IP que se
  reinicia a medianoche UTC. Semantic Scholar limita la tasa y devuelve 429 con
  descargas grandes.

## Estructura de la literatura citante

Ritmo reciente: entre 230 y 340 trabajos citantes por año en la última década
(2015–2025), sin señal de agotamiento. Los países con más presencia son Estados
Unidos 1,733 · China 551 · Alemania 550 · Australia 446 · Reino Unido 441.

## Entregables que dependen de este conteo

- `../Nota_Bibliometrica_GTAP.md` — nota de respaldo con el método completo
- `../GTAP_Bibliometric_Note_EN.md` — versión en inglés
- `../Ficha_GTAP2029_Monterrey.md` y su PDF
- `../sitio/bibliometria.html` — publicado en <https://iosorio.github.io/GTAP2029_MTY/>
