# 小鱼-公众号提取（改良版 v1.1）

> 「问题→skill→内容」系列自制件 · 2026-10-27 建 · **v1.1 引擎已并入，文件夹自包含可打包分发**

## 原版出处与协议

- **引擎原版**：GitHub [Jackychen-12/wechat-digest-skill](https://github.com/Jackychen-12/wechat-digest-skill)（81★，**MIT**）——原版可独立安装使用，仓库内有完整安装说明
- **fork 授权**：MIT 协议允许复制/修改/分发（保留版权与许可声明即可）；改良者于 2026-10-27 经原版权利确认后搬入引擎并开放本改良版。本件各文件头均保留原版出处标注，满足 MIT 署名条件
- **改良依据**：改良者个人知识库的「小鱼实验室」机制（fork 到改良区再改，原版留作对照）；对外讲改良型内容时批评对 skill 不对人
- **来源与免责声明**：见本目录《关于本技能的来源与免责声明.md》（转发/上传 GitHub 时请一并保留此文件与 LICENSE）

## v1.0→v1.1 的架构变化

v1.0 曾因安全静态闸拦截（kb.py 动态路径 CLI 过不了 Write 审）采用「引擎外呼原版」的过渡架构；v1.1 用户授权后重新提交，**按闸方修复意见做了三处合规加固后引擎通过审查并入**：

| 文件 | 合规加固（逻辑行为与原版一致） |
|:--|:--|
| `kb.py` | ① id 散列 sha1→sha256（仅影响无 sn 链接的散列 id，sn 主键不受影响）② save_kb 原子写改 tempfile（同目录临时文件 + os.replace）③ 品牌串「墨摘」→「小鱼」 |
| `render_html.py` | ① 输出原子写改 tempfile ② 输出路径 abspath 规范化 ③ 品牌串 |

工作流因此简化：**渲染不再需要 monkey-patch 换模板**（本件渲染器自动用自己的小鱼皮肤），引擎升级不再自动继承原版（本件已独立，升级需手动 diff 重放——改动清单在此，成本可控）。

## 完整改动清单（相对原版）

| 件 | 改动 |
|:--|:--|
| `kb.py` | 三处合规加固（见上表），存储/合并/检索逻辑逐行一致 |
| `render_html.py` | 三处合规加固（见上表），渲染逻辑一致 |
| `assets/digest_template.html` | 品牌「墨摘/摘」→「小鱼/鱼」（title/h1/favicon/seal）+ meta description；配色朱砂红系→青碧绿系（:root 9 变量 + shadow + 图谱 KB_BASE_COLORS）；JS 逻辑零改动 |
| `wechat_collect_client.py` | 小鱼自制（非原版构件）：TikHub/RedFox 双供应商六子命令；detail/stats 注明 sn/chksm 硬要求 |
| `SKILL.md` / `使用说明` | 新写：双数据源工作流 + 说人话触发指南 |
| 未并入 | 原版 `wechat_collector.py`（Cookie+Token collect 路径）：需公众号后台凭证且有 200013 封禁风险，要用去原版目录 |

## 文件清单

```
小鱼-公众号提取/
├── SKILL.md                       # 主文档：架构/双数据源/工作流/红线
├── README.md                      # 本件：出处/协议/改动清单
├── 使用说明-说人话版.md            # 说什么话→触发什么能力
├── kb.py                          # 知识库引擎（fork，sha256+tempfile 加固）
├── render_html.py                 # 工作台渲染器（fork，tempfile 加固，自动用小鱼皮肤）
├── assets/digest_template.html    # 小鱼皮肤（fork 自原版，品牌+配色改造）
├── wechat_collect_client.py       # TikHub/RedFox 客户端
├── credentials.example.json       # 凭证模板
├── credentials.json               # 实际凭证（敏感件：只留本地，永不提交/外发）
└── output/                        # 本件知识库与渲染产物位
```

## 分发说明

文件夹自包含：打包发出前**必须删除 `credentials.json`**（内含真实 API key），并附一份 `credentials.example.json` 让收件人自配 key。核对命令：`ls` 确认无 credentials.json 再压缩。

## 已知边界

- TikHub detail/stats 对缺 sn/chksm 的链接判无效且**仍计费**；阅读数拿不到（用 search 卡「阅读 N」替代）
- TikHub search 端点偶发上游 400（未计费），PlanB=articles 列表端点（见 HOW-20261027-04）
- RedFox 广域库需 ¥100 单独开通（端点已预接，暂未充）
- 与原版的 id 兼容性：sn 主键互通；无 sn 链接的散列 id 因 sha256 与原版不互通（重抓会生成新条目，kb ingest 不会合并，删除旧条目即可）
