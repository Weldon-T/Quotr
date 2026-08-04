"""Migration: 迁移执行 + 数据完整性测试（占位）。

需要访问 staging 数据库，入职后配置 DB 连接信息后启用。
"""
import pytest


@pytest.mark.migration
@pytest.mark.p0
class TestMigrationRun:
    @pytest.mark.skip(reason="需 staging DB 连接信息 — 入职后配置")
    def test_migration_runs_without_error(self):
        pass

    @pytest.mark.skip(reason="需 staging DB 连接信息 — 入职后配置")
    def test_migration_data_integrity(self):
        pass
