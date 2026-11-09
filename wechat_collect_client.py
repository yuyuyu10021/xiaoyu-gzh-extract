#!/usr/bin/env python3
"""小鱼-公众号提取 · 数据客户端 v0.2（2026-10-27 并入小鱼-公众号提取 skill）。
本件为小鱼自制（原「小鱼-公众号采集」客户端并入），非 wechat-digest-skill 原版构件；
原版引擎（kb.py/render_html.py）住在 01-外部原版，本 skill 以 --kb 外指 + 模板替换方式使用。

TikHub + RedFox 双供应商公众号数据客户端（用户只管供 key）。

凭证纪律：key 只从 同目录 credentials.json 或环境变量 TIKHUB_API_KEY / REDFOX_API_KEY 读，
源码零密钥字面量。credentials.json 只留本地，永不提交、永不外发。

供应商现状（2026-10-27 实测）：
  TikHub  https://api.tikhub.io   公众号 API 现役：关键词搜索（微信搜一搜）/账号文章列表/文章详情(H5)/互动数据
  RedFox  https://redfox.hk       公众号广域库两端口需 ¥100 单独开通（key 有效、已预接等开通）

出参一律 stdout JSON（调用方自行落盘），本脚本零文件写入。
"""
import json
import os
import sys
from urllib.parse import urlparse

import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(SCRIPT_DIR, "credentials.json")

TIKHUB_BASE = "https://api.tikhub.io"
REDFOX_BASE = "https://redfox.hk"
# 仅允许的正文链接 host（防 SSRF：article url 一律校验后再发请求）
ALLOWED_ARTICLE_HOSTS = {"mp.weixin.qq.com"}


def load_credentials():
    """凭证优先级：环境变量 > credentials.json。"""
    creds = {"TIKHUB_API_KEY": "", "REDFOX_API_KEY": ""}
    for k in creds:
        creds[k] = os.environ.get(k, "") or creds[k]
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, encoding="utf-8") as f:
                data = json.load(f)
            for k in creds:
                creds[k] = creds[k] or str(data.get(k, "") or "")
        except Exception as e:
            print(f"⚠️  credentials.json 读取失败：{e}", file=sys.stderr)
    return creds


def validate_article_url(url):
    """只放行 https + 白名单 host；拒绝一切内网/环回地址。"""
    p = urlparse(url)
    if p.scheme != "https":
        raise ValueError(f"仅允许 https 链接：{url}")
    if p.hostname in ("localhost", "127.0.0.1", "0.0.0.0") or (p.hostname or "").startswith("192.168.") or (p.hostname or "").startswith("10."):
        raise ValueError(f"拒绝内网/环回地址：{url}")
    if p.hostname not in ALLOWED_ARTICLE_HOSTS:
        raise ValueError(f"host 不在白名单（{ALLOWED_ARTICLE_HOSTS}）：{url}")
    return url


def post_json(url, headers, payload, timeout=60):
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:300]}")
    return resp.json()


# ---------------- TikHub ----------------

def tikhub_headers(creds):
    if not creds["TIKHUB_API_KEY"]:
        raise SystemExit("✗ 缺 TIKHUB_API_KEY（环境变量或 credentials.json）")
    return {"Authorization": f"Bearer {creds['TIKHUB_API_KEY']}", "Content-Type": "application/json"}


def tikhub_search(creds, keyword, business_type="all", sort="default", publish_time="all", offset=0, **_):
    """微信搜一搜综合搜索（关键词→文章/账号等混合结果）。"""
    payload = {"keyword": keyword, "business_type": business_type, "sort": sort,
               "publish_time": publish_time, "offset": offset, "raw": True}
    return post_json(f"{TIKHUB_BASE}/api/v1/wechat_search/v2/fetch_search", tikhub_headers(creds), payload)


def tikhub_account_articles(creds, username, page_size=20, offset=None, **_):
    """公众号文章列表。username=公众号微信号（gh_ 开头）。"""
    payload = {"username": username, "page_size": int(page_size), "raw": True}
    if offset:
        payload["offset"] = offset
    return post_json(f"{TIKHUB_BASE}/api/v1/wechat_mp/v2/fetch_account_articles", tikhub_headers(creds), payload)


def tikhub_article_detail(creds, url, **_):
    """文章详情（H5 版，官方推荐），含正文。url 必须带 sn（search 结果 doc_url 自带）。"""
    validate_article_url(url)
    return post_json(f"{TIKHUB_BASE}/api/v1/wechat_mp/v2/fetch_article_detail_h5",
                     tikhub_headers(creds), {"url": url, "raw": True})


def tikhub_article_stats(creds, url, **_):
    """文章互动数据。url 必须带 chksm 完整形态（search 结果 doc_url 自带）。"""
    validate_article_url(url)
    return post_json(f"{TIKHUB_BASE}/api/v1/wechat_mp/v2/fetch_article_stats_h5",
                     tikhub_headers(creds), {"url": url, "raw": True})


# ---------------- RedFox ----------------

def redfox_headers(creds):
    if not creds["REDFOX_API_KEY"]:
        raise SystemExit("✗ 缺 REDFOX_API_KEY（环境变量或 credentials.json）")
    return {"REDFOX_API_KEY": creds["REDFOX_API_KEY"], "Content-Type": "application/json"}


def redfox_work_list(creds, account=None, wx_id=None, biz_info=None, offset=0, sort_type="0", **_):
    """⚠️ 需 ¥100 单独开通（2026-10-27 实测 code 3210）。账号作品列表：三选一，每页 200。"""
    payload = {"offset": int(offset), "sortType": str(sort_type)}
    if wx_id:
        payload["wxId"] = wx_id
    elif biz_info:
        payload["bizInfo"] = biz_info
    elif account:
        payload["account"] = account
    else:
        raise SystemExit("✗ account / wxId / bizInfo 至少传一个")
    return post_json(f"{REDFOX_BASE}/story/api/gzh/data/queryWorkList", redfox_headers(creds), payload)


def redfox_work_detail(creds, work_uuid, **_):
    """⚠️ 需 ¥100 单独开通。按 workUuid 取作品详情（含正文与互动数）。"""
    return post_json(f"{REDFOX_BASE}/story/api/gzh/data/workDetail", redfox_headers(creds),
                     {"workUuid": work_uuid})


# ---------------- CLI ----------------

COMMANDS = {
    "search":        (tikhub_search, 1, "微信搜一搜关键词搜索（TikHub）：search <关键词> [--business-type article]"),
    "articles":      (tikhub_account_articles, 1, "公众号文章列表（TikHub）：articles <gh_用户名> [--page-size 20]"),
    "detail":        (tikhub_article_detail, 1, "文章详情含正文（TikHub H5 版）：detail <带sn的mp链接>"),
    "stats":         (tikhub_article_stats, 1, "文章互动数据（TikHub）：stats <带chksm的mp链接>"),
    "redfox-list":   (redfox_work_list, 0, "账号作品列表（RedFox ⚠️需开通）：redfox-list --account <微信号>"),
    "redfox-detail": (redfox_work_detail, 1, "作品详情（RedFox ⚠️需开通）：redfox-detail <workUuid>"),
}


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        print("子命令：")
        for name, (_, _, desc) in COMMANDS.items():
            print(f"  {name:14s} {desc}")
        print("  check          校验凭证在位情况（不消耗调用）")
        return 0
    creds = load_credentials()
    cmd = args[0]
    if cmd == "check":
        print(json.dumps({
            "TIKHUB_API_KEY": "在位" if creds["TIKHUB_API_KEY"] else "缺失",
            "REDFOX_API_KEY": "在位" if creds["REDFOX_API_KEY"] else "缺失",
            "credentials_file": CREDENTIALS_FILE,
        }, ensure_ascii=False, indent=2))
        return 0
    if cmd not in COMMANDS:
        print(f"✗ 未知命令 {cmd}，--help 看清单")
        return 1
    fn, npos, _ = COMMANDS[cmd]
    kwargs = {}
    positional = []
    i = 1
    while i < len(args):
        a = args[i]
        if a.startswith("--"):
            key = a[2:].replace("-", "_")
            nxt = args[i + 1] if i + 1 < len(args) else ""
            kwargs[key] = nxt
            i += 2
        else:
            positional.append(a)
            i += 1
    if len(positional) < npos:
        print(f"✗ {cmd} 缺必选位置参数（{npos} 个）")
        return 1
    try:
        result = fn(creds, *positional, **kwargs)
    except (ValueError, RuntimeError, SystemExit) as e:
        print(f"✗ {e}")
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
