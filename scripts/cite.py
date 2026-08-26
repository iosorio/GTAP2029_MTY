import json, time, urllib.request, urllib.parse

S2="https://api.semanticscholar.org/graph/v1"
def get(url):
    for a in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'gtap-bib/1.0'}), timeout=40) as r:
                return json.load(r)
        except Exception as e:
            time.sleep(3*(a+1))
    return None

# --- 1. canonical works ---
canon = [
 ("Hertel (ed.) 1997 — Global Trade Analysis: Modeling and Applications", "search", "Global Trade Analysis Modeling and Applications Hertel"),
 ("Corong et al. 2017 — The Standard GTAP Model, Version 7", "doi", "10.21642/JGEA.020101AF"),
 ("Aguiar et al. 2019 — The GTAP Data Base: Version 10", "search", "The GTAP Data Base Version 10"),
 ("Aguiar et al. 2022 — The GTAP Data Base: Version 11", "search", "The GTAP Data Base Version 11"),
 ("Aguiar et al. 2016 — An Overview of the GTAP 9 Data Base", "search", "An Overview of the GTAP 9 Data Base"),
 ("Hertel & Tsigas — Structure of GTAP", "search", "Structure of GTAP Hertel Tsigas"),
]
rows=[]
for label, kind, q in canon:
    if kind=="doi":
        d = get(f"{S2}/paper/DOI:{q}?fields=title,year,citationCount,externalIds")
    else:
        r = get(f"{S2}/paper/search?query={urllib.parse.quote(q)}&limit=3&fields=title,year,citationCount")
        d = (r or {}).get('data',[None])[0]
    if d: rows.append((label, d.get('year'), d.get('citationCount'), d.get('title')))
    else: rows.append((label, None, None, "NO ENCONTRADO"))
    time.sleep(1.2)

print("=== OBRAS CANONICAS (Semantic Scholar) ===")
tot=0
for l,y,c,t in rows:
    print(f"{c if c is not None else '?':>7}  {y}  {l}")
    if c: tot+=c
print(f"{tot:>7}  SUMA")

# --- 2. corpus: papers mentioning GTAP, by year ---
print("\n=== CORPUS ===")
for term in ['GTAP', '"Global Trade Analysis Project"']:
    years={}; token=None; n=0; total=None
    while True:
        u=f"{S2}/paper/search/bulk?query={urllib.parse.quote(term)}&fields=year"
        if token: u+=f"&token={token}"
        d=get(u)
        if not d: break
        if total is None: total=d.get('total')
        for p in d.get('data',[]):
            y=p.get('year')
            if y: years[y]=years.get(y,0)+1
            n+=1
        token=d.get('token')
        if not token or n>=20000: break
        time.sleep(1.2)
    print(f"\n--- termino: {term} --- total reportado: {total} | recuperados: {n}")
    for y in sorted(years):
        if y>=2000: print(f"  {y}: {years[y]}")
    json.dump(years, open(f"years_{'gtap' if term=='GTAP' else 'gtaproject'}.json",'w'))
