"""Final node: always runs, regardless of branch. Rewrites whichever
branch's raw_answer into one short, plain-language reply. Passes warnings
through untouched rather than inventing content around them.
"""

import logging

from langchain_core.prompts import ChatPromptTemplate

from chatbot.llm import get_chat_llm
from chatbot.state import ChatState

logger = logging.getLogger("ai_marketing_strategist")

_SYSTEM_PROMPT = """\
Rewrite the answer below into 2-4 short, plain-language sentences for a
marketing manager. Do not add new facts. If a warning is present, keep it
and state it plainly - do not minimize or hide it."""

_prompt = ChatPromptTemplate.from_messages(
    [("system", _SYSTEM_PROMPT), ("human", "ANSWER\n{raw_answer}\n\nWARNING\n{warning}")]
)


def simplify_answer(state: ChatState) -> dict:
    raw_answer = state.get("raw_answer", "")
    warning = state.get("warning")

    try:
        llm = get_chat_llm()
        chain = _prompt | llm
        response = chain.invoke({"raw_answer": raw_answer, "warning": warning or "(none)"})
        final_answer = response.content if hasattr(response, "content") else str(response)
        return {"final_answer": final_answer}
    except Exception:
        logger.exception("simplify failed - returning the raw answer unmodified.")
        return {"final_answer": raw_answer}
