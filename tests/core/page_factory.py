"""Page Object Factory — Registry pattern: lazy instantiation with caching.

Usage:
    app = PageFactory(page)
    app.login.login()
    app.dashboard.go_project()
"""
from __future__ import annotations
from typing import TypeVar, Type, Dict
from playwright.sync_api import Page

T = TypeVar("T")


class PageFactory:
    """Lazily creates and caches page objects. One factory per browser page."""

    def __init__(self, page: Page):
        self._page = page
        self._cache: Dict[Type, object] = {}

    @property
    def page(self) -> Page:
        """直接访问底层 Playwright Page（用于 evaluate、screenshot 等操作）。"""
        return self._page

    def _get(self, cls: Type[T]) -> T:
        if cls not in self._cache:
            self._cache[cls] = cls(self._page)
        return self._cache[cls]

    @property
    def login(self):
        from tests.pages.login_page import LoginPage
        return self._get(LoginPage)

    @property
    def dashboard(self):
        from tests.pages.dashboard_page import DashboardPage
        return self._get(DashboardPage)

    @property
    def project(self):
        from tests.pages.project_page import ProjectPage
        return self._get(ProjectPage)

    @property
    def database(self):
        from tests.pages.database_page import DatabasePage
        return self._get(DatabasePage)

    @property
    def template(self):
        from tests.pages.template_page import TemplatePage
        return self._get(TemplatePage)

    @property
    def procurement(self):
        from tests.pages.procurement_page import ProcurementPage
        return self._get(ProcurementPage)
