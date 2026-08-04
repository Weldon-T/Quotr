"""Payment: Stripe Webhook 测试（占位）。

Webhook 事件处理验证，需 Stripe CLI 转发到本地。
"""
import pytest


@pytest.mark.payment
@pytest.mark.p1
class TestWebhook:
    @pytest.mark.skip(reason="需 Stripe CLI 配置 — 入职后实现")
    def test_payment_succeeded_webhook(self):
        pass

    @pytest.mark.skip(reason="需 Stripe CLI 配置 — 入职后实现")
    def test_payment_failed_webhook(self):
        pass

    @pytest.mark.skip(reason="需 Stripe CLI 配置 — 入职后实现")
    def test_subscription_deleted_webhook(self):
        pass
