"""Accessibility: axe-core 自动化扫描。

使用 @axe-core/playwright 在每个关键页面运行 WCAG 违规检测。
需要 npm install @axe-core/playwright
"""
import pytest


@pytest.mark.a11y
@pytest.mark.p1
class TestAxeCore:
    @pytest.mark.skip(reason="需 npm install @axe-core/playwright — 入职后安装并启用")
    def test_login_page_accessibility(self, page):
        pass

    @pytest.mark.skip(reason="需 npm install @axe-core/playwright — 入职后安装并启用")
    def test_dashboard_accessibility(self, logged_in_page):
        pass

    @pytest.mark.skip(reason="需 npm install @axe-core/playwright — 入职后安装并启用")
    def test_template_page_accessibility(self, logged_in_page):
        pass

    @pytest.mark.skip(reason="需 npm install @axe-core/playwright — 入职后安装并启用")
    def test_suppliers_page_accessibility(self, logged_in_page):
        pass
