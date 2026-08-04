"""L2 Regression: Suppliers (Procurement) 模块。"""
import pytest


@pytest.mark.regression
@pytest.mark.p1
class TestProcurementNavigation:
    def test_suppliers_page_loads(self, logged_in_app):
        logged_in_app.procurement.go()
        assert not logged_in_app.procurement.is_white_screen(), "Suppliers 白屏"

    def test_has_three_tabs(self, logged_in_app):
        logged_in_app.procurement.go()
        tabs = logged_in_app.procurement.tab_names
        assert len(tabs) >= 3, f"期望 ≥3 Tab，实际: {tabs}"


@pytest.mark.regression
@pytest.mark.p1
class TestSupplierList:
    def test_has_existing_supplier(self, logged_in_app):
        logged_in_app.procurement.go()
        names = logged_in_app.procurement.get_supplier_names()
        assert "test_sup1" in names, f"缺 test_sup1，实际: {names}"

    def test_table_not_empty(self, logged_in_app):
        logged_in_app.procurement.go()
        assert logged_in_app.procurement.row_count > 0, "供应商表格为空"


@pytest.mark.regression
@pytest.mark.p1
class TestSupplierCreate:
    def test_add_supplier_button_opens_form(self, logged_in_app):
        logged_in_app.procurement.go()
        assert logged_in_app.procurement.click_add_supplier(), "Add New Supplier 按钮未找到"
        modal = logged_in_app.page.locator(".ant-modal, .ant-drawer").first
        assert modal.is_visible(timeout=5000), "创建表单未打开"


@pytest.mark.regression
@pytest.mark.p1
class TestSupplierEdit:
    def test_edit_button_exists(self, logged_in_app):
        logged_in_app.procurement.go()
        assert logged_in_app.procurement.click_edit("test_sup1"), "Edit 按钮不可用"

    def test_delete_button_exists(self, logged_in_app):
        logged_in_app.procurement.go()
        assert logged_in_app.procurement.click_delete("test_sup1"), "Delete 按钮不可用"
        logged_in_app.page.locator("button:has-text('Cancel'), button:has-text('No')").first.click()
