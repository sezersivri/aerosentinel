"""
AeroSentinel Configuration
All settings in one place. Secrets come from environment variables.

# ============================================================
#  HOW TO EDIT KEYWORDS
# ============================================================
#  Keywords are organized into 3 priority tiers derived from:
#  "Prediction of Aerodynamic Heating on High-Speed Missiles
#   Using Gaussian Process Based Surrogate Models"
#
#  Priority 1 (+25 pts) — AI/ML in aerothermodynamics (core research)
#  Priority 2 (+15 pts) — General aerothermodynamics & heating
#  Priority 3 (baseline)  — Broader aerospace & CFD
#
#  To adjust: move keywords between tiers or add new ones.
#  Each keyword is searched across all academic sources.
#  The KEYWORD_PRIORITY dict is built automatically from the lists.
#
#  Future: /keywords Telegram command or external YAML config.
# ============================================================
"""
import os

# --- API KEYS (from GitHub Secrets / environment) ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")
IEEE_API_KEY = os.environ.get("IEEE_API_KEY", "")

# --- LLM MODEL ---
GEMINI_MODEL = "gemini-2.5-flash"  # Smartest free-tier model
GEMINI_MAX_TOKENS = 16384  # Needs headroom for 6 papers + rich prompts

# --- LANGUAGES ---
LANGUAGES = ["en", "tr"]

# --- KEYWORD TIERS ---

# Priority 1 — AI/ML in Aerothermodynamics (core thesis research)
PRIORITY_1_KEYWORDS = [
    "machine learning aerodynamic heating",
    "surrogate model aerodynamic heating",
    "Gaussian process regression aerodynamics",
    "deep learning heat flux prediction",
    "neural network CFD prediction",
    "physics-informed neural network aerodynamics",
    "multi-fidelity model aerodynamics",
    "deep kernel learning aerothermodynamics",
]

# Priority 2 — General Aerothermodynamics & Aerodynamic Heating
PRIORITY_2_KEYWORDS = [
    "aerodynamic heating prediction",
    "aerodynamic heating missile",
    "stagnation point heat transfer",
    "hypersonic boundary layer transition",
    "shock wave boundary layer interaction",
    "conjugate heat transfer hypersonic",
    "ablation thermal protection system",
    "reentry vehicle heating",
    "high enthalpy flow",
]

# Priority 3 — Broader Aerospace & CFD
PRIORITY_3_KEYWORDS = [
    "missile aerodynamics",
    "computational fluid dynamics hypersonic",
    "scramjet aerothermodynamics",
    "rarefied gas dynamics reentry",
    "turbulence modeling hypersonic",
]

# Combined flat list (used by hunter search loops)
KEYWORDS = PRIORITY_1_KEYWORDS + PRIORITY_2_KEYWORDS + PRIORITY_3_KEYWORDS

# Priority lookup dict: keyword -> bonus points (used in rank_and_select)
KEYWORD_PRIORITY = {}
for _kw in PRIORITY_1_KEYWORDS:
    KEYWORD_PRIORITY[_kw.lower()] = 25
for _kw in PRIORITY_2_KEYWORDS:
    KEYWORD_PRIORITY[_kw.lower()] = 15
for _kw in PRIORITY_3_KEYWORDS:
    KEYWORD_PRIORITY[_kw.lower()] = 0

# --- CURATED TAG VOCABULARY (35 tags) ---
CURATED_TAGS = {
    "research_domains": [
        "Aerothermodynamics", "Hypersonic Aerodynamics", "Supersonic Aerodynamics",
        "Thermal Protection Systems", "Flight Vehicle Design", "Reentry Physics",
        "Scramjet Propulsion",
    ],
    "methodologies": [
        "Gaussian Process Surrogates", "Neural Network Surrogates", "Deep Learning",
        "Multi-Fidelity Modeling", "Design Optimization", "Reduced-Order Modeling",
        "Data-Driven Methods", "Analytical Methods",
    ],
    "physical_phenomena": [
        "Stagnation Point Heating", "Shock-Boundary Layer Interaction", "Real Gas Effects",
        "Turbulent Heating", "Radiative Heating", "Ablation Modeling",
        "Laminar Heating", "Entropy Layer Effects",
    ],
    "flow_regimes": [
        "Hypersonic Flow", "High Enthalpy Flow", "Rarefied Flow",
    ],
    "applications": [
        "Missile Aerothermodynamics", "Reentry Vehicles", "Launch Vehicles",
        "Planetary Entry",
    ],
    "cross_cutting": [
        "Heat Flux Prediction", "Surrogate Modeling", "High-Performance Computing",
        "Review Paper", "Thesis Research",
    ],
}

# Flat set for fast membership checks
VALID_TAGS = {tag for tags in CURATED_TAGS.values() for tag in tags}

# Lowercase -> canonical mapping for normalization
VALID_TAGS_LOWER = {tag.lower(): tag for tag in VALID_TAGS}

# --- VALID PAPER TYPES (8 types) ---
VALID_PAPER_TYPES = [
    "ml_heating", "ml_aerodynamics", "ml_transition",
    "numerical_cfd", "experimental", "analytical",
    "review", "multi_method", "thesis",
]

# --- SCORING & FILTERING THRESHOLDS ---
MIN_HUNTER_SCORE = 30
MIN_RELEVANCE_SCORE = 40
MAX_PAPER_AGE_DAYS = 90

# --- TWO-TIER POST STRUCTURE ---
# Core focus: papers directly on these topics get full solo reviews.
# Everything else goes into a narrative "Broader Context" section.
CORE_FOCUS_KEYWORDS = [
    "aerodynamic heating",
    "heat flux prediction",
    "thermal protection",
    "stagnation point heating",
    "surface heating",
    "aeroheating",
    "aerothermodynamic heating",
    "machine learning aerodynamics",
    "surrogate model",
    "gaussian process",
    "neural network cfd",
    "deep learning aerodynamics",
    "physics-informed neural network",
    "data-driven cfd",
    "ml surrogate",
]
# Core paper types — these are always considered core focus
CORE_PAPER_TYPES = ["ml_heating", "ml_aerodynamics", "ml_transition"]
# Below this score, papers are dropped entirely (truly irrelevant)
MIN_PERIPHERAL_SCORE = 20

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

# --- USAGE STATS ---
USAGE_STATS_FILE = "usage_stats.json"

# --- TAG-TO-KEYWORDS MAPPING (for custom searches) ---
TAG_TO_KEYWORDS = {
    "Aerothermodynamics": ["aerodynamic heating", "aerothermodynamics"],
    "Hypersonic Aerodynamics": ["hypersonic aerodynamics", "hypersonic flow prediction"],
    "Supersonic Aerodynamics": ["supersonic aerodynamics", "supersonic flow"],
    "Thermal Protection Systems": ["thermal protection system", "heat shield material"],
    "Flight Vehicle Design": ["flight vehicle design", "aerospace vehicle configuration"],
    "Reentry Physics": ["reentry aerothermodynamics", "atmospheric reentry heating"],
    "Scramjet Propulsion": ["scramjet aerothermodynamics", "scramjet combustion"],
    "Gaussian Process Surrogates": ["Gaussian process regression aerodynamics", "kriging surrogate model aerodynamic"],
    "Neural Network Surrogates": ["neural network surrogate model CFD", "deep learning surrogate aerodynamics"],
    "Deep Learning": ["deep learning heat flux prediction", "neural network CFD prediction"],
    "Multi-Fidelity Modeling": ["multi-fidelity model aerodynamics", "multi-fidelity surrogate"],
    "Design Optimization": ["aerodynamic shape optimization", "multidisciplinary design optimization aerospace"],
    "Reduced-Order Modeling": ["reduced order model aerodynamics", "proper orthogonal decomposition CFD"],
    "Data-Driven Methods": ["data-driven aerodynamic prediction", "machine learning aerodynamic heating"],
    "Analytical Methods": ["analytical aerodynamic heating", "engineering correlation heat transfer"],
    "Stagnation Point Heating": ["stagnation point heat transfer", "nose tip heating prediction"],
    "Shock-Boundary Layer Interaction": ["shock wave boundary layer interaction", "SWBLI hypersonic"],
    "Real Gas Effects": ["real gas effects hypersonic", "thermochemical nonequilibrium"],
    "Turbulent Heating": ["turbulent heating prediction", "turbulent heat flux hypersonic"],
    "Radiative Heating": ["radiative heating reentry", "thermal radiation hypersonic"],
    "Ablation Modeling": ["ablation thermal protection", "ablative heat shield modeling"],
    "Laminar Heating": ["laminar heating prediction", "laminar boundary layer heating"],
    "Entropy Layer Effects": ["entropy layer effects hypersonic", "entropy swallowing"],
    "Hypersonic Flow": ["hypersonic flow simulation", "Mach 5 flow CFD"],
    "High Enthalpy Flow": ["high enthalpy flow", "high temperature gas dynamics"],
    "Rarefied Flow": ["rarefied gas dynamics reentry", "DSMC hypersonic"],
    "Missile Aerothermodynamics": ["missile aerodynamic heating", "missile thermal analysis"],
    "Reentry Vehicles": ["reentry vehicle aerothermodynamics", "capsule heat shield"],
    "Launch Vehicles": ["launch vehicle aerodynamics", "rocket aerothermal"],
    "Planetary Entry": ["Mars entry heating", "planetary entry aerothermodynamics"],
    "Heat Flux Prediction": ["heat flux prediction CFD", "surface heat transfer rate"],
    "Surrogate Modeling": ["surrogate model aerodynamics", "metamodel aerospace"],
    "High-Performance Computing": ["high performance computing CFD", "GPU accelerated CFD"],
    "Review Paper": ["review aerodynamic heating", "survey hypersonic aerothermodynamics"],
}
