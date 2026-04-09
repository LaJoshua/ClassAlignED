import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path.home() / "Desktop" / "CLASS_ALIGNED_MVP_UI_DEMO"

RAW_SYLLABI = PROJECT_ROOT / "raw/syllabi"
RAW_POLICIES = PROJECT_ROOT / "raw/policies"

PROC_TEXT = PROJECT_ROOT / "processed/text"
PROC_CHUNKS = PROJECT_ROOT / "processed/chunks"
PROC_EXTRACTED = PROJECT_ROOT / "processed/extracted"

GRAPHRAG_WS = PROJECT_ROOT / "processed/graphrag_workspace"

OUTPUT_REPORTS = PROJECT_ROOT / "outputs/reports"

MODEL_NAME = "gemini-2.5-flash"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")