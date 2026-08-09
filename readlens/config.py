"""配置加载：合并 config.yaml、环境变量与默认值。"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

DEFAULTS: Dict[str, Any] = {
    "platform": "mock",
    "weread": {
        "base_url": "https://i.weread.qq.com/api/agent/gateway",
        "api_key": None,
        "skill_version": "1.0.3",
    },
    "ai": {"engine": "offline", "model": "gpt-4o-mini", "temperature": 0.4},
    "export": {"out_dir": "./export_output", "obsidian_vault": None},
    "report": {"out_dir": "./report_output", "theme_color": "#07c160"},
}


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        elif v is not None:
            out[k] = v
    return out


@dataclass
class Config:
    data: Dict[str, Any] = field(default_factory=lambda: dict(DEFAULTS))

    @classmethod
    def load(cls, path: Optional[str] = None) -> "Config":
        data = dict(DEFAULTS)
        if path and os.path.exists(path) and yaml is not None:
            with open(path, "r", encoding="utf-8") as f:
                data = _deep_merge(data, yaml.safe_load(f) or {})
        # 环境变量覆盖
        if os.getenv("WEREAD_API_KEY"):
            data["weread"]["api_key"] = os.getenv("WEREAD_API_KEY")
            # 便利：设了微信读书 Key 且未显式指定平台时，自动切到 weread
            if data.get("platform", "mock") == "mock":
                data["platform"] = "weread"
        if os.getenv("OPENAI_API_KEY"):
            data["ai"]["engine"] = "openai"
        if os.getenv("READLENS_LLM_MODEL"):
            data["ai"]["model"] = os.getenv("READLENS_LLM_MODEL")
        return cls(data=data)

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def get(self, key: str, default=None) -> Any:
        return self.data.get(key, default)
