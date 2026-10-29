from pathlib import Path
import concurrent.futures, json, re, requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent
IDS = ['2606.10423', '2606.06708', '2602.12276', '2609.02057']

def fetch(aid):
    url = 'https://arxiv.org/html/' + aid
    r = requests.get(url, timeout=45)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    article = soup.select_one('article') or soup
    sections = []
    for sec in article.select('section'):
        h = sec.find(re.compile('^h[1-6]$'), recursive=False)
        if not h:
            continue
        paras = [x.get_text(' ', strip=True) for x in sec.find_all(['p', 'table'], recursive=False)]
        if not paras:
            paras = [x.get_text(' ', strip=True) for x in sec.select('.ltx_para') if x.find_parent('section') == sec]
        sections.append({'heading': h.get_text(' ', strip=True), 'text': '\n'.join(paras)})
    data = {'id': aid, 'url': url, 'title': article.select_one('h1').get_text(' ', strip=True),
            'links': sorted(set(a['href'] for a in article.select('a[href]') if any(x in a['href'] for x in ['github.com', 'github.io', 'huggingface.co']))),
            'sections': sections, 'text': article.get_text('\n', strip=True)}
    dest = ROOT / '来源文本' / (aid + '.json')
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return {k: v for k, v in data.items() if k not in ['text', 'sections']}

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for row in pool.map(fetch, IDS):
            print(json.dumps(row, ensure_ascii=False))
