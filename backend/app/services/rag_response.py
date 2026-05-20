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
    category: str,
    conversation_history: str = ""
) -> dict:
    """
    Generate customer service response using RAG.

    Args:
        feedback_text: Original customer feedback
        sentiment: Sentiment analysis result
        category: Feedback category
        conversation_history: Full conversation history for context

    Returns:
        dict: Generated response
    """

    search_query = f"{category} {sentiment} {feedback_text}"
    relevant_guidelines = knowledge_base.search_relevant_guidelines(search_query, n_results=3)

    history_section = ""
    if conversation_history:
        history_section = f"""
CONVERSATION HISTORY:
{conversation_history}

"""

    prompt = f"""You are a specialized HUMAN customer service representative for AURON, a premium professional road bike brand. 
Read the latest message and the history carefully to understand the customer's emotional state and current situation.

RELEVANT COMPANY GUIDELINES (Reference these for facts/policies, but use natural, human language):
{relevant_guidelines}

{history_section}CUSTOMER FEEDBACK ANALYSIS:
- Sentiment: {sentiment}
- Category: {category}
- Latest message: "{feedback_text}"

WRITE A RESPONSE THAT FOLLOWS THESE CRITICAL RULES:
1. PRIORITIZE EMPATHY: If the customer mentions an accident, injury, or distress, your first priority is their well-being. Sound like a real person who cares.
2. NO REDUNDANCY: NEVER ask for details the customer has already mentioned (e.g., if they said the brakes failed, don't ask what happened).
3. NATURAL TONE: Avoid robotic "According to our policy" phrasing. Integrate necessary facts seamlessly and empathetically.
4. SITUATIONAL AWARENESS: Acknowledge specific details like "hospital", "accident", or "refund" directly.
5. CONCISENESS: Keep it to 2-4 high-impact sentences.

Write ONLY the response text."""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a warm, highly empathetic Customer Success Manager at AURON. You treat customers like friends, providing professional support with a deeply human touch. You never repeat what the customer already said."
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