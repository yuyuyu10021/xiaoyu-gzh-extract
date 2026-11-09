---
name: xiaoyu-gzh-extract
description: |
  小鱼公众号情报库（小鱼改良版 v1.1）：公众号文章「采集 → 全文 → 知识库精析 → 离线情报工作台」一站式，
  **引擎已并入、文件夹自包含可直接打包分发**。双数据源：TikHub API（关键词搜索/同号列表/单篇详情/互动数据，
  现役主力）+ 内置知识库引擎（fork 自 wechat-digest-skill，MIT 已授权，sha256+tempfile 两处合规加固）。
  小鱼定制皮肤（青碧绿 · 「小鱼公众号情报库」）。
  触发词：公众号提取、公众号采集、搜公众号文章、同号文章、公众号情报库、工作台更新、小鱼情报库。
version: 1.1.0
name_zh: 小鱼-公众号提取
updated: 2026-10-27
---

# 小鱼-公众号提取（小鱼改良版 v1.1）

> 「我要哪个号的情报 → 采回来 → 拆好 → 打开情报库就能看」。本件是小鱼实验室 02-小鱼制造 的改良版：
> v1.0 引擎外呼原版；**v1.1 起引擎已并入本件（用户授权 fork），文件夹自包含，可直接打包分发**。

## 架构（全在本文件夹内，自包含）

| 件 | 说明 |
|:--|:--|
| `kb.py` / `render_html.py` | 知识库引擎+渲染器，fork 自原版（MIT 已授权）。与原版的差异仅三处合规加固：sha256 散列、tempfile 原子写、品牌串——存储/合并/检索逻辑逐行一致 |
| `assets/digest_template.html` | 小鱼皮肤：品牌「小鱼 · 公众号情报库」+ 印章「鱼」+ 青碧绿主题（fork 自原版模板，JS 零改动） |
| `wechat_collect_client.py` | 数据客户端：TikHub/RedFox 双供应商，六子命令，key 走 credentials.json |
| `output/knowledge_base.json` | 本件知识库（当前主库仍在 `03-产出\wechat-digest-skill\`，两库同构可合并） |
| `credentials.json` | 实际凭证（敏感件：只留本地，永不提交/外发） |

## 数据源 A：TikHub API（现役主力）

```bash
python wechat_collect_client.py check                              # 凭证在位检查（免费）
python wechat_collect_client.py search "关键词"                     # ① 关键词搜索（微信搜一搜）
python wechat_collect_client.py articles gh_xxxxxxxx                # ② 同号文章列表
python wechat_collect_client.py detail "<带sn的链接>"               # ③ 单篇全文（sn 从①②结果取）
python wechat_collect_client.py stats "<带chksm的链接>"             # ④ 互动数据（仅评论数可用）
```

硬规矩（学费已交，见 HOW-20261027-04）：
- **detail/stats 必须用带 sn（+chksm）的完整链接**——从 search/articles 返回的 doc_url/contentUrl 原样程序化取，**禁止人肉拷贝拼接**（截断+编造=无效计费）
- **sn 的正解 = 拿标题跑一次 search**，本地 curl 解短链必被微信拦
- 阅读数：stats 端点拿不到（unavailable），用 search 结果卡的「阅读 N」tag 替代
- 出参全 stdout，调用方自行落 JSON；产出归 `03-产出/小鱼-公众号提取/`

## 数据源 B：内置知识库引擎（免费路径）

```bash
python kb.py --kb <知识库.json> ingest <articles.json>               # 入库（去重合并）
python kb.py --kb <知识库.json> stats                                # 统计
python kb.py --kb <知识库.json> list --unanalyzed --content --json   # 取待分析批次
python kb.py --kb <知识库.json> apply --file <batch.json>            # agent 写回五段式
```

原版 `wechat_collector.py`（公众号后台 Cookie+Token 的 collect 路径）**未并入**：需个人订阅号凭证且有 200013 绑账号封禁风险，要用去原版目录跑（`01-外部原版\wechat-digest-skill\`）。

## 标准工作流（一次完整采集）

1. **搜/选**：`search 关键词` 或 `articles gh_xxx` 挑文章 → 拿到带 sn 的链接
2. **抓全文**：逐篇 `detail` → 存 `03-产出/小鱼-公众号提取/detail-*.json`
3. **转格式**：按映射转 articles 数组（content_text→content、author→account、sn→id、扫 mmbiz 图≤20 张）；**转换用 python -c 内联**（bash 单引号包裹、代码零单引号、字面量路径——Mimosa 闸实测，见 HOW-20261027-01 复现追加）
4. **入库**：`kb.py ingest` → 主题 `topic-upsert` → agent 读全文做**五段式精析**（summary/viewpoints/data/tags/audience，不复读原文、数据带数字）→ `apply` 批量写回 + crossRefs 互链
5. **出工作台**（小鱼皮肤，本件渲染器自动用自己的模板）：

```bash
python render_html.py --kb <知识库.json> --out <输出digest.html>
```

6. **看**：`python kb.py serve --kb <知识库.json>` 起本地服务（收藏夹自动存回），或双击 digest.html

## 小鱼皮肤说明

- 品牌：印章「鱼」+ 「小鱼 **公众号情报库**」+ meta 描述
- 配色：纸面 #f1f4ea / 主色青碧 #0e8a6d / 墨绿黑 #16201b（原版朱砂红 #d8401f 系全量替换，含图谱 KB_BASE_COLORS）
- 皮肤文件 fork 自原版模板（55KB），改动仅 brand/meta/三处色值，JS 逻辑零改动——原版模板升级时可 diff 快速重放

## 红线

- 凭证零入码；正文链接白名单仅 mp.weixin.qq.com
- 与原版（01-外部原版）的差异仅限 README 改动清单所列三项加固+皮肤，额外改动先补清单
- 产出不进本件 output/ 以外的位置；正式写作素材走 LINE-01 进收集箱
