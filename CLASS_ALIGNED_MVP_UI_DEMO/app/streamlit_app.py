import json
import streamlit as st
from pipeline import process_uploaded_files

st.set_page_config(
    page_title="CLASS AlignED",
    layout="wide"
)

st.title("CLASS AlignED")
st.subheader("Upload a syllabus and university AI policy to generate analysis and recommendations")

with st.sidebar:
    st.header("Inputs")
    syllabus_file = st.file_uploader("Upload Syllabus", type=["pdf", "docx"])
    policy_file = st.file_uploader("Upload University AI Policy", type=["pdf"])
    run_btn = st.button("Run Analysis", type="primary")


def format_assessment_item(item):
    if isinstance(item, str):
        cleaned = item.strip()
        return cleaned if cleaned else "Assessment"

    if isinstance(item, dict):
        # Try several possible field names
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
            # Last resort: show raw dict compactly so you can see what's there
            visible = {k: v for k, v in item.items() if v not in ("", None, [], {})}
            return str(visible) if visible else "Assessment"

        extras = []
        if percentage not in ("", None, 0):
            extras.append(f"{percentage}%")
        if points not in ("", None, 0):
            extras.append(f"{points} points")
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
        ptype = item.get("policy_type", "").strip()
        desc = item.get("description", "").strip()

        if ptype and desc:
            return f"{ptype}: {desc}"
        if desc:
            return desc
        if ptype:
            return ptype

    return str(item)


def render_course_summary(course: dict):
    st.header("📘 Course Summary")
    st.markdown(
        f"""
**Title:** {course.get("title", "")}  
**Code:** {course.get("code", "")}  
**Term:** {course.get("term", "")}
"""
    )


def render_learning_outcomes(outcomes):
    st.header("🎯 Learning Outcomes")
    if not outcomes:
        st.info("No learning outcomes were extracted.")
        return

    for i, outcome in enumerate(outcomes, start=1):
        if isinstance(outcome, dict):
            st.write(f"{i}. {outcome.get('text', '')}")
        else:
            st.write(f"{i}. {outcome}")


def render_assessments(assessments):
    st.header("📝 Assessments")
    if not assessments:
        st.info("No assessments were extracted.")
        return

    for item in assessments:
        st.write(f"- {format_assessment_item(item)}")


def render_syllabus_policies(policies):
    st.header("📜 Syllabus Policies")
    if not policies:
        st.info("No syllabus policies were extracted.")
        return

    shown = 0
    for item in policies:
        formatted = format_policy_item(item)
        if formatted:
            st.write(f"- {formatted}")
            shown += 1

    if shown == 0:
        st.info("No syllabus policies were extracted.")


def render_university_ai_policy(policy_data):
    st.header("🏛️ University AI Policy")

    if not policy_data:
        st.info("No university AI policy analysis available.")
        return

    summary = policy_data.get("ai_policy_summary", "")
    if summary:
        st.markdown(f"**Summary:** {summary}")

    allowed = policy_data.get("allowed_ai_uses", [])
    restricted = policy_data.get("restricted_ai_uses", [])
    disclosures = policy_data.get("required_disclosures", [])
    governance = policy_data.get("governance_considerations", [])

    if allowed:
        st.subheader("Allowed AI Uses")
        for item in allowed:
            st.write(f"- {item}")

    if restricted:
        st.subheader("Restricted AI Uses")
        for item in restricted:
            st.write(f"- {item}")

    if disclosures:
        st.subheader("Required Disclosures")
        for item in disclosures:
            st.write(f"- {item}")

    if governance:
        st.subheader("Governance Considerations")
        for item in governance:
            st.write(f"- {item}")


def render_recommendations(recommendations):
    st.header("🤖 AI Recommendations")
    if not recommendations:
        st.info("No recommendations were generated.")
        return

    for i, rec in enumerate(recommendations, start=1):
        if isinstance(rec, dict):
            title = rec.get("title", f"Recommendation {i}")
            description = rec.get("description", "")
            ai_activity_type = rec.get("ai_activity_type", "")
            expected_benefit = rec.get("expected_benefit", "")
            policy_alignment = rec.get("policy_alignment", "")
            implementation_note = rec.get("implementation_note", "")

            st.markdown(f"### {i}. {title}")

            if ai_activity_type:
                st.markdown(f"**AI Activity Type:** {ai_activity_type}")

            if description:
                st.write(description)

            if expected_benefit:
                st.markdown(f"**Expected Benefit:** {expected_benefit}")

            if policy_alignment:
                st.markdown(f"**Policy Alignment:** {policy_alignment}")

            if implementation_note:
                st.markdown(f"**Implementation Note:** {implementation_note}")

            st.markdown("---")
        else:
            st.write(f"{i}. {rec}")


def render_graphrag_answer(answer: str):
    st.header("🧠 GraphRAG Insights")
    if not answer or not answer.strip():
        st.info("No GraphRAG answer available.")
        return

    if answer.lower().startswith("graphrag is currently unavailable"):
        st.warning(answer)
        return

    st.write(answer)


def render_report(report_text: str):
    st.header("📄 Final Report")
    if not report_text or not report_text.strip():
        st.info("No report available.")
        return
    st.markdown(report_text)


if run_btn:
    if syllabus_file is None:
        st.error("Please upload a syllabus.")
    else:
        try:
            with st.spinner("Saving files and running pipeline..."):
                result = process_uploaded_files(syllabus_file, policy_file)

            st.success("Analysis complete.")

            tab1, tab2, tab3, tab4 = st.tabs(
                ["Summary", "Policy", "Recommendations", "GraphRAG / Report"]
            )

            with tab1:
                render_course_summary(result.get("course", {}))
                render_learning_outcomes(result.get("learning_outcomes", []))
                render_assessments(result.get("assessments", []))
                render_syllabus_policies(result.get("syllabus_policies", []))

            with tab2:
                render_university_ai_policy(result.get("university_ai_policy", {}))

            with tab3:
                render_recommendations(result.get("recommendations", []))

            with tab4:
                render_graphrag_answer(result.get("graphrag_answer", ""))
                render_report(result.get("report_text", ""))

            st.download_button(
                "Download JSON Results",
                data=json.dumps(result, indent=2),
                file_name="class_aligned_result.json",
                mime="application/json"
            )

            st.download_button(
                "Download Faculty Report",
                data=result.get("report_text", ""),
                file_name="faculty_report.md",
                mime="text/markdown"
            )

        except Exception as e:
            st.error(str(e))
            st.stop()