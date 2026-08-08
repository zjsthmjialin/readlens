"""平台适配器工厂。"""
from __future__ import annotations

from typing import Optional

from .base import ReadingPlatform
from .mock import MockPlatform


def get_platform(config) -> ReadingPlatform:
    """根据配置返回一个平台适配器实例。

    config 需支持 config["platform"] 与 config["weread"]。
    """
    name = config["platform"] if hasattr(config, "__getitem__") else "mock"
    if name == "mock":
        return MockPlatform()
    if name == "weread":
        from .weread import WeReadPlatform
        wr = config["weread"]
        return WeReadPlatform(
            base_url=wr.get("base_url"),
            api_key=wr.get("api_key"),
            skill_version=wr.get("skill_version", "1.0.3"),
        )
    raise ValueError(f"未知平台适配器：{name}（当前支持 mock / weread）")


__all__ = ["ReadingPlatform", "MockPlatform", "get_platform"]
