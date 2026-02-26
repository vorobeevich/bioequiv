import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Загружаем .env если есть
_env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(_env_path):
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())

EAEU_REGISTRY_CSV = os.path.join(DATA_DIR, "eaeu_registry.csv")
DRUGBANK_CSV = os.path.join(DATA_DIR, "drugbank_pk.csv")
VIDAL_MOLECULES_CSV = os.path.join(DATA_DIR, "vidal_molecules.csv")
VIDAL_DRUGS_CSV = os.path.join(DATA_DIR, "vidal_drugs_merged.csv")
EDRUG3D_CSV = os.path.join(DATA_DIR, "edrug3d_pk.csv")
OSP_CSV = os.path.join(DATA_DIR, "osp_pk_parameters.csv")

OHLP_CSV = os.path.join(DATA_DIR, "ohlp_pk_texts.csv")
OHLP_ENABLED = os.path.exists(OHLP_CSV)

CVINTRA_PMC_CSV = os.path.join(DATA_DIR, "cvintra_pmc.csv")

FDA_PSG_CSV = os.path.join(DATA_DIR, "fda_psg_parsed.csv")
FDA_PSG_ENABLED = os.path.exists(FDA_PSG_CSV)

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = "deepseek-chat"

FUZZY_THRESHOLD = 80
