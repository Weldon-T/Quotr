"""Payment: 发票生成测试（占位）。"""
import pytest


@pytest.mark.payment
@pytest.mark.p1
class TestInvoice:
    @pytest.mark.skip(reason="需 Stripe test mode 配置 — 入职后实现")
    def test_invoice_generated_after_subscription(self):
        pass

    @pytest.mark.skip(reason="需 Stripe test mode 配置 — 入职后实现")
    def test_invoice_info_correct(self):
        pass
