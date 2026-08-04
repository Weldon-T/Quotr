"""Ant Design 组件选择器辅助。

Ant Design v5 使用 CSS variables 和哈希类名，裸选择器不稳定。
此模块提供语义化封装，减少测试用例中的脆弱选择器。
"""
import re


def antd_table_rows(page):
    """获取 Ant Table 所有可见行数据，返回 list[list[str]]。"""
    return page.evaluate("""() => {
        const rows = document.querySelectorAll('.ant-table-row, tr[data-row-key]');
        return [...rows].map(r =>
            [...r.querySelectorAll('td, .ant-table-cell')].map(c => c.textContent.trim())
        );
    }""")


def antd_table_row_count(page):
    """返回 Ant Table 可见行数。"""
    return page.evaluate("""() => document.querySelectorAll('.ant-table-row, tr[data-row-key]').length""")


def antd_select_open(page, label_text: str):
    """根据 label 文本找到对应的 Ant Design Select 并展开下拉。"""
    # Ant Design Form.Item 的 label 关联到 input
    form_item = page.locator(f".ant-form-item:has-text('{label_text}')")
    select = form_item.locator(".ant-select-selector").first
    select.click()
    page.wait_for_timeout(500)


def antd_select_option(page, option_text: str):
    """在下拉列表中选择一个选项。"""
    option = page.locator(f".ant-select-item-option:has-text('{option_text}')").first
    option.click()


def antd_modal(page):
    """获取当前可见的 Ant Design Modal。"""
    return page.locator(".ant-modal:visible, .ant-modal-content").first


def antd_modal_close(page):
    """关闭当前 Modal。"""
    close_btn = page.locator(".ant-modal-close").first
    if close_btn.is_visible():
        close_btn.click()


def antd_modal_confirm(page):
    """点击 Modal 的确定按钮。"""
    btn = page.locator(".ant-modal-footer .ant-btn-primary").first
    btn.click()


def antd_tabs(page):
    """返回当前页面所有可见 Tab 的文本列表。"""
    tabs = []
    for el in page.locator(".ant-tabs-tab, [role='tab']").all():
        try:
            if el.is_visible():
                text = el.inner_text().strip()
                if text:
                    tabs.append(text)
        except Exception:
            pass
    return tabs


def antd_tab_click(page, tab_text: str):
    """点击指定文本的 Tab。"""
    tab = page.locator(f".ant-tabs-tab:has-text('{tab_text}')").first
    tab.click()


def antd_form_items(page):
    """返回当前页面所有表单字段的 name/placeholder 信息。"""
    return page.evaluate("""() => {
        return [...document.querySelectorAll('input, textarea, .ant-select-selector')].map(el => ({
            tag: el.tagName,
            name: el.name || '',
            type: el.type || '',
            placeholder: el.placeholder || '',
            text: (el.textContent || '').trim().substring(0, 50)
        }));
    }""")


def antd_empty(page):
    """检查页面是否有 Ant Design Empty 组件。"""
    empty = page.locator(".ant-empty, .ant-empty-image").first
    return empty.is_visible()


def antd_spinning(page):
    """检查页面是否在加载中。"""
    spin = page.locator(".ant-spin-spinning").first
    return spin.is_visible()
