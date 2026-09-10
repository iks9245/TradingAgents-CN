from tests.preview.offline import run_graph


def test_real_agent_graph_completes_with_offline_model_and_data():
    state, decision = run_graph()
    for name in ("market_report", "investment_plan", "trader_investment_plan", "final_trade_decision"):
        assert "繁體預覽驗收" in state[name]
    assert state["investment_debate_state"]["count"] >= 2
    assert state["risk_debate_state"]["count"] >= 3
    assert decision["action"] == "买入"
    assert decision["target_price"] == 125.5
