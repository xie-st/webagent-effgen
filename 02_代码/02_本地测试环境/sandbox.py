"""Loopback-only practice websites. Synthetic fixtures, not official benchmarks."""
import argparse
import threading
import time
from dataclasses import dataclass, field
from uuid import uuid4

from flask import Flask, abort, redirect, render_template_string, request
from werkzeug.serving import make_server


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
    delay: float = 0
    rate_once: bool = False
    require_login: bool = False
    authenticated: bool = False
    lock: object = field(default_factory=threading.RLock, repr=False)

    def task(self, name):
        values = {"profile": f"把个人简介改为 开发者-{self.token}",
                  "post": f"发表标题为 并行调度-{self.token} 的帖子",
                  "reply": f"回复内容为 已确认-{self.token}",
                  "subscribe": "订阅技术版块", "vote": "点赞技术帖子一次",
                  "cart": "把键盘加入购物车", "checkout": "购买键盘并提交订单"}
        return values[name]

    def grade(self, name):
        return {"profile": self.bio == f"开发者-{self.token}",
                "post": self.title == f"并行调度-{self.token}",
                "reply": self.reply == f"已确认-{self.token}",
                "subscribe": self.subscribed, "vote": self.votes == 1,
                "cart": "键盘" in self.cart,
                "checkout": self.ordered and "键盘" in self.cart}[name]


LAYOUT = """<!doctype html><html lang="zh"><meta charset="utf-8">
<title>WebAgent 本地练习站</title>
<style>body{font:18px system-ui;max-width:900px;margin:40px auto;padding:20px}
nav a{margin-right:24px}input,button{font:inherit;margin:10px;padding:8px}section{margin:30px 0}</style>
<nav><a href="/forum">论坛</a><a href="/shop">电商</a><a href="/slow/a">资料 A</a><a href="/slow/b">资料 B</a></nav>
{{ body|safe }}</html>"""


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
        with fixture.lock:
            if operation in ("profile", "post", "reply"):
                setattr(fixture, {"profile": "bio", "post": "title", "reply": "reply"}[operation], request.form.get("value", ""))
            elif operation == "subscribe":
                fixture.subscribed = True
            elif operation == "vote":
                fixture.votes += 1
            else:
                abort(404)
        return redirect("/forum")

    @app.route("/shop")
    def shop():
        return page('''<h1>电商商城</h1><section><h2>键盘</h2><p>价格：199 元</p>
        <form method="post" action="/cart"><button>键盘加入购物车</button></form></section>
        <p>购物车：{{ f.cart|join('、') }}</p><p>订单：{{ '已提交' if f.ordered else '未提交' }}</p>
        <form method="post" action="/checkout"><button>提交订单</button></form>''')

    @app.route("/cart", methods=["POST"])
    def cart():
        with fixture.lock:
            fixture.cart.append("键盘")
        return redirect("/shop")

    @app.route("/checkout", methods=["POST"])
    def checkout():
        with fixture.lock:
            fixture.ordered = bool(fixture.cart)
        return redirect("/shop")

    @app.route("/slow/<name>")
    def slow(name):
        time.sleep(0.8)
        return page('<h1>资料 {{ name }}</h1><p>结果 {{ name }}-{{ f.token }}</p>', name=name)

    return app


class LocalServer:
    def __init__(self, fixture=None, port=0):
        self.fixture = fixture or Fixture()
        self.server = make_server("127.0.0.1", port, create_app(self.fixture), threaded=True)
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
