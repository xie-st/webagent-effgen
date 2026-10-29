"""Environment integration checks using scripted browser operations, no LLM."""
import asyncio
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
from runner import BrowserAdapter
from sandbox import Fixture, LocalServer
from report_paths import new_environment_result

ROOT = Path(__file__).resolve().parent


def profile_driver(*, task, observation, history, action_history, state):
    """Scripted fixture driver ONLY for runner/log/trace integration testing."""
    import re
    step = state.get('step', 0)
    state['step'] = step + 1
    if step == 0:
        element_id = re.search(r'\[(\d+)\] input: value', observation['text'])[1]
        action = f'type [{element_id}] [{task.split()[-1]}]'
    elif step == 1:
        element_id = re.search(r'\[(\d+)\] button: 保存简介', observation['text'])[1]
        action = f'click [{element_id}]'
    else:
        action = 'stop'
    return {'action': action, 'model_calls': 0, 'tokens': 0}


async def parallel_check(url):
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        context = await browser.new_context()
        a, b = await context.new_page(), await context.new_page()
        started = time.perf_counter()
        await a.goto(url + '/slow/a')
        await b.goto(url + '/slow/b')
        serial = time.perf_counter() - started
        started = time.perf_counter()
        await asyncio.gather(a.goto(url + '/slow/a'), b.goto(url + '/slow/b'))
        parallel = time.perf_counter() - started
        assert '结果 a-' in await a.inner_text('body')
        assert '结果 b-' in await b.inner_text('body')
        await browser.close()
        return {'serial_seconds': serial, 'parallel_seconds': parallel,
                'speedup': serial / parallel, 'measurement': 'synthetic browser IO only'}


def main():
    results = []
    fixture = Fixture()
    with LocalServer(fixture) as server:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.goto(server.url + '/forum')
            adapter = BrowserAdapter(page, server.url)
            observation = adapter.observe()
            assert '个人简介' in observation['text']
            field_id = next(key for key, value in adapter.elements.items()
                            if value.get_attribute('name') == 'value')
            adapter.act(f'type [{field_id}] [开发者-{fixture.token}]')
            try:
                adapter.act(f'type [{field_id}] [stale]')
                raise AssertionError('stale ID accepted')
            except ValueError:
                pass
            adapter.observe()
            button_id = next(key for key, value in adapter.elements.items()
                             if value.inner_text() == '保存简介')
            adapter.act(f'click [{button_id}]')
            assert fixture.grade('profile')
            assert f'开发者-{fixture.token}' in page.inner_text('body')
            results.extend(['single_action_profile', 'stale_id_rejected'])
            for task, label, button, text in [
                ('post', '帖子标题', '发表帖子', f'并行调度-{fixture.token}'),
                ('reply', '回复内容', '发送回复', f'已确认-{fixture.token}')]:
                page.get_by_label(label).fill(text)
                page.get_by_role('button', name=button, exact=True).click()
                assert fixture.grade(task)
                assert text in page.inner_text('body')
                results.append(task)
            for task, button in [('subscribe', '订阅技术版块'), ('vote', '点赞技术帖子')]:
                page.get_by_role('button', name=button, exact=True).click()
                assert fixture.grade(task)
                results.append(task)
            page.goto(server.url + '/shop')
            page.get_by_role('button', name='键盘加入购物车').click()
            assert fixture.grade('cart')
            page.get_by_role('button', name='提交订单').click()
            assert fixture.grade('checkout')
            results.extend(['cart', 'checkout'])
            fixture.rate_once = True
            with page.expect_response(lambda r: r.status == 429) as response:
                page.get_by_role('button', name='提交订单').click()
            assert response.value.headers['retry-after'] == '1'
            # A scheduler must obey Retry-After before retrying.
            time.sleep(1)
            page.goto(server.url + '/shop')
            page.get_by_role('button', name='提交订单').click()
            assert '已提交' in page.inner_text('body')
            results.append('429_then_retry')
            fixture.require_login = True
            page.goto(server.url + '/forum')
            assert page.url.endswith('/login')
            page.get_by_role('button', name='用户完成登录').click()
            assert page.url.endswith('/forum')
            assert fixture.bio == f'开发者-{fixture.token}'
            results.append('login_resume_simulated_by_test')
            fixture.delay = 0.35
            started = time.perf_counter()
            page.get_by_role('button', name='订阅技术版块').click()
            assert time.perf_counter() - started >= 0.35
            results.append('delayed_write')
            browser.close()
        parallel = asyncio.run(parallel_check(server.url))
    report = {'kind': 'environment_smoke_not_agent_benchmark', 'model_calls': 0,
              'checks': results, 'all_passed': True, 'parallel_io': parallel}
    result_dir = new_environment_result()
    (result_dir / 'smoke.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    (result_dir / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(result_dir)


if __name__ == '__main__':
    main()
