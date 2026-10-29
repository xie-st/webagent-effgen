# -*- coding: utf-8 -*-
"""批量下载 arXiv HTML 论文并转换为 Markdown（增强版）。

处理要点：
- 公式：LaTeXML 的 <math alttext> 保存原始 LaTeX。行内公式还原为 $...$，
  展示级公式（display="block"）还原为 $$ 块。占位符策略避免转义破坏公式。
- 表格：自写解析转管道式 Markdown；等式对齐环境（单元格全是公式的表）
  还原为逐行展示公式，不当数据表处理；嵌套子表（多级表头）拍平进父单元格。
- 图片：全部下载到本地 images/<篇名>/，正文引用改写为相对路径，离线可读。
- 排版：作者块合并为单行、清理 mailto 链接与链接 title 噪声、
  去除表格行尾空单元格与全空行。
"""
import base64
import re
import sys
import time
from urllib.parse import urljoin, unquote, urlparse
from pathlib import Path

import requests
from bs4 import BeautifulSoup, NavigableString
from markdownify import markdownify as md

BASE_DIR = Path(r"D:\Dwen\Alpha26fall\华为2026Hackathon_WebAgent\论文库")
MD_DIR = BASE_DIR / "30篇全文md"
HTML_DIR = BASE_DIR / "_html_cache"
MD_DIR.mkdir(parents=True, exist_ok=True)
HTML_DIR.mkdir(parents=True, exist_ok=True)

PAPERS = [
    (1, "MACU", "https://arxiv.org/html/2606.01533v1"),
    (2, "FCPAgent", "https://arxiv.org/html/2607.24167v1"),
    (3, "Verifiers", "https://arxiv.org/html/2604.06240v1"),
    (4, "ContractSkill", "https://arxiv.org/html/2603.20340v3"),
    (5, "AgentJIT", "https://arxiv.org/html/2605.21470v2"),
    (6, "BudgetConstrained", "https://arxiv.org/html/2606.15017v2"),
    (7, "Region4Web", "https://arxiv.org/html/2605.07134v1"),
    (8, "WebFovea", "https://arxiv.org/html/2610.03036v2"),
    (9, "ALTK", "https://arxiv.org/html/2603.15473v2"),
    (10, "PoS", "https://arxiv.org/html/2610.01415v1"),
    (11, "StressWeb", "https://arxiv.org/html/2604.16385v1"),
    (12, "ParaGUIBench", "https://arxiv.org/html/2607.22689v1"),
    (13, "Skim", "https://arxiv.org/html/2605.16565v2"),
    (14, "WebChallenger", "https://arxiv.org/html/2606.10423"),
    (15, "Prune4Web", "https://arxiv.org/html/2511.21398v1"),
    (16, "ObservationReduction", "https://arxiv.org/html/2605.29397v1"),
    (17, "CUADebug", "https://arxiv.org/html/2608.02643v2"),
    (18, "ActionEngine", "https://arxiv.org/html/2602.20502v1"),
    (19, "M2_DualMemory", "https://arxiv.org/html/2603.00503v1"),
    (20, "ReadMoreThinkMore", "https://arxiv.org/html/2604.01535v1"),
    (21, "AgentProg", "https://arxiv.org/html/2512.10371v2"),
    (22, "CUA-Skill", "https://arxiv.org/html/2601.21123v2"),
    (23, "PRISM", "https://arxiv.org/html/2609.05736v1"),
    (24, "MonitoringWebAgents", "https://arxiv.org/html/2609.02057"),
    (25, "ReTRACE", "https://arxiv.org/html/2610.27954v1"),
    (26, "CATTS", "https://arxiv.org/html/2602.12276"),
    (27, "STITCH", "https://arxiv.org/html/2609.38912v1"),
    (28, "AreWeDoneYet", "https://arxiv.org/html/2511.20067v1"),
    (29, "SCOPE", "https://arxiv.org/html/2512.15374v2"),
    (30, "ShopGym", "https://arxiv.org/html/2605.16116v1"),
]

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) research-paper-archiver"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

MATH_PH = re.compile(r"ZZMATHZZ\d+ZZ")
MAX_IMG_BYTES = 15 * 1024 * 1024


def fetch(url: str, timeout: int = 90) -> requests.Response:
    last_err = None
    for attempt in range(3):
        try:
            r = SESSION.get(url, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            last_err = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"下载失败: {last_err}")


def download(url: str) -> str:
    r = fetch(url)
    if len(r.text) < 20000:
        raise RuntimeError(f"页面过短({len(r.text)} 字节)，疑似 404/跳转页")
    return r.text


# ---------- 图片 ----------

def save_image(src: str, base_url: str, img_dir: Path, rel_prefix: str, cache: dict) -> str:
    """下载一张图片，返回 Markdown 中的相对路径；失败返回原 URL。"""
    if src.startswith("data:"):
        key = src[:64]
        if key in cache:
            return cache[key]
        mobj = re.match(r"data:image/(\w+);base64,(.*)", src, re.S)
        if not mobj:
            return src
        ext = {"jpeg": "jpg", "svg+xml": "svg"}.get(mobj.group(1), mobj.group(1))
        data = base64.b64decode(mobj.group(2))
        n = len(cache)
        path = img_dir / f"inline_{n}.{ext}"
        path.write_bytes(data)
        rel = f"{rel_prefix}/{path.name}"
        cache[key] = rel
        return rel

    abs_url = urljoin(base_url, src)
    if abs_url in cache:
        return cache[abs_url]
    name = unquote(urlparse(abs_url).path).rstrip("/").split("/")[-1] or "img"
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    if not Path(name).suffix:
        name += ".png"
    path = img_dir / name
    if path.exists() and path.stat().st_size > 0:
        rel = f"{rel_prefix}/{name}"
        cache[abs_url] = rel
        return rel
    try:
        r = fetch(abs_url, timeout=60)
        if len(r.content) > MAX_IMG_BYTES:
            print(f"    [img] 跳过过大文件 {name} ({len(r.content)} B)")
            return abs_url
        path.write_bytes(r.content)
        rel = f"{rel_prefix}/{name}"
        cache[abs_url] = rel
        return rel
    except Exception as e:
        print(f"    [img] 下载失败 {abs_url}: {e}", file=sys.stderr)
        return abs_url


def localize_images(content, base_url: str, img_dir: Path, rel_prefix: str) -> int:
    cache = {}
    img_dir.mkdir(parents=True, exist_ok=True)
    seen = set()
    # <object data="*.svg">：LaTeXML 内嵌矢量图，转成本地 <img>
    for obj in list(content.find_all("object")):
        data = obj.get("data")
        if data:
            new_src = save_image(data, base_url, img_dir, rel_prefix, cache)
            img = content.new_tag("img")
            img["src"] = new_src
            img["alt"] = ""
            img["data-localized"] = "1"
            obj.replace_with(img)
            seen.add(new_src)
        else:
            obj.decompose()
    for img in content.find_all("img"):
        if img.get("data-localized"):
            continue
        src = img.get("src")
        if not src:
            img.decompose()
            continue
        new_src = save_image(src, base_url, img_dir, rel_prefix, cache)
        img["src"] = new_src
        img["alt"] = img.get("alt") or ""
        seen.add(new_src)
    return len(seen)


# ---------- 表格 ----------

def cell_text(cell) -> str:
    txt = cell.get_text(" ", strip=True)
    txt = re.sub(r"\s+", " ", txt)
    return txt.replace("|", "\\|")


def table_to_markdown(table, math_map: dict) -> str:
    rows = table.find_all("tr")
    if not rows:
        return ""
    grid = []
    for tr in rows:
        row = []
        for cell in tr.find_all(["th", "td"]):
            row.append(cell_text(cell))
            colspan = int(cell.get("colspan", 1) or 1)
            row.extend([""] * (colspan - 1))
        while row and row[-1] == "":
            row.pop()
        grid.append(row)
    grid = [r for r in grid if r]  # 去全空行
    if not grid:
        return ""

    # 等式对齐环境：所有非空单元格都是公式占位符 -> 逐行展示公式
    def is_equation_row(r):
        return all(
            all(MATH_PH.fullmatch(tok) for tok in c.split())
            for c in r
        )

    if all(is_equation_row(r) for r in grid):
        lines = []
        for r in grid:
            for c in r:
                for tok in c.split():
                    alt, disp = math_map.get(tok, ("", False))
                    lines.append(f"$$\n{alt}\n$$")
        return "\n\n".join(lines)

    ncols = max(len(r) for r in grid)
    for r in grid:
        r.extend([""] * (ncols - len(r)))

    def fmt_row(r):
        return "| " + " | ".join(r) + " |"

    sep = "|" + "|".join([" --- "] * ncols) + "|"
    lines = [fmt_row(grid[0]), sep]
    for r in grid[1:]:
        lines.append(fmt_row(r))
    return "\n".join(lines)


# ---------- 转换 ----------

def convert(html_text: str, base_url: str, img_dir: Path = None, rel_prefix: str = None):
    soup = BeautifulSoup(html_text, "lxml")

    for tag in soup.find_all(["script", "style", "nav", "footer"]):
        tag.decompose()

    content = soup.select_one("div.ltx_page_content") or soup.body or soup

    n_imgs = 0
    if img_dir is not None:
        n_imgs = localize_images(content, base_url, img_dir, rel_prefix)

    # 链接清理：去 title 噪声、去 mailto 链接壳
    for a in content.find_all("a"):
        if a.get("title"):
            del a["title"]
        href = a.get("href") or ""
        if href.startswith("mailto:"):
            a.unwrap()

    # 作者块：HTML 层解析重建为单行列表
    authors_map = {}
    for i, creator in enumerate(content.select(".ltx_creator.ltx_role_author")):
        pn = creator.select_one(".ltx_personname")
        name = pn.get_text(" ", strip=True) if pn else ""
        parts_aff, parts_mail = [], []
        for contact in creator.select(".ltx_contact"):
            cn = contact.select_one(".ltx_contact_name")
            if cn:
                cn.decompose()
            txt = " ".join(contact.get_text(" ", strip=True).split())
            # 纯符号碎片（如破损模板残留 "["）跳过
            if not txt or not re.search(r"[A-Za-z0-9]", txt):
                continue
            if "ltx_role_email" in (contact.get("class") or []):
                parts_mail.append(txt)
            else:
                parts_aff.append(txt)
        if not (name or parts_aff or parts_mail):
            continue
        entry = f"- **{name}**" if name else "-"
        if parts_aff:
            entry += " · " + "; ".join(parts_aff)
        if parts_mail:
            entry += " · " + ", ".join(parts_mail)
        ph = f"ZZAUTHORZZ{i}ZZ"
        authors_map[ph] = entry
        creator.replace_with(NavigableString(f"\n\n{ph}\n\n"))
    # 作者间分隔符（","/"and" 等）
    for sep in content.select(".ltx_author_before"):
        sep.decompose()
    # ACM CCS 分类等元数据噪声
    for meta in content.select(".ltx_classification"):
        meta.decompose()

    # 公式：alttext -> 占位符（区分行内/展示级）
    math_map = {}
    for i, m in enumerate(content.find_all("math")):
        alt = m.get("alttext")
        if not alt:
            continue
        ph = f"ZZMATHZZ{i}ZZ"
        is_display = m.get("display") == "block" or "ltx_equation" in (m.parent.get("class") or [])
        math_map[ph] = (alt, is_display)
        m.replace_with(NavigableString(f" {ph} "))

    # 表格（reversed 使嵌套内层表先处理）
    table_map = {}
    for i, table in enumerate(reversed(content.find_all("table"))):
        if table.parent.name in ("td", "th"):
            flat = " / ".join(
                cell_text(c)
                for tr in table.find_all("tr")
                for c in tr.find_all(["th", "td"])
            )
            table.replace_with(NavigableString(" " + flat + " "))
            continue
        tmd = table_to_markdown(table, math_map)
        if not tmd:
            continue
        ph = f"ZZTABLEZZ{i}ZZ"
        table_map[ph] = tmd
        table.replace_with(NavigableString(f"\n\n{ph}\n\n"))

    markdown = md(str(content), heading_style="ATX", bullets="-")

    # 作者还原
    for ph, line in authors_map.items():
        markdown = markdown.replace(ph, line)

    # 表格还原（多轮兜底）
    for _ in range(5):
        if not re.search(r"ZZTABLEZZ\d+ZZ", markdown):
            break
        for ph, tmd in table_map.items():
            markdown = markdown.replace(ph, tmd)

    # 公式还原：展示级 -> $$ 块，行内 -> $...$
    for ph, (alt, disp) in math_map.items():
        markdown = markdown.replace(
            ph, f"\n\n$$\n{alt}\n$$\n\n" if disp else f"${alt}$"
        )

    markdown = polish(markdown)
    markdown = re.sub(r"\n{4,}", "\n\n\n", markdown)
    return markdown.strip() + "\n", n_imgs


def polish(markdown: str) -> str:
    """作者块合并、清理空白分隔行等排版收尾。"""
    # 不换行空格统一为普通空格（LaTeXML 大量使用 \xa0，影响行匹配与阅读）
    markdown = markdown.replace("\xa0", " ")
    lines = markdown.split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if (
            i + 2 < len(lines)
            and line.strip()
            and not line.startswith("#")
            and lines[i + 1].startswith("Affiliation: ")
            and lines[i + 2].startswith("Email: ")
        ):
            name = line.strip()
            aff = lines[i + 1][len("Affiliation: "):].strip()
            email = lines[i + 2][len("Email: "):].strip()
            parts = [f"**{name}**"]
            if aff:
                parts.append(aff)
            if email:
                parts.append(email)
            out.append("- " + " · ".join(parts))
            i += 3
            continue
        out.append(line)
        i += 1
    md2 = "\n".join(out)
    # LaTeX 命令泄漏清理（仅限摘要之前的扉页区，如 "\affiliationbreak3]" 索引残渣）
    head, sep, rest = md2.partition("\n###### Abstract")
    if sep:
        head_lines = []
        for ln in head.split("\n"):
            s = ln.strip()
            if s.startswith("\\contribution") or s.startswith("\\website"):
                continue
            s2 = re.sub(r"^\\affiliationbreak\s*", "", s)
            s2 = re.sub(r"^\d+\]\s*", "", s2)
            if s2 != s:
                if s2:
                    head_lines.append(s2)
                continue
            head_lines.append(ln)
        md2 = "\n".join(head_lines) + sep + rest
    # 作者块之间的全空白分隔行（含特殊空格）
    md2 = re.sub(r"\n[ \u2002\u2003\u2007\u2009\u00a0]+\n", "\n\n", md2)
    return md2


def extract_title(html_text: str) -> str:
    soup = BeautifulSoup(html_text, "lxml")
    t = soup.select_one("h1.ltx_title")
    if t:
        return t.get_text(" ", strip=True)
    if soup.title:
        return soup.title.get_text(strip=True)
    return ""


def main():
    results = []
    total_imgs = 0
    for idx, short, url in PAPERS:
        cache = HTML_DIR / f"{idx:02d}_{short}.html"
        out = MD_DIR / f"{idx:02d}_{short}.md"
        img_dir = MD_DIR / "images" / f"{idx:02d}_{short}"
        rel_prefix = f"images/{idx:02d}_{short}"
        try:
            if cache.exists() and cache.stat().st_size > 20000:
                html_text = cache.read_text(encoding="utf-8", errors="replace")
            else:
                html_text = download(url)
                cache.write_text(html_text, encoding="utf-8")
                print(f"[{idx:02d}] {short}: 下载 {len(html_text)} 字节")
            title = extract_title(html_text)
            markdown, n_imgs = convert(html_text, url, img_dir, rel_prefix)
            total_imgs += n_imgs
            header = (
                f"---\ntitle: \"{title}\"\n"
                f"arxiv_html: {url}\n"
                f"downloaded: 2026-10-29\n"
                f"converted: arxiv LaTeXML HTML -> Markdown（本地图片 + alttext 公式还原）\n---\n\n"
            )
            out.write_text(header + markdown, encoding="utf-8")
            print(f"[{idx:02d}] {short}: -> {out.name} ({len(markdown)} 字符, {n_imgs} 张图片)")
            results.append((idx, short, "OK", f"{len(markdown)} chars, {n_imgs} imgs"))
        except Exception as e:
            print(f"[{idx:02d}] {short}: FAIL - {e}", file=sys.stderr)
            results.append((idx, short, "FAIL", str(e)))

    print("\n===== 汇总 =====")
    ok = sum(1 for r in results if r[2] == "OK")
    print(f"成功 {ok}/{len(results)}，共下载图片 {total_imgs} 张")
    for idx, short, status, msg in results:
        if status == "FAIL":
            print(f"  FAIL [{idx:02d}] {short}: {msg}")


if __name__ == "__main__":
    main()
