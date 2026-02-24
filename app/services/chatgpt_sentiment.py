import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def analyze_sentiment(feedback_text: str) -> dict:
    """
    Analyze the sentiment of customer feedback using ChatGPT.

    This function sends the feedback to ChatGPT and asks it to determine
    if the sentiment is positive, negative, neutral, or mixed.

    Args:
        feedback_text (str): The customer's feedback text to analyze

    Returns:
        dict: {
            'sentiment': str,  # 'positive', 'negative', 'neutral', or 'mixed'
            'confidence': float,  # How confident the AI is (0-1)
            'reasoning': str  # Why the AI chose this sentiment
        }
    """

    # Create a prompt for ChatGPT
    prompt = f"""Analyze the sentiment of this customer feedback and classify it as one of:
- positive: Customer is happy/satisfied
- negative: Customer is unhappy/dissatisfied
- neutral: No strong emotion either way
- mixed: Both positive and negative aspects

Customer Feedback: "{feedback_text}"

Respond in this exact format:
Sentiment: [positive/negative/neutral/mixed]
Confidence: [0.0 to 1.0]
Reasoning: [brief explanation]"""

    try:
        # Call ChatGPT API
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a sentiment analysis expert. Analyze customer feedback accurately and concisely."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,  # Lower temperature = more consistent results
            max_tokens=150
        )

        # Extract the response text
        result_text = response.choices[0].message.content.strip()

        # Parse the response (simple parsing - extract sentiment, confidence, reasoning)
        sentiment = "neutral"
        confidence = 0.5
        reasoning = "Unable to parse response"

        # Parse line by line
        for line in result_text.split('\n'):
            if line.startswith('Sentiment:'):
                sentiment = line.split(':', 1)[1].strip().lower()
            elif line.startswith('Confidence:'):
                try:
                    confidence = float(line.split(':', 1)[1].strip())
                except ValueError:
                    confidence = 0.5
            elif line.startswith('Reasoning:'):
                reasoning = line.split(':', 1)[1].strip()

        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "reasoning": reasoning
        }

    except Exception as e:
        # If something goes wrong, return a default response
        print(f"Error in sentiment analysis: {str(e)}")
        return {
            "sentiment": "neutral",
            "confidence": 0.0,
            "reasoning": f"Error: {str(e)}"
        }