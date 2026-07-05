#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen-manifest.py — 扫描 reports/ + 更新 index.html 内嵌数据
用法: python gen-manifest.py

v2 新增字段:
  - belief: buy|hold|reduce|avoid|compare
  - beliefLabel: 显示用标签
  - evidence: {s, a, b} 各等级证据数量
  - too_late: bool 是否触发太晚检测
  - sector: 所属板块
  - date: 报告日期

v3 新增字段 (链捕手 × AI Berkshire 双验证):
  - berkshire_validated: 是否经过 AI Berkshire 深度验证
  - buffett_score: 巴菲特护城河评分 (0-10)
  - munger_score: 芒格逆向测试评分 (0-10)
  - duan_score: 段永平商业模式评分 (0-10)
  - lilu_score: 李录文明趋势评分 (0-10)
  - valuation_range: PE 估值区间描述
  - composite_conviction: 联合确信度
"""

import os, json, re, glob

HERE = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(HERE, "reports")
INDEX_PATH = os.path.join(HERE, "index.html")
MANIFEST_PATH = os.path.join(HERE, "reports-manifest.json")

# ──────────────────────────────────────────────
# 报告元数据 (v3: 支持双验证扩展字段)
# 向后兼容: 缺少新字段 = 纯链捕手报告
# ──────────────────────────────────────────────
REPORT_META = {
    "三安光电_链捕手分析": {
        "code": "600703.SH", "name": "三安光电",
        "desc": "国内唯一全品类化合物半导体IDM · SiC长单70亿 · 意法半导体合资32亿美元 · Mini/Micro LED全球龙头",
        "tags": "三安光电 SiC 碳化硅 化合物半导体 氮化镓 第三代半导体 国产芯片 LED MiniLED 汽车芯片",
        "sector": "半导体",
        "belief": "hold", "beliefLabel": "🟡 观望",
        "evidence": {"s": 5, "a": 3, "b": 2},
        "too_late": False,
        "kpis": [{"n":"840 亿","l":"市值"},{"n":"‑212×","l":"PE","c":"r"},{"n":"70 亿","l":"SiC长单","c":"o"},{"n":"意法合资","l":"32亿美元"}],
        "date": "2026-06-29",
        # Berkshire 双验证扩展字段 (v3)
        "berkshire_validated": False,
        "buffett_score": None, "munger_score": None,
        "duan_score": None, "lilu_score": None,
        "valuation_range": None,
        "composite_conviction": None,
    },
    "厦门钨业_链捕手分析": {
        "code": "600549.SH", "name": "厦门钨业",
        "desc": "钨全产业链龙头 · '反向卡脖子'战略资源 · 半导体钨靶材(台积电认证) · 锂电正极全球第一",
        "tags": "钨 小金属 战略资源 稀土 半导体 靶材 锂电池 军工 出口管制",
        "sector": "有色金属",
        "belief": "hold", "beliefLabel": "🟡 观望",
        "evidence": {"s": 3, "a": 4, "b": 2},
        "too_late": False,
        "kpis": [{"n":"1,331 亿","l":"市值"},{"n":"0.22","l":"PEG","c":"g"},{"n":"+189%","l":"Q1净利增速","c":"g"},{"n":"⚔️","l":"战略资源"}],
        "date": "2026-06-29",
        "berkshire_validated": False,
        "buffett_score": None, "munger_score": None,
        "duan_score": None, "lilu_score": None,
        "valuation_range": None,
        "composite_conviction": None,
    },
    "双环传动_链捕手分析": {
        "code": "002472.SZ", "name": "双环传动",
        "desc": "国产 RV 减速器龙头 · 新能源车齿轮龙头 · 机器人关节核心 · 但利润增速仅+2.9% PEG=7.72",
        "tags": "双环传动 减速器 RV减速器 机器人 新能源车 齿轮 精密传动 人形机器人",
        "sector": "机器人",
        "belief": "hold", "beliefLabel": "🟡 观望",
        "evidence": {"s": 2, "a": 3, "b": 4},
        "too_late": True,
        "kpis": [{"n":"520 亿","l":"市值"},{"n":"27.8×","l":"PE"},{"n":"7.72","l":"PEG","c":"r"},{"n":"+2.9%","l":"Q1利润增速"}],
        "date": "2026-06-29",
        "berkshire_validated": False,
        "buffett_score": None, "munger_score": None,
        "duan_score": None, "lilu_score": None,
        "valuation_range": None,
        "composite_conviction": None,
    },
    "天赐材料_链捕手_v3": {
        "code": "002709.SZ", "name": "天赐材料",
        "desc": "全球电解液龙头 · PEG 0.04 · 三大新催化（宁德时代业绩 + AI 储能 + G5 电子氢氟酸芯片材料）",
        "tags": "电池 电解液 锂电 储能 半导体 G5 氢氟酸 固态电池",
        "sector": "锂电",
        "belief": "hold", "beliefLabel": "🟡 观望",
        "evidence": {"s": 4, "a": 3, "b": 1},
        "too_late": False,
        "kpis": [{"n":"1,038 亿","l":"市值"},{"n":"0.04","l":"PEG","c":"g"},{"n":"36.2×","l":"PE"},{"n":"+1017%","l":"盈利增速","c":"g"}],
        "date": "2026-06-29",
        "berkshire_validated": False,
        "buffett_score": None, "munger_score": None,
        "duan_score": None, "lilu_score": None,
        "valuation_range": None,
        "composite_conviction": None,
    },
    "巨化股份_链捕手分析": {
        "code": "600160.SH", "name": "巨化股份",
        "desc": "氟化工全链龙头 · 半导体材料隐形冠军 · 中巨芯(G5 级电氢) + 国家大基金 + AI 液冷",
        "tags": "氟化工 制冷剂 半导体 G5 氢氟酸 芯片 电子气体 AI液冷 大基金",
        "sector": "化工",
        "belief": "hold", "beliefLabel": "🟡 观望",
        "evidence": {"s": 3, "a": 4, "b": 2},
        "too_late": False,
        "kpis": [{"n":"1,452 亿","l":"市值"},{"n":"35.0×","l":"PE"},{"n":"+45.9%","l":"Q1净利增速","c":"g"},{"n":"G5 级","l":"电子氢氟酸"}],
        "date": "2026-06-29",
        "berkshire_validated": False,
        "buffett_score": None, "munger_score": None,
        "duan_score": None, "lilu_score": None,
        "valuation_range": None,
        "composite_conviction": None,
    },
    "浪潮信息_链捕手分析": {
        "code": "000977.SZ", "name": "浪潮信息",
        "desc": "AI 服务器龙头 · 订单排至 2027 · 'ALL in 液冷' · 字节跳动核心供应商",
        "tags": "AI服务器 算力 液冷 数据中心 信创 字节跳动 英伟达",
        "sector": "AI算力",
        "belief": "hold", "beliefLabel": "🟡 观望",
        "evidence": {"s": 3, "a": 3, "b": 3},
        "too_late": False,
        "kpis": [{"n":"967 亿","l":"市值"},{"n":"37.8×","l":"PE"},{"n":"+43.3%","l":"营收增速","c":"g"},{"n":"‑24.3%","l":"Q1营收","c":"r"}],
        "date": "2026-06-29",
        "berkshire_validated": False,
        "buffett_score": None, "munger_score": None,
        "duan_score": None, "lilu_score": None,
        "valuation_range": None,
        "composite_conviction": None,
    },
    "氟化工_多氟多_链捕手": {
        "code": "002407.SZ", "name": "氟化工 · 多氟多",
        "desc": "多氟多为核心标的 · 六氟磷酸锂+台积电G5氢氟酸+新国标7月实施+AI液冷 · 三重结构性需求爆发",
        "tags": "氟化工 多氟多 六氟磷酸锂 台积电 半导体 氢氟酸 AI液冷 新国标",
        "sector": "化工",
        "belief": "hold", "beliefLabel": "🟡 观望",
        "evidence": {"s": 3, "a": 3, "b": 2},
        "too_late": False,
        "kpis": [{"n":"21.02","l":"现价"},{"n":"+480%","l":"Q1净利增速","c":"g"},{"n":"‑49.9%","l":"距高点","c":"r"},{"n":"台积电","l":"G5氢氟酸","c":"o"}],
        "date": "2026-06-29",
        "berkshire_validated": False,
        "buffett_score": None, "munger_score": None,
        "duan_score": None, "lilu_score": None,
        "valuation_range": None,
        "composite_conviction": None,
    },
    "锂矿板块_链捕手对比": {
        "code": "板块", "name": "锂矿板块 · 5 大标的横向对比",
        "desc": "碳酸锂 V 型反转 · 赣锋锂业/盐湖股份/天齐锂业/永兴材料/中矿资源 · PEG/PE/增速全景对比",
        "tags": "锂矿 碳酸锂 赣锋锂业 天齐锂业 盐湖股份 永兴材料 能源金属 锂电池",
        "sector": "锂电",
        "belief": "compare", "beliefLabel": "📊 对比",
        "evidence": {"s": 8, "a": 6, "b": 2},
        "too_late": False,
        "kpis": [{"n":"5 只","l":"标的对比"},{"n":"0.07","l":"最低PEG","c":"g"},{"n":"15.2×","l":"最低PE","c":"g"},{"n":"V 型","l":"周期反转"}],
        "date": "2026-06-29",
        "berkshire_validated": False,
        "buffett_score": None, "munger_score": None,
        "duan_score": None, "lilu_score": None,
        "valuation_range": None,
        "composite_conviction": None,
    },
}


def _normalize_meta(fname: str, meta: dict) -> dict:
    """
    规范化 REPORT_META 条目,确保 v3 字段存在。
    向后兼容: 旧条目（无 berkshire_validated 字段）自动填充默认值。
    """
    defaults = {
        "berkshire_validated": False,
        "buffett_score": None, "munger_score": None,
        "duan_score": None, "lilu_score": None,
        "valuation_range": None,
        "composite_conviction": None,
    }
    for k, v in defaults.items():
        if k not in meta:
            meta[k] = v
    return meta


def build_manifest():
    """扫描 reports/ 目录,合并 REPORT_META,生成 manifest 数组"""
    html_files = sorted(glob.glob(os.path.join(REPORTS_DIR, "*.html")))
    manifest = []
    for fp in html_files:
        fname = os.path.splitext(os.path.basename(fp))[0]
        meta = REPORT_META.get(fname)
        if meta:
            meta = _normalize_meta(fname, meta)
            manifest.append({
                "file": f"reports/{os.path.basename(fp)}",
                **meta,
            })
        else:
            print(f"⚠️ 未识别: {fname} — 请在 REPORT_META 中添加")
            manifest.append({
                "file": f"reports/{os.path.basename(fp)}",
                "code": "?", "name": fname, "desc": "自动识别", "tags": fname,
                "sector": "未分类",
                "belief": "hold", "beliefLabel": "🟡 观望",
                "evidence": {"s": 0, "a": 0, "b": 0},
                "too_late": False,
                "kpis": [{"n":"?","l":"报告"}],
                "date": "",
                "berkshire_validated": False,
                "buffett_score": None, "munger_score": None,
                "duan_score": None, "lilu_score": None,
                "valuation_range": None,
                "composite_conviction": None,
            })
    return manifest


def js_string(manifest):
    """把 manifest 转成 JS 数组字符串"""
    return json.dumps(manifest, ensure_ascii=False, indent=None)


def update_index(manifest):
    """替换 index.html 中 `const reports = [...]` 内嵌数据"""
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    js_data = js_string(manifest)
    pattern = r'const reports = \[.*?\];'
    replacement = f'const reports = {js_data};'

    if re.search(pattern, html, re.DOTALL):
        html = re.sub(pattern, replacement, html, flags=re.DOTALL)
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✅ 已更新 index.html（{len(manifest)} 篇报告）")
    else:
        print("❌ 未在 index.html 中找到 `const reports = [...]`，请手动替换")


if __name__ == "__main__":
    manifest = build_manifest()
    # 写入 JSON manifest
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"✅ 已生成 reports-manifest.json")
    # 更新 index.html 内嵌数据
    update_index(manifest)
