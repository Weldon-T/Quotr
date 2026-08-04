"""Payment: Stripe 订阅测试（占位）。

订阅创建/取消/升级测试，需要 Stripe test mode 环境。
入职后配置 Stripe test keys 并实现。
"""
import pytest


@pytest.mark.payment
@pytest.mark.p0
class TestSubscription:
    @pytest.mark.skip(reason="需 Stripe test mode 配置 — 入职后实现")
    def test_create_subscription(self):
        pass

    @pytest.mark.skip(reason="需 Stripe test mode 配置 — 入职后实现")
    def test_cancel_subscription(self):
        pass

    @pytest.mark.skip(reason="需 Stripe test mode 配置 — 入职后实现")
    def test_upgrade_subscription(self):
        pass
