# 📘 CLASS AlignED

**Bridging the gap between AI policy and classroom practice**

CLASS AlignED is an AI-powered system that helps educators align course design with university AI policies by transforming syllabi and policy documents into **actionable, policy-aware teaching recommendations**.

---

# 🚨 Problem

As AI adoption grows in higher education, faculty face a major challenge:

- Universities provide **AI policies**, but  
- Faculty lack **practical guidance** on how to apply them in real courses  

This creates a **policy–practice gap**:

> Policies exist, but instructors don’t know how to implement them in assignments, assessments, or lesson planning.

---

# 💡 Solution

CLASS AlignED solves this by:

- Ingesting **course syllabi** + **university AI policies**
- Structuring and analyzing them using AI
- Generating **clear, policy-aligned recommendations** for teaching

👉 Instead of interpreting policy manually, faculty receive **ready-to-use guidance**.

---

# 🧠 System Overview

The system works as a pipeline:

## 1. 📥 Input
- Upload:
  - Course syllabus (PDF/DOCX)
  - University AI policy

---

## 2. ⚙️ Processing
- Extract text from documents
- Chunk content into manageable pieces
- Structure data using AI

---

## 3. 🤖 AI Recommendation Engine
- Uses **Gemini (LLM)** to extract:
  - Learning outcomes
  - Assessments
  - Policies
- Uses **GraphRAG** to:
  - Connect syllabus + policy + contextual knowledge
  - Generate grounded recommendations

---

## 4. 📊 Output

Produces:
- Course summary
- Learning outcomes
- Assessment breakdown
- Policy interpretation
- AI-supported teaching recommendations

---

# 🏗️ Tech Stack

### Core AI
- **Gemini API** → structured extraction + reasoning  
- **GraphRAG** → knowledge graph + contextual querying  

### Backend
- Python
- JSON / JSONL pipelines
- Subprocess-based GraphRAG integration

### Document Processing
- `pypdf` → PDF parsing  
- `python-docx` → DOCX parsing  

### UI (Demo App)
- **Streamlit** → interactive frontend  

---

# 📁 Projects

## 1️⃣ CLASS_AlignED_MVP

The original backend system that:

- Processes syllabus + policy documents
- Chunks and extracts structured data
- Runs GraphRAG indexing + querying
- Outputs:
  - JSON results
  - Graph-based insights
  - Faculty-facing reports

### Key Features
- End-to-end pipeline (CLI-based)
- GraphRAG knowledge integration
- Policy-aware AI recommendations

---

## 2️⃣ CLASS_ALIGNED_MVP_UI_DEMO

A user-facing application built on top of the MVP.

### What we added:
- 📤 File upload interface (Streamlit)
- 📂 Automatic file routing:
  - `raw/syllabi`
  - `raw/policies`
- ⚙️ Integrated pipeline execution
- 📊 Clean UI outputs:
  - Course summary
  - Learning outcomes
  - Assessments
  - Policies
  - AI recommendations
  - GraphRAG insights

### Goal:
> Make the system usable by **non-technical faculty**

---

# 🔄 How It Works (Step-by-Step)

1. User uploads syllabus + policy  
2. Files are saved to structured directories  
3. Text is extracted and chunked  
4. Gemini extracts structured course data  
5. GraphRAG builds relationships + context  
6. System generates:
   - Recommendations
   - Reports
   - Insights  

---

# 🎯 Key Innovation

CLASS AlignED doesn’t just analyze documents — it:

> **Transforms static policies into actionable teaching strategies**

---

# 📈 Impact

- Reduces faculty uncertainty around AI usage  
- Embeds policy into real classroom workflows  
- Supports scalable adoption of AI in education  
- Especially impactful for institutions with limited resources  

---

# 🚀 Future Work

- Stronger policy–recommendation alignment  
- Improved GraphRAG grounding with research datasets  
- Better UI/UX for faculty workflows  
- Integration with LMS platforms (e.g., Blackboard, Canvas)  

---

# 🧑‍🏫 Example Use Case

An instructor uploads:
- A syllabus  
- Their university’s AI policy  

The system returns:
- AI-supported assignment ideas  
- Policy-compliant usage guidelines  
- Suggestions to improve engagement and learning outcomes  

---

# 🧪 Running the Project

## 🔧 1. Set Up Environment

```bash
# Create virtual environment (if needed)
python -m venv graphrag-env

# Activate it
source graphrag-env/bin/activate  # Mac/Linux
# or
graphrag-env\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## 🔑 2. Set API Key

Create a `.env` file in your project root:

```env
GEMINI_API_KEY=your_api_key_here
```

---

## 🧠 3. Run CLASS_AlignED_MVP (Backend)

Navigate to your GraphRAG workspace:

```bash
cd processed/graphrag_workspace
```

### Index documents
```bash
graphrag index --root .
```

### Run a query
```bash
graphrag query --root . --method local "Identify AI-supported teaching strategies"
```

---

## 🖥️ 4. Run CLASS_ALIGNED_MVP_UI_DEMO (Frontend App)

From the UI demo project root:

```bash
cd ~/Desktop/CLASS_ALIGNED_MVP_UI_DEMO
```

Start the app:

```bash
streamlit run app/streamlit_app.py
```

---

## 📂 5. Using the UI

1. Upload:
   - Course syllabus (PDF or DOCX)
   - University AI policy

2. The system will automatically:
   - Save files to:
     - `raw/syllabi`
     - `raw/policies`
   - Extract and chunk text
   - Run Gemini extraction
   - Run GraphRAG query

3. View results in the UI:
   - Course summary
   - Learning outcomes
   - Assessments
   - Policies
   - AI recommendations
   - GraphRAG insights

---

## ⚠️ Notes

- Make sure your `GEMINI_API_KEY` is valid and loaded  
- Ensure GraphRAG workspace is initialized before querying  
- If GraphRAG errors occur, re-run:

```bash
graphrag index --root .
```

---

## ✅ Quick Start (TL;DR)

```bash
# Activate env
source graphrag-env/bin/activate

# Run UI
cd ~/Desktop/CLASS_ALIGNED_MVP_UI_DEMO
streamlit run app/streamlit_app.py
```
