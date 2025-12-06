# TradingAgents 中文增強版

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/Version-cn--0.1.15-green.svg)](./VERSION)
[![Documentation](https://img.shields.io/badge/docs-中文文檔-green.svg)](./docs/)
[![Original](https://img.shields.io/badge/基於-TauricResearch/TradingAgents-orange.svg)](https://github.com/TauricResearch/TradingAgents)

>
> 🎓 **學習中心**: AI基礎 | 提示詞工程 | 模型選擇 | 多智能體分析原理 | 風險與局限 | 源項目與論文 | 實戰教程（部分為外鏈） | 常見問題
> 🎯 **核心功能**: 原生OpenAI支持 | Google AI全面集成 | 自定義端點配置 | 智能模型選擇 | 多LLM提供商支持 | 模型選擇持久化 | Docker容器化部署 | 專業報告導出 | 完整A股支持 | 中文本地化

面向中文使用者的**多智能體與大模型股票分析學習平台**。幫助你系統化學習如何使用多智能體交易框架與 AI 大模型進行合規的股票研究與策略實驗，不提供實盤交易指令，平台定位為學習與研究用途。

## 🙏 致敬源項目

感謝 [Tauric Research](https://github.com/TauricResearch) 團隊創造的革命性多智能體交易框架 [TradingAgents](https://github.com/TauricResearch/TradingAgents)！

**🎯 我們的定位與使命**: 專注學習與研究，提供中文化學習中心與工具，合規友好，支持 A股/港股/美股 的分析與教學，推動 AI 金融技術在中文社群的普及與正確使用。

## 🎉 v1.0.0-preview 版本上線 - 全新架構升級

> 🚀 **重磅發布**: v1.0.0-preview 版本現已正式！全新的 FastAPI + Vue 3 架構，帶來企業級的性能和體驗！

### ✨ 核心特性

#### 🏗️ **全新技術架構**
- **後端升級**: 從 Streamlit 遷移到 FastAPI，提供更強大的 RESTful API
- **前端重構**: 採用 Vue 3 + Element Plus，打造現代化的單頁應用
- **資料庫優化**: MongoDB + Redis 雙資料庫架構，性能提升 10 倍
- **容器化部署**: 完整的 Docker 多架構支持（amd64 + arm64）

#### 🎯 **企業級功能**
- **使用者權限管理**: 完整的使用者認證、角色管理、操作日誌系統
- **配置管理中心**: 可視化的大模型配置、資料來源管理、系統設定
- **快取管理系統**: 智慧快取策略，支持 MongoDB/Redis/檔案多級快取
- **即時通知系統**: SSE+WebSocket 雙通道推送，即時追蹤分析進度和系統狀態
- **批量分析功能**: 支持多支股票同時分析，提升工作效率
- **智能股票篩選**: 基於多維度指標的股票篩選和排序系統
- **自選股管理**: 個人自選股收藏、分組管理和追蹤功能
- **個股詳情頁**: 完整的個股資訊展示和歷史分析記錄
- **模擬交易系統**: 虛擬交易環境，驗證投資策略效果

#### 🤖 **智能分析增強**
- **動態供應商管理**: 支持動態新增和配置 LLM 供應商
- **模型能力管理**: 智慧模型選擇，根據任務自動匹配最佳模型
- **多資料來源同步**: 統一的資料來源管理，支持 Tushare、AkShare、BaoStock
- **報告導出功能**: 支持 Markdown/Word/PDF 多格式專業報告導出

#### 🐞 **重大Bug修復**
- **技術指標計算修復**: 徹底解決市場分析師技術指標計算不準確問題
- **基本面資料修復**: 修復基本面分析師PE、PB等關鍵財務資料計算錯誤
- **死迴圈問題修復**: 解決部分使用者在分析過程中觸發的無限迴圈問題
- **資料一致性優化**: 確保所有分析師使用統一、準確的資料來源

#### 🐳 **Docker 多架構支持**
- **跨平台部署**: 支持 x86_64 和 ARM64 架構（Apple Silicon、樹莓派、AWS Graviton）
- **GitHub Actions**: 自動化建置和發布 Docker 映像檔
- **一鍵部署**: 完整的 Docker Compose 配置，5 分鐘快速啟動

### 📊 技術棧升級

| 元件 | v0.1.x | v1.0.0-preview |
|------|--------|----------------|
| **後端框架** | Streamlit | FastAPI + Uvicorn |
| **前端框架** | Streamlit | Vue 3 + Vite + Element Plus |
| **資料庫** | 可選 MongoDB | MongoDB + Redis |
| **API 架構** | 單體應用 | RESTful API + WebSocket |
| **部署方式** | 本地/Docker | Docker 多架構 + GitHub Actions |



#### 📥 安裝部署

**三種部署方式，任選其一**：

| 部署方式 | 適用場景 | 難度 | 文檔連結 |
|---------|---------|------|---------|
| 🟢 **綠色版** | Windows 使用者、快速體驗 | ⭐ 簡單 | [綠色版安裝指南](https://mp.weixin.qq.com/s/eoo_HeIGxaQZVT76LBbRJQ) |
| 🐳 **Docker版** | 生產環境、跨平台 | ⭐⭐ 中等 | [Docker 部署指南](https://mp.weixin.qq.com/s/JkA0cOu8xJnoY_3LC5oXNw) |
| 💻 **本地程式碼版** | 開發者、客製化需求 | ⭐⭐⭐ 較難 | [本地安裝指南](https://mp.weixin.qq.com/s/cqUGf-sAzcBV19gdI4sYfA) |

⚠️ **重要提醒**：在分析股票之前，請按相關文檔要求，將股票資料同步完成，否則分析結果將會出現資料錯誤。



#### 📚 使用指南

在使用前，建議先閱讀詳細的使用指南：

- **[1、📘 TradingAgents-CN v1.0.0-preview 使用指南](https://mp.weixin.qq.com/s/ppsYiBncynxlsfKFG8uEbw)**
- **[2、📘 使用 Docker Compose 部署TradingAgents-CN v1.0.0-preview（完全版）](https://mp.weixin.qq.com/s/JkA0cOu8xJnoY_3LC5oXNw)**
- **[3、📘 從 Docker Hub 更新 TradingAgents‑CN 映像檔](https://mp.weixin.qq.com/s/WKYhW8J80Watpg8K6E_dSQ)**
- **[4、📘 TradingAgents-CN v1.0.0-preview綠色版安裝和升級指南](https://mp.weixin.qq.com/s/eoo_HeIGxaQZVT76LBbRJQ)**
- **[5、📘 TradingAgents-CN v1.0.0-preview綠色版埠配置說明](https://mp.weixin.qq.com/s/o5QdNuh2-iKkIHzJXCj7vQ)**
- **[6、📘 TradingAgents v1.0.0-preview 原始碼版安裝手冊（修訂版）](https://mp.weixin.qq.com/s/cqUGf-sAzcBV19gdI4sYfA)**
- **[7、📘 TradingAgents v1.0.0-preview 原始碼安裝影片教程](https://www.bilibili.com/video/BV1FxCtBHEte/?vd_source=5d790a5b8d2f46d2c10fd4e770be1594)**


使用指南包含：
- ✅ 完整的功能介紹和操作演示
- ✅ 詳細的配置說明和最佳實踐
- ✅ 常見問題解答和故障排除
- ✅ 實際使用案例和效果展示

#### 關注公眾號

1. **關注公眾號**: 微信搜尋 **"TradingAgents-CN"** 並關注
2. 公眾號每天推送項目最新進展和使用教程


- **微信公眾號**: TradingAgents-CN（推薦）

  <img src="assets/wexin.png" alt="微信公眾號" width="200"/>


## 🆚 中文增強特色

**相比原版新增**: 智能新聞解析 | 多層次新聞過濾 | 新聞品質評估 | 統一新聞工具 | 多LLM提供商整合 | 模型選擇持久化 | 快速切換按鈕 | | 實時進度顯示 | 智能會話管理 | 中文介面 | A股資料 | 國產LLM | Docker部署 | 專業報告導出 | 統一日誌管理 | Web配置介面 | 成本優化



## 🤝 貢獻指南

我們歡迎各種形式的貢獻：

### 貢獻類型

- 🐛 **Bug修復** - 發現並修復問題
- ✨ **新功能** - 新增新的功能特性
- 📚 **文檔改進** - 完善文檔和教程
- 🌐 **本地化** - 翻譯和本地化工作
- 🎨 **程式碼優化** - 性能優化和程式碼重構

### 貢獻流程

1. Fork 本倉庫
2. 建立特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 建立 Pull Request

### 📋 查看貢獻者

查看所有貢獻者和詳細貢獻內容：**[🤝 貢獻者名單](CONTRIBUTORS.md)**

## 📄 許可證

本項目採用**混合許可證**模式，詳見 [LICENSE](LICENSE) 檔案：

### 🔓 開源部分（Apache 2.0）
- **適用範圍**：除 `app/` 和 `frontend/` 外的所有檔案
- **權限**：商業使用 ✅ | 修改分發 ✅ | 私人使用 ✅ | 專利使用 ✅
- **條件**：保留版權聲明 ❗ | 包含許可證副本 ❗

### 🔒 專有部分（需商業授權）
- **適用範圍**：`app/`（FastAPI後端）和 `frontend/`（Vue前端）目錄
- **商業使用**：需要單獨授權協議
- **聯繫授權**：[hsliup@163.com](mailto:hsliup@163.com)

### 📋 許可證選擇建議
- **個人學習/研究**：可自由使用全部功能
- **商業應用**：請聯繫獲取專有元件授權
- **客製化開發**：歡迎諮詢商業合作方案

## 🙏 致謝與感恩

### 🌟 向源項目開發者致敬

我們向 [Tauric Research](https://github.com/TauricResearch) 團隊表達最深的敬意和感謝：

- **🎯 願景領導者**: 感謝您們在AI金融領域的前瞻性思考和創新實踐
- **💎 珍貴原始碼**: 感謝您們開源的每一行程式碼，它們凝聚著無數的智慧和心血
- **🏗️ 架構大師**: 感謝您們設計了如此優雅、可擴展的多智能體框架
- **💡 技術先驅**: 感謝您們將前沿AI技術與金融實務完美結合
- **🔄 持續貢獻**: 感謝您們持續的維護、更新和改進工作

### 🤝 社群貢獻者致謝

感謝所有為TradingAgents-CN項目做出貢獻的開發者和使用者！

詳細的貢獻者名單和貢獻內容請查看：**[📋 貢獻者名單](CONTRIBUTORS.md)**

包括但不限於：

- 🐳 **Docker容器化** - 部署方案優化
- 📄 **報告導出功能** - 多格式輸出支持
- 🐛 **Bug修復** - 系統穩定性提升
- 🔧 **程式碼優化** - 使用者體驗改進
- 📝 **文檔完善** - 使用指南和教程
- 🌍 **社群建設** - 問題回饋和推廣
- **🌍 開源貢獻**: 感謝您們選擇Apache 2.0協議，給予開發者最大的自由
- **📚 知識分享**: 感謝您們提供的詳細文檔和最佳實踐指導

**特別感謝**：[TradingAgents](https://github.com/TauricResearch/TradingAgents) 項目為我們提供了堅實的技術基礎。雖然Apache 2.0協議賦予了我們使用原始碼的權利，但我們深知每一行程式碼的珍貴價值，將永遠銘記並感謝您們的無私貢獻。

### 🇨🇳 推廣使命的初心

創建這個中文增強版本，我們懷著以下初心：

- **🌉 技術傳播**: 讓優秀的TradingAgents技術在中國得到更廣泛的應用
- **🎓 教育普及**: 為中國的AI金融教育提供更好的工具和資源
- **🤝 文化橋樑**: 在中西方技術社群之間搭建交流合作的橋樑
- **🚀 創新推動**: 推動中國金融科技領域的AI技術創新和應用

### 🌍 開源社群

感謝所有為本項目貢獻程式碼、文檔、建議和回饋的開發者和使用者。正是因為有了大家的支持，我們才能更好地服務中文使用者社群。

### 🤝 合作共贏

我們承諾：

- **尊重原創**: 始終尊重源項目的智慧財產權和開源協議
- **回饋貢獻**: 將有價值的改進和創新回饋給源項目和開源社群
- **持續改進**: 不斷完善中文增強版本，提供更好的使用者體驗
- **開放合作**: 歡迎與源項目團隊和全球開發者進行技術交流與合作

## 📈 版本歷史

- **v0.1.13** (2025-08-02): 🤖 原生OpenAI支持與Google AI生態系統全面整合 ✨ **最新版本**
- **v0.1.12** (2025-07-29): 🧠 智能新聞分析模組與項目結構優化
- **v0.1.11** (2025-07-27): 🤖 多LLM提供商整合與模型選擇持久化
- **v0.1.10** (2025-07-18): 🚀 Web介面實時進度顯示與智能會話管理
- **v0.1.9** (2025-07-16): 🎯 CLI使用者體驗重大優化與統一日誌管理
- **v0.1.8** (2025-07-15): 🎨 Web介面全面優化與使用者體驗提升
- **v0.1.7** (2025-07-13): 🐳 容器化部署與專業報告導出
- **v0.1.6** (2025-07-11): 🔧 阿里百煉修復與資料來源升級
- **v0.1.5** (2025-07-08): 📊 新增Deepseek模型支持
- **v0.1.4** (2025-07-05): 🏗️ 架構優化與配置管理重構
- **v0.1.3** (2025-06-28): 🇨🇳 A股市場完整支持
- **v0.1.2** (2025-06-15): 🌐 Web介面和配置管理
- **v0.1.1** (2025-06-01): 🧠 國產LLM整合

📋 **詳細更新日誌**: [CHANGELOG.md](./docs/releases/CHANGELOG.md)

## 📞 聯繫方式

- **GitHub Issues**: [提交問題和建議](https://github.com/hsliuping/TradingAgents-CN/issues)
- **郵箱**: hsliup@163.com
- 項目ＱＱ群：187537480
- 項目微信公眾號：TradingAgents-CN

  <img src="assets/wexin.png" alt="微信公眾號" width="200"/>

- **原項目**: [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents)
- **文檔**: [完整文檔目錄](docs/)

## ⚠️ 風險提示

**重要聲明**: 本框架僅用於研究和教育目的，不構成投資建議。

- 📊 交易表現可能因多種因素而異
- 🤖 AI模型的預測存在不確定性
- 💰 投資有風險，決策需謹慎
- 👨‍💼 建議諮詢專業財務顧問

---

<div align="center">

**🌟 如果這個項目對您有幫助，請給我們一個 Star！**

[⭐ Star this repo](https://github.com/hsliuping/TradingAgents-CN) | [🍴 Fork this repo](https://github.com/hsliuping/TradingAgents-CN/fork) | [📖 Read the docs](./docs/)

</div>

此專案為 <你的GitHub帳號> Fork 並進行個人學習改造
