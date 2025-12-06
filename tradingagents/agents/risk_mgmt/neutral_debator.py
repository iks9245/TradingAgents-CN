import time
import json

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
logger = get_logger("default")


def create_neutral_debator(llm):
    def neutral_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        neutral_history = risk_debate_state.get("neutral_history", "")

        current_risky_response = risk_debate_state.get("current_risky_response", "")
        current_safe_response = risk_debate_state.get("current_safe_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        trader_decision = state["trader_investment_plan"]

        # 📊 记录所有输入数据的长度，用于性能分析
        logger.info(f"📊 [Neutral Analyst] 输入数据长度统计:")
        logger.info(f"  - market_report: {len(market_research_report):,} 字符 (~{len(market_research_report)//4:,} tokens)")
        logger.info(f"  - sentiment_report: {len(sentiment_report):,} 字符 (~{len(sentiment_report)//4:,} tokens)")
        logger.info(f"  - news_report: {len(news_report):,} 字符 (~{len(news_report)//4:,} tokens)")
        logger.info(f"  - fundamentals_report: {len(fundamentals_report):,} 字符 (~{len(fundamentals_report)//4:,} tokens)")
        logger.info(f"  - trader_decision: {len(trader_decision):,} 字符 (~{len(trader_decision)//4:,} tokens)")
        logger.info(f"  - history: {len(history):,} 字符 (~{len(history)//4:,} tokens)")
        logger.info(f"  - current_risky_response: {len(current_risky_response):,} 字符 (~{len(current_risky_response)//4:,} tokens)")
        logger.info(f"  - current_safe_response: {len(current_safe_response):,} 字符 (~{len(current_safe_response)//4:,} tokens)")

        # 计算总prompt长度
        total_prompt_length = (len(market_research_report) + len(sentiment_report) +
                              len(news_report) + len(fundamentals_report) +
                              len(trader_decision) + len(history) +
                              len(current_risky_response) + len(current_safe_response))
        logger.info(f"  - 🚨 总Prompt长度: {total_prompt_length:,} 字符 (~{total_prompt_length//4:,} tokens)")

        prompt = f"""作為中性風險分析師，您的角色是提供平衡的視角，權衡交易員決策或計畫的潛在收益和風險。您優先考慮全面的方法，評估上行和下行風險，同時考慮更廣泛的市場趨勢、潛在的經濟變化和多元化策略。以下是交易員的決策：

{trader_decision}

您的任務是挑戰激進和安全分析師，指出每種觀點可能過於樂觀或過於謹慎的地方。使用以下資料來源的見解來支援調整交易員決策的溫和、可持續策略：

市場研究報告：{market_research_report}
社交媒體情緒報告：{sentiment_report}
最新世界事務報告：{news_report}
公司基本面報告：{fundamentals_report}
以下是當前對話歷史：{history} 以下是激進分析師的最後回應：{current_risky_response} 以下是安全分析師的最後回應：{current_safe_response}。如果其他觀點沒有回應，請不要虛構，只需提出您的觀點。

透過批判性地分析雙方來積極參與，解決激進和保守論點中的弱點，倡導更平衡的方法。挑戰他們的每個觀點，說明為什麼適度風險策略可能提供兩全其美的效果，既提供成長潛力又防範極端波動。專注於辯論而不是簡單地呈現資料，旨在表明平衡的觀點可以帶來最可靠的結果。請用中文以對話方式輸出，就像您在說話一樣，不使用任何特殊格式。"""

        logger.info(f"⏱️ [Neutral Analyst] 开始调用LLM...")
        llm_start_time = time.time()

        response = llm.invoke(prompt)

        llm_elapsed = time.time() - llm_start_time
        logger.info(f"⏱️ [Neutral Analyst] LLM调用完成，耗时: {llm_elapsed:.2f}秒")
        logger.info(f"📝 [Neutral Analyst] 响应长度: {len(response.content):,} 字符")

        argument = f"Neutral Analyst: {response.content}"

        new_count = risk_debate_state["count"] + 1
        logger.info(f"⚖️ [中性风险分析师] 发言完成，计数: {risk_debate_state['count']} -> {new_count}")

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "risky_history": risk_debate_state.get("risky_history", ""),
            "safe_history": risk_debate_state.get("safe_history", ""),
            "neutral_history": neutral_history + "\n" + argument,
            "latest_speaker": "Neutral",
            "current_risky_response": risk_debate_state.get(
                "current_risky_response", ""
            ),
            "current_safe_response": risk_debate_state.get("current_safe_response", ""),
            "current_neutral_response": argument,
            "count": new_count,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return neutral_node
