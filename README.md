# 東淦工程有限公司 Jumbo Orient Contracting Limited
### 📋 eHRP 入職資料智能助手 | eHRP Onboarding Assistant
`jo-ehrp-onboarding-assistant`

本工具專為東淦 HR 團隊設計。透過多模態 Vision AI 光學辨識與指向性資料來源核對（Source Grounding）技術，自動將新員工入職表格、僱傭合約、身份證及銀行卡影印本等複雜文件解析並標準化，精準對齊 eHRP 系統之欄位結構與資料格式 (Schema Alignment)，大幅提升 HR onboarding 自動化填表效率。

An AI-powered client-side helper tool designed for Jumbo Orient's HR team. Utilizing multimodal Vision AI and Source Grounding techniques, it automatically parses and normalizes onboarding forms, employment contracts, ID copies, and bank cards to ensure seamless field schema alignment with the eHRP system.

👉 **[點擊此處開啟應用程式 / Launch Web App](https://jo-ehrp-onboard-assistant.streamlit.app/)**  
🌐 **[東淦工程官方網站 / Official Website](https://jumboorient.com.hk/)**

---

## 💡 核心功能與設計亮點 / Key Features & Highlights

* **🎯 指向性資料來源核對 (Source Grounding / Multi-source Verification)：** 
  * **僱傭條件與薪酬 / Employment Terms & Salary:** 嚴格以《月薪僱傭合約》第 3 條及《面試評估表》為絕對準則提煉 Rank, Grade, Point 及 Salary。 (Strictly grounded on Clause 3 of the Employment Contract and Interview Evaluation Form).
  * **身份與戶口 / Identity & Bank Account:** 嚴格以《香港身份證副本》核對全名與號碼；以《銀行卡影印本》核對銀行與帳號。 (Strictly verified against HKID and Bank Card copies).
  * **履歷與證件 / Background & Qualifications:** 從《職位申請表 (HRF-006)》、《CV》及各類專業證書副本（急救證、電工證、吊運 safety 等）提煉學歷、工作履歷及證書紀錄。 (Extracted from Job Application Forms, CVs, and professional certificates).
* **👁️ 強效雙軌 Vision OCR 引擎 / Dual-engine Vision OCR:** 自動識別向量文字與影印本圖片，搭配高階 JPEG 轉碼與 100% 零幻視（Zero Hallucination）原則，不確定欄位寧缺勿濫，確保數據 100% 精準。 (Combines vector text extraction with Vision OCR, adhering to Zero Hallucination principles by leaving uncertain fields blank).
* **📐 eHRP 欄位結構精準對齊 / Precision Schema Mapping:** 嚴格按 eHRP 微觀欄位名稱與選項進行標準化（如中文姓名自動拆分、部門名稱自動轉化為 HOF/PMD/HRD 等內部代碼），與 eHRP 資料庫及自動填表腳本無縫對接。 (Normalizes data structure, splitting Chinese names and converting department names to internal codes like HOF/PMD).
* **📦 一鍵匯出 JSON Payload / One-click Export for Chrome Extension:** 支援一鍵下載 JSON Clean Payload，方便搭配 Chrome 自動化擴充套件實現 1 秒一鍵填表。 (Allows 1-click JSON export for automated form filling via Chrome Extensions).

---

## 🛠️ 使用說明書 / User Guide (3-Step Workflow)

1. **上傳文件 / Upload Files:** 打開網頁連結後，在側邊欄上傳新員工的入職表格、合約及證件附件合集（支援多頁 PDF 或圖片）。 (Upload the onboarding package, contract, and document scans via the sidebar).
2. **啟動解析 / Start Processing:** 點擊 **「🚀 開始解析並清洗數據」**，畫面將即時顯示頁面渲染與 AI 語意校驗進度。 (Click "Start Parsing" and monitor the real-time processing progress).
3. **校對與下載 / Review & Export:** 在對齊 eHRP 結構的 Tab 頁面中核對資料，無誤後可在「JSON 數據庫」Tab 下載 `.json` 檔案進行自動填表。 (Review data in structured tabs and download the `.json` payload).

---

## 🛡️ ISO 國際標準與私隱管治合規 / Governance & Compliance (AIMS & ISMS)

本系統在架構設計上嚴格遵從 **ISO/IEC 42001:2023 (人工智能管理系統 AIMS)**、**ISO/IEC 27001 (資訊安全管理系統 ISMS)** 及 **香港 Personal Data (Privacy) Ordinance (PDPO)** 的控制規範：

* **數據最小化與純 Session 記憶體 (Data Minimization - ISO 42001 Annex A.6.2)：** 所有上傳文件僅於 Streamlit 瀏覽器 Session 記憶體內處理，系統無任何持久化資料庫。網頁關閉即刻**瞬間物理銷毀**。 (All data resides purely in session memory and is destroyed immediately upon session reset or tab closure).
* **零 PII 外洩與憑證安全 (Data Leakage Protection - ISO 27001 A.8.12)：** API Key 加密保護，前端 UI 完全隱藏；程式碼庫 **100% 無任何寫死之個人數據 (Zero Hardcoded PII)**。 (Secrets are backend-encrypted; repository maintains zero hardcoded PII).
* **零 AI 幻覺與可審計性 (Explainability & Trust - ISO 42001 Annex A.8.2)：** 嚴格限制 Vision AI 不得憑空臆測，不確定欄位維持空白 `""`，確保輸出結果可追溯，符合 Human-in-the-Loop 管治要求。 (Uncertain fields remain empty to prevent hallucinations and maintain human-in-the-loop oversight).

---

## 📜 免責宣告 / Disclaimer
本系統為 HR onboarding 資料清洗與格式標準化輔助工具，其提取與對齊結果僅供內部 HR 專員校對使用。提交至 eHRP 系統前，HR 專員仍須手動確認核心數據之準確性。  
This tool serves as an administrative assistant for onboarding data normalization. Final verification by HR professionals is required prior to submitting data to the eHRP system.
