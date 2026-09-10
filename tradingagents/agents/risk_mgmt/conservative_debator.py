from langchain_core.messages import AIMessage
import time
import json

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
logger = get_logger("default")


def create_safe_debator(llm):
    def safe_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        safe_history = risk_debate_state.get("safe_history", "")

        current_risky_response = risk_debate_state.get("current_risky_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        trader_decision = state["trader_investment_plan"]

        # 📊 记录输入数据长度
        logger.info(f"📊 [Safe Analyst] 输入数据长度统计:")
        logger.info(f"  - market_report: {len(market_research_report):,} 字符")
        logger.info(f"  - sentiment_report: {len(sentiment_report):,} 字符")
        logger.info(f"  - news_report: {len(news_report):,} 字符")
        logger.info(f"  - fundamentals_report: {len(fundamentals_report):,} 字符")
        logger.info(f"  - trader_decision: {len(trader_decision):,} 字符")
        logger.info(f"  - history: {len(history):,} 字符")
        total_length = (len(market_research_report) + len(sentiment_report) +
                       len(news_report) + len(fundamentals_report) +
                       len(trader_decision) + len(history) +
                       len(current_risky_response) + len(current_neutral_response))
        logger.info(f"  - 总Prompt长度: {total_length:,} 字符 (~{total_length//4:,} tokens)")

        prompt = f"""作為安全/保守風險分析師，您的主要目標是保護資產、最小化波動性，並確保穩定、可靠的成長。您優先考慮穩定性、安全性和風險緩解，仔細評估潛在損失、經濟衰退和市場波動。在評估交易員的決策或計畫時，請批判性地審查高風險要素，指出決策可能使公司面臨不當風險的地方，以及更謹慎的替代方案如何能夠確保長期收益。以下是交易員的決策：

{trader_decision}

您的任務是積極反駁激進和中性分析師的論點，突出他們的觀點可能忽視的潛在威脅或未能優先考慮可持續性的地方。直接回應他們的觀點，利用以下資料來源為交易員決策的低風險方法調整建立令人信服的案例：

市場研究報告：{market_research_report}
社交媒體情緒報告：{sentiment_report}
最新世界事務報告：{news_report}
公司基本面報告：{fundamentals_report}
以下是當前對話歷史：{history} 以下是激進分析師的最後回應：{current_risky_response} 以下是中性分析師的最後回應：{current_neutral_response}。如果其他觀點沒有回應，請不要虛構，只需提出您的觀點。

透過質疑他們的樂觀態度並強調他們可能忽視的潛在下行風險來參與討論。解決他們的每個反駁點，展示為什麼保守立場最終是公司資產最安全的道路。專注於辯論和批評他們的論點，證明低風險策略相對於他們方法的優勢。請用繁體中文以對話方式輸出，就像您在說話一樣，不使用任何特殊格式。"""

        logger.info(f"⏱️ [Safe Analyst] 开始调用LLM...")
        llm_start_time = time.time()

        response = llm.invoke(prompt)

        llm_elapsed = time.time() - llm_start_time
        logger.info(f"⏱️ [Safe Analyst] LLM调用完成，耗时: {llm_elapsed:.2f}秒")

        argument = f"Safe Analyst: {response.content}"

        new_count = risk_debate_state["count"] + 1
        logger.info(f"🛡️ [保守风险分析师] 发言完成，计数: {risk_debate_state['count']} -> {new_count}")

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "risky_history": risk_debate_state.get("risky_history", ""),
            "safe_history": safe_history + "\n" + argument,
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Safe",
            "current_risky_response": risk_debate_state.get(
                "current_risky_response", ""
            ),
            "current_safe_response": argument,
            "current_neutral_response": risk_debate_state.get(
                "current_neutral_response", ""
            ),
            "count": new_count,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return safe_node
