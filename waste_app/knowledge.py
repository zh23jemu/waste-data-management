from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WasteKnowledge:
    """垃圾分类知识条目。"""

    name: str
    category: str
    aliases: tuple[str, ...]
    guide: str
    examples: tuple[str, ...]


CATEGORY_LABELS = {
    "recyclable": "可回收物",
    "hazardous": "有害垃圾",
    "kitchen": "厨余垃圾",
    "other": "其他垃圾",
}

CLASS_RATIONALES = {
    "recyclable": "该类物品通常具有再生利用价值，投放前应尽量清洁、压扁或分类整理。",
    "hazardous": "该类物品可能含有有毒有害成分，应投放至有害垃圾收集容器，避免混入普通垃圾。",
    "kitchen": "该类物品以易腐有机物为主，适合进入厨余垃圾处理链路，投放前应沥干水分。",
    "other": "该类物品当前难以回收或不适合进入厨余/有害链路，应投放至其他垃圾容器。",
}

KNOWLEDGE_BASE = [
    WasteKnowledge("塑料瓶", "recyclable", ("饮料瓶", "矿泉水瓶", "PET瓶"), "清空内容物并压扁后投放至可回收物。", ("矿泉水瓶", "饮料瓶")),
    WasteKnowledge("废纸箱", "recyclable", ("纸盒", "快递箱"), "去除胶带和污染物，压平后投放。", ("快递纸箱", "包装盒")),
    WasteKnowledge("玻璃瓶", "recyclable", ("酒瓶", "调料瓶"), "倒空液体，避免破碎伤人，投放至可回收物。", ("啤酒瓶", "酱油瓶")),
    WasteKnowledge("旧衣物", "recyclable", ("衣服", "纺织物"), "干净衣物可回收或捐赠，严重污染时按其他垃圾处理。", ("外套", "裤子")),
    WasteKnowledge("废电池", "hazardous", ("电池", "纽扣电池"), "含重金属或化学物质，应投放有害垃圾。", ("纽扣电池", "充电电池")),
    WasteKnowledge("过期药品", "hazardous", ("药片", "胶囊"), "连同包装投放至有害垃圾，避免随意丢弃。", ("感冒药", "消炎药")),
    WasteKnowledge("灯管", "hazardous", ("荧光灯", "节能灯"), "可能含汞，需轻放至有害垃圾收集点。", ("节能灯管", "荧光灯管")),
    WasteKnowledge("油漆桶", "hazardous", ("涂料桶", "油漆"), "残留油漆属于有害成分，应按有害垃圾处理。", ("油漆桶", "涂料罐")),
    WasteKnowledge("剩饭剩菜", "kitchen", ("饭菜", "厨余"), "沥干水分后投放至厨余垃圾。", ("米饭", "菜叶")),
    WasteKnowledge("果皮", "kitchen", ("水果皮", "香蕉皮"), "属于易腐有机物，应投放厨余垃圾。", ("苹果皮", "橘子皮")),
    WasteKnowledge("茶叶渣", "kitchen", ("茶渣", "咖啡渣"), "滤干液体后作为厨余垃圾投放。", ("茶叶", "咖啡粉")),
    WasteKnowledge("骨头", "kitchen", ("小骨头", "鱼骨"), "小骨头可按厨余处理，大骨头一般按其他垃圾处理。", ("鱼骨", "鸡骨")),
    WasteKnowledge("餐巾纸", "other", ("纸巾", "卫生纸"), "受污染且纤维短，不适合回收，按其他垃圾处理。", ("湿纸巾", "餐巾纸")),
    WasteKnowledge("陶瓷碎片", "other", ("瓷片", "陶瓷"), "无再生回收价值且易伤人，应包裹后投放其他垃圾。", ("碎碗", "瓷杯")),
    WasteKnowledge("烟蒂", "other", ("烟头",), "污染严重且不可回收，投放其他垃圾。", ("烟头", "烟灰")),
    WasteKnowledge("一次性餐盒", "other", ("外卖盒", "餐盒"), "污染严重时按其他垃圾处理；干净塑料餐盒可按可回收物处理。", ("外卖餐盒", "打包盒")),
]

HOT_KEYWORDS = ["电池", "塑料瓶", "过期药品", "果皮", "餐巾纸", "玻璃瓶", "灯管", "剩饭剩菜"]

QUESTIONS = [
    {"id": 1, "type": "choice", "question": "废电池应投放到哪类垃圾？", "options": ["可回收物", "有害垃圾", "厨余垃圾", "其他垃圾"], "answer": "有害垃圾", "explanation": "废电池可能含有重金属或化学物质，应单独投放。"},
    {"id": 2, "type": "choice", "question": "矿泉水瓶清空后通常属于哪类垃圾？", "options": ["可回收物", "有害垃圾", "厨余垃圾", "其他垃圾"], "answer": "可回收物", "explanation": "塑料瓶具有再生利用价值。"},
    {"id": 3, "type": "judge", "question": "过期药品可以直接投入其他垃圾桶。", "options": ["正确", "错误"], "answer": "错误", "explanation": "过期药品属于有害垃圾。"},
    {"id": 4, "type": "choice", "question": "香蕉皮属于哪类垃圾？", "options": ["可回收物", "有害垃圾", "厨余垃圾", "其他垃圾"], "answer": "厨余垃圾", "explanation": "果皮是易腐有机物。"},
    {"id": 5, "type": "judge", "question": "受污染的餐巾纸通常不适合回收。", "options": ["正确", "错误"], "answer": "正确", "explanation": "纸巾纤维短且常被污染。"},
    {"id": 6, "type": "choice", "question": "荧光灯管应投放到哪类垃圾？", "options": ["可回收物", "有害垃圾", "厨余垃圾", "其他垃圾"], "answer": "有害垃圾", "explanation": "灯管可能含汞。"},
    {"id": 7, "type": "choice", "question": "干净废纸箱属于哪类垃圾？", "options": ["可回收物", "有害垃圾", "厨余垃圾", "其他垃圾"], "answer": "可回收物", "explanation": "纸箱可再生利用。"},
    {"id": 8, "type": "judge", "question": "厨余垃圾投放前应尽量沥干水分。", "options": ["正确", "错误"], "answer": "正确", "explanation": "沥干水分有利于后续收运和处理。"},
    {"id": 9, "type": "choice", "question": "陶瓷碎片通常属于哪类垃圾？", "options": ["可回收物", "有害垃圾", "厨余垃圾", "其他垃圾"], "answer": "其他垃圾", "explanation": "陶瓷不属于常规可回收物。"},
    {"id": 10, "type": "choice", "question": "剩饭剩菜应投放到哪类垃圾？", "options": ["可回收物", "有害垃圾", "厨余垃圾", "其他垃圾"], "answer": "厨余垃圾", "explanation": "剩饭剩菜是典型厨余垃圾。"},
    {"id": 11, "type": "judge", "question": "玻璃瓶倒空后可以作为可回收物投放。", "options": ["正确", "错误"], "answer": "正确", "explanation": "玻璃瓶具有回收价值。"},
    {"id": 12, "type": "choice", "question": "油漆桶内仍有残留时应按哪类垃圾处理？", "options": ["可回收物", "有害垃圾", "厨余垃圾", "其他垃圾"], "answer": "有害垃圾", "explanation": "油漆残留含有害化学成分。"},
    {"id": 13, "type": "choice", "question": "茶叶渣通常属于哪类垃圾？", "options": ["可回收物", "有害垃圾", "厨余垃圾", "其他垃圾"], "answer": "厨余垃圾", "explanation": "茶叶渣属于易腐有机物。"},
    {"id": 14, "type": "judge", "question": "旧衣物在干净完整时可以进入回收或捐赠渠道。", "options": ["正确", "错误"], "answer": "正确", "explanation": "旧衣物属于可再利用资源。"},
    {"id": 15, "type": "choice", "question": "烟蒂通常属于哪类垃圾？", "options": ["可回收物", "有害垃圾", "厨余垃圾", "其他垃圾"], "answer": "其他垃圾", "explanation": "烟蒂污染严重且不可回收。"},
    {"id": 16, "type": "judge", "question": "所有外卖餐盒都一定属于可回收物。", "options": ["正确", "错误"], "answer": "错误", "explanation": "污染严重的外卖餐盒通常按其他垃圾处理。"},
    {"id": 17, "type": "choice", "question": "纽扣电池属于哪类垃圾？", "options": ["可回收物", "有害垃圾", "厨余垃圾", "其他垃圾"], "answer": "有害垃圾", "explanation": "纽扣电池有较高环境风险。"},
    {"id": 18, "type": "choice", "question": "苹果核通常属于哪类垃圾？", "options": ["可回收物", "有害垃圾", "厨余垃圾", "其他垃圾"], "answer": "厨余垃圾", "explanation": "苹果核属于易腐有机物。"},
    {"id": 19, "type": "judge", "question": "可回收物投放前应尽量保持清洁干燥。", "options": ["正确", "错误"], "answer": "正确", "explanation": "清洁干燥能提升回收质量。"},
    {"id": 20, "type": "choice", "question": "严重污染的塑料袋通常按哪类垃圾处理？", "options": ["可回收物", "有害垃圾", "厨余垃圾", "其他垃圾"], "answer": "其他垃圾", "explanation": "严重污染会降低回收价值。"},
]


def search_knowledge(keyword: str) -> list[dict[str, object]]:
    """按关键词检索知识库。"""
    normalized = keyword.strip().lower()
    if not normalized:
        return []
    results = []
    for item in KNOWLEDGE_BASE:
        haystack = " ".join((item.name, item.category, *item.aliases, item.guide, *item.examples)).lower()
        if normalized in haystack:
            results.append({
                "name": item.name,
                "category": item.category,
                "category_label": CATEGORY_LABELS[item.category],
                "guide": item.guide,
                "examples": list(item.examples),
            })
    return results
