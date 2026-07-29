# 東淦工程有限公司 (Jumbo Orient)
### 📋 eHRP 入職資料智能助手 (jo-ehrp-onboarding-assistant)

本工具專為東淦 HR 團隊設計。透過多模態 Vision AI 光學辨識與指向性資料來源核對（Source Grounding）技術，自動將新員工入職表格、僱傭合約、身份證及銀行卡影印本等複雜文件解析並標準化，精準對齊 eHRP 系統之欄位結構與資料格式 (Schema Alignment)，大幅提升 HR onboarding 自動化填表效率。

👉 **[點擊此處直接打開：東淦 eHRP 入職資料智能助手](https://jo-ehrp-onboard-assistant.streamlit.app/)**  
🌐 **[公司網站](https://jumboorient.com.hk/)**

---

## 💡 核心功能與設計亮點

* **指向性資料來源核對 (Source Grounding)：** 
  * **僱傭條件與薪酬：** 嚴格以《月薪僱傭合約》第 3 條及《面試評估表》為準（精準提煉 Rank, Grade, Point, Salary）。
  * **身份與戶口：** 嚴格以《香港身份證副本》核對全名與號碼；以《銀行卡影印本》核對銀行與帳號。
  * **履歷與證件：** 從《職位申請表 (HRF-006)》及各類專業證書副本（急救證、電工證、吊運 safety 等）提煉學歷、工作履歷及證書紀錄。
* **強效雙軌 Vision OCR 引擎：** 自動識別向量文字與影印本圖片，搭配高階 JPEG 轉碼與 100% 零幻視（Zero Hallucination）原則，不確定欄位寧缺勿濫，確保數據 100% 精準。
* **eHRP 系統欄位結構精準對齊 (Schema Mapping)：** 嚴格按 eHRP 微觀欄位名稱與選項進行標準化（如中文姓名自動拆分、部門名稱自動轉化為 HOF/PMD/HRD 等內部代碼），確保與 eHRP 資料庫及自動填表腳本無縫對接。
* **一鍵匯出與 Chrome Extension 對接：** 支援一鍵下載 JSON Clean Payload，方便搭配 Chrome 自動化擴充套件實現 1 秒一鍵填表。

---

## 🛠️ 使用說明書（HR 專員三步到位）

1. **拖入文件：** 打開網頁連結後，在側邊欄直接上傳新員工的入職表格、合約及證件附件合集（支援多頁 PDF 或圖片）。
2. **啟動解析：** 系統預設開啟「強制光學辨識」，點擊 **「🚀 開始解析並清洗數據」**，畫面將即時顯示頁面渲染與 AI 語意校驗進度。
3. **校對與下載：** 在對齊 eHRP 結構的 Tab 頁面中核對資料，無誤後可在「JSON 數據庫」Tab 下載 `.json` 檔案或複製 Payload 進行自動填表。

---

## 🛡️ ISO 國際標準與私隱管治合規 (AIMS & ISMS Compliance)

本系統在架構設計上嚴格遵從 **ISO/IEC 42001:2023 (人工智能管理系統 AIMS)**、**ISO/IEC 27001 (資訊安全管理系統 ISMS)** 及 **香港 Personal Data (Privacy) Ordinance (PDPO)** 的控制規範：

* **數據最小化與純 Session 記憶體 (ISO 42001 Annex A.6.2)：** 所有上傳之入職表格/CV 僅於 Streamlit 瀏覽器 Session 記憶體內進行格式標準化，系統無任何持久化資料庫。網頁一關閉或重新整理，所有 PII 個人資料即刻**瞬間物理銷毀**。
* **零 PII 外洩與憑證安全 (ISO 27001 A.8.12)：** API Key 採用 Streamlit Secrets 後端加密保護，前端 UI 完全隱藏；程式碼庫** 100% 無任何寫死之個人數據 (Zero Hardcoded PII)**。
* **零 AI 幻覺與可審計性 (Explainability - ISO 42001 Annex A.8.2)：** 嚴格限制 Vision AI 不得憑空臆測，不確定之欄位一律維持空白 `""`，確保輸出結果可追溯、可審計，符合 Human-in-the-Loop 管治要求。

---

## 📜 內部免責宣告
本系統為 HR onboarding 資料清洗與格式標準化輔助工具，其提取與對齊結果僅供內部校對使用。提交至 eHRP 系統前，HR 仍須手動確認核心數據之準確性。
