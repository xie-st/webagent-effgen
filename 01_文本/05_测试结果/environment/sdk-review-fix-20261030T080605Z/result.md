# SDK独立复核意见修正：主线程验收通过

独立DSH Flash `hub-21-mvuiohia`只读固定候选9fc1716，未发现纯文本兼容阻塞，提出目录切换缓存和stop后截图事件两项问题。主线程接受并修正：同帧切换证据目录时复制已验证缓存，不重复下载；读取缓存再次校验完整性；run_end后拒绝取图。

使用固定M2候选ee4d380的Git导出副本，仅覆盖主线程拥有的screenshots.py、my_agent.py、test_screenshot.py后亲跑三个反例，3/3通过。源码指纹见[source-sha256.json](source-sha256.json)，原始输出见[test-output.txt](test-output.txt)。与并行中的新增任务覆盖修正不混用工作树。
