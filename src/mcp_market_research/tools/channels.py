from __future__ import annotations

from ..config import Settings
from ..logging_setup import traced_tool
from ..models import ChannelGuide
from ..parsers.excel_guide import get_channel_guide, list_channel_names


def list_channels_tool(settings: Settings) -> list[str]:
    @traced_tool("list_channels")
    def _impl() -> list[str]:
        return list_channel_names(settings.excel_guide_path)

    return _impl()


def get_channel_guide_tool(settings: Settings, channel: str) -> ChannelGuide:
    @traced_tool("get_channel_guide")
    def _impl() -> ChannelGuide:
        return get_channel_guide(settings.excel_guide_path, channel)

    return _impl()
