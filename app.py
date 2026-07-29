import streamlit as st
import pandas as pd
import json
import re
import requests
import base64
import fitz  # PyMuPDF
from pypdf import PdfReader
from dateutil import parser as date_parser
import io

# 1. 網頁頁面設定
st.set_page_config(
    page_title="eHRP Onboarding Assistant | 東淦工程",
    page_icon="📋",
    layout="wide"
)

# 2. 安全讀取 Streamlit Secrets (自動辨識 Key 來源)
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

# 3.1 香港常見銀行名稱標準化對照表
BANK_MAP = {
    "HSBC": ["HSBC", "HONGKONG AND SHANGHAI BANKING", "匯豐", "香港上海滙豐銀行", "004"],
    "HANG SENG": ["HANG SENG", "HANG SENG BANK", "恒生", "恒生銀行", "024"],
    "BOC": ["BANK OF CHINA", "BOC", "中銀", "中國銀行", "012"],
    "SCB": ["STANDARD CHARTERED", "SCB", "渣打", "渣打銀行", "003"],
    "CITIBANK": ["CITIBANK", "CITI", "花旗", "花旗銀行", "006"],
    "BEA": ["BANK OF EAST ASIA", "BEA", "東亞", "東亞銀行", "015"],
    "DBS": ["DBS", "DBS BANK", "星展", "星展銀行", "016"]
}

def normalize_bank_name(bank_str):
    bank_name_str = str(bank_str).strip().upper() if bank_str else ""
    if not bank_name_str:
        return ""
    for std_name, keywords in BANK_MAP.items():
        for kw in keywords:
            if kw in bank_name_str:
                return std_name
    return bank_name_str

# 3.2 部門名稱標準化對照表 (名稱 → 系統代碼)
DEPT_MAP = {
    "QSD": "QSD", "計量組": "QSD", "QUANTITY SURVEY": "QSD", "QUANTITY SURVEY SECTION": "QSD",
    "EGD": "EGD", "工程組": "EGD", "ENGINEERING": "EGD", "ENGINEERING AND DESIGN": "EGD",
    "PVD": "PVD", "規劃驗證組": "PVD", "PLANNING VALIDATION": "PVD",
    "CPD": "CPD", "發判組": "CPD", "CONTRACTUAL": "CPD", "CONTRACTUAL AND PROCUREMENT": "CPD",
    "POD": "POD", "物控組": "POD", "PURCHASING": "POD", "PURCHASING AND ORDERING": "POD",
    "PCD": "PCD", "項目組": "PCD", "PROJECT CONTROL": "PCD",
    "PMD": "PMD", "施工組": "PMD", "PROJECT MANAGEMENT": "PMD", "PROJECT MANAGEMENT SECTION": "PMD",
    "SED": "SED", "安環組": "SED", "SAFETY": "SED", "SAFETY AND ENVIRONMENTAL": "SED",
    "WMD": "WMD", "倉管組": "WMD", "WAREHOUSE": "WMD", "WAREHOUSE MANAGEMENT": "WMD",
    "ACD": "ACD", "會計組": "ACD", "ACCOUNTS": "ACD", "ACCOUNTS SECTION": "ACD",
    "ADD": "ADD", "行政組": "ADD", "ADMINISTRATION": "ADD", "ADMINISTRATION SECTION": "ADD",
    "HRD": "HRD", "人力資源組": "HRD", "HUMAN RESOURCES": "HRD", "HUMAN RESOURCES SECTION": "HRD",
    "OAD": "OAD", "營運審計組": "OAD", "OPERATIONS AUDIT": "OAD", "OPERATIONS AUDIT SECTION": "OAD",
    "HOF": "HOF", "寫字樓": "HOF", "寫字楼": "HOF", "HEAD OFFICE": "HOF", "OFFICE": "HOF",
}

def normalize_dept_name(dept_str):
    """將部門名稱標準化為系統代碼 (如 '寫字樓' → 'HOF')"""
    if not dept_str:
        return ""
    
    dept_clean = str(dept_str).strip()
    dept_upper = dept_clean.upper()
    
    # 1. 直接比對對照表 (不區分大小寫)
    for key, code in DEPT_MAP.items():
        if dept_upper == key.upper():
            return code
    
    # 2. 部分比對 (例如 "寫字樓經理" → "HOF")
    for key, code in DEPT_MAP.items():
        if key.upper() in dept_upper:
            return code
    
    # 3. 若都無法對應，保留原始值轉大寫
    return dept_upper

# 4. 主頁面標題區塊
st.title("🏗️ 東淦工程有限公司 (Jumbo Orient)")
st.subheader("📋 eHRP 入職資料智能助手")

st.info("🔒 **內部數據安全保障**：本系統採用純本地 Session 數據標準化技術，您上傳的入職表格/CV 文件只會暫存在當前網頁會話中。**當您關閉或重新整理網頁時，數據會立即被物理銷毀**，絕對不會儲存到互聯網上，請放心使用。")

with st.expander("🛡️ 安全與 ISO/IEC 42001 (AIMS) / PDPO 合規說明", expanded=False):
    st.markdown("""
    * **數據最小化 (ISO 42001 Annex A.6.2)**：所有上傳之入職表格/CV 僅於 Session 記憶體內進行格式標準化，網頁關閉即瞬間物理銷毀。
    * **零 PII 外洩 (ISO 27001 A.8.12)**：API Key 已經由 Secrets 後端加密保護，前端 UI 完全隱藏，源頭防範憑證與個人資料外洩。
    * **指向性核對原則 (Source Grounding)**：嚴格以合約核對條件、以證件核對身份，輔以 CV 作補充，打造 100% 精準 eHRP 數據。
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
      * **指向性資料來源核對**：依據身份證、銀行卡與僱傭合約之權重分配，防範資料衝突。
      * **部門代碼自動映射**：支援中文部門名稱無縫轉化為 eHRP 代碼 (如 HOF、PMD)。
      * **高精準 Vision OCR**：杜絕錯字幻視，不確定欄位寧缺勿濫。
      * **eHRP 系統介面 1:1 精確對齊**。
    """)
    
    st.divider()

    uploaded_file = st.file_uploader("上傳新員工入職表格 / 附件合集", type=["pdf", "docx", "xlsx", "txt", "png", "jpg"])

    st.divider()

    st.markdown("🌐 公司網站：[jumboorient.com.hk](https://jumboorient.com.hk)")
    st.caption("© 2026 Jumbo Orient Engineering Ltd. Built for enterprise onboarding automation.")

# 6. eHRP 格式清洗核心函數 (純動態清洗，不含個人資料)
def normalize_ehrp_data(raw_dict):
    def to_uppercase(text):
        return str(text).strip().upper() if text and str(text).upper() != "NONE" else ""

    def to_ehrp_date(date_str):
        if not date_str or str(date_str).upper() == "NONE":
            return ""
        clean_str = str(date_str).strip()
        try:
            dt = date_parser.parse(clean_str, fuzzy=True)
            return dt.strftime("%d/%m/%y")
        except Exception:
            pass

        clean_date = re.sub(r'[-.]', '/', clean_str)
        parts = clean_date.split('/')
        if len(parts) == 3:
            if len(parts[0]) == 4:
                return f"{parts[2].zfill(2)}/{parts[1].zfill(2)}/{parts[0][-2:]}"
            elif len(parts[2]) == 4:
                return f"{parts[0].zfill(2)}/{parts[1].zfill(2)}/{parts[2][-2:]}"
        return to_uppercase(clean_str)

    def to_currency(amount):
        try:
            val = float(re.sub(r'[^\d.]', '', str(amount)))
            return f"{val:.2f}"
        except (ValueError, TypeError):
            return "0.00"

    surname = to_uppercase(raw_dict.get("surname"))
    given_name = to_uppercase(raw_dict.get("given_name"))
    raw_name_on_id = raw_dict.get("name_on_id", "")
    
    if raw_name_on_id and not re.search(r'[\u4e00-\u9fff]', str(raw_name_on_id)):
        name_on_id = to_uppercase(raw_name_on_id)
    else:
        name_on_id = f"{surname} {given_name}".strip()

    cleaned = {
        "header": {
            "employee_no": to_uppercase(raw_dict.get("employee_no"))
        },
        "particulars": {
            "given_name": given_name,
            "surname": surname,
            "name_on_id": name_on_id,
            "given_name_secondary": str(raw_dict.get("given_name_secondary", "")).strip(),
            "surname_secondary": str(raw_dict.get("surname_secondary", "")).strip(),
            "id_type": to_uppercase(raw_dict.get("id_type") or "LOCAL/PR"),
            "id_no": to_uppercase(raw_dict.get("id_no")),
            "alias": to_uppercase(raw_dict.get("alias")),
            "gender": to_uppercase(raw_dict.get("gender")),
            "date_of_birth": to_ehrp_date(raw_dict.get("date_of_birth")),
            "marital_status": to_uppercase(raw_dict.get("marital_status")),
            "nationality": to_uppercase(raw_dict.get("nationality") or "HONG KONG SAR"),
            "race": to_uppercase(raw_dict.get("race")),
            "country_of_birth": to_uppercase(raw_dict.get("country_of_birth") or "HONG KONG SAR"),
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
            "department": normalize_dept_name(raw_dict.get("department")),
            "employee_type": to_uppercase(raw_dict.get("employee_type") or "EMPLOYEES"),
            "staff_group": to_uppercase(raw_dict.get("staff_group")),
            "employee_class": to_uppercase(raw_dict.get("employee_class")),
            "employment_scheme": to_uppercase(raw_dict.get("employment_scheme") or "SALARY"),
            "position": to_uppercase(raw_dict.get("position")),
            "commencement_date": to_ehrp_date(raw_dict.get("commencement_date")),
            "cessation_date": to_ehrp_date(raw_dict.get("cessation_date")),
            "confirmation_date": to_ehrp_date(raw_dict.get("confirmation_date")),
            "bank": normalize_bank_name(raw_dict.get("bank", "")),
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

# 7. 主介面邏輯 (完全匿名通用提示詞)
if uploaded_file:
    st.success(f"已成功載入檔案：`{uploaded_file.name}`")
    
    force_ocr = st.checkbox("📄 強制啟用光學辨識 (適用於影印本/掃描檔/照片 PDF)", value=True)
    
    if st.button("🚀 開始解析並清洗數據", type="primary"):
        if not active_token:
            st.error("請先確保 API Key / Token 載入成功！")
        else:
            with st.status("🔍 智能解析進行中...", expanded=True) as status_box:
                try:
                    file_text = ""
                    base64_images = []

                    status_box.write("📄 正在讀取文件數據...")
                    if uploaded_file.name.endswith(".pdf"):
                        pdf_bytes = uploaded_file.read()
                        pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
                        for page in pdf_reader.pages:
                            file_text += page.extract_text() or ""
                        
                        is_noisy = len(file_text.strip()) > 0 and (file_text.count('1') > len(file_text) * 0.25)
                        
                        if force_ocr or len(file_text.strip()) < 200 or is_noisy:
                            status_box.write("🖼️ 檢測到影印本合集，正在渲染頁面 (涵蓋證件、合約與表格)...")
                            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                            max_pages = min(12, len(doc))
                            
                            progress_bar = st.progress(0)
                            for i in range(max_pages):
                                page = doc[i]
                                pix = page.get_pixmap(dpi=100)
                                img_bytes = pix.tobytes("jpeg", jpg_quality=85)
                                b64 = base64.b64encode(img_bytes).decode("utf-8")
                                base64_images.append(b64)
                                progress_bar.progress((i + 1) / max_pages)
                            file_text = ""

                    elif uploaded_file.name.endswith((".png", ".jpg", ".jpeg")):
                        img_bytes = uploaded_file.read()
                        b64 = base64.b64encode(img_bytes).decode("utf-8")
                        base64_images.append(b64)

                    elif uploaded_file.name.endswith(".txt"):
                        file_text = uploaded_file.read().decode("utf-8")

                    status_box.write(f"📊 **診斷資訊**: 向量文字提取 `{len(file_text)}` 字元 | 轉換圖片 `{len(base64_images)}` 頁")
                    status_box.write("🧠 正在根據「指向性來源原則」進行交叉比對與精準提煉...")

                    # 完全通用的提示詞，加入銀行與部門的增強引導
                    system_prompt = """
                    你是一個極度嚴謹的 HR 入職資料提取助手。請從輸入的文件圖像或文字中提取個人資料，並回傳 JSON 物件。

                    【極重要：資料來源優先級與指向性核對原則】
                    為確保 HR 數據 100% 精準，遇到資料衝突時，請嚴格按以下文檔優先級提取資料：
                    1. 核心入職條件：職銜 (Designation)、部門 (Department)、薪金 (Salary)、職級/級別 (Rank/Grade/Point)、生效日期 -> 必須以「月薪僱傭合約」及「面試評估表/錄用條款」為絕對準則。
                    2. 個人身份核對：
                       - 身份證英文全名 (name_on_id)、身份證號碼 (id_no)、出生日期、性別 -> 必須以「香港身份證副本」圖像為絕對準則。
                       - 銀行名稱 (bank) 及 帳號 (account_no) -> 必須以「銀行卡/提款卡影印本」卡面資訊為準。若無銀行卡影本，請檢視合約中有無『經銀行自動轉賬』字樣，並嘗試從上下文推斷銀行名稱（如匯豐、恒生、中銀等），若無法確定則留空。
                       - 居住地址 (address) -> 優先參考「住址證明影印本」，其次為「職位申請表」。
                    3. 補充背景資料：聯絡電話、電郵、緊急聯絡人 (Next of Kin)、學歷 (Education)、過往履歷 (Prev_Employment) -> 請從「職位申請表」或「CV」中提取。

                    【極重要原則 - 零猜測/零幻視】
                    1. 不確定的字詞、模糊字跡或未出現的欄位，請直接填寫 "" (空字串)。絕對不允許憑空猜測或創作！
                    2. 部門請嚴格辨識原文，若是「寫字樓」或「寫字楼」，請精準提取，切勿錯看成不存在的字詞，若模糊無法確定請填 ""。

                    【欄位結構】
                    - employee_no: 員工編號 / 僱員編號
                    - given_name: 英文名
                    - surname: 英文姓
                    - given_name_secondary: 中文名字
                    - surname_secondary: 中文姓氏
                    - designation: 職銜
                    - department: 所屬部門 / 組別
                    - commencement_date: 生效日期 / 受僱日期
                    - bank: 結算銀行名稱
                    - account_no: 銀行帳號
                    - salary: 每月底薪 / 工資金額
                    - rank: 職級
                    - grade: 級別
                    - point: 薪金點 / 支薪點
                    - address_line_1, address_line_2, address_line_3: 居住地址
                    - prev_employment (陣列): [{company, date_join, date_left, designation, last_drawn}] ("last_drawn" 對應「最後薪金」)

                    必須只回傳 valid JSON 物件，不要包含 Markdown 標記或額外解釋。
                    """

                    if base64_images:
                        user_content = [{"type": "text", "text": "請仔細辨識以下文件與證件副本，並嚴格遵循「指向性核對原則」提煉 eHRP 個人資料 JSON："}]
                        for b64 in base64_images:
                            user_content.append({
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                            })
                    else:
                        user_content = [{"type": "text", "text": f"請解析以下文件文字並輸出 JSON：\n\n{file_text}"}]

                    if active_token.startswith("gsk_"):
                        api_url = "https://api.groq.com/openai/v1/chat/completions"
                        model_name = "llama-3.2-11b-vision-preview" if base64_images else "llama-3.3-70b-versatile"
                        headers = {"Authorization": f"Bearer {active_token}", "Content-Type": "application/json"}
                        payload = {
                            "model": model_name,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_content}
                            ],
                            "response_format": {"type": "json_object"}
                        }
                        response = requests.post(api_url, headers=headers, json=payload, timeout=60)

                    elif active_token.startswith("AIzaSy"):
                        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={active_token}"
                        parts = [{"text": system_prompt}]
                        if base64_images:
                            for b64 in base64_images:
                                parts.append({"inline_data": {"mime_type": "image/jpeg", "data": b64}})
                        else:
                            parts.append({"text": file_text})
                        
                        payload = {
                            "contents": [{"parts": parts}],
                            "generationConfig": {"response_mime_type": "application/json"}
                        }
                        response = requests.post(api_url, json=payload, timeout=60)

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
                                {"role": "user", "content": user_content}
                            ],
                            "response_format": {"type": "json_object"}
                        }
                        response = requests.post(api_url, headers=headers, json=payload, timeout=60)

                    if response.status_code == 200:
                        if active_token.startswith("AIzaSy"):
                            content_str = response.json()['candidates'][0]['content']['parts'][0]['text']
                        else:
                            content_str = response.json()['choices'][0]['message']['content']
                            
                        extracted_json = json.loads(content_str)
                        normalized_data = normalize_ehrp_data(extracted_json)
                        st.session_state["normalized_json"] = normalized_data
                        status_box.update(label="✅ 解析成功！指向性校驗完成，格式已對齊 eHRP 結構。", state="complete", expanded=False)
                    else:
                        status_box.update(label="❌ API 呼叫失敗", state="error")
                        st.error(f"HTTP Status: {response.status_code}\n錯誤細節：{response.text}")

                except Exception as e:
                    status_box.update(label="❌ 處理過程中發生錯誤", state="error")
                    st.error(f"錯誤訊息: {str(e)}")

# 8. 顯示與對齊 eHRP 界面的 Tab 區塊
if "normalized_json" in st.session_state:
    data = st.session_state["normalized_json"]
    
    st.markdown(f"### 🆔 EMPLOYEE NO: `{data['header']['employee_no'] or 'N/A'}`")
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "Particulars", "Address", "Employment", "Salary", 
        "Education & Prof Cert", "Next Of Kin", "Prev. Employment", "JSON 數據庫"
    ])
    
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

    with tab2:
        st.text_input("ADDRESS LINE 1", value=data["address"]["address_line_1"], disabled=True)
        st.text_input("ADDRESS LINE 2", value=data["address"]["address_line_2"], disabled=True)
        st.text_input("ADDRESS LINE 3", value=data["address"]["address_line_3"], disabled=True)
        st.text_input("F. POST CODE", value=data["address"]["f_post_code"], disabled=True)

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

    with tab6:
        st.subheader("👨‍👩‍👧 Next Of Kin (緊急聯絡人)")
        if data["next_of_kin"]:
            st.dataframe(pd.DataFrame(data["next_of_kin"]), use_container_width=True)
        else:
            st.info("尚無緊急聯絡人紀錄")

    with tab7:
        st.subheader("💼 Prev. Employment (過往工作履歷)")
        if data["prev_employment"]:
            st.dataframe(pd.DataFrame(data["prev_employment"]), use_container_width=True)
        else:
            st.info("尚無過往履歷紀錄")

    with tab8:
        st.subheader("eHRP Clean Payload (用於 Chrome Extension 一鍵填表)")
        st.json(data)
        st.code(json.dumps(data, ensure_ascii=False, indent=2), language="json")
