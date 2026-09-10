"""Offline external boundaries; production agent graph and persistence stay real.

Only imported by preview tests / the local preview harness, never by app.main.
"""

import asyncio
import json
from types import SimpleNamespace

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode

from tradingagents.graph.conditional_logic import ConditionalLogic
from tradingagents.graph.propagation import Propagator
from tradingagents.graph.setup import GraphSetup
from tradingagents.graph.signal_processing import SignalProcessor


REPORT = (
    "## 繁體預覽驗收報告\n"
    "這是固定測試資料，僅用於驗證軟體流程，不代表真實行情或投資建議。\n"
    "測試股票 AAPL，測試現價 100 美元，目標價位: 125.50。\n"
    "市場分析、研究辯論與風險評估均使用離線模型回覆；測試涵蓋資料工具、"
    "狀態流轉、報告保存與模擬訂單。\n最終交易建議: **買入**"
)


class PreviewLLM(BaseChatModel):
    @property
    def _llm_type(self):
        return "offline-preview-fixture"

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        system = str(messages[0].content)
        if "股票技術分析師" in system and not any(isinstance(m, ToolMessage) for m in messages):
            message = AIMessage(content="", tool_calls=[{
                "name": "get_stock_market_data_unified",
                "args": {"ticker": "AAPL", "start_date": "2025-12-05", "end_date": "2025-12-05"},
                "id": "preview-market-data",
            }])
        elif "JSON" in system:
            message = AIMessage(content=json.dumps({
                "action": "買入", "target_price": 125.5,
                "confidence": 0.7, "risk_score": 0.5, "reasoning": "離線驗收測試",
            }, ensure_ascii=False))
        else:
            message = AIMessage(content=REPORT)
        return ChatResult(generations=[ChatGeneration(message=message)])


@tool
def get_stock_market_data_unified(ticker: str, start_date: str, end_date: str) -> str:
    """Return explicitly synthetic data for preview acceptance only."""
    return f"離線測試資料：{ticker}, {start_date} 至 {end_date}, 現價 100 USD, RSI 50。"


def run_graph():
    llm = PreviewLLM()
    graph = GraphSetup(
        llm, llm, SimpleNamespace(get_stock_market_data_unified=get_stock_market_data_unified),
        {"market": ToolNode([get_stock_market_data_unified])},
        None, None, None, None, None, ConditionalLogic(1, 1),
    ).setup_graph(["market"])
    initial = Propagator().create_initial_state("AAPL", "2025-12-05")
    state = graph.invoke(initial, config={"recursion_limit": 50})
    decision = SignalProcessor(llm).process_signal(state["final_trade_decision"], "AAPL")
    return state, decision


async def execute_preview_analysis(task_id, user_id, request, progress_tracker=None):
    if request.get_symbol() != "AAPL":
        raise ValueError("Offline preview supports only AAPL")
    state, decision = await asyncio.to_thread(run_graph)
    return {
        "stock_symbol": "AAPL", "stock_code": "AAPL", "stock_name": "蘋果公司（測試）",
        "analysis_date": "2025-12-05", "state": state, "decision": decision,
        "summary": REPORT, "recommendation": decision["action"],
        "confidence_score": decision["confidence"], "risk_level": "中等",
        "analysts": ["market"], "research_depth": 1, "model_info": "offline-preview-fixture",
    }


async def prepare_preview_data(**kwargs):
    return SimpleNamespace(
        is_valid=kwargs["stock_code"] == "AAPL", stock_name="蘋果公司（測試）",
        market_type="美股", has_historical_data=True, has_basic_info=True,
        error_message="Offline preview supports only AAPL", suggestion="使用 AAPL",
    )


async def preview_quote(self, market, code, **kwargs):
    if market == "US" and code == "AAPL":
        return {"price": 100.0, "current_price": 100.0, "currency": "USD"}
    return None


def install_offline_boundaries(monkeypatch, service):
    monkeypatch.setattr(service, "_execute_analysis_sync", execute_preview_analysis)
    monkeypatch.setattr(service, "_resolve_stock_name", lambda code: "蘋果公司（測試）")
    monkeypatch.setattr("tradingagents.utils.stock_validator.prepare_stock_data_async", prepare_preview_data)
    monkeypatch.setattr("app.services.foreign_stock_service.ForeignStockService.get_quote", preview_quote)
