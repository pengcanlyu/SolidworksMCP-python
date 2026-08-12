"""Regression tests for the Codex-specific SolidWorks lifecycle behavior."""

from unittest.mock import AsyncMock, Mock

import pytest
import pywintypes

from solidworks_mcp.adapters import pywin32_adapter as adapter_module
from solidworks_mcp.adapters.pywin32_adapter import PyWin32Adapter
from solidworks_mcp.exceptions import SolidWorksMCPError


@pytest.mark.asyncio
async def test_attach_only_connection_never_dispatches_new_application(monkeypatch):
    """A lazy tool read must not launch SolidWorks when it is closed."""
    adapter = PyWin32Adapter()
    unavailable = pywintypes.com_error(-2147221021, "unavailable", None, None)
    monkeypatch.setattr(
        adapter_module.win32com.client,
        "GetActiveObject",
        Mock(side_effect=unavailable),
    )
    dispatch = Mock()
    monkeypatch.setattr(adapter_module, "_dynamic_dispatch", dispatch)

    with pytest.raises(SolidWorksMCPError):
        await adapter._session_coordinator.acquire_solidworks_application(
            start_if_missing=False
        )

    dispatch.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_connected_returns_false_when_solidworks_is_closed():
    """No running application is a normal tool-level unavailable state."""
    adapter = PyWin32Adapter()
    adapter._session_coordinator.connect = AsyncMock(
        side_effect=SolidWorksMCPError("not running")
    )

    assert await adapter._ensure_connected() is False
    adapter._session_coordinator.connect.assert_awaited_once_with(
        start_if_missing=False
    )
