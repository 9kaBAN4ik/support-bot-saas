from openai import OpenAI
from config import GROQ_API_KEY, CHAT_MODEL
import rag


client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)


def answer_question(business_id: int, question: str, system_prompt: str = "") -> str:
    context_chunks = rag.search(business_id, question)

    if context_chunks:
        context = "\n\n---\n\n".join(context_chunks)
        system = (
            f"{system_prompt}\n\n"
            "Answer the user's question based ONLY on the knowledge base below. "
            "If the answer is not in the knowledge base, say you don't have that information "
            "and suggest contacting support directly.\n\n"
            f"Knowledge base:\n{context}"
        )
    else:
        system = (
            f"{system_prompt}\n\n"
            "The knowledge base is empty. Tell the user that the support system "
            "is being set up and suggest contacting the business directly."
        )

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": question},
        ],
        max_tokens=500,
        temperature=0.3,
    )
    return response.choices[0].message.content
