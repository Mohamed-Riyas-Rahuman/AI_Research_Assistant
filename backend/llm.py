import os
from groq import Groq

API_KEY = os.environ.get("GROQ_API_KEY", "")

SYSTEM_PROMPT = """You are a research assistant that answers questions using ONLY the
provided context extracted from the user's uploaded PDF documents.

Rules:
1. Answer strictly using the context below. Do not use outside knowledge.
2. If the answer is not present in the context, respond exactly:
   "I don't know based on the uploaded documents."
3. Be concise and accurate.
"""

def build_prompt(context: str, question: str, chat_history: str = "") -> str:
    history_block = f"\nConversation so far:\n{chat_history}\n" if chat_history else ""
    return f"""Context:
{context}
{history_block}
Question: {question}

Answer:"""

def generate_answer(context: str, question: str, chat_history: str = "") -> str:
    if not API_KEY:
        return "GROQ_API_KEY is not set in .env file."

    try:
        client = Groq(api_key=API_KEY)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_prompt(context, question, chat_history)}
            ],
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        return f"LLM error: {exc}"