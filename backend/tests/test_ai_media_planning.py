import json
import unittest
from unittest.mock import patch

from app.ai.schemas import ModelConfig, PolishRequest
from app.ai.service import CONNECTION_MAX_TOKENS, POLISH_MAX_TOKENS, polish_copy, test_connection
from app.media_planning.ai_strategy import MEDIA_STRATEGY_MAX_TOKENS, suggest
from app.media_planning.schemas import CreateMediaPlanRequest


def model_config(model: str = "deepseek-v4-pro") -> dict:
    return {
        "provider": "custom",
        "model": model,
        "base_url": "https://token-plan.example.com/compatible-mode/v1",
        "api_key": "test-key",
    }


class TextModelBudgetTests(unittest.IsolatedAsyncioTestCase):
    async def test_connection_uses_expanded_output_budget(self):
        captured = {}

        async def fake_request(config, payload):
            captured.update(payload)
            return {"choices": [{"message": {"content": "OK"}}]}

        with patch("app.ai.service._request_completion", side_effect=fake_request):
            await test_connection(ModelConfig.model_validate(model_config()))

        self.assertEqual(captured["max_tokens"], CONNECTION_MAX_TOKENS)
        self.assertEqual(CONNECTION_MAX_TOKENS, 256)

    async def test_polish_uses_expanded_output_budget(self):
        captured = {}

        async def fake_request(config, payload):
            captured.update(payload)
            content = json.dumps({
                "headline": "恒温舒适每一天",
                "eyebrow": "COMFORT IN EVERY DROP",
                "description": "稳定水温与细腻出水，让日常沐浴更从容。",
                "features": ["恒温出水", "便捷切换", "舒适顶喷"],
                "cta": "立即了解",
            }, ensure_ascii=False)
            return {"choices": [{"message": {"content": content}}]}

        request = PolishRequest.model_validate({
            "config": model_config(),
            "style_id": "quiet-luxury",
            "product": {"product_name": "恒温花洒"},
            "current_copy": {},
        })
        with patch("app.ai.service._request_completion", side_effect=fake_request):
            result = await polish_copy(request)

        self.assertEqual(result.cta, "立即了解")
        self.assertEqual(captured["max_tokens"], POLISH_MAX_TOKENS)
        self.assertEqual(POLISH_MAX_TOKENS, 4096)


class MediaStrategyInputTests(unittest.IsolatedAsyncioTestCase):
    async def test_deepseek_receives_text_only_when_creative_image_exists(self):
        captured = {}

        async def fake_request(config, payload):
            captured.update(payload)
            content = json.dumps({
                "product_category": "卫浴花洒",
                "creative_positioning": "恒温与舒适体验",
                "strategy_summary": "先验证高意向装修人群，再逐步拓量。",
                "interests": ["卫浴产品"],
                "behaviors": ["近期装修"],
                "purchase_intents": ["花洒选购"],
                "core_hypothesis": "高意向装修人群更容易提交咨询。",
                "expansion_hypothesis": "品质生活人群可能被体验表达吸引。",
                "creative_angles": ["恒温体验"],
                "compliance_observations": [],
                "uncertainties": ["实际成本需投放验证"],
            }, ensure_ascii=False)
            return {"choices": [{"message": {"content": content}}]}

        request = CreateMediaPlanRequest.model_validate({
            "product": {"name": "恒温花洒"},
            "creative_source": {"type": "original"},
            "business": {
                "objective": "lead_generation",
                "platforms": ["generic_cn_paid_social"],
                "duration_days": 14,
                "budget_cap": 20000,
                "service_areas": ["上海"],
            },
            "model_config": model_config(),
        })
        with patch("app.media_planning.ai_strategy._request_completion", side_effect=fake_request):
            result = await suggest(request, [], b"image-bytes", "image/png")

        user_content = captured["messages"][1]["content"]
        self.assertIsInstance(user_content, str)
        self.assertEqual(result.product_category, "卫浴花洒")
        self.assertEqual(captured["max_tokens"], MEDIA_STRATEGY_MAX_TOKENS)
        self.assertEqual(MEDIA_STRATEGY_MAX_TOKENS, 4096)


if __name__ == "__main__":
    unittest.main()
