"""Procurement Page — 供应商管理（Manage / RFQ / Quotes）。

当前状态：正常渲染，三个 Tab，Add New Supplier 按钮可用，已有测试数据。
"""
from playwright.sync_api import Page

from tests.config.routes import SUPPLIERS
from tests.pages.base_page import BasePage
from tests.utils.antd_selectors import (
    antd_tabs,
    antd_tab_click,
    antd_table_rows,
    antd_table_row_count,
    antd_form_items,
    antd_modal,
    antd_modal_confirm,
    antd_modal_close,
)


class ProcurementPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def go(self):
        self.goto(SUPPLIERS)
        return self

    # ---- Tabs ----

    @property
    def tab_names(self) -> list[str]:
        return antd_tabs(self.page)

    def switch_tab(self, tab_name: str):
        antd_tab_click(self.page, tab_name)
        self.page.locator(".ant-tabs-tabpane-active").first.wait_for(state="visible", timeout=5000)
        return self

    # ---- 供应商列表 ----

    @property
    def row_count(self) -> int:
        return antd_table_row_count(self.page)

    @property
    def table_data(self) -> list[list[str]]:
        return antd_table_rows(self.page)

    def get_supplier_names(self) -> list[str]:
        """获取所有供应商名称（表格第一列）。"""
        rows = self.table_data
        return [r[0] for r in rows if r]

    # ---- 创建 ----

    def click_add_supplier(self) -> bool:
        for text in ["Add New Supplier", "New Supplier", "Create Supplier", "Add Supplier"]:
            try:
                btn = self.page.locator(f"button:has-text('{text}')").first
                if btn.is_visible(timeout=2000):
                    btn.click()
                    self.page.locator(".ant-modal, .ant-drawer").first.wait_for(
                        state="visible", timeout=5000
                    )
                    return True
            except Exception:
                continue
        return False

    @property
    def create_form_fields(self) -> list[dict]:
        return antd_form_items(self.page)

    def fill_field(self, name: str, value: str):
        self.page.locator(f"input[name='{name}']").first.fill(value)

    def submit_create(self):
        antd_modal_confirm(self.page)
        self.page.locator(".ant-modal, .ant-drawer").first.wait_for(
            state="hidden", timeout=5000
        )

    # ---- 编辑/删除 ----

    def click_edit(self, supplier_name: str) -> bool:
        """点击指定供应商行的 Edit 按钮。"""
        try:
            row = self.page.locator(f".ant-table-row:has-text('{supplier_name}')").first
            edit_btn = row.locator("button:has-text('Edit'), a:has-text('Edit')").first
            if edit_btn.is_visible(timeout=2000):
                edit_btn.click()
                self.page.locator(".ant-modal, .ant-drawer, .ant-form").first.wait_for(
                    state="visible", timeout=3000
                )
                return True
        except Exception:
            pass
        return False

    def click_delete(self, supplier_name: str) -> bool:
        """点击指定供应商行的 Delete 按钮。"""
        try:
            row = self.page.locator(f".ant-table-row:has-text('{supplier_name}')").first
            del_btn = row.locator("button:has-text('Delete'), a:has-text('Delete')").first
            if del_btn.is_visible(timeout=2000):
                del_btn.click()
                self.page.locator(".ant-popconfirm, .ant-modal-confirm").first.wait_for(
                    state="visible", timeout=3000
                )
                return True
        except Exception:
            pass
        return False
