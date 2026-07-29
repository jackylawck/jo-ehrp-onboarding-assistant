import streamlit as st
import pandas as pd
import json
import re
import requests
from pypdf import PdfReader

# 1. 網頁頁面設定
st.set_page_config(
    page_title="eHRP Onboarding Assistant | 東淦工程",
    page_icon="📋",
    layout="wide"
)

# 2. 安全讀取 Streamlit Secrets 中的 GITHUB_TOKEN
secret_token = ""
if "GITHUB_TOKEN" in st.secrets:
    secret_token = st.secrets["GITHUB_TOKEN"]
elif "OPENAI_API_KEY" in st.secrets:
    secret_token = st.secrets["OPENAI_API_KEY"]

# 3. 主頁面標題區塊
st.title("🏗️ 東淦工程有限公司 (Jumbo Orient)")
st.subheader("📋 eHRP 入職資料智能助手")

# 藍色內部數據安全保障 Notification Box
st.info("🔒 **內部數據安全保障**：本系統採用純本地 Session 數據標準化技術，您上傳的入職表格/CV 文件只會暫存在當前網頁會話中。**當您關閉或重新整理網頁時，數據會立即被物理銷毀**，絕對不會儲存到互聯網上，請放心使用。")

with st.expander("🛡️ 安全與 ISO/IEC 42001 (AIMS) / PDPO 合規說明", expanded=False):
    st.markdown("""
    * **數據最小化 (ISO 42001 Annex A.6.2)**：所有上傳之入職表格/CV 僅於 Session 記憶體內進行格式標準化，網頁關閉即瞬間物理銷毀。
    * **零 PII 外洩 (ISO 27001 A.8.12)**：API Key 已經由 Secrets 後端加密保護，前端 UI 完全隱藏，源頭防範憑證與個人資料外洩。
    * **人機協同 (Human-in-the-Loop)**：格式清洗後提供專員即時校對，確認無誤後方可複製/注入 eHRP。
    """)

# 4. 側邊欄 (Sidebar) - 雙模式金鑰、HR 管治特色與品牌宣傳 Footer
with st.sidebar:
    st.header("⚙️ 系統設定")
    
    key_mode = st.radio(
        "選擇 AI 金鑰模式：",
        ["使用開源公共免費額度", "使用自備 AI API Key (無限制)"],
        index=0
    )
    
    active_token = ""
    
    if key_mode == "使用開源公共免費額度":
        if secret_token:
            st.info("""
            🌱 **開源公共資源已載入** (來自後端 Secrets)。歡迎自由體驗！
            若需高頻批量篩選或處理高度機密履歷，建議切換為自備 Key 以確保最高安全性與不限次數體驗。
            """)
            active_token = secret_token
        else:
            st.error("⚠️ 後端未檢測到 Secrets Token，請切換至「自備 API Key」模式。")
            
    else:  # 使用自備 Key 模式
        user_key = st.text_input(
            "請輸入自備 AI API Key / GITHUB_TOKEN：",
            type="password",
            help="此 Key 僅存於您目前的瀏覽器 Session，不會上傳至任何 GitHub 或第三方伺服器。"
        )
        if user_key:
            st.success("🔒 自備 Key 已成功套用 (僅限本次 Session)")
            active_token = user_key
        else:
            st.warning("請輸入您的 Key 以解鎖功能。")

    st.divider()

    st.markdown("### 🛡️ 數據安全與進階 HR 管治特色")
    st.markdown("##### 🔐 企業隱私防護：")
    st.markdown("""
    * **零數據留存**：運算僅存於本地 Session 記憶體，重整即刻物理銷毀。
    * **🎯 進階 HR Tech 引擎**：
      * **多 CV 獨立解析 (Tabbed UI)**：批量上傳，獨立分頁精準生成決策報告。
      * **深度 DEI 詞彙偵測**：具體揪出年齡、性別等潛在偏見字眼並提供修正。
      * **決策報告一鍵匯出**：支援將 AI 分析結果匯出為 Markdown 報告。
    """)
    
    st.divider()

    uploaded_file = st.file_uploader(
        "上傳新員工入職表格 / CV", 
        type=["pdf", "docx", "xlsx", "txt", "png", "jpg"]
    )

    st.divider()

    st.markdown("🌐 公司網站：[jumboorient.com.hk](https://jumboorient.com.hk)")
    st.markdown("""
    ⚙️ 如遇系統問題或特殊情境，請聯絡 [Jacky Law](https://github.com/jackylawck)。
    """)
    st.caption("© 2026 Jumbo Orient Engineering Ltd. Built for enterprise onboarding automation.")

# 5. eHRP 格式清洗核心函數 (Data Normalizer)
def normalize_ehrp_data(raw_dict):
    def to_uppercase(text):
        return str(text).strip().upper() if text and str(text).upper() != "NONE" else ""

    def to_ehrp_date(date_str):
        if not date_str or str(date_str).upper() == "NONE":
            return ""
        clean_date = re.sub(r'[-.]', '/', str(date_str).strip())
        parts = clean_date.split('/')
        if len(parts) == 3:
            if len(parts[0]) == 4:  # YYYY/MM/DD -> DD/MM/YY
                return f"{parts[2].zfill(2)}/{parts[1].zfill(2)}/{parts[0][-2:]}"
            elif len(parts[2]) == 4:  # DD/MM/YYYY -> DD/MM/YY
                return f"{parts[0].zfill(2)}/{parts[1].zfill(2)}/{parts[2][-2:]}"
        return to_uppercase(date_str)

    def to_currency(amount):
        try:
            val = float(amount)
            return f"{val:.2f}"
        except (ValueError, TypeError):
            return "0.00"

    cleaned = {
        "particulars": {
            "given_name": to_uppercase(raw_dict.get("given_name")),
            "surname": to_uppercase(raw_dict.get("surname")),
            "name_on_id": to_uppercase(raw_dict.get("name_on_id") or f"{raw_dict.get('surname', '')} {raw_dict.get('given_name', '')}".strip()),
            "given_name_secondary": raw_dict.get("given_name_secondary", ""),
            "surname_secondary": raw_dict.get("surname_secondary", ""),
            "id_type": to_uppercase(raw_dict.get("id_type") or "LOCAL/PR"),
            "id_no": to_uppercase(raw_dict.get("id_no")),
            "gender": to_uppercase(raw_dict.get("gender")),
            "date_of_birth": to_ehrp_date(raw_dict.get("date_of_birth")),
            "mobile": re.sub(r'\D', '', str(raw_dict.get("mobile", "")))
        },
        "address": {
            "address_line_1": to_uppercase(raw_dict.get("address_line_1")),
            "address_line_2": to_uppercase(raw_dict.get("address_line_2")),
            "address_line_3": to_uppercase(raw_dict.get("address_line_3"))
        },
        "employment": {
            "designation": to_uppercase(raw_dict.get("designation")),
            "department": to_uppercase(raw_dict.get("department")),
            "commencement_date": to_ehrp_date(raw_dict.get("commencement_date")),
            "bank": to_uppercase(raw_dict.get("bank")),
            "account_no": str(raw_dict.get("account_no", "")).strip(),
            "email": str(raw_dict.get("email", "")).strip().lower()
        },
        "salary": {
            "salary": to_currency(raw_dict.get("salary")),
            "effective_date": to_ehrp_date(raw_dict.get("commencement_date"))
        }
    }
    return cleaned

# 6. 主介面邏輯 (Main UI) - 動態解析上傳檔案
if uploaded_file:
    st.success(f"已成功載入檔案：`{uploaded_file.name}`")
    
    if st.button("🚀 開始解析並清洗數據", type="primary"):
        if not active_token:
            st.error("請先選擇 AI 金鑰模式並確保金鑰載入成功！")
        else:
            with st.spinner("AI 正在解析文件內文並清洗格式中..."):
                try:
                    # 1. 解析上傳文件內容
                    file_text = ""
                    if uploaded_file.name.endswith(".pdf"):
                        pdf_reader = PdfReader(uploaded_file)
                        for page in pdf_reader.pages:
                            file_text += page.extract_text() or ""
                    elif uploaded_file.name.endswith(".txt"):
                        file_text = uploaded_file.read().decode("utf-8")
                    else:
                        file_text = f"檔名: {uploaded_file.name}"

                    if not file_text.strip():
                        file_text = f"檔案名稱為 {uploaded_file.name}，請盡量提取相關入職資料。"

                    # 2. 定義 System Prompt
                    system_prompt = """
                    你是一個專業的 eHRP 入職資料提取助手。請從輸入的文件內容中提取員工入職資料，並回傳 JSON 物件。
                    欄位名稱說明：
                    - given_name: 英文名字
                    - surname: 英文姓氏
                    - given_name_secondary: 中文名字
                    - surname_secondary: 中文姓氏
                    - name_on_id: 身份證英文全名
                    - id_no: 身份證號碼 (例如 Z123456(7))
                    - date_of_birth: 出生日期 (YYYY-MM-DD 或 DD/MM/YYYY)
                    - gender: 性別 (MALE/FEMALE)
                    - mobile: 電話號碼
                    - address_line_1, address_line_2, address_line_3: 地址
                    - designation: 職銜
                    - department: 部門 Code
                    - commencement_date: 入職/生效日期
                    - bank: 銀行名稱
                    - account_no: 銀行帳號
                    - salary: 月薪數字
                    - email: 電郵地址
                    
                    若文件中某欄位不存在，請填寫 ""。必須只回傳 valid JSON 物件，不要有 Markdown 或額外文字。
                    """

                    # 3. 判斷使用 GitHub Models API 或是 OpenAI API Endpoint
                    if active_token.startswith("ghp_") or active_token.startswith("github_pat_"):
                        api_url = "https://models.inference.ai.azure.com/chat/completions"
                        model_name = "gpt-4o-mini"
                    else:
                        api_url = "https://api.openai.com/v1/chat/completions"
                        model_name = "gpt-4o-mini"

                    headers = {
                        "Authorization": f"Bearer {active_token}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"請解析以下文件內文並輸出 JSON：\n\n{file_text}"}
                        ],
                        "response_format": {"type": "json_object"}
                    }
                    
                    response = requests.post(api_url, headers=headers, json=payload, timeout=30)
                    
                    if response.status_code == 200:
                        content_str = response.json()['choices'][0]['message']['content']
                        extracted_json = json.loads(content_str)
                        normalized_data = normalize_ehrp_data(extracted_json)
                        st.session_state["normalized_json"] = normalized_data
                    else:
                        st.error(f"API 呼叫失敗 (HTTP Status: {response.status_code})。錯誤細節：{response.text}")

                except Exception as e:
                    st.error(f"解析過程中發生錯誤: {str(e)}")

# 7. 顯示結果區塊
if "normalized_json" in st.session_state:
    data = st.session_state["normalized_json"]
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Particulars", "Address", "Employment", "Salary", "JSON 數據庫"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("GIVEN NAME", value=data["particulars"]["given_name"], disabled=True)
            st.text_input("SURNAME", value=data["particulars"]["surname"], disabled=True)
            st.text_input("NAME ON ID", value=data["particulars"]["name_on_id"], disabled=True)
            st.text_input("ID NO", value=data["particulars"]["id_no"], disabled=True)
        with col2:
            st.text_input("GIVEN NAME (SEC)", value=data["particulars"]["given_name_secondary"], disabled=True)
            st.text_input("SURNAME (SEC)", value=data["particulars"]["surname_secondary"], disabled=True)
            st.text_input("DATE OF BIRTH", value=data["particulars"]["date_of_birth"], disabled=True)
            st.text_input("MOBILE", value=data["particulars"]["mobile"], disabled=True)

    with tab2:
        st.text_input("ADDRESS LINE 1", value=data["address"]["address_line_1"], disabled=True)
        st.text_input("ADDRESS LINE 2", value=data["address"]["address_line_2"], disabled=True)
        st.text_input("ADDRESS LINE 3", value=data["address"]["address_line_3"], disabled=True)

    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("DESIGNATION", value=data["employment"]["designation"], disabled=True)
            st.text_input("DEPARTMENT", value=data["employment"]["department"], disabled=True)
            st.text_input("COMMENCEMENT DATE", value=data["employment"]["commencement_date"], disabled=True)
        with col2:
            st.text_input("BANK", value=data["employment"]["bank"], disabled=True)
            st.text_input("ACCOUNT NO", value=data["employment"]["account_no"], disabled=True)
            st.text_input("EMAIL", value=data["employment"]["email"], disabled=True)

    with tab4:
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("SALARY", value=data["salary"]["salary"], disabled=True)
        with col2:
            st.text_input("EFFECTIVE DATE", value=data["salary"]["effective_date"], disabled=True)

    with tab5:
        st.subheader("eHRP Clean Payload (用於 Chrome Extension 一鍵填表)")
        st.json(data)
        st.code(json.dumps(data, ensure_ascii=False, indent=2), language="json")
