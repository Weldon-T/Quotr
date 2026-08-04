"""Accessibility: 键盘导航自动化。

验证 Tab/Enter/Escape 在关键页面上的基本行为。
"""
import pytest


@pytest.mark.a11y
@pytest.mark.p1
class TestKeyboardNavigation:
    @pytest.mark.skip(reason="需要非 headless 模式或复杂焦点追踪 — 手动测试阶段后再自动化")
    def test_tab_order_on_dashboard(self, logged_in_page):
        pass

    @pytest.mark.skip(reason="需要非 headless 模式或复杂焦点追踪 — 手动测试阶段后再自动化")
    def test_escape_closes_modal(self, logged_in_page):
        pass
