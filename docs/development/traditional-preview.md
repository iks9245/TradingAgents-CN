# 可穩定跑完一次分析的繁體預覽版

此里程碑驗證「登入 → 單股分析 → 查看／匯出報告 → 模擬交易」。它不代表所有市場、模型、匯出格式及介面均已完成驗收。

## 修復範圍

- 補回風險管理器兩處多行字串結尾，恢復分析引擎載入。
- JSON 與備援文字解析同時接受繁體、簡體、英文動作；優先讀取最終建議，避免辯論中的買入字眼覆蓋最終賣出。
- 保持既有 API 的簡體動作值，避免破壞下游介面；原始報告保留模型輸出的文字。
- 報告頁支援繁體買賣建議與目標價，能銜接模擬訂單。
- 市場分析、研究辯論、交易員及風險評估提示明確要求繁體中文；並非將簡體輸出事後轉字。
- 儀表板與模擬交易頁保留多幣別帳戶的零值，避免將整個物件傳給數值格式化函式。
- 美股／港股任務建立時，不再呼叫僅支援 A 股的名稱查詢服務。
- 統一 `yfinance`／`yahoo_finance` 資料源名稱，避免預設免費行情來源被跳過。
- 報告轉模擬交易支援美股 1 股起、正確幣別；行情不可用時阻止下單，不再預填虛構價格。確認框明示市價單，移除不會傳至後端的可編輯價格。
- 日期選擇器送出本地日曆日期；報告保存使用研究日期，建立時間另存於 `created_at`。
- 將資料庫中的模型輸出上限、溫度、逾時及重試設定傳入分析引擎，避免一直使用預設 4,000 token 而截斷報告。
- 阻止分析引擎把執行期 API key 複製到一般 `settings.json`；模型仍從程序內取得憑證。
- 修正既有行業補充腳本的 `async def` 語法，使全庫語法檢查可執行。

## 自動驗證

GitHub workflow：`.github/workflows/preview-ci.yml`。PR、main 推送及手動觸發均會執行。

後端使用 Python 3.11、`pyproject.toml` 搭配既有 `requirements-lock.txt` 的版本約束。CI 啟動獨立 MongoDB 7 與 Redis 7；只執行 `tests/preview`，不掃描會呼叫真實供應商的舊測試腳本。

```sh
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r pyproject.toml -c requirements-lock.txt pytest pytest-asyncio
.venv/bin/python scripts/validation/check_python_syntax.py
.venv/bin/python -m pytest -q tests/preview
```

最後一條命令在未啟用隔離資料庫時，會明確跳過 API 整合驗收。完整 API 測試需要先启动以下本機容器；若名稱或連接埠已存在，使用現有驗收容器或改用其他獨立連接埠。

```sh
docker run -d --rm --name tradingagents-preview-mongo -p 127.0.0.1:27028:27017 mongo:7
docker run -d --rm --name tradingagents-preview-redis -p 127.0.0.1:6388:6379 redis:7-alpine
PREVIEW_INTEGRATION=1 MONGODB_HOST=127.0.0.1 MONGODB_PORT=27028 MONGODB_DATABASE=tradingagents_preview_acceptance REDIS_HOST=127.0.0.1 REDIS_PORT=6388 REDIS_ENABLED=true JWT_SECRET=local-preview-only .venv/bin/python -m pytest -q tests/preview
```

整合驗收使用真實認證、JWT、API 路由、代理圖、MongoDB 報告保存、Markdown／JSON 下載，以及模擬帳戶／持倉／訂單。LLM、行情與資料準備使用明確標示的離線資料，不耗供應商額度。另驗證錯誤密碼、未登入存取與超額賣出。

```sh
cd frontend
npx --yes yarn@1.22.22 install --frozen-lockfile --production=false --registry https://registry.npmjs.org
npx vite build
node scripts/check-type-regressions.mjs
node --experimental-strip-types --test tests/*.test.mjs
```

先建置再做型別檢查，讓 Vue 自動匯入宣告生成。嚴格型別檢查仍有既有技術債；`scripts/typecheck-baseline.json` 記錄目前的 242 項診斷，CI 按檔案、錯誤碼、訊息及數量拒絕新增錯誤。它**不表示 `npm run type-check` 或含全量型別檢查的 `npm run build` 已通過**。修復舊錯誤後應刪除對應基準，不能以增加基準來繞過新錯誤。

## 本機瀏覽器驗收

```sh
.venv/bin/python -m tests.preview.serve
```

這個明確獨立的測試入口啟動真實 API，省略排程同步作業，預設套用離線外部服務。僅監聽 `127.0.0.1:8018`，使用 `tradingagents_preview_browser` 資料庫。另開終端：

```sh
cd frontend
VITE_PROXY_TARGET=http://127.0.0.1:8018 npm run dev -- --host 127.0.0.1 --port 3018
```

開啟 `http://127.0.0.1:3018`。測試帳戶為 `preview-user`，密碼為 `Preview-Local-Only-2026`，僅適用於此隔離環境。此入口不應用於公開部署。

若已明確授權使用 OpenClaw 的 MiMo 設定，可指定 `PREVIEW_OPENCLAW_CONFIG=/absolute/path/to/openclaw.json` 啟動同一入口。它只讀取 `models.providers.xiaomi-coding`，將金鑰放入伺服器程序環境，不寫入專案設定或測試資料庫；改用真實 MiMo 與真實行情服務。**CI 永遠不設定此變數。**

MiMo 驗收設定使用 8,192 token 輸出上限。4,000 token 的試跑曾將市場章節截斷，不能只依據任務完成狀態判定報告完整；應同時檢查章節尾端。當模型或報告長度改變時，仍需重新驗證輸出上限。

人工驗收步驟：

1. 登入，確認儀表板的零持倉與三幣別帳戶能顯示。
2. 選 AAPL、快速分析、市場分析師；確認模型為 MiMo v2.5、日期與送出值一致。
3. 等待任務完成，確認最終決策、研究辯論與風險報告都有內容。
4. 查看報告，下載 Markdown／JSON；確認包含繁體內容。
5. 在模擬交易中提交測試訂單，核對成交、USD 現金與持倉；這不是券商實盤交易。

測試資料存在獨立、無具名資料卷的容器中。停止上述兩個 `--rm` 容器會移除驗收資料；需要留存的報告應先下載。瀏覽器截圖與本機報告保存在忽略版控的 `output/playwright/`。

## 2026-09-11 本機驗收紀錄

- 分支：`codex/stable-zh-tw-preview`，基於 main `db894c7`。以下為提交 PR 前的本機驗收紀錄；遠端 CI 結果以 PR checks 為準。
- Python 3.11 隔離環境：37 項測試通過；另於全新、依 CI 約束安裝的環境重跑 37 項通過。
- 1,040 個 Python 檔案語法檢查通過；Vite production build、3 項前端測試及型別增量檢查通過（242 項既有診斷、0 新增）。
- 真實模型：MiMo v2.5，實際輸出上限 8,192；真實行情來源 yfinance。AAPL、研究日期 2025-12-05、快速深度、市場分析師，保留研究與風險辯論。
- 最後完整任務：`af98e369-1058-4546-8987-b936215ba3af`，耗時約 386 秒，11 個章節均有內容，各章尾端已人工檢查；市場章節不再截斷。
- 報告：`AAPL_20260910_222924`；瀏覽器實際下載 Markdown（61,239 bytes）及 JSON（64,940 bytes），研究日期正確。
- 模擬訂單：先買入 2 股、前一份報告連動賣出 1 股、最後完整報告連動買入 1 股，均以測試行情約 USD 326.57 成交。最終 AAPL 持倉 2 股、USD 現金 99,346.86；CNY/HKD 帳戶未變。
- 匯出與截圖：`output/playwright/mimo-preview-report.md`、同名 `.json`、`report-to-paper-confirm.png`、`paper-journey-completed.png`，均不納入版控。
- 安全檢查曾發現舊程式將執行期金鑰複製至忽略版控的 `config/settings.json`；副本已移除，新增防落盤修復與測試。原始 OpenClaw 設定未更動，重掃專案變更、驗收輸出、伺服器日誌及隔離資料庫未發現該金鑰副本。

此結果驗收的是指定組合的一次完整流程，不是所有設定的可靠性保證。市場分析與最終風控正文為繁體，但部分中間辯論仍回覆簡體；原始模型輸出未事後轉字，語系一致性仍待改善。

## 尚未涵蓋

- 全站繁體介面統一與全部既有型別錯誤清理。
- PDF／Word 的渲染品質、多市場並發、完整供應商矩陣。
- 取消與程序重啟恢復：實測現有取消 API 對單股背景任務回傳 400；中止的本機驗收任務已明確標記失敗。應統一 QueueService 與單股任務生命週期，不能將本預覽視為可可靠取消／復原。
- 自動偵測模型 `finish_reason=length` 並提示／補全；目前以足夠輸出上限與人工章節尾端檢查驗收。
- 分析輸出的投資正確性、目標價合理性及回測績效。
