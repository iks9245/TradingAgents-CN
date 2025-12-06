from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
import traceback

# 导入分析模块日志装饰器
from tradingagents.utils.tool_logging import log_analyst_module

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
logger = get_logger("default")

# 导入Google工具调用处理器
from tradingagents.agents.utils.google_tool_handler import GoogleToolCallHandler


def _get_company_name(ticker: str, market_info: dict) -> str:
    """
    根据股票代码获取公司名称

    Args:
        ticker: 股票代码
        market_info: 市场信息字典

    Returns:
        str: 公司名称
    """
    try:
        if market_info['is_china']:
            # 中国A股：使用统一接口获取股票信息
            from tradingagents.dataflows.interface import get_china_stock_info_unified
            stock_info = get_china_stock_info_unified(ticker)

            logger.debug(f"📊 [市场分析师] 获取股票信息返回: {stock_info[:200] if stock_info else 'None'}...")

            # 解析股票名称
            if stock_info and "股票名称:" in stock_info:
                company_name = stock_info.split("股票名称:")[1].split("\n")[0].strip()
                logger.info(f"✅ [市场分析师] 成功获取中国股票名称: {ticker} -> {company_name}")
                return company_name
            else:
                # 降级方案：尝试直接从数据源管理器获取
                logger.warning(f"⚠️ [市场分析师] 无法从统一接口解析股票名称: {ticker}，尝试降级方案")
                try:
                    from tradingagents.dataflows.data_source_manager import get_china_stock_info_unified as get_info_dict
                    info_dict = get_info_dict(ticker)
                    if info_dict and info_dict.get('name'):
                        company_name = info_dict['name']
                        logger.info(f"✅ [市场分析师] 降级方案成功获取股票名称: {ticker} -> {company_name}")
                        return company_name
                except Exception as e:
                    logger.error(f"❌ [市场分析师] 降级方案也失败: {e}")

                logger.error(f"❌ [市场分析师] 所有方案都无法获取股票名称: {ticker}")
                return f"股票代码{ticker}"

        elif market_info['is_hk']:
            # 港股：使用改进的港股工具
            try:
                from tradingagents.dataflows.providers.hk.improved_hk import get_hk_company_name_improved
                company_name = get_hk_company_name_improved(ticker)
                logger.debug(f"📊 [DEBUG] 使用改进港股工具获取名称: {ticker} -> {company_name}")
                return company_name
            except Exception as e:
                logger.debug(f"📊 [DEBUG] 改进港股工具获取名称失败: {e}")
                # 降级方案：生成友好的默认名称
                clean_ticker = ticker.replace('.HK', '').replace('.hk', '')
                return f"港股{clean_ticker}"

        elif market_info['is_us']:
            # 美股：使用简单映射或返回代码
            us_stock_names = {
                'AAPL': '苹果公司',
                'TSLA': '特斯拉',
                'NVDA': '英伟达',
                'MSFT': '微软',
                'GOOGL': '谷歌',
                'AMZN': '亚马逊',
                'META': 'Meta',
                'NFLX': '奈飞'
            }

            company_name = us_stock_names.get(ticker.upper(), f"美股{ticker}")
            logger.debug(f"📊 [DEBUG] 美股名称映射: {ticker} -> {company_name}")
            return company_name

        else:
            return f"股票{ticker}"

    except Exception as e:
        logger.error(f"❌ [DEBUG] 获取公司名称失败: {e}")
        return f"股票{ticker}"


def create_market_analyst(llm, toolkit):

    def market_analyst_node(state):
        logger.debug(f"📈 [DEBUG] ===== 市场分析师节点开始 =====")

        # 🔧 工具调用计数器 - 防止无限循环
        tool_call_count = state.get("market_tool_call_count", 0)
        max_tool_calls = 3  # 最大工具调用次数
        logger.info(f"🔧 [死循环修复] 当前工具调用次数: {tool_call_count}/{max_tool_calls}")

        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        logger.debug(f"📈 [DEBUG] 输入参数: ticker={ticker}, date={current_date}")
        logger.debug(f"📈 [DEBUG] 当前状态中的消息数量: {len(state.get('messages', []))}")
        logger.debug(f"📈 [DEBUG] 现有市场报告: {state.get('market_report', 'None')}")

        # 根据股票代码格式选择数据源
        from tradingagents.utils.stock_utils import StockUtils

        market_info = StockUtils.get_market_info(ticker)

        logger.debug(f"📈 [DEBUG] 股票类型检查: {ticker} -> {market_info['market_name']} ({market_info['currency_name']})")

        # 获取公司名称
        company_name = _get_company_name(ticker, market_info)
        logger.debug(f"📈 [DEBUG] 公司名称: {ticker} -> {company_name}")

        # 统一使用 get_stock_market_data_unified 工具
        # 该工具内部会自动识别股票类型（A股/港股/美股）并调用相应的数据源
        logger.info(f"📊 [市场分析师] 使用统一市场数据工具，自动识别股票类型")
        tools = [toolkit.get_stock_market_data_unified]

        # 安全地获取工具名称用于调试
        tool_names_debug = []
        for tool in tools:
            if hasattr(tool, 'name'):
                tool_names_debug.append(tool.name)
            elif hasattr(tool, '__name__'):
                tool_names_debug.append(tool.__name__)
            else:
                tool_names_debug.append(str(tool))
        logger.info(f"📊 [市场分析师] 绑定的工具: {tool_names_debug}")
        logger.info(f"📊 [市场分析师] 目标市场: {market_info['market_name']}")

        # 🔥 优化：将输出格式要求放在系统提示的开头，确保LLM遵循格式
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是一位專業的股票技術分析師，與其他分析師協作。\n"
                    "\n"
                    "📋 **分析對象：**\n"
                    "- 公司名稱：{company_name}\n"
                    "- 股票代碼：{ticker}\n"
                    "- 所屬市場：{market_name}\n"
                    "- 計價貨幣：{currency_name}（{currency_symbol}）\n"
                    "- 分析日期：{current_date}\n"
                    "\n"
                    "🔧 **工具使用：**\n"
                    "你可以使用以下工具：{tool_names}\n"
                    "⚠️ 重要工作流程：\n"
                    "1. 如果消息歷史中沒有工具結果，立即調用 get_stock_market_data_unified 工具\n"
                    "   - ticker: {ticker}\n"
                    "   - start_date: {current_date}\n"
                    "   - end_date: {current_date}\n"
                    "   注意：系統會自動擴展到365天歷史數據，你只需要傳遞當前分析日期即可\n"
                    "2. 如果消息歷史中已經有工具結果（ToolMessage），立即基於工具數據生成最終分析報告\n"
                    "3. 不要重複調用工具！一次工具調用就足夠了！\n"
                    "4. 接收到工具數據後，必須立即生成完整的技術分析報告，不要再調用任何工具\n"
                    "\n"
                    "📝 **輸出格式要求（必須嚴格遵守）：**\n"
                    "\n"
                    "## 📊 股票基本信息\n"
                    "- 公司名稱：{company_name}\n"
                    "- 股票代碼：{ticker}\n"
                    "- 所屬市場：{market_name}\n"
                    "\n"
                    "## 📈 技術指標分析\n"
                    "[在這裡分析移動平均線、MACD、RSI、布林帶等技術指標，提供具體數值]\n"
                    "\n"
                    "## 📉 價格趨勢分析\n"
                    "[在這裡分析價格趨勢，考慮{market_name}市場特點]\n"
                    "\n"
                    "## 💭 投資建議\n"
                    "[在這裡給出明確的投資建議：買入/持有/賣出]\n"
                    "\n"
                    "⚠️ **重要提醒：**\n"
                    "- 必須使用上述格式輸出，不要自創標題格式\n"
                    "- 所有價格數據使用{currency_name}（{currency_symbol}）表示\n"
                    "- 確保在分析中正確使用公司名稱\"{company_name}\"和股票代碼\"{ticker}\"\n"
                    "- 不要在標題中使用\"技術分析報告\"等自創標題\n"
                    "- 如果你有明確的技術面投資建議（買入/持有/賣出），請在投資建議部分明確標註\n"
                    "- 不要使用'最終交易建議'前綴，因為最終決策需要綜合所有分析師的意見\n"
                    "\n"
                    "請使用中文，基於真實數據進行分析。",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        # 安全地获取工具名称，处理函数和工具对象
        tool_names = []
        for tool in tools:
            if hasattr(tool, 'name'):
                tool_names.append(tool.name)
            elif hasattr(tool, '__name__'):
                tool_names.append(tool.__name__)
            else:
                tool_names.append(str(tool))

        # 🔥 设置所有模板变量
        prompt = prompt.partial(tool_names=", ".join(tool_names))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)
        prompt = prompt.partial(company_name=company_name)
        prompt = prompt.partial(market_name=market_info['market_name'])
        prompt = prompt.partial(currency_name=market_info['currency_name'])
        prompt = prompt.partial(currency_symbol=market_info['currency_symbol'])

        # 添加详细日志
        logger.info(f"📊 [市场分析师] LLM类型: {llm.__class__.__name__}")
        logger.info(f"📊 [市场分析师] LLM模型: {getattr(llm, 'model_name', 'unknown')}")
        logger.info(f"📊 [市场分析师] 消息历史数量: {len(state['messages'])}")
        logger.info(f"📊 [市场分析师] 公司名称: {company_name}")
        logger.info(f"📊 [市场分析师] 股票代码: {ticker}")

        # 打印提示词模板信息
        logger.info("📊 [市场分析师] ========== 提示词模板信息 ==========")
        logger.info(f"📊 [市场分析师] 模板变量已设置: company_name={company_name}, ticker={ticker}, market={market_info['market_name']}")
        logger.info("📊 [市场分析师] ==========================================")

        # 打印实际传递给LLM的消息
        logger.info(f"📊 [市场分析师] ========== 传递给LLM的消息 ==========")
        for i, msg in enumerate(state["messages"]):
            msg_type = type(msg).__name__
            # 🔥 修复：更安全地提取消息内容
            if hasattr(msg, 'content'):
                msg_content = str(msg.content)[:500]  # 增加到500字符以便查看完整内容
            elif isinstance(msg, tuple) and len(msg) >= 2:
                # 处理旧格式的元组消息 ("human", "content")
                msg_content = f"[元组消息] 类型={msg[0]}, 内容={str(msg[1])[:500]}"
            else:
                msg_content = str(msg)[:500]
            logger.info(f"📊 [市场分析师] 消息[{i}] 类型={msg_type}, 内容={msg_content}")
        logger.info(f"📊 [市场分析师] ========== 消息列表结束 ==========")

        chain = prompt | llm.bind_tools(tools)

        logger.info(f"📊 [市场分析师] 开始调用LLM...")
        # 修复：传递字典而不是直接传递消息列表，以便 ChatPromptTemplate 能正确处理所有变量
        result = chain.invoke({"messages": state["messages"]})
        logger.info(f"📊 [市场分析师] LLM调用完成")

        # 打印LLM响应
        logger.info(f"📊 [市场分析师] ========== LLM响应开始 ==========")
        logger.info(f"📊 [市场分析师] 响应类型: {type(result).__name__}")
        logger.info(f"📊 [市场分析师] 响应内容: {str(result.content)[:1000]}...")
        if hasattr(result, 'tool_calls') and result.tool_calls:
            logger.info(f"📊 [市场分析师] 工具调用: {result.tool_calls}")
        logger.info(f"📊 [市场分析师] ========== LLM响应结束 ==========")

        # 使用统一的Google工具调用处理器
        if GoogleToolCallHandler.is_google_model(llm):
            logger.info(f"📊 [市场分析师] 检测到Google模型，使用统一工具调用处理器")
            
            # 创建分析提示词
            analysis_prompt_template = GoogleToolCallHandler.create_analysis_prompt(
                ticker=ticker,
                company_name=company_name,
                analyst_type="市場分析",
                specific_requirements="重點關注市場數據、價格走勢、交易量變化等市場指標。"
            )
            
            # 处理Google模型工具调用
            report, messages = GoogleToolCallHandler.handle_google_tool_calls(
                result=result,
                llm=llm,
                tools=tools,
                state=state,
                analysis_prompt_template=analysis_prompt_template,
                analyst_name="市場分析師"
            )

            # 🔧 更新工具调用计数器
            return {
                "messages": [result],
                "market_report": report,
                "market_tool_call_count": tool_call_count + 1
            }
        else:
            # 非Google模型的处理逻辑
            logger.info(f"📊 [市场分析师] 非Google模型 ({llm.__class__.__name__})，使用标准处理逻辑")
            logger.info(f"📊 [市场分析师] 检查LLM返回结果...")
            logger.info(f"📊 [市场分析师] - 是否有tool_calls: {hasattr(result, 'tool_calls')}")
            if hasattr(result, 'tool_calls'):
                logger.info(f"📊 [市场分析师] - tool_calls数量: {len(result.tool_calls)}")
                if result.tool_calls:
                    for i, tc in enumerate(result.tool_calls):
                        logger.info(f"📊 [市场分析师] - tool_call[{i}]: {tc.get('name', 'unknown')}")

            # 处理市场分析报告
            if len(result.tool_calls) == 0:
                # 没有工具调用，直接使用LLM的回复
                report = result.content
                logger.info(f"📊 [市场分析师] ✅ 直接回复（无工具调用），长度: {len(report)}")
                logger.debug(f"📊 [DEBUG] 直接回复内容预览: {report[:200]}...")
            else:
                # 有工具调用，执行工具并生成完整分析报告
                logger.info(f"📊 [市场分析师] 🔧 检测到工具调用: {[call.get('name', 'unknown') for call in result.tool_calls]}")

                try:
                    # 执行工具调用
                    from langchain_core.messages import ToolMessage, HumanMessage

                    tool_messages = []
                    for tool_call in result.tool_calls:
                        tool_name = tool_call.get('name')
                        tool_args = tool_call.get('args', {})
                        tool_id = tool_call.get('id')

                        logger.debug(f"📊 [DEBUG] 执行工具: {tool_name}, 参数: {tool_args}")

                        # 找到对应的工具并执行
                        tool_result = None
                        for tool in tools:
                            # 安全地获取工具名称进行比较
                            current_tool_name = None
                            if hasattr(tool, 'name'):
                                current_tool_name = tool.name
                            elif hasattr(tool, '__name__'):
                                current_tool_name = tool.__name__

                            if current_tool_name == tool_name:
                                try:
                                    if tool_name == "get_china_stock_data":
                                        # 中国股票数据工具
                                        tool_result = tool.invoke(tool_args)
                                    else:
                                        # 其他工具
                                        tool_result = tool.invoke(tool_args)
                                    logger.debug(f"📊 [DEBUG] 工具执行成功，结果长度: {len(str(tool_result))}")
                                    break
                                except Exception as tool_error:
                                    logger.error(f"❌ [DEBUG] 工具执行失败: {tool_error}")
                                    tool_result = f"工具执行失败: {str(tool_error)}"

                        if tool_result is None:
                            tool_result = f"未找到工具: {tool_name}"

                        # 创建工具消息
                        tool_message = ToolMessage(
                            content=str(tool_result),
                            tool_call_id=tool_id
                        )
                        tool_messages.append(tool_message)

                    # 基于工具结果生成完整分析报告
                    # 🔥 重要：这里必须包含公司名称和输出格式要求，确保LLM生成正确的报告标题
                    analysis_prompt = f"""現在請基於上述工具獲取的數據，生成詳細的技術分析報告。

**分析對象：**
- 公司名稱：{company_name}
- 股票代碼：{ticker}
- 所屬市場：{market_info['market_name']}
- 計價貨幣：{market_info['currency_name']}（{market_info['currency_symbol']}）

**輸出格式要求（必須嚴格遵守）：**

請按照以下專業格式輸出報告，不要使用emoji符號（如📊📈📉💭等），使用純文本標題：

# **{company_name}（{ticker}）技術分析報告**
**分析日期：[當前日期]**

---

## 一、股票基本信息

- **公司名稱**：{company_name}
- **股票代碼**：{ticker}
- **所屬市場**：{market_info['market_name']}
- **當前價格**：[從工具數據中獲取] {market_info['currency_symbol']}
- **漲跌幅**：[從工具數據中獲取]
- **成交量**：[從工具數據中獲取]

---

## 二、技術指標分析

### 1. 移動平均線（MA）分析

[分析MA5、MA10、MA20、MA60等均線系統，包括：]
- 當前各均線數值
- 均線排列形態（多頭/空頭）
- 價格與均線的位置關係
- 均線交叉信號

### 2. MACD指標分析

[分析MACD指標，包括：]
- DIF、DEA、MACD柱狀圖當前數值
- 金叉/死叉信號
- 背離現象
- 趨勢強度判斷

### 3. RSI相對強弱指標

[分析RSI指標，包括：]
- RSI當前數值
- 超買/超賣區域判斷
- 背離信號
- 趨勢確認

### 4. 布林帶（BOLL）分析

[分析布林帶指標，包括：]
- 上軌、中軌、下軌數值
- 價格在布林帶中的位置
- 帶寬變化趨勢
- 突破信號

---

## 三、價格趨勢分析

### 1. 短期趨勢（5-10個交易日）

[分析短期價格走勢，包括支撐位、壓力位、關鍵價格區間]

### 2. 中期趨勢（20-60個交易日）

[分析中期價格走勢，結合均線系統判斷趨勢方向]

### 3. 成交量分析

[分析成交量變化，量價配合情況]

---

## 四、投資建議

### 1. 綜合評估

[基於上述技術指標，給出綜合評估]

### 2. 操作建議

- **投資評級**：買入/持有/賣出
- **目標價位**：[給出具體價格區間] {market_info['currency_symbol']}
- **止損位**：[給出止損價格] {market_info['currency_symbol']}
- **風險提示**：[列出主要風險因素]

### 3. 關鍵價格區間

- **支撐位**：[具體價格]
- **壓力位**：[具體價格]
- **突破買入價**：[具體價格]
- **跌破賣出價**：[具體價格]

---

**重要提醒：**
- 必須嚴格按照上述格式輸出，使用標準的Markdown標題（#、##、###）
- 不要使用emoji符號（📊📈📉💭等）
- 所有價格數據使用{market_info['currency_name']}（{market_info['currency_symbol']}）表示
- 確保在分析中正確使用公司名稱"{company_name}"和股票代碼"{ticker}"
- 報告標題必須是：# **{company_name}（{ticker}）技術分析報告**
- 報告必須基於工具返回的真實數據進行分析
- 包含具體的技術指標數值和專業分析
- 提供明確的投資建議和風險提示
- 報告長度不少於800字
- 使用中文撰寫
- 使用表格展示數據時，確保格式規範"""

                    # 构建完整的消息序列
                    messages = state["messages"] + [result] + tool_messages + [HumanMessage(content=analysis_prompt)]

                    # 生成最终分析报告
                    final_result = llm.invoke(messages)
                    report = final_result.content

                    logger.info(f"📊 [市场分析师] 生成完整分析报告，长度: {len(report)}")

                    # 返回包含工具调用和最终分析的完整消息序列
                    # 🔧 更新工具调用计数器
                    return {
                        "messages": [result] + tool_messages + [final_result],
                        "market_report": report,
                        "market_tool_call_count": tool_call_count + 1
                    }

                except Exception as e:
                    logger.error(f"❌ [市场分析师] 工具执行或分析生成失败: {e}")
                    traceback.print_exc()

                    # 降级处理：返回工具调用信息
                    report = f"市场分析师调用了工具但分析生成失败: {[call.get('name', 'unknown') for call in result.tool_calls]}"

                    # 🔧 更新工具调用计数器
                    return {
                        "messages": [result],
                        "market_report": report,
                        "market_tool_call_count": tool_call_count + 1
                    }

            # 🔧 更新工具调用计数器
            return {
                "messages": [result],
                "market_report": report,
                "market_tool_call_count": tool_call_count + 1
            }

    return market_analyst_node
