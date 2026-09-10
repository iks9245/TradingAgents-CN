import time
import json

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
logger = get_logger("default")


def create_risky_debator(llm):
    def risky_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        risky_history = risk_debate_state.get("risky_history", "")

        current_safe_response = risk_debate_state.get("current_safe_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        trader_decision = state["trader_investment_plan"]

        # 📊 记录输入数据长度
        logger.info(f"📊 [Risky Analyst] 输入数据长度统计:")
        logger.info(f"  - market_report: {len(market_research_report):,} 字符")
        logger.info(f"  - sentiment_report: {len(sentiment_report):,} 字符")
        logger.info(f"  - news_report: {len(news_report):,} 字符")
        logger.info(f"  - fundamentals_report: {len(fundamentals_report):,} 字符")
        logger.info(f"  - trader_decision: {len(trader_decision):,} 字符")
        logger.info(f"  - history: {len(history):,} 字符")
        total_length = (len(market_research_report) + len(sentiment_report) +
                       len(news_report) + len(fundamentals_report) +
                       len(trader_decision) + len(history) +
                       len(current_safe_response) + len(current_neutral_response))
        logger.info(f"  - 总Prompt长度: {total_length:,} 字符 (~{total_length//4:,} tokens)")

        prompt = f"""作為激進風險分析師，您的職責是積極倡導高回報、高風險的投資機會，強調大膽策略和競爭優勢。在評估交易員的決策或計劃時，請重點關注潛在的上漲空間、增長潛力和創新收益——即使這些伴隨著較高的風險。使用提供的市場數據和情緒分析來加強您的論點，並挑戰對立觀點。具體來說，請直接回應保守和中性分析師提出的每個觀點，用數據驅動的反駁和有說服力的推理進行反擊。突出他們的謹慎態度可能錯過的關鍵機會，或者他們的假設可能過於保守的地方。以下是交易員的決策：

{trader_decision}

您的任務是通過質疑和批評保守和中性立場來為交易員的決策創建一個令人信服的案例，證明為什麼您的高回報視角提供了最佳的前進道路。將以下來源的見解納入您的論點：

市場研究報告：{market_research_report}
社交媒體情緒報告：{sentiment_report}
最新世界事務報告：{news_report}
公司基本面報告：{fundamentals_report}
以下是當前對話歷史：{history} 以下是保守分析師的最後論點：{current_safe_response} 以下是中性分析師的最後論點：{current_neutral_response}。如果其他觀點沒有回應，請不要虛構，只需提出您的觀點。

積極參與，解決提出的任何具體擔憂，反駁他們邏輯中的弱點，並斷言承擔風險的好處以超越市場常規。專注於辯論和說服，而不僅僅是呈現數據。挑戰每個反駁點，強調為什麼高風險方法是最優的。請用繁體中文以對話方式輸出，就像您在說話一樣，不使用任何特殊格式。"""

        logger.info(f"⏱️ [Risky Analyst] 开始调用LLM...")
        import time
        llm_start_time = time.time()

        response = llm.invoke(prompt)

        llm_elapsed = time.time() - llm_start_time
        logger.info(f"⏱️ [Risky Analyst] LLM调用完成，耗时: {llm_elapsed:.2f}秒")

        argument = f"Risky Analyst: {response.content}"

        new_count = risk_debate_state["count"] + 1
        logger.info(f"🔥 [激进风险分析师] 发言完成，计数: {risk_debate_state['count']} -> {new_count}")

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "risky_history": risky_history + "\n" + argument,
            "safe_history": risk_debate_state.get("safe_history", ""),
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Risky",
            "current_risky_response": argument,
            "current_safe_response": risk_debate_state.get("current_safe_response", ""),
            "current_neutral_response": risk_debate_state.get(
                "current_neutral_response", ""
            ),
            "count": new_count,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return risky_node
