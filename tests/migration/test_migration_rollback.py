"""Migration: 回滚测试（占位）。"""
import pytest


@pytest.mark.migration
@pytest.mark.p1
class TestMigrationRollback:
    @pytest.mark.skip(reason="需 staging DB 连接信息 — 入职后配置")
    def test_rollback_restores_previous_state(self):
        pass
