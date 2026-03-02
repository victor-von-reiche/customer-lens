"""
RAG Response Generator Service
Generates responses using retrieved company guidelines.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
from app.rag.vectorstore import knowledge_base

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def generate_response(
    feedback_text: str,
    sentiment: str,
    category: str
) -> dict:
    """
    Generate customer service response using RAG.

    Args:
        feedback_text: Original customer feedback
        sentiment: Sentiment analysis result
        category: Feedback category

    Returns:
        dict: Generated response
    """

    search_query = f"{category} {sentiment} {feedback_text}"
    relevant_guidelines = knowledge_base.search_relevant_guidelines(search_query, n_results=3)

    prompt = f"""You are a customer service representative for AURON, a professional road bike web shop.

RELEVANT COMPANY GUIDELINES:
{relevant_guidelines}

CUSTOMER FEEDBACK ANALYSIS:
- Sentiment: {sentiment}
- Category: {category}
- Feedback: "{feedback_text}"

Write a professional response following the guidelines above.
Requirements:
- Be empathetic and solution-oriented
- Reference specific policies if relevant
- Keep it concise (2-4 sentences)
- Maintain AURON's professional tone

Write only the response text."""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a customer service representative for AURON road bikes. Write professional, empathetic responses."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=200
        )

        generated_response = response.choices[0].message.content.strip()

        return {"response": generated_response}

    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return {
            "response": "Thank you for contacting AURON. We will review your feedback and respond shortly."
        }