#!/usr/bin/env python3
"""
md2pdf.py — Markdown a PDF con Chrome headless.

Uso:
    python3 md2pdf.py Ficha_GTAP2029_Monterrey.md
    python3 md2pdf.py Ficha_GTAP2029_Monterrey.md 8.0     # cuerpo en 8.0 pt

El segundo argumento es el tamaño del cuerpo de texto en puntos (default 8.3).
Es la perilla para ajustar cuántas páginas ocupa: bájalo si se desborda,
súbelo si sobra espacio. Imprime el número de páginas al terminar.

Construcciones soportadas: `#`, `##`, `###`, `---`, tablas con `|`,
listas con `- `, párrafos, `**negrita**`, `*cursiva*`, `[enlace](url)`, y el
recuadro `:::nombre … :::` (nombres usados: `resumen`, `key`) y el salto de
línea explícito `<br>`, que sirve para partir una etiqueta de tabla. No hay soporte
para citas ni listas anidadas. Al tocar el parser, correr antes y después:

    python3 md2pdf.py fuente/prueba_parser.md

No requiere instalar nada: solo Python 3 (viene con macOS) y Google Chrome.
"""
import html, os, re, subprocess, sys, shutil

FONT_SIZE = float(sys.argv[2]) if len(sys.argv) > 2 else 8.3
SRC = sys.argv[1] if len(sys.argv) > 1 else sys.exit("Falta el archivo .md")
OUT = os.path.splitext(SRC)[0] + ".pdf"
TMP = os.path.splitext(SRC)[0] + ".tmp.html"

CHROME_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/opt/pw-browsers/chromium",
]

CSS = """
@page {{ size: letter; margin: 13mm 15mm; }}
body {{ font-family: Georgia,'Times New Roman',serif; font-size:{fs}pt;
        line-height:1.33; color:#16181d; margin:0; }}
h1 {{ font-family:Helvetica,Arial,sans-serif; font-size:15pt; line-height:1.15;
      margin:0 0 1.6mm; color:#0f2b46; letter-spacing:-0.2px; }}
h1 + p {{ font-family:Helvetica,Arial,sans-serif; font-size:7.8pt; color:#5b6470;
          margin:0 0 2.4mm; }}
h2 {{ font-family:Helvetica,Arial,sans-serif; font-size:9.2pt; color:#0f2b46;
      margin:3.4mm 0 1.2mm; padding-bottom:0.6mm; border-bottom:0.6pt solid #c9d2dc; }}
h3 {{ font-family:Helvetica,Arial,sans-serif; font-size:8.4pt; color:#0f2b46;
      margin:2.6mm 0 1mm; }}
p {{ margin:0 0 1.6mm; text-align:justify; hyphens:auto; }}
ul {{ margin:0 0 1.7mm; padding-left:4mm; }}
li {{ margin-bottom:0.9mm; text-align:justify; }}
table {{ width:100%; border-collapse:collapse; margin:0 0 1.9mm; }}
td {{ border-bottom:0.4pt solid #dfe4ea; padding:0.9mm 1.5mm; vertical-align:top; }}
td:first-child {{ width:26%; font-family:Helvetica,Arial,sans-serif; font-size:7.9pt;
                  color:#0f2b46; font-weight:600; }}
tr:last-child td {{ border-bottom:none; }}
hr {{ border:none; border-top:0.8pt solid #0f2b46; margin:3mm 0 2.6mm; }}
strong {{ color:#0f2b46; }}
a {{ color:#1a4f7a; text-decoration:none; }}
em {{ color:#5b6470; }}
.resumen td:first-child {{ width:21%; }}
.resumen, .key {{ background:#f4f6f8; border-left:2.2pt solid #0f2b46;
                  padding:1.5mm 2.4mm 0.4mm; margin:0 0 2.6mm; }}
.resumen > :last-child, .key > :last-child {{ margin-bottom:0; }}
.resumen tr:last-child td, .key tr:last-child td {{ border-bottom:none; }}
"""


def inline(t):
    t = html.escape(t)
    t = t.replace('&lt;br&gt;', '<br>')      # único salto de línea explícito
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', t)
    return t


def md_to_html(md):
    lines, out, i = md.split('\n'), [], 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith('# '):
            out.append(f'<h1>{inline(ln[2:])}</h1>'); i += 1
        elif ln.startswith('### '):
            out.append(f'<h3>{inline(ln[4:])}</h3>'); i += 1
        elif ln.startswith('## '):
            out.append(f'<h2>{inline(ln[3:])}</h2>'); i += 1
        elif ln.strip() == '---':
            out.append('<hr>'); i += 1
        elif ln.startswith(':::'):
            cls, i = ln[3:].strip() or 'key', i + 1
            buf = []
            while i < len(lines) and lines[i].strip() != ':::':
                buf.append(lines[i]); i += 1
            i += 1                                   # consume el ::: de cierre
            out.append(f'<div class="{cls}">' + md_to_html('\n'.join(buf)) + '</div>')
        elif ln.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append(lines[i]); i += 1
            cells = [[c.strip() for c in r.strip().strip('|').split('|')] for r in rows]
            cells = [c for c in cells
                     if not all(set(x) <= set('-: ') and x for x in c)]   # quita separadores
            out.append('<table>' + ''.join(
                '<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>'
                for r in cells) + '</table>')
        elif ln.startswith('- '):
            items = []
            while i < len(lines) and lines[i].startswith('- '):
                items.append(f'<li>{inline(lines[i][2:])}</li>'); i += 1
            out.append('<ul>' + ''.join(items) + '</ul>')
        elif not ln.strip():
            i += 1
        else:
            buf = []
            while (i < len(lines) and lines[i].strip()
                   and not lines[i].startswith(('#', '|', '- ', '---', ':::'))):
                buf.append(lines[i]); i += 1
            out.append('<p>' + inline(' '.join(buf)) + '</p>')
    return ''.join(out)


chrome = next((p for p in CHROME_PATHS if os.path.exists(p)), None) or shutil.which("chromium")
if not chrome:
    sys.exit("No encontré Chrome. Instálalo o edita CHROME_PATHS.")

body = md_to_html(open(SRC, encoding='utf-8').read())
open(TMP, 'w', encoding='utf-8').write(
    f'<!doctype html><html lang="es"><head><meta charset="utf-8">'
    f'<style>{CSS.format(fs=FONT_SIZE)}</style></head><body>{body}</body></html>')

def run_chrome(extra=()):
    return subprocess.run(
        [chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer", *extra,
         f"--print-to-pdf={OUT}", "file://" + os.path.abspath(TMP)],
        capture_output=True)

r = run_chrome()
if r.returncode != 0:
    # Algunos entornos Linux (contenedores, root) necesitan --no-sandbox.
    # En macOS con Chrome normal el primer intento basta y no se degrada nada.
    r = run_chrome(["--no-sandbox"])
if r.returncode != 0:
    sys.exit("Chrome falló:\n" + r.stderr.decode()[:800])
os.remove(TMP)

try:
    from pypdf import PdfReader
    n = len(PdfReader(OUT).pages)
    print(f"{OUT} — {n} páginas (cuerpo {FONT_SIZE} pt)")
except ImportError:
    print(f"{OUT} — listo (cuerpo {FONT_SIZE} pt)")
