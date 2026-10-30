"""User-authorized Xiaohongshu draft-only test; no fabricated completion counts.

Uses the M3 Runtime/API for search, per-post assessment and drafting. The runner
collects observed links, deduplicates notes and independently records screenshot
and cancellation outcomes. Credentials and complete evidence stay in raw/.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import threading
import time
from types import SimpleNamespace
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[2]
HARNESS=ROOT/'02_代码/01_harness/当前版本'
sys.path[:0]=[str(HARNESS),str(HARNESS/'sdk')]
from playwright.sync_api import sync_playwright
from web_agent.adapters.browser import BrowserSession,DraftSpec,SiteLimiter,create_context
from web_agent.ax import AXTree
from web_agent.http_model import make_runtime


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-env',type=Path,required=True)
    parser.add_argument('--storage-state',type=Path,required=True)
    parser.add_argument('--read-post-file',type=Path,required=True,help='Audited exact read endpoint URL array')
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--target',type=int,default=20)
    parser.add_argument('--timeout',type=float,default=1800)
    parser.add_argument('--candidates',type=int,default=60)
    args=parser.parse_args()
    args.out=args.out.resolve();args.out.mkdir(parents=True,exist_ok=False)
    raw=args.out/'raw';raw.mkdir()
    os.environ['WEBAGENT_MODEL_ENV']=str(args.model_env.resolve())
    os.environ['WEBAGENT_M3_OUT']=str(args.out)
    endpoints=json.loads(args.read_post_file.read_text(encoding='utf-8'))
    deadline=time.time()+args.timeout
    limiter=SiteLimiter(spacing=.4)
    ledger=[];completed=0;blockers=[]

    def write_summary():
        summary={'case':'Xiaohongshu Mate90 unsent comments','target':args.target,'completed':completed,
                 'status':'complete' if completed>=args.target else 'incomplete','blockers':blockers,'items':ledger,
                 'search_coverage':'Observed search results only; exhaustive site-wide coverage is not asserted.'}
        (args.out/'result.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
        return summary

    def session(browser,name,url,task,*,draft=None):
        context=create_context(browser,storage_state=str(args.storage_state))
        runtime=make_runtime({'name':name},SimpleNamespace(inputs={},deadline=deadline))
        try:
            active=BrowserSession(context.new_page(),runtime,task=task,url=url,deadline=deadline,tab=name,
                limiter=limiter,draft=draft,readonly=draft is None,read_post_urls=endpoints)
            return context,runtime,active
        except Exception:
            context.close();runtime.close();raise

    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=False)
        try:
            context,runtime,search=session(browser,'search','https://www.xiaohongshu.com/explore',
                '在小红书搜索 Mate90。不要点赞、收藏、关注、发帖或发送评论。停留在搜索结果列表页面，确认搜索生效后stop。若要求登录或验证码，停止并说明。')
            try:
                result=search.run()
                (raw/'search.json').write_text(json.dumps({'checkpoint':search.checkpoint(),'events':search.events},ensure_ascii=False,indent=2),encoding='utf-8')
                candidates={};unchanged=0
                for scroll in range(16):
                    links=search.page.locator('a[href*="/explore/"]').evaluate_all('els=>els.map(e=>e.href)')
                    before=len(candidates)
                    for link in links:
                        parsed=urlsplit(link)
                        note=parsed.path.rsplit('/',1)[-1]
                        if parsed.hostname=='www.xiaohongshu.com' and note:
                            candidates.setdefault(note,link)
                    unchanged=unchanged+1 if before==len(candidates) else 0
                    if len(candidates)>=args.candidates or unchanged>=3 or time.time()>=deadline:break
                    search.page.mouse.wheel(0,700);search.page.wait_for_timeout(800)
                (raw/'candidates.json').write_text(json.dumps(candidates,ensure_ascii=False,indent=2),encoding='utf-8')
                if not candidates:
                    blockers.append('No observed note links: inspect search/login/read-network evidence')
            finally:
                search.close();context.close();runtime.close()

            for index,(note,url) in enumerate(candidates.items()):
                if completed>=args.target or index>=args.candidates or time.time()+10>=deadline:break
                item={'note_id':note,'url':'https://www.xiaohongshu.com/explore/'+note,'status':'incomplete'}
                ledger.append(item)
                context=runtime=reader=None
                try:
                    task=('阅读当前这条笔记正文，判断是否确实讨论Mate90，且整体评价相对中性或正向。不得操作点赞收藏关注评论。'
                          '结束动作stop的答案必须是JSON对象：{"eligible":true或false,"quote":"正文中的一段精确原文","reason":"简短判断"}。'
                          '无法读到正文、内容不相关或主要是负面评价时eligible=false。不要把搜索框内容当正文。')
                    context,runtime,reader=session(browser,f'assess_{index}',url,task)
                    result=reader.run()
                    observation=reader.history[-1]['observation'] if reader.history else {}
                    tree=AXTree(SimpleNamespace(ax=observation.get('text',''),url=observation.get('url','')))
                    business='\n'.join(tree.business_texts())
                    assessment=json.loads(result.action[6:-1]) if result.complete else {}
                    quote=assessment.get('quote')
                    eligible=assessment.get('eligible') is True and isinstance(quote,str) and len(quote)>=4 and quote in business
                    fields=[node.name for node in tree.nodes if node.role=='textbox' and '搜索' not in node.name and 'search' not in node.name.casefold()]
                    (raw/f'assess-{note}.json').write_text(json.dumps({'assessment':assessment,'observation':observation,'events':reader.events},ensure_ascii=False,indent=2),encoding='utf-8')
                    item['assessment']=assessment;item['eligible_with_observed_quote']=eligible
                    if not eligible:
                        item['status']='not_selected';continue
                    if len(fields)!=1:
                        item['status']='editor_unresolved';continue
                    field=fields[0]
                except Exception as exc:
                    item['status']='assessment_failed';item['error_type']=type(exc).__name__;continue
                finally:
                    if reader is not None:reader.close()
                    if context is not None:context.close()
                    if runtime is not None:runtime.close()
                    write_summary()
                context=runtime=drafter=None
                try:
                    comment='谢谢分享Mate90的真实体验，感谢关注与支持 😊📱'
                    screenshot=raw/(note+'-draft.png')
                    context,runtime,drafter=session(browser,f'draft_{index}',url,
                        '在当前笔记下的评论框编辑以下精确文字：'+comment+'。不要点击发送，不点赞收藏关注，不提交任何评论。草稿准备好后stop，由程序截图并立即清空取消。',
                        draft=DraftSpec(field,comment,str(screenshot)))
                    result=drafter.run()
                    cancelled=any(event.get('event')=='draft_cancelled' for event in drafter.events)
                    item.update(comment=comment,screenshot=str(screenshot.relative_to(args.out)),cancelled=cancelled)
                    (raw/f'draft-{note}.json').write_text(json.dumps({'checkpoint':drafter.checkpoint(),'events':drafter.events},ensure_ascii=False,indent=2),encoding='utf-8')
                    if result.complete and screenshot.is_file() and cancelled:
                        item['status']='completed';completed+=1
                    else:item['status']='draft_incomplete'
                except Exception as exc:
                    item['status']='draft_failed';item['error_type']=type(exc).__name__
                finally:
                    if drafter is not None:drafter.close()
                    if context is not None:context.close()
                    if runtime is not None:runtime.close()
                    write_summary()
                print(json.dumps({'inspected':len(ledger),'completed':completed,'target':args.target}),flush=True)
        except Exception as exc:
            blockers.append(type(exc).__name__)
        finally:
            browser.close();summary=write_summary()
    print(json.dumps({'completed':completed,'target':args.target,'blockers':blockers}),flush=True)
    return 0 if summary['status']=='complete' else 1


if __name__=='__main__':raise SystemExit(main())
