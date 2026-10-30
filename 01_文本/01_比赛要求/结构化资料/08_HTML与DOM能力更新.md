# HTML 与原始 DOM 更新

2026-10-30：用户告知平台开放HTML/DOM能力。本机在用户下载目录找到官方ZIP，字节数27176，SHA-256 `ec1a6697656d5e1b6ba328ea4c69601a6c6e82ab9e63f428f23db71afa16feb4`。直接下载端点本轮返回401，因此使用该原始ZIP，不声称重新下载成功。原件与README见[来源目录](../原始资料/2026-10-30_HTML_DOM客户端_ec1a6697/)。

- HTML：`observation.html`给出本次快照的html_id、step、字节数和SHA；在有效Agent回调中使用`browser.get_html(html_id)`下载。它是page.content()快照，未必包含表单实时属性，最大4MiB。
- DOM：按当前README，原始`DOM.getDocument(depth=-1,pierce=True)`结果直接随`observation.dom.root`返回，无需下载。SDK同时保留`get_dom(dom_id)`接口，但本项目优先使用本步已有root，不额外请求。
- DOM节点ID/HTML id均不是AX动作编号。新接口不开放任意JS、CDP操作或选择器执行。历史不重复携带旧DOM；不可复用缺失帧的旧资料。
- 新能力只提供参考，不能单独把草稿、隐藏节点、静态属性当作已保存业务结果。当前接入按需精简资料，动作仍按AX，精确值与未知提交保护继续保留。

当前版本SDK原件与SOURCE已更新；代码层离线验证单独记录，HTML/DOM在线链路尚未实测，不以接口存在替代完成证据。
