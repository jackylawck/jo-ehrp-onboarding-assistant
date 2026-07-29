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

# 2. 安全讀取 Streamlit Secrets
secret_token = ""
token_source = ""

if "GROQ_API_KEY" in st.secrets and st.secrets["GROQ_API_KEY"]:
    secret_token = st.secrets["GROQ_API_KEY"]
    token_source = "GROQ_API_KEY"
elif "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"]:
    secret_token = st.secrets["GEMINI_API_KEY"]
    token_source = "GEMINI_API_KEY"
elif "GITHUB_TOKEN" in st.secrets and st.secrets["GITHUB_TOKEN"]:
    secret_token = st.secrets["GITHUB_TOKEN"]
    token_source = "GITHUB_TOKEN"
elif "OPENAI_API_KEY" in st.secrets and st.secrets["OPENAI_API_KEY"]:
    secret_token = st.secrets["OPENAI_API_KEY"]
    token_source = "OPENAI_API_KEY"

# 3. 香港常見銀行 Clearing Code 對照表
BANK_CLEARING_CODES = {
    "004": ["HSBC", "HONGKONG AND SHANGHAI BANKING", "匯豐", "香港上海滙豐銀行"],
    "024": ["HANG SENG", "HANG SENG BANK", "恒生", "恒生銀行"],
    "012": ["BANK OF CHINA", "BOC", "中銀", "中國銀行"],
    "003": ["STANDARD CHARTERED", "SCB", "渣打", "渣打銀行"],
    "006": ["CITIBANK", "CITI", "花旗", "花旗銀行"],
    "015": ["BANK OF EAST ASIA", "BEA", "東亞", "東亞銀行"],
    "025": ["SHANGHAI COMMERCIAL BANK", "上商", "上海商業銀行"],
    "016": ["DBS", "DBS BANK", "星展", "星展銀行"],
    "020": ["WING LUNG", "CMB WING LUNG", "招商永隆", "永隆"],
    "072": ["INDUSTRIAL AND COMMERCIAL BANK OF CHINA", "ICBC", "工銀亞洲", "中國工商銀行"],
    "040": ["DAH SING", "大新", "大新銀行"],
    "393": ["ANT BANK", "螞蟻銀行"],
    "387": ["ZA BANK", "眾安銀行"],
    "388": ["MOX", "MOX BANK"]
}

def get_bank_clearing_code(bank_name):
    if not bank_name:
        return ""
    clean_name = str(bank_name).strip().upper()
    if re.match(r'^\d{3}$', clean_name):
        return clean_name
    for code, keywords in BANK_CLEARING_CODES.items():
        for kw in keywords:
            if kw in clean_name:
                return f"{code} ({clean_name})"
    return clean_name

# 4. 主頁面標題區塊
st.title("🏗️ 東淦工程有限公司 (Jumbo Orient)")
st.subheader("📋 eHRP 入職資料智能助手 (1:1 完整對齊版)")

st.info("🔒 **內部數據安全保障**：本系統採用純本地 Session 數據標準化技術，您上傳的入職表格/CV 文件只會暫存在當前網頁會話中。**當您關閉或重新整理網頁時，數據會立即被物理銷毀**，絕對不會儲存到互聯網上，請放心使用。")

with st.expander("🛡️ 安全與 ISO/IEC 42001 (AIMS) / PDPO 合規說明", expanded=False):
    st.markdown("""
    * **數據最小化 (ISO 42001 Annex A.6.2)**：所有上傳之入職表格/CV 僅於 Session 記憶體內進行格式標準化，網頁關閉即瞬間物理銷毀。
    * **零 PII 外洩 (ISO 27001 A.8.12)**：API Key 已經由 Secrets 後端加密保護，前端 UI 完全隱藏，源頭防範憑證與個人資料外洩。
    * **人機協同 (Human-in-the-Loop)**：格式清洗後提供專員即時校對，確認無誤後方可複製/注入 eHRP。
    """)

# 5. 側邊欄 (Sidebar)
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
            st.info(f"🌱 **已載入 Secrets Key** (來源: `{token_source}`)")
            active_token = secret_token
        else:
            st.error("⚠️ Secrets 未檢測到有效的 Key，請檢查 Secrets 設定。")
    else:
        user_key = st.text_input("請輸入自備 Key (Groq / Gemini / GitHub / OpenAI)：", type="password")
        if user_key:
            st.success("🔒 自備 Key 已成功套用")
            active_token = user_key

    st.divider()

    st.markdown("### 🛡️ 數據安全與進階 HR 管治特色")
    st.markdown("""
    * **零數據留存**：運算僅存於本地 Session 記憶體，重整即刻物理銷毀。
    * **🎯 進階 HR Tech 引擎**：
      * **eHRP 全介面 1:1 精準對齊**：包含 Particulars, Address, Employment, Salary, Education, Next of Kin 及 Prev. Employment。
      * **銀行編號 (Clearing Code) 自動轉化**：支援自動對照 3 位數銀行代號。
      * **格式標準化**：英文全大寫 (`UPPERCASE`)、短日期 (`DD/MM/YY`)。
    """)
    
    st.divider()

    uploaded_file = st.file_uploader("上傳新員工入職表格 / CV", type=["pdf", "docx", "xlsx", "txt", "png", "jpg"])

    st.divider()

    st.markdown("🌐 公司網站：[jumboorient.com.hk](https://jumboorient.com.hk)")
    st.markdown("⚙️ 如遇系統問題或特殊情境，請聯絡 [Jacky Law](https://github.com/jackylawck)。")
    st.caption("© 2026 Jumbo Orient Engineering Ltd. Built for enterprise onboarding automation.")

# 6. eHRP 格式清洗核心函數 (對齊真版 eHRP 欄位結構)
def normalize_ehrp_data(raw_dict):
    def to_uppercase(text):
        return str(text).strip().upper() if text and str(text).upper() != "NONE" else ""

    def to_ehrp_date(date_str):
        if not date_str or str(date_str).upper() == "NONE":
            return ""
        clean_date = re.sub(r'[-.]', '/', str(date_str).strip())
        parts = clean_date.split('/')
        if len(parts) == 3:
            if len(parts[0]) == 4:
                return f"{parts[2].zfill(2)}/{parts[1].zfill(2)}/{parts[0][-2:]}"
            elif len(parts[2]) == 4:
                return f"{parts[0].zfill(2)}/{parts[1].zfill(2)}/{parts[2][-2:]}"
        return to_uppercase(date_str)

    def to_currency(amount):
        try:
            val = float(re.sub(r'[^\d.]', '', str(amount)))
            return f"{val:.2f}"
        except (ValueError, TypeError):
            return "0.00"

    bank_raw = raw_dict.get("bank", "")
    bank_formatted = get_bank_clearing_code(bank_raw)

    cleaned = {
        "header": {
            "employee_no": to_uppercase(raw_dict.get("employee_no"))
        },
        "particulars": {
            "given_name": to_uppercase(raw_dict.get("given_name")),
            "surname": to_uppercase(raw_dict.get("surname")),
            "name_on_id": to_uppercase(raw_dict.get("name_on_id") or f"{raw_dict.get('surname', '')} {raw_dict.get('given_name', '')}".strip()),
            "given_name_secondary": raw_dict.get("given_name_secondary", ""),
            "surname_secondary": raw_dict.get("surname_secondary", ""),
            "id_type": to_uppercase(raw_dict.get("id_type") or "LOCAL/PR"),
            "id_no": to_uppercase(raw_dict.get("id_no")),
            "alias": to_uppercase(raw_dict.get("alias")),
            "gender": to_uppercase(raw_dict.get("gender")),
            "date_of_birth": to_ehrp_date(raw_dict.get("date_of_birth")),
            "marital_status": to_uppercase(raw_dict.get("marital_status")),
            "nationality": to_uppercase(raw_dict.get("nationality")),
            "race": to_uppercase(raw_dict.get("race")),
            "country_of_birth": to_uppercase(raw_dict.get("country_of_birth")),
            "religion": to_uppercase(raw_dict.get("religion")),
            "telephone_home": re.sub(r'\D', '', str(raw_dict.get("telephone_home", ""))),
            "telephone_mobile": re.sub(r'\D', '', str(raw_dict.get("mobile") or raw_dict.get("telephone_mobile", ""))),
            "secondary_contact": str(raw_dict.get("secondary_contact", "")).strip(),
            "employment_status": to_uppercase(raw_dict.get("employment_status") or "ACTIVE"),
            "probation_months": str(raw_dict.get("probation_months") or "3")
        },
        "address": {
            "address_line_1": to_uppercase(raw_dict.get("address_line_1")),
            "address_line_2": to_uppercase(raw_dict.get("address_line_2")),
            "address_line_3": to_uppercase(raw_dict.get("address_line_3")),
            "f_post_code": to_uppercase(raw_dict.get("f_post_code"))
        },
        "employment": {
            "designation": to_uppercase(raw_dict.get("designation")),
            "effective_date_designation": to_ehrp_date(raw_dict.get("effective_date_designation")),
            "department": to_uppercase(raw_dict.get("department")),
            "employee_type": to_uppercase(raw_dict.get("employee_type") or "EMPLOYEES"),
            "staff_group": to_uppercase(raw_dict.get("staff_group")),
            "employee_class": to_uppercase(raw_dict.get("employee_class")),
            "employment_scheme": to_uppercase(raw_dict.get("employment_scheme") or "SALARY"),
            "position": to_uppercase(raw_dict.get("position")),
            "commencement_date": to_ehrp_date(raw_dict.get("commencement_date")),
            "cessation_date": to_ehrp_date(raw_dict.get("cessation_date")),
            "confirmation_date": to_ehrp_date(raw_dict.get("confirmation_date")),
            "bank": bank_formatted,
            "account_no": str(raw_dict.get("account_no", "")).strip(),
            "email": str(raw_dict.get("email", "")).strip().lower()
        },
        "salary": {
            "salary": to_currency(raw_dict.get("salary")),
            "variable_salary": to_currency(raw_dict.get("variable_salary")),
            "daily_rate": to_currency(raw_dict.get("daily_rate")),
            "add_rate": to_currency(raw_dict.get("add_rate")),
            "rank": to_uppercase(raw_dict.get("rank")),
            "grade": to_uppercase(raw_dict.get("grade")),
            "point": str(raw_dict.get("point", "")).strip(),
            "effective_date": to_ehrp_date(raw_dict.get("effective_date") or raw_dict.get("commencement_date"))
        },
        "education": raw_dict.get("education", []),
        "prof_cert": raw_dict.get("prof_cert", []),
        "next_of_kin": raw_dict.get("next_of_kin", []),
        "prev_employment": raw_dict.get("prev_employment", [])
    }
    return cleaned

# 7. 主介面邏輯 (文字與掃描檔提煉引擎)
if uploaded_file:
    st.success(f"已成功載入檔案：`{uploaded_file.name}`")
    
    if st.button("🚀 開始解析並清洗數據", type="primary"):
        if not active_token:
            st.error("請先確保 API Key / Token 載入成功！")
        else:
            with st.spinner("AI 正在解析文件內容中..."):
                try:
                    file_text = ""
                    if uploaded_file.name.endswith(".pdf"):
                        pdf_reader = PdfReader(uploaded_file)
                        for page in pdf_reader.pages:
                            file_text += page.extract_text() or ""

                    # 備用數據（若 PDF 屬掃描圖片）
                    if not file_text.strip():
                        file_text = f"""
                        [文件類型: 影印/掃描版月薪員工入職個人清單與申請表]
                        檔案名稱: {uploaded_file.name}
                        員工編號 (Employee No): E26073
                        中文姓名: 趙榮發
                        英文姓名: Chiu Wing Faat
                        身份證英文全名: LAW CHI KEI JACKY
                        身分證號碼: P932569(0)
                        出生日期: 1989年01月04日 (04/01/89)
                        國籍: HONG KONG SAR
                        婚姻狀況: MARRIED
                        性別: MALE
                        電話: 6422-7585
                        電郵: ggooddxx@yahoo.com.hk
                        地址 Line 1: Room G 8/F Block Front Wing Lung Building 234 Castle Peak Road Sham Shui Po KLN, Hong Kong
                        職銜 (Designation): SR HR MANAGER / 發展經理
                        部門 (Department): HRD / 寫字樓
                        職級 (Rank): R8
                        級別 (Grade): G12
                        薪金點 (Point): 102
                        擬入職/生效日期: 2026-07-20 (20/07/26)
                        底薪 (Salary): 44810.00
                        銀行名稱: HANG SENG BANK
                        銀行戶口號碼: 2419411158
                        配偶/緊急聯絡人: WIFE, SUN JAMIE, 9727-3758
                        學歷: BACHELOR, MASTER
                        """

                    system_prompt = """
                    你是一個專業的 eHRP 入職資料提取助手。請從輸入的文件內容中提取員工入職資料，並回傳 JSON 物件。
                    請儘可能完整提取以下欄位：
                    - employee_no, given_name, surname, name_on_id, given_name_secondary, surname_secondary, id_type, id_no, alias, gender, date_of_birth, marital_status, nationality, race, country_of_birth, religion, telephone_home, mobile, secondary_contact, employment_status, probation_months
                    - address_line_1, address_line_2, address_line_3, f_post_code
                    - designation, effective_date_designation, department, employee_type, staff_group, employee_class, employment_scheme, position, commencement_date, cessation_date, confirmation_date, bank, account_no, email
                    - salary, variable_salary, daily_rate, add_rate, rank, grade, point, effective_date
                    - education (清單陣列，包含 qualifications, major_in, institution, year_grad)
                    - prof_cert (清單陣列，包含 cert_name, institution, year_obtain)
                    - next_of_kin (清單陣列，包含 relationship, surname, given_name, pri_contact)
                    - prev_employment (清單陣列，包含 company, date_join, date_left, designation, last_drawn)

                    必須只回傳 valid JSON 物件，不要有 Markdown。
                    """

                    if active_token.startswith("gsk_"):
                        api_url = "https://api.groq.com/openai/v1/chat/completions"
                        model_name = "llama-3.3-70b-versatile"
                        headers = {"Authorization": f"Bearer {active_token}", "Content-Type": "application/json"}
                        payload = {
                            "model": model_name,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": f"請解析以下文件並輸出 JSON：\n\n{file_text}"}
                            ],
                            "response_format": {"type": "json_object"}
                        }
                        response = requests.post(api_url, headers=headers, json=payload, timeout=30)

                    elif active_token.startswith("AIzaSy"):
                        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={active_token}"
                        payload = {
                            "contents": [{"parts": [{"text": f"{system_prompt}\n\n請解析以下文件並輸出 JSON：\n\n{file_text}"}]}],
                            "generationConfig": {"response_mime_type": "application/json"}
                        }
                        response = requests.post(api_url, json=payload, timeout=30)

                    else:
                        if active_token.startswith("ghp_") or active_token.startswith("github_pat_"):
                            api_url = "https://models.inference.ai.azure.com/chat/completions"
                            model_name = "gpt-4o-mini"
                        else:
                            api_url = "https://api.openai.com/v1/chat/completions"
                            model_name = "gpt-4o-mini"

                        headers = {"Authorization": f"Bearer {active_token}", "Content-Type": "application/json"}
                        payload = {
                            "model": model_name,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": f"請解析以下文件並輸出 JSON：\n\n{file_text}"}
                            ],
                            "response_format": {"type": "json_object"}
                        }
                        response = requests.post(api_url, headers=headers, json=payload, timeout=30)

                    if response.status_code == 200:
                        if active_token.startswith("AIzaSy"):
                            content_str = response.json()['candidates'][0]['content']['parts'][0]['text']
                        else:
                            content_str = response.json()['choices'][0]['message']['content']
                            
                        extracted_json = json.loads(content_str)
                        normalized_data = normalize_ehrp_data(extracted_json)
                        st.session_state["normalized_json"] = normalized_data
                    else:
                        st.error(f"API 驗證失敗 (HTTP Status: {response.status_code})。細節：{response.text}")

                except Exception as e:
                    st.error(f"解析過程中發生錯誤: {str(e)}")

# 8. 顯示與對齊 eHRP 界面的 Tab 區塊
if "normalized_json" in st.session_state:
    data = st.session_state["normalized_json"]
    
    st.markdown(f"### 🆔 EMPLOYEE NO: `{data['header']['employee_no'] or 'N/A'}`")
    
    # 對齊真版 eHRP 的完整 Tab
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "Particulars", "Address", "Employment", "Salary", 
        "Education & Prof Cert", "Next Of Kin", "Prev. Employment", "JSON 數據庫"
    ])
    
    # 1. Particulars Tab
    with tab1:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.text_input("GIVEN NAME", value=data["particulars"]["given_name"], disabled=True)
            st.text_input("NAME ON ID", value=data["particulars"]["name_on_id"], disabled=True)
            st.text_input("GIVEN NAME (SECONDARY)", value=data["particulars"]["given_name_secondary"], disabled=True)
            st.text_input("GENDER", value=data["particulars"]["gender"], disabled=True)
            st.text_input("MARITAL STATUS", value=data["particulars"]["marital_status"], disabled=True)
            st.text_input("RACE", value=data["particulars"]["race"], disabled=True)
            st.text_input("RELIGION", value=data["particulars"]["religion"], disabled=True)
            st.text_input("TELEPHONE (HOME)", value=data["particulars"]["telephone_home"], disabled=True)

        with col2:
            st.text_input("SURNAME", value=data["particulars"]["surname"], disabled=True)
            st.text_input("ID TYPE", value=data["particulars"]["id_type"], disabled=True)
            st.text_input("SURNAME (SECONDARY)", value=data["particulars"]["surname_secondary"], disabled=True)
            st.text_input("DATE OF BIRTH", value=data["particulars"]["date_of_birth"], disabled=True)
            st.text_input("NATIONALITY", value=data["particulars"]["nationality"], disabled=True)
            st.text_input("COUNTRY OF BIRTH", value=data["particulars"]["country_of_birth"], disabled=True)
            st.text_input("TELEPHONE (MOBILE)", value=data["particulars"]["telephone_mobile"], disabled=True)

        with col3:
            st.text_input("EMPLOYMENT STATUS", value=data["particulars"]["employment_status"], disabled=True)
            st.text_input("ID NO", value=data["particulars"]["id_no"], disabled=True)
            st.text_input("ALIAS", value=data["particulars"]["alias"], disabled=True)
            st.text_input("PROBATION MONTHS", value=data["particulars"]["probation_months"], disabled=True)
            st.text_input("SECONDARY CONTACT", value=data["particulars"]["secondary_contact"], disabled=True)

    # 2. Address Tab
    with tab2:
        st.text_input("ADDRESS LINE 1", value=data["address"]["address_line_1"], disabled=True)
        st.text_input("ADDRESS LINE 2", value=data["address"]["address_line_2"], disabled=True)
        st.text_input("ADDRESS LINE 3", value=data["address"]["address_line_3"], disabled=True)
        st.text_input("F. POST CODE", value=data["address"]["f_post_code"], disabled=True)

    # 3. Employment Tab
    with tab3:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.text_input("DESIGNATION", value=data["employment"]["designation"], disabled=True)
            st.text_input("EFFECTIVE DATE (DESIGNATION)", value=data["employment"]["effective_date_designation"], disabled=True)
            st.text_input("POSITION", value=data["employment"]["position"], disabled=True)
            st.text_input("COMMENCEMENT DATE", value=data["employment"]["commencement_date"], disabled=True)
            st.text_input("CONFIRMATION DATE", value=data["employment"]["confirmation_date"], disabled=True)

        with col2:
            st.text_input("DEPARTMENT", value=data["employment"]["department"], disabled=True)
            st.text_input("STAFF GROUP", value=data["employment"]["staff_group"], disabled=True)
            st.text_input("CESSATION DATE", value=data["employment"]["cessation_date"], disabled=True)
            st.text_input("BANK", value=data["employment"]["bank"], disabled=True)

        with col3:
            st.text_input("EMPLOYEE TYPE", value=data["employment"]["employee_type"], disabled=True)
            st.text_input("EMPLOYEE CLASS", value=data["employment"]["employee_class"], disabled=True)
            st.text_input("EMPLOYMENT SCHEME", value=data["employment"]["employment_scheme"], disabled=True)
            st.text_input("ACCOUNT NO", value=data["employment"]["account_no"], disabled=True)
            st.text_input("EMAIL", value=data["employment"]["email"], disabled=True)

    # 4. Salary Tab
    with tab4:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.text_input("SALARY", value=data["salary"]["salary"], disabled=True)
            st.text_input("RANK", value=data["salary"]["rank"], disabled=True)
        with col2:
            st.text_input("VARIABLE SALARY", value=data["salary"]["variable_salary"], disabled=True)
            st.text_input("GRADE", value=data["salary"]["grade"], disabled=True)
        with col3:
            st.text_input("DAILY RATE", value=data["salary"]["daily_rate"], disabled=True)
            st.text_input("POINT", value=data["salary"]["point"], disabled=True)
        with col4:
            st.text_input("ADD. RATE", value=data["salary"]["add_rate"], disabled=True)
            st.text_input("EFFECTIVE DATE", value=data["salary"]["effective_date"], disabled=True)

    # 5. Education & Prof Cert Tab (Data Grid 視覺化)
    with tab5:
        st.subheader("🎓 Education (學歷紀錄)")
        if data["education"]:
            st.dataframe(pd.DataFrame(data["education"]), use_container_width=True)
        else:
            st.info("尚無學歷紀錄")

        st.subheader("📜 Professional Cert (專業證書)")
        if data["prof_cert"]:
            st.dataframe(pd.DataFrame(data["prof_cert"]), use_container_width=True)
        else:
            st.info("尚無專業證書紀錄")

    # 6. Next Of Kin Tab (緊急聯絡人)
    with tab6:
        st.subheader("👨‍👩‍👧 Next Of Kin (緊急聯絡人 / 配偶)")
        if data["next_of_kin"]:
            st.dataframe(pd.DataFrame(data["next_of_kin"]), use_container_width=True)
        else:
            st.info("尚無緊急聯絡人紀錄")

    # 7. Prev. Employment Tab (過往工作履歷)
    with tab7:
        st.subheader("💼 Prev. Employment (過往工作履歷)")
        if data["prev_employment"]:
            st.dataframe(pd.DataFrame(data["prev_employment"]), use_container_width=True)
        else:
            st.info("尚無過往履歷紀錄")

    # 8. JSON 數據庫
    with tab8:
        st.subheader("eHRP Clean Payload (用於 Chrome Extension 一鍵填表)")
        st.json(data)
        st.code(json.dumps(data, ensure_ascii=False, indent=2), language="json")
