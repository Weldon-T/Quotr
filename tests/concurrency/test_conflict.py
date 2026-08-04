"""Concurrency: 并发冲突测试（占位）。"""
import pytest


@pytest.mark.concurrency
@pytest.mark.p1
class TestConflict:
    @pytest.mark.skip(reason="需要 2 个独立测试账号 — 入职后申请")
    def test_concurrent_project_edit_conflict_detection(self):
        pass

    @pytest.mark.skip(reason="需要 2 个独立测试账号 — 入职后申请")
    def test_concurrent_supplier_delete_while_editing(self):
        pass
