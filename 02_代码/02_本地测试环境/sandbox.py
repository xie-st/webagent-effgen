"""Loopback-only practice websites. Synthetic fixtures, not official benchmarks."""
import argparse
import threading
import time
from dataclasses import dataclass, field
from uuid import uuid4

from flask import Flask, abort, redirect, render_template_string, request
from werkzeug.serving import make_server

from m2_faults import FaultPlan, SCALAR_OPERATIONS


@dataclass
class Fixture:
    token: str = field(default_factory=lambda: uuid4().hex[:8])
    bio: str = ""
    title: str = ""
    reply: str = ""
    subscribed: bool = False
    votes: int = 0
    cart: list = field(default_factory=list)
    ordered: bool = False
    orders: list = field(default_factory=list)
    delay: float = 0
    rate_once: bool = False
    require_login: bool = False
    authenticated: bool = False
    fault_plan: FaultPlan = field(default_factory=FaultPlan)
    write_counts: dict = field(default_factory=dict)
    attempt_counts: dict = field(default_factory=dict)
    write_events: list = field(default_factory=list)
    lock: object = field(default_factory=threading.RLock, repr=False)

    def __post_init__(self):
        self.fault_plan.apply_seed(self)

    def task(self, name):
        from m2_grading import task_prompt
        return task_prompt(name, self.token)

    def grade(self, name):
        from m2_grading import grade
        return grade(self, name)["passed"]

    def grade_report(self, name, actor_claims=None):
        from m2_grading import grade
        return grade(self, name, actor_claims=actor_claims)

    def operation_state(self, operation):
        values = {"profile": lambda: self.bio,
                  "post": lambda: self.title,
                  "reply": lambda: self.reply,
                  "subscribe": lambda: bool(self.subscribed),
                  "vote": lambda: int(self.votes),
                  "cart": lambda: list(self.cart),
                  "checkout": lambda: list(self.orders)}
        if operation not in values:
            raise KeyError(operation)
        return values[operation]()

    def record_attempt(self, operation):
        self.attempt_counts[operation] = self.attempt_counts.get(operation, 0) + 1

    def record_write(self, operation, requested, before, after, fault_mode, stored=None):
        self.write_counts[operation] = self.write_counts.get(operation, 0) + 1
        self.write_events.append({
            "operation": operation,
            "requested": requested,
            "stored": after if stored is None else stored,
            "before": before,
            "after": after,
            "fault": fault_mode,
            "committed": True,
        })

    def business_snapshot(self):
        return {
            "token": self.token,
            "bio": self.bio,
            "title": self.title,
            "reply": self.reply,
            "subscribed": bool(self.subscribed),
            "votes": int(self.votes),
            "cart": list(self.cart),
            "ordered": bool(self.ordered),
            "orders": list(self.orders),
            "write_counts": dict(self.write_counts),
            "attempt_counts": dict(self.attempt_counts),
            "write_events": [dict(event) for event in self.write_events],
            "faults": self.fault_plan.to_dict(),
        }


LAYOUT = """<!doctype html><html lang="zh"><meta charset="utf-8">
<title>WebAgent 本地练习站</title>
<style>body{font:18px system-ui;max-width:900px;margin:40px auto;padding:20px}
nav a{margin-right:24px}input,button{font:inherit;margin:10px;padding:8px}section{margin:30px 0}</style>
<nav><a href="/forum">论坛</a><a href="/shop">电商</a><a href="/slow/a">资料 A</a><a href="/slow/b">资料 B</a></nav>
{{ body|safe }}</html>"""

FIELD_NAMES = {"profile": "bio", "post": "title", "reply": "reply"}


def _home_for(operation):
    return "/shop" if operation in ("cart", "checkout") else "/forum"


def _missing_body(operation):
    return {
        "profile": "<h1>用户资料不存在</h1><p>目标用户资料缺项，个人简介未保存。</p>",
        "post": "<h1>目标版块不存在</h1><p>目标版块缺项，帖子未发表。</p>",
        "reply": "<h1>目标帖子不存在</h1><p>目标帖子缺项，回复未发送。</p>",
        "subscribe": "<h1>目标版块不存在</h1><p>技术版块缺项，未订阅。</p>",
        "vote": "<h1>目标帖子不存在</h1><p>技术帖子缺项，未点赞。</p>",
        "cart": "<h1>商品不存在</h1><p>目标商品“键盘”缺项，未加入购物车。</p>",
        "checkout": "<h1>无法提交订单</h1><p>购物车或目标商品缺项，未生成订单。</p>",
    }[operation]


LOST_RECEIPT_BODY = """<h1>写入结果未知</h1>
<p>服务端可能已经提交，但回执丢失。请先查询当前状态，再决定是否重试。</p>
<p>未确认前不得重复写入。</p>"""


def create_app(fixture):
    app = Flask(__name__)

    def page(body, **values):
        return render_template_string(LAYOUT, body=render_template_string(body, f=fixture, **values))

    @app.before_request
    def perturb():
        if request.path in ("/login", "/favicon.ico"):
            return None
        if fixture.require_login and not fixture.authenticated:
            return redirect("/login")
        if request.method == "POST":
            with fixture.lock:
                if fixture.rate_once:
                    fixture.rate_once = False
                    return "请求过于频繁，请稍后重试", 429, {"Retry-After": "1"}
            if fixture.delay:
                time.sleep(fixture.delay)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            fixture.authenticated = True
            return redirect("/forum")
        return page('<h1>需要人工登录</h1><form method="post"><button>用户完成登录</button></form>')

    @app.route("/")
    def home():
        return redirect("/forum")

    @app.route("/forum")
    def forum():
        return page('''<h1>技术论坛</h1><p>个人简介：{{ f.bio }}</p>
        <form method="post" action="/write/profile"><label>个人简介<input name="value"></label><button>保存简介</button></form>
        <p>帖子：{{ f.title }}</p><form method="post" action="/write/post"><label>帖子标题<input name="value"></label><button>发表帖子</button></form>
        <p>回复：{{ f.reply }}</p><form method="post" action="/write/reply"><label>回复内容<input name="value"></label><button>发送回复</button></form>
        <p>订阅状态：{{ '已订阅' if f.subscribed else '未订阅' }}</p><form method="post" action="/write/subscribe"><button>订阅技术版块</button></form>
        <p>点赞数：{{ f.votes }}</p><form method="post" action="/write/vote"><button>点赞技术帖子</button></form>''')

    @app.route("/write/<operation>", methods=["POST"])
    def write(operation):
        if operation not in ("profile", "post", "reply", "subscribe", "vote", "cart", "checkout"):
            abort(404)
        with fixture.lock:
            fixture.record_attempt(operation)
            fault = fixture.fault_plan.take(operation)
            mode = fault["mode"] if fault else "normal"
            requested = request.form.get("value", "")
            value = requested

            if mode == "no_effect_success":
                # Looks exactly like a successful redirect, but no state changes.
                return redirect(_home_for(operation))
            if mode == "missing_target":
                return page(_missing_body(operation))

            if mode == "append_value":
                if operation not in SCALAR_OPERATIONS:
                    abort(400)
                value = str(getattr(fixture, FIELD_NAMES[operation])) + value

            before = fixture.operation_state(operation)
            if operation in FIELD_NAMES:
                setattr(fixture, FIELD_NAMES[operation], value)
            elif operation == "subscribe":
                fixture.subscribed = True
            elif operation == "vote":
                fixture.votes += 1
            elif operation == "cart":
                fixture.cart.append("键盘")
            elif operation == "checkout":
                if fixture.cart:
                    fixture.orders.append(f"order-{len(fixture.orders) + 1}-{uuid4().hex[:6]}")
                    fixture.ordered = True
                else:
                    fixture.ordered = False
            after = fixture.operation_state(operation)

            # Checkout with an empty cart is a failed attempt, not a committed
            # business write.  All other operations commit one write event.
            if operation == "checkout" and not after:
                return redirect(_home_for(operation))
            fixture.record_write(operation, requested, before, after, mode, stored=value)
            if mode == "commit_lost_receipt":
                return page(LOST_RECEIPT_BODY), 503
        return redirect(_home_for(operation))

    @app.route("/shop")
    def shop():
        return page('''<h1>电商商城</h1><section><h2>键盘</h2><p>价格：199 元</p>
        <form method="post" action="/cart"><button>键盘加入购物车</button></form></section>
        <p>购物车：{{ f.cart|join('、') }}</p><p>订单：{{ '已提交' if f.ordered else '未提交' }}（{{ f.orders|length }} 个）</p>
        <form method="post" action="/checkout"><button>提交订单</button></form>''')

    @app.route("/cart", methods=["POST"])
    def cart():
        with fixture.lock:
            fixture.record_attempt("cart")
            fault = fixture.fault_plan.take("cart")
            mode = fault["mode"] if fault else "normal"
            if mode == "no_effect_success":
                return redirect("/shop")
            if mode == "missing_target":
                return page(_missing_body("cart"))
            before = fixture.operation_state("cart")
            fixture.cart.append("键盘")
            after = fixture.operation_state("cart")
            fixture.record_write("cart", "键盘", before, after, mode)
            if mode == "commit_lost_receipt":
                return page(LOST_RECEIPT_BODY), 503
        return redirect("/shop")

    @app.route("/checkout", methods=["POST"])
    def checkout():
        with fixture.lock:
            fixture.record_attempt("checkout")
            fault = fixture.fault_plan.take("checkout")
            mode = fault["mode"] if fault else "normal"
            if mode == "no_effect_success":
                return redirect("/shop")
            if mode == "missing_target":
                return page(_missing_body("checkout"))
            before = fixture.operation_state("checkout")
            if fixture.cart:
                fixture.orders.append(f"order-{len(fixture.orders) + 1}-{uuid4().hex[:6]}")
                fixture.ordered = True
            else:
                fixture.ordered = False
            after = fixture.operation_state("checkout")
            if not after:
                return redirect("/shop")
            fixture.record_write("checkout", "提交订单", before, after, mode)
            if mode == "commit_lost_receipt":
                return page(LOST_RECEIPT_BODY), 503
        return redirect("/shop")

    @app.route("/slow/<name>")
    def slow(name):
        time.sleep(0.8)
        return page('<h1>资料 {{ name }}</h1><p>结果 {{ name }}-{{ f.token }}</p>', name=name)

    return app


# Chromium refuses a few otherwise valid TCP ports (ERR_UNSAFE_PORT).
# Ephemeral bindings can land on one, so retry before handing the URL to
# Playwright.  The list covers Chromium's restricted ports that fall inside
# the ephemeral range used on this machine.
UNSAFE_BROWSER_PORTS = frozenset({
    1719, 1720, 1723, 2049, 3659, 4045, 5060, 5061, 6000, 6566,
    6665, 6666, 6667, 6668, 6669, 6697, 10080,
})


class LocalServer:
    def __init__(self, fixture=None, port=0):
        self.fixture = fixture or Fixture()
        app = create_app(self.fixture)
        for _ in range(20):
            server = make_server("127.0.0.1", port, app, threaded=True)
            if server.server_port not in UNSAFE_BROWSER_PORTS:
                break
            server.server_close()
        else:
            raise RuntimeError("could not bind a browser-safe local port")
        self.server = server
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--scenario", choices=["normal", "slow", "rate", "login"], default="normal")
    args = parser.parse_args()
    fixture = Fixture(delay=0.8 if args.scenario == "slow" else 0,
                      rate_once=args.scenario == "rate", require_login=args.scenario == "login")
    with LocalServer(fixture, args.port) as server:
        print(server.url, flush=True)
        for name in ("profile", "post", "reply", "subscribe", "vote", "cart", "checkout"):
            print(name, fixture.task(name), flush=True)
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass
