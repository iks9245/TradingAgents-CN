from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from datetime import datetime

# 导入统一日志系统和分析模块日志装饰器
from tradingagents.utils.logging_init import get_logger
from tradingagents.utils.tool_logging import log_analyst_module
# 导入统一新闻工具
from tradingagents.tools.unified_news_tool import create_unified_news_tool
# 导入股票工具类
from tradingagents.utils.stock_utils import StockUtils
# 导入Google工具调用处理器
from tradingagents.agents.utils.google_tool_handler import GoogleToolCallHandler

logger = get_logger("analysts.news")


def create_news_analyst(llm, toolkit):
    @log_analyst_module("news")
    def news_analyst_node(state):
        start_time = datetime.now()

        # 🔧 工具调用计数器 - 防止无限循环
        tool_call_count = state.get("news_tool_call_count", 0)
        max_tool_calls = 3  # 最大工具调用次数
        logger.info(f"🔧 [死循环修复] 当前工具调用次数: {tool_call_count}/{max_tool_calls}")

        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        logger.info(f"[新闻分析师] 开始分析 {ticker} 的新闻，交易日期: {current_date}")
        session_id = state.get("session_id", "未知会话")
        logger.info(f"[新闻分析师] 会话ID: {session_id}，开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 获取市场信息
        market_info = StockUtils.get_market_info(ticker)
        logger.info(f"[新闻分析师] 股票类型: {market_info['market_name']}")
        
        # 获取公司名称
        def _get_company_name(ticker: str, market_info: dict) -> str:
            """根据股票代码获取公司名称"""
            try:
                if market_info['is_china']:
                    # 中国A股：使用统一接口获取股票信息
                    from tradingagents.dataflows.interface import get_china_stock_info_unified
                    stock_info = get_china_stock_info_unified(ticker)
                    
                    # 解析股票名称
                    if "股票名称:" in stock_info:
                        company_name = stock_info.split("股票名称:")[1].split("\n")[0].strip()
                        logger.debug(f"📊 [DEBUG] 从统一接口获取中国股票名称: {ticker} -> {company_name}")
                        return company_name
                    else:
                        logger.warning(f"⚠️ [DEBUG] 无法从统一接口解析股票名称: {ticker}")
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
        
        company_name = _get_company_name(ticker, market_info)
        logger.info(f"[新闻分析师] 公司名称: {company_name}")
        
        # 🔧 使用统一新闻工具，简化工具调用
        logger.info(f"[新闻分析师] 使用统一新闻工具，自动识别股票类型并获取相应新闻")
   # 创建统一新闻工具
        unified_news_tool = create_unified_news_tool(toolkit)
        unified_news_tool.name = "get_stock_news_unified"
        
        tools = [unified_news_tool]
        logger.info(f"[新闻分析师] 已加载统一新闻工具: get_stock_news_unified")

        system_message = (
            """您是一位專業的財經新聞分析師，負責分析最新的市場新聞和事件對股票價格的潛在影響。

您的主要職責包括：
1. 獲取和分析最新的實時新聞（優先15-30分鐘內的新聞）
2. 評估新聞事件的緊急程度和市場影響
3. 識別可能影響股價的關鍵信息
4. 分析新聞的時效性和可靠性
5. 提供基於新聞的交易建議和價格影響評估

重點關注的新聞類型：
- 財報發布和業績指導
- 重大合作和併購消息
- 政策變化和監管動態
- 突發事件和危機管理
- 行業趨勢和技術突破
- 管理層變動和戰略調整

分析要點：
- 新聞的時效性（發布時間距離現在多久）
- 新聞的可信度（來源權威性）
- 市場影響程度（對股價的潛在影響）
- 投資者情緒變化（正面/負面/中性）
- 與歷史類似事件的對比

📊 新聞影響分析要求：
- 評估新聞對股價的短期影響（1-3天）和市場情緒變化
- 分析新聞的利好/利空程度和可能的市場反應
- 評估新聞對公司基本面和長期投資價值的影響
- 識別新聞中的關鍵信息點和潛在風險
- 對比歷史類似事件的市場反應
- 不允許回覆'無法評估影響'或'需要更多信息'

請特別注意：
⚠️ 如果新聞數據存在滯後（超過2小時），請在分析中明確說明時效性限制
✅ 優先分析最新的、高相關性的新聞事件
📊 提供新聞對市場情緒和投資者信心的影響評估
💰 必須包含基於新聞的市場反應預期和投資建議
🎯 聚焦新聞內容本身的解讀，不涉及技術指標分析

請撰寫詳細的中文分析報告，並在報告末尾附上Markdown表格總結關鍵發現。"""
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "您是一位专业的财经新闻分析师。"
                    "\n🚨 CRITICAL REQUIREMENT - 絕對強制要求："
                    "\n"
                    "\n❌ 禁止行为："
                    "\n- 絕對禁止在沒有調用工具的情況下直接回答"
                    "\n- 絕對禁止基於推測或假設生成任何分析內容"
                    "\n- 絕對禁止跳過工具調用步驟"
                    "\n- 絕對禁止說'我無法獲取實時數據'等藉口"
                    "\n"
                    "\n✅ 强制执行步骤："
                    "\n1. 您的第一個動作必須是調用 get_stock_news_unified 工具"
                    "\n2. 該工具會自動識別股票類型（A股、港股、美股）並獲取相應新聞"
                    "\n3. 只有在成功獲取新聞數據後，才能開始分析"
                    "\n4. 您的回答必須基於工具返回的真實數據"
                    "\n"
                    "\n🔧 工具调用格式示例："
                    "\n調用: get_stock_news_unified(stock_code='{ticker}', max_news=10)"
                    "\n"
                    "\n⚠️ 如果您不調用工具，您的回答將被視為無效並被拒絕。"
                    "\n⚠️ 您必須先調用工具獲取數據，然後基於數據進行分析。"
                    "\n⚠️ 沒有例外，沒有藉口，必須調用工具。"
                    "\n"
                    "\n您可以访问以下工具：{tool_names}。"
                    "\n{system_message}"
                    "\n供您參考，當前日期是{current_date}。我們正在查看公司{ticker}。"
                    "\n請按照上述要求執行，用中文撰寫所有分析內容。",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)
        
        # 获取模型信息用于统一新闻工具的特殊处理
        model_info = ""
        try:
            if hasattr(llm, 'model_name'):
                model_info = f"{llm.__class__.__name__}:{llm.model_name}"
            else:
                model_info = llm.__class__.__name__
        except:
            model_info = "Unknown"
        
        logger.info(f"[新闻分析师] 准备调用LLM进行新闻分析，模型: {model_info}")
        
        # 🚨 DashScope/DeepSeek/Zhipu预处理：强制获取新闻数据
        pre_fetched_news = None
        if ('DashScope' in llm.__class__.__name__ 
            or 'DeepSeek' in llm.__class__.__name__
            or 'Zhipu' in llm.__class__.__name__
            ):
            logger.warning(f"[新闻分析师] 🚨 检测到{llm.__class__.__name__}模型，启动预处理强制新闻获取...")
            try:
                # 强制预先获取新闻数据
                logger.info(f"[新闻分析师] 🔧 预处理：强制调用统一新闻工具...")
                logger.info(f"[新闻分析师] 📊 调用参数: stock_code={ticker}, max_news=10, model_info={model_info}")

                pre_fetched_news = unified_news_tool(stock_code=ticker, max_news=10, model_info=model_info)

                logger.info(f"[新闻分析师] 📋 预处理返回结果长度: {len(pre_fetched_news) if pre_fetched_news else 0} 字符")
                logger.info(f"[新闻分析师] 📄 预处理返回结果预览 (前500字符): {pre_fetched_news[:500] if pre_fetched_news else 'None'}")

                if pre_fetched_news and len(pre_fetched_news.strip()) > 100:
                    logger.info(f"[新闻分析师] ✅ 预处理成功获取新闻: {len(pre_fetched_news)} 字符")

                    # 直接基于预获取的新闻生成分析，跳过工具调用
                    enhanced_prompt = f"""
您是一位專業的財經新聞分析師。請基於以下已獲取的最新新聞數據，對股票 {ticker}（{company_name}）進行詳細分析：

=== 最新新聞數據 ===
{pre_fetched_news}

=== 分析要求 ===
{system_message}

請基於上述真實新聞數據撰寫詳細的中文分析報告。注意：新聞數據已經提供，您無需再調用任何工具。
"""

                    logger.info(f"[新闻分析师] 🔄 使用预获取新闻数据直接生成分析...")
                    logger.info(f"[新闻分析师] 📝 增强提示词长度: {len(enhanced_prompt)} 字符")

                    llm_start_time = datetime.now()
                    result = llm.invoke([{"role": "user", "content": enhanced_prompt}])

                    llm_end_time = datetime.now()
                    llm_time_taken = (llm_end_time - llm_start_time).total_seconds()
                    logger.info(f"[新闻分析师] LLM调用完成（预处理模式），耗时: {llm_time_taken:.2f}秒")

                    # 直接返回结果，跳过后续的工具调用检测
                    if hasattr(result, 'content') and result.content:
                        report = result.content
                        logger.info(f"[新闻分析师] ✅ 预处理模式成功，报告长度: {len(report)} 字符")
                        logger.info(f"[新闻分析师] 📄 报告预览 (前300字符): {report[:300]}")

                        # 跳转到最终处理
                        from langchain_core.messages import AIMessage
                        clean_message = AIMessage(content=report)

                        end_time = datetime.now()
                        time_taken = (end_time - start_time).total_seconds()
                        logger.info(f"[新闻分析师] 新闻分析完成（预处理模式），总耗时: {time_taken:.2f}秒")
                        # 🔧 更新工具调用计数器
                        return {
                            "messages": [clean_message],
                            "news_report": report,
                            "news_tool_call_count": tool_call_count + 1
                        }
                    else:
                        logger.warning(f"[新闻分析师] ⚠️ LLM返回结果为空，回退到标准模式")

                else:
                    logger.warning(f"[新闻分析师] ⚠️ 预处理获取新闻失败或内容过短（{len(pre_fetched_news) if pre_fetched_news else 0}字符），回退到标准模式")
                    if pre_fetched_news:
                        logger.warning(f"[新闻分析师] 📄 失败的新闻内容: {pre_fetched_news}")

            except Exception as e:
                logger.error(f"[新闻分析师] ❌ 预处理失败: {e}，回退到标准模式")
                import traceback
                logger.error(f"[新闻分析师] 📋 异常堆栈: {traceback.format_exc()}")
        
        # 使用统一的Google工具调用处理器
        llm_start_time = datetime.now()
        chain = prompt | llm.bind_tools(tools)
        logger.info(f"[新闻分析师] 开始LLM调用，分析 {ticker} 的新闻")
        # 修复：传递字典而不是直接传递消息列表，以便 ChatPromptTemplate 能正确处理所有变量
        result = chain.invoke({"messages": state["messages"]})
        
        llm_end_time = datetime.now()
        llm_time_taken = (llm_end_time - llm_start_time).total_seconds()
        logger.info(f"[新闻分析师] LLM调用完成，耗时: {llm_time_taken:.2f}秒")

        # 使用统一的Google工具调用处理器
        if GoogleToolCallHandler.is_google_model(llm):
            logger.info(f"📊 [新闻分析师] 检测到Google模型，使用统一工具调用处理器")
            
            # 创建分析提示词
            analysis_prompt_template = GoogleToolCallHandler.create_analysis_prompt(
                ticker=ticker,
                company_name=company_name,
                analyst_type="新闻分析",
                specific_requirements="重点关注新闻事件对股价的影响、市场情绪变化、政策影响等。"
            )
            
            # 处理Google模型工具调用
            report, messages = GoogleToolCallHandler.handle_google_tool_calls(
                result=result,
                llm=llm,
                tools=tools,
                state=state,
                analysis_prompt_template=analysis_prompt_template,
                analyst_name="新闻分析师"
            )
        else:
            # 非Google模型的处理逻辑
            logger.info(f"[新闻分析师] 非Google模型 ({llm.__class__.__name__})，使用标准处理逻辑")

            # 检查工具调用情况
            current_tool_calls = len(result.tool_calls) if hasattr(result, 'tool_calls') else 0
            logger.info(f"[新闻分析师] LLM调用了 {current_tool_calls} 个工具")
            logger.debug(f"📊 [DEBUG] 累计工具调用次数: {tool_call_count}/{max_tool_calls}")

            if current_tool_calls == 0:
                logger.warning(f"[新闻分析师] ⚠️ {llm.__class__.__name__} 没有调用任何工具，启动补救机制...")
                logger.warning(f"[新闻分析师] 📄 LLM原始响应内容 (前500字符): {result.content[:500] if hasattr(result, 'content') else 'No content'}")

                try:
                    # 强制获取新闻数据
                    logger.info(f"[新闻分析师] 🔧 强制调用统一新闻工具获取新闻数据...")
                    logger.info(f"[新闻分析师] 📊 调用参数: stock_code={ticker}, max_news=10")

                    forced_news = unified_news_tool(stock_code=ticker, max_news=10, model_info=model_info)

                    logger.info(f"[新闻分析师] 📋 强制获取返回结果长度: {len(forced_news) if forced_news else 0} 字符")
                    logger.info(f"[新闻分析师] 📄 强制获取返回结果预览 (前500字符): {forced_news[:500] if forced_news else 'None'}")

                    if forced_news and len(forced_news.strip()) > 100:
                        logger.info(f"[新闻分析师] ✅ 强制获取新闻成功: {len(forced_news)} 字符")

                        # 基于真实新闻数据重新生成分析
                        forced_prompt = f"""
您是一位專業的財經新聞分析師。請基於以下最新獲取的新聞數據，對股票 {ticker}（{company_name}）進行詳細的新聞分析：

=== 最新新聞數據 ===
{forced_news}

=== 分析要求 ===
{system_message}

請基於上述真實新聞數據撰寫詳細的中文分析報告。
"""

                        logger.info(f"[新闻分析师] 🔄 基于强制获取的新闻数据重新生成完整分析...")
                        logger.info(f"[新闻分析师] 📝 强制提示词长度: {len(forced_prompt)} 字符")

                        forced_result = llm.invoke([{"role": "user", "content": forced_prompt}])

                        if hasattr(forced_result, 'content') and forced_result.content:
                            report = forced_result.content
                            logger.info(f"[新闻分析师] ✅ 强制补救成功，生成基于真实数据的报告，长度: {len(report)} 字符")
                            logger.info(f"[新闻分析师] 📄 报告预览 (前300字符): {report[:300]}")
                        else:
                            logger.warning(f"[新闻分析师] ⚠️ 强制补救LLM返回为空，使用原始结果")
                            report = result.content if hasattr(result, 'content') else ""
                    else:
                        logger.warning(f"[新闻分析师] ⚠️ 统一新闻工具获取失败或内容过短（{len(forced_news) if forced_news else 0}字符），使用原始结果")
                        if forced_news:
                            logger.warning(f"[新闻分析师] 📄 失败的新闻内容: {forced_news}")
                        report = result.content if hasattr(result, 'content') else ""

                except Exception as e:
                    logger.error(f"[新闻分析师] ❌ 强制补救过程失败: {e}")
                    import traceback
                    logger.error(f"[新闻分析师] 📋 异常堆栈: {traceback.format_exc()}")
                    report = result.content if hasattr(result, 'content') else ""
            else:
                # 有工具调用，直接使用结果
                report = result.content
        
        total_time_taken = (datetime.now() - start_time).total_seconds()
        logger.info(f"[新闻分析师] 新闻分析完成，总耗时: {total_time_taken:.2f}秒")

        # 🔧 修复死循环问题：返回清洁的AIMessage，不包含tool_calls
        # 这确保工作流图能正确判断分析已完成，避免重复调用
        from langchain_core.messages import AIMessage
        clean_message = AIMessage(content=report)

        logger.info(f"[新闻分析师] ✅ 返回清洁消息，报告长度: {len(report)} 字符")

        # 🔧 更新工具调用计数器
        return {
            "messages": [clean_message],
            "news_report": report,
            "news_tool_call_count": tool_call_count + 1
        }

    return news_analyst_node
