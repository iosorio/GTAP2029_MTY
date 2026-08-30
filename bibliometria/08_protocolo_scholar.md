# Ruta B — captura en Google Scholar con Publish or Perish

Documento único del protocolo. Sustituye a `PROTOCOLO_publish_or_perish.md` y a
`consultas_publish_or_perish.txt`, ambos retirados el 30 de agosto de 2026.

**Dónde:** MacPro, `/Applications/Publish or Perish.app` v8.19.5300.9483.
**Pestaña:** Google Scholar.
**Quién opera:** una persona, a mano. Ver *La restricción*.

---

## Qué mide esta ruta y qué no

Mide **una sola cantidad**: la razón entre las citas que Google Scholar atribuye
a una obra y las que le atribuye OpenAlex, obra por obra. Ese cociente es el
**factor de cobertura**.

Hace falta porque la reconciliación con el «24,400+» de 2017
(`07_reconciliacion_2017.py`) descompone la brecha en dos factores, y solo uno
está medido:

| factor | valor | estado |
|---|---:|---|
| universo semilla | 1.73x | **medido** sobre OpenAlex |
| cobertura de Scholar | 5.00x | **deducido por residuo** ← esto es lo que se verifica aquí |
| brecha total | 8.66x | 2,818 × 8.66 ≈ 24,400 |

El 5.00x es lo que Scholar tendría que estar contando de más, por obra y a igual
fecha, para que el 24,400 cuadre. No es una medición: es lo que sobra al despejar.

**No mide, y no puede medir, un conteo de trabajos distintos.** Scholar no
permite calcular la unión de citantes de varias obras. La unión sale de OpenAlex
(`05_universo_ampliado.py`). Las dos rutas responden preguntas distintas: sus
cifras no se suman ni se promedian.

---

## Lo que sabemos y lo que no sobre por qué falló el intento previo

El 25 de agosto se corrieron dos consultas con un minuto de diferencia. Los CSV
están en `pop_csv/` y son el único experimento disponible. Decodificando el
parámetro `scioq` de la columna `RelatedURL` —que es la cadena que Scholar
recibió de verdad— resulta esto:

| | consulta efectiva | devolvió |
|---|---|---|
| `PoP001.csv` | `intitle:"global trade analysis modeling and applications"` | ✅ `BOOK`, **5,742** citas |
| `PoP002.csv` | `intitle:"the standard gtap model version 7"` | ❌ dos fichas `CITATION`, 2 citas cada una |

**Las dos usaron el campo Title, las dos entrecomilladas, las dos con `intitle:`.**
La que funcionó lo hizo con exactamente la misma forma que la que falló.

Esto descarta las dos explicaciones que circularon:

- *«la frase entrecomillada debe ir en texto libre, nunca en `intitle:`»* — no lo
  explica: PoP001 usó `intitle:` con comillas y funcionó.
- *«Scholar no resuelve una frase entrecomillada dentro de `intitle:`»* — misma
  objeción, y era la tesis de `PROTOCOLO_publish_or_perish.md`.

Lo que cambió entre una y otra **no fue el campo: fue la obra.** Scholar tiene el
libro de Hertel como registro real indexado; del artículo de JGEA solo tiene
fichas fabricadas a partir de bibliografías ajenas. Con un éxito y un fallo no
hay base para culpar a la sintaxis.

**Consecuencia para el método:** no se declara una regla de campo que no está
medida. Se prueba la vía más ancha primero, y **se anota cuál funcionó en cada
obra** — ese registro es parte del resultado, no burocracia.

---

## Las tres trampas

### 1. Los registros fantasma (`CITATION`)

Es la que arruinó el intento previo. Un registro de tipo `CITATION` es una
entrada que Scholar fabrica a partir de una referencia suelta que no logró
vincular con el documento real. No es la obra. Tiene 2 o 3 citas cuando la obra
verdadera tiene cientos.

PoP resumió la consulta fallida como `cites_total = 4`. Tomado al pie de la
letra implicaría que Scholar cuenta **menos** que OpenAlex (293) — la brecha al
revés de la realidad.

**Regla:** mira siempre la columna `Type`. Sirven `BOOK`, `ARTICLE`, `JOURNAL`,
o tipo vacío con `ArticleURL` presente. Si las únicas filas son `CITATION`, la
consulta falló aunque devuelva un número.

### 2. El total agregado no es el dato

PoP reporta `cites_total`: la suma de todas las filas devueltas, incluida la
basura. El dato es la columna **`Cites` de la fila que corresponde a la obra**,
identificada por autor y año.

### 3. Scholar consolida donde OpenAlex fragmenta

El libro de Hertel de 1997 dio 5,742 en Scholar contra 895 en OpenAlex. Parte de
esa diferencia no es cobertura: Scholar agrupa bajo el registro del libro sus
ediciones, reimpresiones y capítulos, mientras OpenAlex lista «Structure of
GTAP» (el capítulo 2) como obra aparte con 260 citas propias.

**Regla:** para el libro se anotan las dos lecturas — contra el libro solo
(6.42x) y contra libro + capítulo, 1,155 (4.97x). La razón de un libro es el
**techo** del factor de cobertura, no su valor típico. Los artículos de revista
son la medición limpia.

---

## Procedimiento

Para cada obra de la tabla, en orden:

1. **Vía primaria — texto libre.** Campo **Keywords** (o *All of the words*): la
   frase de la columna *Consulta*, **con comillas**. Campo **Title words**
   vacío. **Authors** solo donde la tabla lo indique.
2. **Max results** 200. Años en blanco.
3. Correr. **Guardar la consulta** (queda en `My searches`). El nombre no
   importa: los archivos se leen solos.
4. Validar la fila elegida con las tres pruebas de abajo.
5. Si falla, bajar por el plan de respaldo y **anotar qué vía funcionó**.

### Las tres pruebas antes de dar por buena una fila

1. El **título** de la fila es la obra buscada, no un trabajo que la cita.
2. El **tipo no es `CITATION`**.
3. El **conteo es plausible**: centenas o miles. La excepción declarada es la
   obra #10 (Version 12, 2025), donde un número chico es correcto.

Si Scholar tiene la obra partida en varios registros legítimos con cifras
comparables, anota **la mayor y la suma**, marcando cuál es cuál. Se fusionan
igual que se fusionaron los duplicados de OpenAlex. Las fichas `CITATION` de dos
o tres citas son ruido y no se suman.

### Plan de respaldo

En este orden, hasta que aparezca un registro no-`CITATION`:

- **a.** Misma frase en **Title words**, con comillas. Es la forma que funcionó
  en PoP001.
- **b.** Misma frase en **Title words**, sin comillas y sin puntuación.
- **c.** Acortar a la parte distintiva: `Standard GTAP Model` en vez del título
  completo con número de versión.
- **d.** Por **Authors + Year** en vez de por título: `Corong`, años 2017–2018.
- **e.** Fuente **Google Scholar Profile** con el autor: `Thomas W. Hertel`,
  `Angel Aguiar`, `Erwin Corong`. El perfil da los mismos conteos «Cited by» y
  evita el emparejamiento por título. Es la vía más confiable para JGEA.

---

## Bloque A — las 10 obras que producen razón

De aquí sale el factor de cobertura. Ordenadas de mayor a menor peso.
La columna OpenAlex está medida el 30 de agosto de 2026 y **ya viene fusionada**
donde OpenAlex parte la obra en dos registros: no la vuelvas a sumar.

| # | Consulta (Keywords, con comillas) | Authors | OpenAlex |
|---|---|---|---:|
| 1 | `"Global Trade Assistance and Production The GTAP 5 Data Base"` | | 1,122 |
| 2 | `"GTAP-E An Energy-Environmental Version of the GTAP Model"` | | 746 ⁽²⁾ |
| 3 | `"An Overview of the GTAP 9 Data Base"` | | 576 |
| 4 | `"The GTAP Data Base Version 10"` | | 498 |
| 5 | `"The Standard GTAP Model Version 7"` | Corong | 293 ⁽²⁾ |
| 6 | `"Structure of GTAP"` | **Hertel Tsigas** | 260 |
| 7 | `"GTAP-AGR A Framework for Assessing the Implications of Multilateral Changes in Agricultural Policies"` | | 179 ⁽²⁾ |
| 8 | `"The GTAP Data Base Version 11"` | | 154 |
| 9 | `"Dynamic Modeling and Applications for Global Economic Analysis"` | Ianchovichina | 140 |
| 10 | `"The GTAP Data Base Version 12"` | | 1 |

⁽²⁾ suma de dos registros de OpenAlex.

Ya capturada, no repetir: **Global Trade Analysis: Modeling and Applications**
(Hertel, 1997) — OpenAlex 895 · Scholar **5,742** · razón 6.42x, o 4.97x contra
los 1,155 que suman libro + capítulo.

Notas de captura:

- **#5** es la que falló en agosto. Si vuelve a dar solo `CITATION`, salta
  directo al respaldo **e** (perfil de Erwin Corong).
- **#6 «Structure of GTAP»** es un título corto y genérico: sin el campo de
  autores Scholar traerá ruido.
- **#10 (Version 12, 2025)** tiene 1 cita en OpenAlex. Un número chico en
  Scholar aquí es correcto, no un fallo. Se captura y se **excluye** del cálculo
  de la razón: la obra es demasiado reciente para sostener un cociente.

## Bloque B — los tres volúmenes que no producen razón

**Aquí no hay cociente que calcular.** OpenAlex vale 0 para los tres, y una
división por cero no es un factor de cobertura. Miden otra cosa: **cuántas citas
quedan fuera del alcance de la Ruta A por un hueco de indexación.** Se reportan
aparte, en términos absolutos, y no entran en la mediana.

| # | Consulta (Keywords, con comillas) | Authors | OpenAlex |
|---|---|---|---:|
| 11 | `"Global Trade Assistance and Production The GTAP 8 Data Base"` | Narayanan | no indexado |
| 12 | `"Global Trade Assistance and Production The GTAP 7 Data Base"` | Narayanan Walmsley | no indexado |
| 13 | `"Global Trade Assistance and Production The GTAP 6 Data Base"` | Dimaranan | no indexado |

Son los volúmenes de mayor uso entre 2006 y 2016. Es de esperarse que traigan
miles de citas entre los tres. Sostienen la hipótesis del **universo semilla**
(el 1.73x), no la de cobertura.

---

## La restricción

**Publish or Perish operado a mano, sí; scrapers de Google Scholar, no.**
`scholar.google.com/robots.txt` prohíbe el rastreo automatizado. La herramienta
es aceptable porque la opera una persona de forma interactiva. Automatizarla por
SSH o por cualquier otra vía sería evadir el mismo bloqueo por otro camino, así
que no se hace.

Si aparece un captcha, se resuelve a mano. **Si Scholar bloquea la sesión, hay
que detenerse y avisar.** Se reanuda en otro momento. No hay rodeo aceptable.

---

## Al terminar

No hace falta exportar nada a mano. Las consultas guardadas quedan en

    ~/Library/Application Support/Publish or Perish/Results6/*.json

y de ahí las lee `09_procesar_pop.py`, que también acepta los CSV exportados de
`pop_csv/` — las dos vías, un solo script. Calcula la razón obra por obra, la
**mediana y el rango** (no el promedio: con esta n y con el sesgo de los libros,
un promedio no dice nada), y escribe `resultados_pop.json` más la hoja
`comparacion_scholar_openalex.csv`.

```bash
python3 09_procesar_pop.py                 # lee scholar/ y pop_csv/
python3 09_procesar_pop.py --desde-macpro  # copia Results6/ de la MacPro y procesa
```
