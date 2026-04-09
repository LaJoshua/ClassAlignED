import os
import json
import time
import random
import hashlib
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pypdf import PdfReader
from docx import Document
from google import genai

# =========================================================
# Config
# =========================================================

PROJECT_ROOT = Path.home() / "Desktop" / "CLASS_ALIGNED_MVP_UI_DEMO"
load_dotenv(PROJECT_ROOT / ".env", override=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Check your .env file.")

client = genai.Client(api_key=GEMINI_API_KEY)

# Safer for demo/free-tier usage
MODEL_NAME = "gemini-2.5-flash-lite"

RAW_SYLLABI = PROJECT_ROOT / "raw" / "syllabi"
RAW_POLICIES = PROJECT_ROOT / "raw" / "policies"
RAW_REFERENCES = PROJECT_ROOT / "raw" / "references"

PROC_TEXT = PROJECT_ROOT / "processed" / "text"
PROC_CHUNKS = PROJECT_ROOT / "processed" / "chunks"
PROC_EXTRACTED = PROJECT_ROOT / "processed" / "extracted"

GRAPHRAG_WS = PROJECT_ROOT / "processed" / "graphrag_workspace"

OUTPUT_REPORTS = PROJECT_ROOT / "outputs" / "reports"
OUTPUT_EXPORTS = PROJECT_ROOT / "outputs" / "exports"

for p in [
    RAW_SYLLABI,
    RAW_POLICIES,
    RAW_REFERENCES,
    PROC_TEXT,
    PROC_CHUNKS,
    PROC_EXTRACTED,
    OUTPUT_REPORTS,
    OUTPUT_EXPORTS,
]:
    p.mkdir(parents=True, exist_ok=True)


# =========================================================
# Basic utilities
# =========================================================

def stable_id(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def save_uploaded_file(uploaded_file, out_dir) -> str:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / uploaded_file.name
    with open(out_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(out_path)


def extract_pdf_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    parts = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        parts.append(f"\n[PAGE {i+1}]\n{text}")
    return "\n".join(parts)


def extract_docx_text(docx_path: str) -> str:
    doc = Document(docx_path)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])


def extract_text(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return extract_pdf_text(file_path)
    if ext == ".docx":
        return extract_docx_text(file_path)
    raise ValueError(f"Unsupported file type: {ext}")


def chunk_text(text: str, size: int = 1800):
    text = text.strip()
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end
    return chunks


def save_text_and_chunks(file_path: str):
    text = extract_text(file_path)
    doc_id = stable_id(Path(file_path).name)

    text_path = PROC_TEXT / f"{doc_id}.json"
    chunk_path = PROC_CHUNKS / f"{doc_id}.jsonl"

    with open(text_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "doc_id": doc_id,
                "text": text,
                "source_file": Path(file_path).name,
            },
            f,
            indent=2,
        )

    chunks = chunk_text(text)
    with open(chunk_path, "w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks, start=1):
            row = {
                "doc_id": doc_id,
                "chunk_id": f"{doc_id}_chunk_{i}",
                "text": chunk,
                "source_file": Path(file_path).name,
            }
            f.write(json.dumps(row) + "\n")

    return doc_id, str(text_path), str(chunk_path)


def load_jsonl(path: str):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


# =========================================================
# Formatting / normalization helpers
# =========================================================

def normalize_assessments(items):
    normalized = []

    if not isinstance(items, list):
        return normalized

    for item in items:
        if isinstance(item, str):
            cleaned = item.strip()
            if cleaned:
                normalized.append({
                    "type": cleaned,
                    "description": cleaned,
                    "points": "",
                    "percentage": "",
                    "notes": "",
                    "due_date": "",
                })
            continue

        if isinstance(item, dict):
            normalized.append({
                "type": item.get("type", "") or item.get("name", "") or item.get("category", ""),
                "description": item.get("description", "") or item.get("title", "") or item.get("details", ""),
                "points": item.get("points", item.get("score", "")),
                "percentage": item.get("percentage", item.get("weight_percent", item.get("weight", ""))),
                "notes": item.get("notes", item.get("note", "")),
                "due_date": item.get("due_date", item.get("due", "")),
            })
            continue

    return normalized


def normalize_learning_outcomes(items):
    normalized = []

    if not isinstance(items, list):
        return normalized

    for item in items:
        if isinstance(item, str):
            cleaned = item.strip()
            if cleaned:
                normalized.append(cleaned)
        elif isinstance(item, dict):
            text = str(item.get("text", "")).strip()
            if text:
                normalized.append(text)

    return normalized


def normalize_syllabus_policies(items):
    normalized = []

    if not isinstance(items, list):
        return normalized

    for item in items:
        if isinstance(item, str):
            cleaned = item.strip()
            if cleaned:
                normalized.append({
                    "policy_type": "",
                    "description": cleaned,
                })

        elif isinstance(item, dict):
            policy_type = str(
                item.get("policy_type", "") or item.get("type", "") or item.get("category", "")
            ).strip()
            description = str(
                item.get("description", "") or item.get("summary", "") or item.get("text", "")
            ).strip()

            # Only keep non-empty policy rows
            if policy_type or description:
                normalized.append({
                    "policy_type": policy_type,
                    "description": description,
                })

    return normalized


def format_assessment_item(item):
    if isinstance(item, str):
        cleaned = item.strip()
        return cleaned if cleaned else "Assessment"

    if isinstance(item, dict):
        atype = str(item.get("type", "") or item.get("name", "") or item.get("category", "")).strip()
        desc = str(item.get("description", "") or item.get("title", "") or item.get("details", "")).strip()
        points = item.get("points", item.get("score", ""))
        percentage = item.get("percentage", item.get("weight_percent", item.get("weight", "")))
        notes = str(item.get("notes", "") or item.get("note", "")).strip()
        due_date = str(item.get("due_date", "") or item.get("due", "")).strip()

        main = ""
        if atype and desc and desc.lower() != atype.lower():
            main = f"{atype} - {desc}"
        elif atype:
            main = atype
        elif desc:
            main = desc
        else:
            visible = {k: v for k, v in item.items() if v not in ("", None, [], {})}
            return str(visible) if visible else "Assessment"

        extras = []

        if percentage not in ("", None, 0):
            pct = str(percentage).strip()
            if pct.endswith("%"):
                extras.append(pct)
            else:
                extras.append(f"{pct}%")

        if points not in ("", None, 0):
            pts = str(points).strip()
            if "point" in pts.lower():
                extras.append(pts)
            else:
                extras.append(f"{pts} points")

        if due_date:
            extras.append(f"Due: {due_date}")

        if notes:
            extras.append(f"Notes: {notes}")

        if extras:
            main += f" ({'; '.join(extras)})"

        return main

    return str(item)


def format_policy_item(item):
    if isinstance(item, dict):
        ptype = str(item.get("policy_type", "") or item.get("type", "")).strip()
        desc = str(item.get("description", "") or item.get("summary", "")).strip()

        if ptype and desc:
            return f"{ptype}: {desc}"
        if desc:
            return desc
        if ptype:
            return ptype

        return ""

    cleaned = str(item).strip()
    return cleaned

# =========================================================
# Gemini helpers
# =========================================================

def call_gemini_json(prompt: str, debug_name: str = "debug", max_attempts: int = 5):
    base_delay = 3

    for attempt in range(1, max_attempts + 1):
        try:
            resp = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config={
                    "response_mime_type": "application/json"
                }
            )

            raw_text = (resp.text or "").strip()

            if not raw_text:
                raise ValueError("Gemini returned empty text response.")

            if raw_text.startswith("```"):
                raw_text = raw_text.strip("`")
                if raw_text.lower().startswith("json"):
                    raw_text = raw_text[4:].strip()

            return json.loads(raw_text)

        except Exception as e:
            msg = str(e)

            if "503" in msg or "UNAVAILABLE" in msg or "high demand" in msg:
                if attempt == max_attempts:
                    raise ValueError(
                        "Gemini is currently under heavy load. Please try again in a minute."
                    ) from e
                sleep_for = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1)
                time.sleep(sleep_for)
                continue

            debug_path = PROC_EXTRACTED / f"{debug_name}_raw_response.txt"
            try:
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(str(e))
            except Exception:
                pass

            raise


# =========================================================
# Extraction logic
# =========================================================

def run_syllabus_extraction(doc_id: str, chunk_path: str):
    all_chunks = load_jsonl(chunk_path)

    def pick_chunks(keywords, max_chunks=5):
        hits = []
        for ch in all_chunks:
            text = str(ch.get("text", "")).lower()
            if any(k in text for k in keywords):
                hits.append(ch)
        return hits[:max_chunks] if hits else all_chunks[:max_chunks]

    outcome_chunks = pick_chunks(
        ["learning outcome", "learning outcomes", "course outcome", "course outcomes",
         "objective", "objectives", "student learning", "outcomes"],
        max_chunks=5
    )

    assessment_chunks = pick_chunks(
        ["assessment", "assessments", "grading", "evaluation", "exam", "quiz",
         "project", "assignment", "lab", "journal", "participation", "report"],
        max_chunks=6
    )

    policy_chunks = pick_chunks(
        ["policy", "policies", "attendance", "late work", "submission",
         "academic integrity", "participation", "blackboard", "discussion board", "netiquette"],
        max_chunks=6
    )

    # ---- Extract course + learning outcomes ----
    prompt_outcomes = f"""
Return valid JSON only.

Format:
{{
  "course": {{"title": "", "code": "", "term": ""}},
  "learning_outcomes": []
}}

Rules:
- Extract only from the syllabus text
- Focus on course title, code, term, and learning outcomes/objectives
- Output JSON only
- No markdown
- No explanation text

Relevant syllabus chunks:
{json.dumps(outcome_chunks, ensure_ascii=False)}
"""
    outcome_data = call_gemini_json(prompt_outcomes, debug_name=f"{doc_id}_outcomes")
    if not isinstance(outcome_data, dict):
        outcome_data = {}
    outcome_data.setdefault("course", {})
    outcome_data.setdefault("learning_outcomes", [])
    outcome_data["learning_outcomes"] = normalize_learning_outcomes(outcome_data.get("learning_outcomes", []))

    # ---- Extract assessments ----
    prompt_assessments = f"""
Return valid JSON only.

Format:
{{
  "assessments": []
}}

Rules:
- Extract only assessments from the syllabus text
- Include exams, quizzes, projects, labs, reports, participation, journals, etc.
- Output JSON only
- No markdown
- No explanation text

Relevant syllabus chunks:
{json.dumps(assessment_chunks, ensure_ascii=False)}
"""
    assessment_data = call_gemini_json(prompt_assessments, debug_name=f"{doc_id}_assessments")
    if not isinstance(assessment_data, dict):
        assessment_data = {}
    assessment_data.setdefault("assessments", [])
    assessment_data["assessments"] = normalize_assessments(assessment_data.get("assessments", []))

    # ---- Extract syllabus policies ----
    prompt_policies = f"""
Return valid JSON only.

Format:
{{
  "syllabus_policies": []
}}

Rules:
- Extract only course-specific syllabus rules
- These may include attendance, grading, submission rules, participation, late work, academic integrity, Blackboard usage, communication expectations
- Output JSON only
- No markdown
- No explanation text

Relevant syllabus chunks:
{json.dumps(policy_chunks, ensure_ascii=False)}
"""
    policy_data = call_gemini_json(prompt_policies, debug_name=f"{doc_id}_policies")
    if not isinstance(policy_data, dict):
        policy_data = {}
    policy_data.setdefault("syllabus_policies", [])
    policy_data["syllabus_policies"] = normalize_syllabus_policies(policy_data.get("syllabus_policies", []))

    data = {
        "course": outcome_data.get("course", {}),
        "learning_outcomes": outcome_data.get("learning_outcomes", []),
        "assessments": assessment_data.get("assessments", []),
        "syllabus_policies": policy_data.get("syllabus_policies", []),
    }

    out_path = PROC_EXTRACTED / f"{doc_id}_syllabus_extracted.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return data


def run_policy_extraction(doc_id: str, chunk_path: str):
    chunks = load_jsonl(chunk_path)[:4]

    prompt = f"""
Return valid JSON only.

Format:
{{
  "ai_policy_summary": "",
  "allowed_ai_uses": [],
  "restricted_ai_uses": [],
  "required_disclosures": [],
  "governance_considerations": []
}}

Rules:
- Extract only from the uploaded university AI policy
- Focus on AI usage in teaching, classroom activities, assignments, academic integrity, privacy, transparency, and faculty oversight
- Output JSON only
- No markdown
- No explanation text

University AI policy chunks:
{json.dumps(chunks, ensure_ascii=False)}
"""

    data = call_gemini_json(prompt, debug_name=f"{doc_id}_policy")

    if not isinstance(data, dict):
        data = {}

    data.setdefault("ai_policy_summary", "")
    data.setdefault("allowed_ai_uses", [])
    data.setdefault("restricted_ai_uses", [])
    data.setdefault("required_disclosures", [])
    data.setdefault("governance_considerations", [])

    out_path = PROC_EXTRACTED / f"{doc_id}_policy_extracted.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return data


def run_recommendation_generation(syllabus_data: dict, policy_data: dict):
    prompt = f"""
Return valid JSON only.

Format:
{{
  "recommendations": [
    {{
      "title": "",
      "description": "",
      "ai_activity_type": "",
      "expected_benefit": "",
      "policy_alignment": "",
      "implementation_note": ""
    }}
  ]
}}

Task:
Using the syllabus analysis and the university AI policy analysis, generate 5 practical recommendations for AI-supported classroom activities, lesson-planning ideas, or assignment enhancements.

Requirements:
- Recommendations must support student engagement, learning, or performance
- Recommendations must align with the university AI policy
- Avoid generic study tips
- Focus on classroom and assignment use cases
- Mention policy alignment clearly
- Output JSON only

Syllabus analysis:
{json.dumps(syllabus_data, ensure_ascii=False)}

University AI policy analysis:
{json.dumps(policy_data, ensure_ascii=False)}
"""

    data = call_gemini_json(prompt, debug_name="recommendations")

    if not isinstance(data, dict):
        data = {}

    recs = data.get("recommendations", [])
    if not isinstance(recs, list):
        recs = []

    data["recommendations"] = recs
    return data


# =========================================================
# Report builder
# =========================================================

def build_report(extracted: dict, graphrag_answer: str = "") -> str:
    report = []

    report.append("### Faculty-Facing Analysis")
    report.append("")

    course = extracted.get("course", {})
    report.append("#### Course Summary")
    report.append(f"- Title: {course.get('title', '')}")
    report.append(f"- Code: {course.get('code', '')}")
    report.append(f"- Term: {course.get('term', '')}")
    report.append("")

    report.append("#### Learning Outcomes")
    for item in extracted.get("learning_outcomes", []):
        report.append(f"- {item}")
    report.append("")

    report.append("#### Assessments")
    for item in extracted.get("assessments", []):
        report.append(f"- {format_assessment_item(item)}")
    report.append("")

    report.append("#### Syllabus Policies")
    for item in extracted.get("syllabus_policies", []):
        formatted = format_policy_item(item)
        if formatted:
            report.append(f"- {formatted}")
    report.append("")

    ai_policy = extracted.get("university_ai_policy", {})
    report.append("#### University AI Policy Summary")
    report.append(f"- Summary: {ai_policy.get('ai_policy_summary', '')}")
    report.append("")

    report.append("#### Allowed AI Uses")
    for item in ai_policy.get("allowed_ai_uses", []):
        report.append(f"- {item}")
    report.append("")

    report.append("#### Restricted AI Uses")
    for item in ai_policy.get("restricted_ai_uses", []):
        report.append(f"- {item}")
    report.append("")

    report.append("#### Required Disclosures")
    for item in ai_policy.get("required_disclosures", []):
        report.append(f"- {item}")
    report.append("")

    report.append("#### Governance Considerations")
    for item in ai_policy.get("governance_considerations", []):
        report.append(f"- {item}")
    report.append("")

    report.append("#### AI Recommendations")
    for rec in extracted.get("recommendations", []):
        if isinstance(rec, dict):
            report.append(f"- **{rec.get('title', '')}**: {rec.get('description', '')}")
            if rec.get("expected_benefit"):
                report.append(f"  - Expected benefit: {rec.get('expected_benefit')}")
            if rec.get("policy_alignment"):
                report.append(f"  - Policy alignment: {rec.get('policy_alignment')}")
            if rec.get("implementation_note"):
                report.append(f"  - Implementation note: {rec.get('implementation_note')}")
        else:
            report.append(f"- {rec}")

    report.append("")
    report.append("#### GraphRAG Insight")
    report.append(graphrag_answer)

    return "\n".join(report)


# =========================================================
# Main pipeline
# =========================================================

def process_uploaded_files(syllabus_file, policy_file: Optional[object] = None):
    syllabus_path = save_uploaded_file(syllabus_file, RAW_SYLLABI)
    policy_path = save_uploaded_file(policy_file, RAW_POLICIES) if policy_file else None

    syllabus_doc_id, syllabus_text_path, syllabus_chunk_path = save_text_and_chunks(syllabus_path)
    syllabus_data = run_syllabus_extraction(syllabus_doc_id, syllabus_chunk_path)

    policy_data = {
        "ai_policy_summary": "",
        "allowed_ai_uses": [],
        "restricted_ai_uses": [],
        "required_disclosures": [],
        "governance_considerations": [],
    }

    if policy_path:
        policy_doc_id, policy_text_path, policy_chunk_path = save_text_and_chunks(policy_path)
        policy_data = run_policy_extraction(policy_doc_id, policy_chunk_path)

    recommendation_data = run_recommendation_generation(syllabus_data, policy_data)

    graphrag_answer = (
        "GraphRAG reference insights are available only for the pre-indexed knowledge base. "
        "Live upload recommendations in this demo are generated directly from the uploaded syllabus and university AI policy."
    )

    final = {
        "course": syllabus_data.get("course", {}),
        "learning_outcomes": syllabus_data.get("learning_outcomes", []),
        "assessments": syllabus_data.get("assessments", []),
        "syllabus_policies": syllabus_data.get("syllabus_policies", []),
        "university_ai_policy": policy_data,
        "recommendations": recommendation_data.get("recommendations", []),
        "graphrag_answer": graphrag_answer,
    }

    final["report_text"] = build_report(final, graphrag_answer)
    return final