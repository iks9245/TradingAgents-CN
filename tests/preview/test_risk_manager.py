"""Exercise both strings whose terminators were lost during translation."""

from types import SimpleNamespace
from unittest.mock import Mock

from tradingagents.agents.managers.risk_manager import create_risk_manager


def state():
    return {
        "company_of_interest": "600000", "market_report": "市場報告",
        "news_report": "新聞報告", "sentiment_report": "情緒報告",
        "investment_plan": "測試投資計畫",
        "risk_debate_state": {
            "history": "測試辯論", "risky_history": "", "safe_history": "",
            "neutral_history": "", "current_risky_response": "",
            "current_safe_response": "", "current_neutral_response": "", "count": 1,
        },
    }


def test_risk_manager_invokes_llm_and_returns_decision():
    decision = "測試結論：資料顯示風險可控，最終交易建議：買入。"
    llm = Mock()
    llm.invoke.return_value = SimpleNamespace(content=decision)
    result = create_risk_manager(llm, None)(state())
    assert result["final_trade_decision"] == decision
    assert result["risk_debate_state"]["judge_decision"] == decision
    prompt = llm.invoke.call_args.args[0]
    assert "測試投資計畫" in prompt and "測試辯論" in prompt
    assert "繁體中文" in prompt
    assert "prompt_length" not in prompt


def test_risk_manager_exhausted_retries_returns_fallback(monkeypatch):
    monkeypatch.setattr("tradingagents.agents.managers.risk_manager.time.sleep", lambda _: None)
    llm = Mock()
    llm.invoke.side_effect = RuntimeError("offline model unavailable")
    result = create_risk_manager(llm, None)(state())
    assert llm.invoke.call_count == 3
    assert "默認建議：持有" in result["final_trade_decision"]
    assert "600000" in result["final_trade_decision"]
    assert result["risk_debate_state"]["latest_speaker"] == "Judge"
