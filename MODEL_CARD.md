# AI Model Card & System Transparency Report
### 🏗️ Jumbo Orient eHRP Onboarding Assistant (`jo-ehrp-onboarding-assistant`)
**Compliance Standard:** ISO/IEC 42001:2023 (AIMS) Annex A.8 & ISO/IEC 27001:2022 (ISMS)

---

## 1. System Overview & Intended Use (系統概述與預期用途)

* **System Name:** eHRP Onboarding Assistant
* **Developer / Maintainer:** Jumbo Orient Contracting Limited (HR Tech & Governance)
* **Primary Function:** Automated extraction and normalization of multi-source onboarding document packages (scanned PDFs, HKID, Bank Cards, Contracts, Job Application Forms, and Certificates) for structured eHRP system ingestion.
* **Intended Users:** Authorized Human Resources Professionals.
* **Out-of-Scope Uses:** Autonomous HR decision-making, automated hiring/firing, or processing candidate applications without human review.

---

## 2. Underlying AI Architecture & Models (AI 模型架構)

This application employs a **Hybrid Dual-Engine System Architecture** to handle structured and unstructured multi-modal inputs:

| Component | Provider / Engine | Primary Task | ISO 42001 Assessment |
| :--- | :--- | :--- | :--- |
| **Vision OCR Engine** | Groq (`llama-3.2-11b-vision`) / Gemini (`gemini-1.5-flash`) / OpenAI (`gpt-4o-mini`) | Visual text extraction from scanned document images (HKID, Contracts, Certificates). | Multimodal image-to-JSON reasoning. |
| **Vector Text Engine** | PyMuPDF (`fitz`) & `pypdf` | Direct digital PDF stream extraction for non-scanned vector text. | Rule-based text parser. |
| **Data Normalizer** | Python Regular Expressions & `dateutil` | Deterministic data formatting (`DD/MM/YY`, upper-cased text, currency rounding). | Zero-AI deterministic logic. |

---

## 3. Data Source Grounding & Priority Hierarchy (指向性資料來源優先級)

To mitigate hallucinations and resolve data conflicts across multiple documents, the system enforces strict **Source Grounding (AIMS Control A.8.2)**:

1. **Employment Terms (`salary`, `rank`, `grade`, `point`):** 
   * *Ground Truth Source:* **Clause 3 of Employment Contract** & Interview Evaluation Form.
2. **Personal Identity (`name_on_id`, `id_no`):** 
   * *Ground Truth Source:* **Hong Kong Permanent Identity Card Scans**.
3. **Contact & Location (`mobile`, `address`):** 
   * *Ground Truth Source:* **Job Application Form (HRF-006)**.
4. **Banking Information (`bank`, `account_no`):** 
   * *Ground Truth Source:* **Bank Card Scans** & Staff Card Acknowledgment Authorization.
5. **Qualifications & History (`education`, `prof_cert`, `prev_employment`):** 
   * *Ground Truth Source:* **Job Application Form (HRF-006)**, CVs, and Professional Certificate Scans.

---

## 4. Governance, Safety & Risk Controls (管治與風險控制)

### 4.1 Zero Hallucination Principle (零 AI 幻覺控制)
* **Control Mechanism:** System prompt explicitly instructs LLM Vision models to return empty strings (`""`) for ambiguous, illegible, or unstated fields.
* **Validation:** No speculative data generation is permitted.

### 4.2 Privacy & Zero Data Retention (PDPO & ISO 27001 A.8.12)
* **Memory Management:** All image conversions (JPEG 100 DPI) and payload processing occur **strictly within the client-side/temporary Session Memory**.
* **Data Lifecycle:** Physical Destruction occurs instantly upon session termination or page reload. No user Personally Identifiable Information (PII) is stored in persistent databases or external storage.
* **Secrets Management:** API Keys are protected via encrypted backend environment variables (`st.secrets`). No hardcoded secrets or PII reside within the repository codebase.

### 4.3 Human-in-the-Loop Oversight (Human Governance - AIMS Annex A.6.2)
* **Control Mechanism:** The AI assistant functions strictly as a data-formatting pre-processor.
* **Auditability:** Extracted data is presented in a side-by-side verification interface. HR personnel must explicitly review and validate all fields prior to pushing data into the eHRP production system.

---

## 5. Performance Metrics & Limitations (效能指標與系統限制)

* **Supported File Types:** PDF (Vector & Scanned), PNG, JPG, JPEG, TXT.
* **OCR Conversion Limits:** Maximum 12 pages per upload package (JPEG Quality 85 at 100 DPI) to prevent API Payload Size Limit (413 HTTP error).
* **Known Limitations:**
  * Severely degraded or low-contrast hand-written characters may trigger the "Zero Hallucination" safety rule, leaving fields blank for human manual entry.
  * Extracted bank names default to official standard codes (e.g., `HANG SENG`, `HSBC`, `BOC`).

---

## 📜 ISO 42001 Compliance Statement
This Model Card is maintained under **ISO/IEC 42001:2023 AIMS** transparency standards. It serves as evidence of algorithmic accountability, data minimization, and risk-mitigated AI deployment within Jumbo Orient Contracting Limited.
