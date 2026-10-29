from pathlib import Path
import concurrent.futures, json, re, requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent
IDS = '''2606.01533v1 2605.21470v2 2607.22689v1 2607.24167v1 2605.14290v1 2511.21398v1 2605.07134v1 2605.29397v1 2602.20502v1 2602.17245v2 2610.03036v2 2605.16565v2 2604.09718v2 2601.21123v2 2603.00503v1 2610.01415v1 2512.10371v2 2606.15017v2 2603.15473v2 2512.15374v2 2512.07094v2 2608.02643v2 2610.27954v1 2603.20340v3 2604.06240v1 2511.20067v1 2605.16116v1 2604.16385v1 2604.01535v1 2609.38912v1 2609.05736v1'''.split()

def fetch(aid):
    dest = ROOT / '来源文本' / (aid + '.json')
    if dest.exists(): return json.loads(dest.read_text(encoding='utf-8'))
    url = 'https://arxiv.org/html/' + aid
    try:
        r = requests.get(url, timeout=65)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        article = soup.select_one('article') or soup
        title = article.select_one('h1')
        sections=[]
        for sec in article.select('section'):
            h = sec.find(re.compile('^h[1-6]$'), recursive=False)
            if not h: continue
            paras = [p.get_text(' ',strip=True) for p in sec.find_all(['p','table'],recursive=False)]
            if not paras:
                paras=[p.get_text(' ',strip=True) for p in sec.select('.ltx_para') if p.find_parent('section')==sec]
            sections.append({'heading':h.get_text(' ',strip=True),'text':'\n'.join(paras)})
        links=sorted(set(a.get('href','') for a in article.select('a[href]') if any(s in a.get('href','') for s in ['github.com','github.io','huggingface.co'])))
        data={'id':aid,'url':url,'title':title.get_text(' ',strip=True) if title else '', 'links':links,'sections':sections,'text':article.get_text('\n',strip=True)}
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        return data
    except Exception as exc: return {'id':aid,'error':str(exc)}

if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        rows=list(pool.map(fetch,IDS))
    (ROOT/'来源索引.json').write_text(json.dumps([{k:v for k,v in row.items() if k not in ['text','sections']} for row in rows],ensure_ascii=False,indent=2),encoding='utf-8')
    for row in rows:
        print(json.dumps({k:v for k,v in row.items() if k not in ['text','sections']},ensure_ascii=False))
