"""
AeroSentinel Configuration
All settings in one place. Secrets come from environment variables.
"""
import os

# --- API KEYS (from GitHub Secrets / environment) ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")

# --- LLM MODEL ---
GEMINI_MODEL = "gemini-2.0-flash"  # Best free-tier model with generous quota
GEMINI_MAX_TOKENS = 1024

# --- JOURNAL TIERS ---
TIER_1_JOURNALS = [
    "AIAA Journal",
    "Journal of Spacecraft and Rockets",
    "Journal of Thermophysics and Heat Transfer",
    "Physics of Fluids",
    "Journal of Fluid Mechanics",
    "Aerospace Science and Technology",
    "Journal of Guidance, Control, and Dynamics",
    "Experiments in Fluids",
    "Annual Review of Fluid Mechanics",
    "Shock Waves",
]

TIER_2_JOURNALS = [
    "Computers & Fluids",
    "International Journal of Heat and Mass Transfer",
    "Acta Astronautica",
    "Chinese Journal of Aeronautics",
    "Progress in Aerospace Sciences",
    "Aerospace",
    "International Journal of Aerospace Engineering",
    "Flow, Turbulence and Combustion",
    "Applied Thermal Engineering",
    "Journal of Computational Physics",
]

# --- KEYWORDS ---
KEYWORDS = [
    "aerodynamic heating",
    "hypersonic boundary layer",
    "reentry vehicle aerodynamics",
    "shock wave boundary layer interaction",
    "missile aerodynamics",
    "scramjet aerothermodynamics",
    "hypersonic transition prediction",
    "computational fluid dynamics hypersonic",
    "machine learning aerodynamics",
    "ablation thermal protection",
    "high enthalpy flow",
    "aerothermal analysis",
    "catalytic wall effects hypersonic",
    "rarefied gas dynamics reentry",
]

# --- ELITE INSTITUTIONS ---
ELITE_INSTITUTIONS = [
    "NASA", "DLR", "ONERA", "JAXA", "CNRS",
    "Von Karman Institute", "Sandia National Laboratories",
    "Los Alamos National Laboratory", "Air Force Research Laboratory",
    "ESA", "ISRO", "CAST", "CARDC", "TsAGI", "KAIST",
    "Caltech", "Stanford", "MIT", "Purdue",
    "University of Michigan", "University of Minnesota",
    "University of Oxford", "Imperial College", "RWTH Aachen",
]

# --- FILTER SETTINGS ---
LOOKBACK_DAYS = 14
CITATION_VELOCITY_THRESHOLD = 5
MAX_PAPERS_PER_POST = 6
MIN_PAPERS_PER_POST = 2

# --- FILE PATHS ---
HISTORY_FILE = "seen_papers.json"
DRAFTS_DIR = "content/drafts"
POSTS_DIR = "content/posts"

# --- RATE LIMITING ---
S2_REQUESTS_PER_SECOND = 0.5
S2_MAX_RETRIES = 3
