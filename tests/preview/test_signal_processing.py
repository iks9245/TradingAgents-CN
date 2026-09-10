"""Offline regressions for Traditional Chinese model output."""

import json
from types import SimpleNamespace

import pytest

from tradingagents.graph.signal_processing import SignalProcessor


class FakeLLM:
    def __init__(self, content=None, error=None):
        self.content = content
        self.error = error

    def invoke(self, messages):
        if self.error:
            raise self.error
        return SimpleNamespace(content=self.content)


@pytest.mark.parametrize("action,expected", [
    ("買入", "买入"), ("賣出", "卖出"), ("持有", "持有"),
    ("买入", "买入"), ("卖出", "卖出"), ("BUY", "买入"),
    ("sell", "卖出"), (" Hold ", "持有"), (None, "持有"),
])
def test_json_action_normalization(action, expected):
    llm = FakeLLM(json.dumps({"action": action, "target_price": 125}))
    result = SignalProcessor(llm).process_signal("測試分析報告", "AAPL")
    assert result["action"] == expected
    assert result["target_price"] == 125


@pytest.mark.parametrize("action,expected", [
    ("買入", "买入"), ("賣出", "卖出"), ("持有", "持有"),
    ("买入", "买入"), ("卖出", "卖出"), ("SELL", "卖出"),
])
@pytest.mark.parametrize("failure", [False, True])
def test_plain_text_and_llm_failure_preserve_decision(action, expected, failure):
    report = f"目標價位: 125.50\n最終交易建議: **{action}**"
    llm = FakeLLM(report, RuntimeError("offline") if failure else None)
    result = SignalProcessor(llm).process_signal(report, "AAPL")
    assert result["action"] == expected
    assert result["target_price"] == 125.5


def test_final_recommendation_takes_precedence_over_debate():
    report = "研究員建議買入，但風險過高。\n最終交易建議: **賣出**"
    result = SignalProcessor(FakeLLM(report)).process_signal(report, "AAPL")
    assert result["action"] == "卖出"


def test_ambiguous_actions_do_not_silently_prefer_buy():
    processor = SignalProcessor(FakeLLM())
    assert processor._extract_simple_decision("買入/持有/賣出")["action"] == "持有"
    assert processor._extract_simple_decision("shareholder buyer seller")["action"] == "持有"


def test_json_missing_price_extracts_traditional_label():
    llm = FakeLLM(json.dumps({"action": "買入", "target_price": None}))
    result = SignalProcessor(llm).process_signal("目標價位: 42.5\n最終交易建議: 買入", "600000")
    assert result["target_price"] == 42.5
