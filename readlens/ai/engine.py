"""LLM 引擎抽象与两种实现。"""
from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from collections import Counter
from typing import List, Dict, Any


class LLMEngine(ABC):
    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        ...


class OfflineEngine(LLMEngine):
    """不联网的启发式引擎：用抽取式摘要/关键词统计模拟 LLM 输出。

    目的是让整个项目在没有 API Key 时也能演示 AI 流程；接入真实 LLM 后
    输出质量会显著提升，接口保持不变。
    """

    _STOP = set("的了和是在我也就都而及與与你他她它们這这那有一个我们你们没被把让对着与之其为以于且或又很更最只还也要会能可将对于这些那些一些之后之前因为所以但是不过如果虽然".join(" "))

    def complete(self, system: str, user: str) -> str:
        # 从 user 里提取要点句，做抽取式摘要 + 关键词
        text = user
        sents = re.split(r"[。！？\n；;]", text)
        # 跳过指令性句子（含“请”等祈使词）与元信息行，只保留素材内容
        def _is_material(s: str) -> bool:
            if len(s) < 6:
                return False
            if any(w in s for w in ("请", "书名：", "相关划线", "偏好分类",
                                    "我最近读过", "这是我的", "关键词")):
                return False
            return True
        sents = [s.strip().lstrip("-·　 ") for s in sents if _is_material(s.strip())]
        # 关键词（粗糙的中文 2-gram 频次）
        grams = Counter()
        for s in sents:
            clean = re.sub(r"[^一-龥A-Za-z]", "", s)
            for i in range(len(clean) - 1):
                g = clean[i:i + 2]
                if not (set(g) & self._STOP):
                    grams[g] += 1
        keywords = [g for g, _ in grams.most_common(6)]
        top_sents = sents[:3]
        out = []
        out.append("【离线摘要引擎输出 · 接入 LLM 后质量更佳】")
        if keywords:
            out.append("关键词：" + "、".join(keywords))
        if top_sents:
            out.append("要点：")
            out += [f"· {s}" for s in top_sents]
        return "\n".join(out)


class OpenAIEngine(LLMEngine):
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.4):
        try:
            from openai import OpenAI
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("请先 pip install openai") from e
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL") or None,
        )
        self.model = model
        self.temperature = temperature

    def complete(self, system: str, user: str) -> str:  # pragma: no cover
        resp = self.client.chat.completions.create(
            model=self.model, temperature=self.temperature,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}])
        return resp.choices[0].message.content.strip()


def get_engine(config=None) -> LLMEngine:
    ai_cfg: Dict[str, Any] = {}
    if config is not None and hasattr(config, "__getitem__"):
        ai_cfg = config["ai"]
    engine = ai_cfg.get("engine", "offline")
    if engine == "openai" and os.getenv("OPENAI_API_KEY"):
        return OpenAIEngine(model=ai_cfg.get("model", "gpt-4o-mini"),
                            temperature=ai_cfg.get("temperature", 0.4))
    return OfflineEngine()
