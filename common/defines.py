import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DBFILE_DIR = os.path.join(DATA_DIR, "db")
M18_BEND_INI_PATH = os.path.join(APP_DIR, "m18_bend.ini")

# SQLite 기본 파일 경로
DB_FILE_PATH = os.path.join(DBFILE_DIR, "mission18.db")
DEFAULT_DATABASE_URL = f"sqlite:///{DB_FILE_PATH.replace(os.sep, '/')}"

APP_NAME = "mission18-backend"
APP_TITLE = "Mission18 Backend"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "Mission18 FastAPI backend starter project"

SENTIMENT_NEUTRAL_SCORE = 0.5
SENTIMENT_POSITIVE_SCORE = 1.0
SENTIMENT_NEGATIVE_SCORE = 0.0
SENTIMENT_MIN_RATING = 1
SENTIMENT_NEUTRAL_RATING = 3
SENTIMENT_MAX_RATING = 5
SENTIMENT_POSITIVE_KEYWORDS = ["좋", "재밌", "훌륭", "추천", "감동", "최고"]
SENTIMENT_NEGATIVE_KEYWORDS = ["별로", "지루", "최악", "실망", "나쁘", "후회"]

INI_SECTION_SENTIMENT = "sentiment"
INI_SECTION_HUGGINGFACE = "huggingface"
INI_SECTION_OLLAMA = "ollama"

INI_KEY_USEMODEL = "usemodel"
INI_KEY_PROVIDER = "provider"
INI_KEY_HUGGINGFACE_MODEL = "huggingface_model"
INI_KEY_OLLAMA_MODEL = "ollama_model"
INI_KEY_OLLAMA_BASE_URL = "ollama_base_url"
INI_KEY_OLLAMA_TIMEOUT_SEC = "ollama_timeout_sec"

SENTIMENT_PROVIDER_HUGGINGFACE = "huggingface"
SENTIMENT_PROVIDER_OLLAMA = "ollama"
SENTIMENT_PROVIDER_HUGGINFLACE = "hugginflace"

DEFAULT_SENTIMENT_PROVIDER = SENTIMENT_PROVIDER_HUGGINGFACE
DEFAULT_HUGGINGFACE_MODEL = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
DEFAULT_OLLAMA_MODEL = "llama3.1:8b"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_TIMEOUT_SEC = 30