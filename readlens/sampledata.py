"""内置示例数据（随包分发，无需外部文件）。

供 `readlens quickstart --with-manual` 演示手动藏书入库；也可作为手动藏书 JSON 的格式参照。
字段与 CLI 的 `_load_manual_books` 对应（title/author/category/status/owned/... 皆可选）。
"""
from __future__ import annotations

from typing import Dict, List

SAMPLE_MANUAL: List[Dict] = [
    {
        "title": "百年孤独", "author": "加西亚·马尔克斯", "category": "文学",
        "publisher": "南海出版公司", "status": "想读", "owned": "physical",
        "platform_rating": 95,
    },
    {
        "title": "置身事内", "author": "兰小欢", "category": "经济学",
        "publisher": "上海人民出版社", "status": "已读", "owned": "physical",
        "platform_rating": 91,
    },
    {
        "title": "沙丘", "author": "弗兰克·赫伯特", "category": "科幻",
        "status": "想读", "owned": "none",
    },
    {
        "title": "娱乐至死", "author": "尼尔·波兹曼", "category": "社会学",
        "status": "想读", "owned": "none",
    },
]
