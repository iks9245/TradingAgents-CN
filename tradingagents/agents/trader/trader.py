import functools
import time
import json

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
logger = get_logger("default")


def create_trader(llm, memory):
    def trader_node(state, name):
        company_name = state["company_of_interest"]
        investment_plan = state["investment_plan"]
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        # 使用统一的股票类型检测
        from tradingagents.utils.stock_utils import StockUtils
        market_info = StockUtils.get_market_info(company_name)
        is_china = market_info['is_china']
        is_hk = market_info['is_hk']
        is_us = market_info['is_us']

        # 根据股票类型确定货币单位
        currency = market_info['currency_name']
        currency_symbol = market_info['currency_symbol']

        logger.debug(f"💰 [DEBUG] ===== 交易员节点开始 =====")
        logger.debug(f"💰 [DEBUG] 交易员检测股票类型: {company_name} -> {market_info['market_name']}, 货币: {currency}")
        logger.debug(f"💰 [DEBUG] 货币符号: {currency_symbol}")
        logger.debug(f"💰 [DEBUG] 市场详情: 中国A股={is_china}, 港股={is_hk}, 美股={is_us}")
        logger.debug(f"💰 [DEBUG] 基本面报告长度: {len(fundamentals_report)}")
        logger.debug(f"💰 [DEBUG] 基本面报告前200字符: {fundamentals_report[:200]}...")

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"

        # 检查memory是否可用
        if memory is not None:
            logger.warning(f"⚠️ [DEBUG] memory可用，获取历史记忆")
            past_memories = memory.get_memories(curr_situation, n_matches=2)
            past_memory_str = ""
            for i, rec in enumerate(past_memories, 1):
                past_memory_str += rec["recommendation"] + "\n\n"
        else:
            logger.warning(f"⚠️ [DEBUG] memory为None，跳过历史记忆检索")
            past_memories = []
            past_memory_str = "暂无历史记忆数据可参考。"

        context = {
            "role": "user",
            "content": f"Based on a comprehensive analysis by a team of analysts, here is an investment plan tailored for {company_name}. This plan incorporates insights from current technical market trends, macroeconomic indicators, and social media sentiment. Use this plan as a foundation for evaluating your next trading decision.\n\nProposed Investment Plan: {investment_plan}\n\nLeverage these insights to make an informed and strategic decision.",
        }

        messages = [
            {
                "role": "system",
                "content": f"""您是一位專業的交易員，負責分析市場數據並做出投資決策。基於您的分析，請提供具體的買入、賣出或持有建議。

⚠️ 重要提醒：當前分析的股票代碼是 {company_name}，請使用正確的貨幣單位：{currency}（{currency_symbol}）

🔴 嚴格要求：
- 股票代碼 {company_name} 的公司名稱必須嚴格按照基本面報告中的真實數據
- 絕對禁止使用錯誤的公司名稱或混淆不同的股票
- 所有分析必須基於提供的真實數據，不允許假設或編造
- **必須提供具體的目標價位，不允許設置為null或空值**

請在您的分析中包含以下關鍵信息：
1. **投資建議**: 明確的買入/持有/賣出決策
2. **目標價位**: 基於分析的合理目標價格({currency}) - 🚨 強制要求提供具體數值
   - 買入建議：提供目標價位和預期漲幅
   - 持有建議：提供合理價格區間（如：{currency_symbol}XX-XX）
   - 賣出建議：提供止損價位和目標賣出價
3. **置信度**: 對決策的信心程度(0-1之間)
4. **風險評分**: 投資風險等級(0-1之間，0為低風險，1為高風險)
5. **詳細推理**: 支持決策的具體理由

🎯 目標價位計算指導：
- 基於基本面分析中的估值數據（P/E、P/B、DCF等）
- 參考技術分析的支撐位和阻力位
- 考慮行業平均估值水平
- 結合市場情緒和新聞影響
- 即使市場情緒過熱，也要基於合理估值給出目標價

特別注意：
- 如果是中國A股（6位數字代碼），請使用人民幣（¥）作為價格單位
- 如果是美股或港股，請使用美元（$）作為價格單位
- 目標價位必須與當前股價的貨幣單位保持一致
- 必須使用基本面報告中提供的正確公司名稱
- **絕對不允許說"無法確定目標價"或"需要更多信息"**

請用中文撰寫分析內容，並始終以'最終交易建議: **買入/持有/賣出**'結束您的回應以確認您的建議。

請不要忘記利用過去決策的經驗教訓來避免重複錯誤。以下是類似情況下的交易反思和經驗教訓: {past_memory_str}""",
            },
            context,
        ]

        logger.debug(f"💰 [DEBUG] 准备调用LLM，系统提示包含货币: {currency}")
        logger.debug(f"💰 [DEBUG] 系统提示中的关键部分: 目标价格({currency})")

        result = llm.invoke(messages)

        logger.debug(f"💰 [DEBUG] LLM调用完成")
        logger.debug(f"💰 [DEBUG] 交易员回复长度: {len(result.content)}")
        logger.debug(f"💰 [DEBUG] 交易员回复前500字符: {result.content[:500]}...")
        logger.debug(f"💰 [DEBUG] ===== 交易员节点结束 =====")

        return {
            "messages": [result],
            "trader_investment_plan": result.content,
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")
