import json, time, urllib.request, urllib.parse
S2="https://api.semanticscholar.org/graph/v1"
def get(u):
    for a in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent':'gtap-bib/1.0'}), timeout=40) as r:
                return json.load(r)
        except Exception: time.sleep(3*(a+1))
    return None

print("=== LIBRO FUNDACIONAL ===")
for q in ["Global Trade Analysis: Modeling and Applications",
          "Global Trade Analysis Modeling and Applications"]:
    r=get(f"{S2}/paper/search?query={urllib.parse.quote(q)}&limit=5&fields=title,year,citationCount,authors")
    for p in (r or {}).get('data',[]):
        au=", ".join(a['name'] for a in p.get('authors',[])[:2])
        print(f"  {p.get('citationCount'):>6}  {p.get('year')}  {p.get('title')[:70]}  [{au}]")
    time.sleep(1.5)

print("\n=== CORPUS GTAP: citas recibidas ===")
years={}; cites={}; token=None; n=0; total=None; allc=0
while True:
    u=f"{S2}/paper/search/bulk?query=GTAP&fields=year,citationCount"
    if token: u+=f"&token={token}"
    d=get(u)
    if not d: break
    if total is None: total=d.get('total')
    for p in d.get('data',[]):
        y=p.get('year'); c=p.get('citationCount') or 0
        n+=1; allc+=c
        if y: years[y]=years.get(y,0)+1; cites[y]=cites.get(y,0)+c
    token=d.get('token')
    if not token: break
    time.sleep(1.2)
print(f"trabajos indexados que mencionan GTAP: {total} (recuperados {n})")
print(f"citas acumuladas por esos trabajos: {allc:,}")
print(f"promedio de citas por trabajo: {allc/max(n,1):.1f}")
top=sorted(years.items())
print("\naño | trabajos | citas recibidas")
for y,c in top:
    if y>=2010: print(f"{y} | {c:>4} | {cites.get(y,0):>6}")
json.dump({"total":total,"n":n,"allc":allc,"years":years,"cites":cites}, open("corpus.json","w"))
