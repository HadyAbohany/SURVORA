"""Runtime configuration. .env loaded without external dotenv dependency."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_dotenv(path=ROOT / '.env'):
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, val = line.split('=', 1)
        if key.strip() not in os.environ:
            os.environ[key.strip()] = val.strip().strip('"').strip("'")

load_dotenv()

def env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in ('1','true','yes','on')

def keys():
    """Order matters. Distinct keys may still share project quota."""
    candidates = [os.getenv('GEMINI_API_KEY', '').strip()] + [os.getenv(f'GEMINI_API_KEY_{i}', '').strip() for i in range(1, 11)]
    result = []
    for key in candidates:
        if key and key not in result:
            result.append(key)
    return result

TEXT_MODEL = os.getenv('GEMINI_TEXT_MODEL', 'gemini-2.5-flash-lite')
EMBED_MODEL = os.getenv('NOVA_EMBED_MODEL', 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
