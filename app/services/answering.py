from openai import OpenAI
from app.config import settings


def build_answer(question: str, hits: list[dict]) -> str:
    if settings.openai_api_key:
        client = OpenAI(api_key=settings.openai_api_key)
        context = "\n\n".join(f"[{hit['filename']}] {hit['text']}" for hit in hits)
        response = client.chat.completions.create(
            model=settings.openai_model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": "Answer the customer using only the supplied support knowledge. If it does not contain the answer, say you are unsure and recommend a human agent. Cite sources as [filename]. Be concise."},
                {"role": "user", "content": f"Question: {question}\n\nSupport knowledge:\n{context}"},
            ],
        )
        return response.choices[0].message.content or "I couldn't draft an answer. A support specialist can help."
    if not hits:
        return "I couldn't find this in the available support documents. Please contact a support specialist for help."
    # Demo mode quotes the best matching passage so every claim stays grounded.
    return f"Based on {hits[0]['filename']}: {hits[0]['text']}"
