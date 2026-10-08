"""Single source of truth for chatbot env vars/constants, mirroring
rag/config.py's pattern so router.py/table_qa.py/exa_rag.py never drift
apart on model name or Exa knobs.
"""

import os

from dotenv import load_dotenv

# main.py already calls this before importing chatbot.graph, but this module
# may be imported standalone (e.g. in tests) - load here too, same reasoning
# as rag/config.py. Idempotent and harmless to call more than once.
load_dotenv()

EXA_API_KEY = os.environ.get("EXA_API_KEY")
EXA_NUM_RESULTS = int(os.environ.get("EXA_NUM_RESULTS", "8"))
EXA_TOP_K = int(os.environ.get("EXA_TOP_K", "3"))

CHAT_GEMINI_MODEL = os.environ.get("CHAT_GEMINI_MODEL", "gemini-3.5-flash-lite")
CHAT_TEMPERATURE = 0.0
