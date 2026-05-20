import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def categorize_feedback(feedback_text: str) -> dict:
    """
    Categorize customer feedback using ChatGPT.

    This function analyzes feedback and determines which category it belongs to:
    - product: Issues with the product itself (quality, features, functionality)
    - service: Customer service related (support, help, communication)
    - delivery: Shipping and delivery issues (speed, packaging, tracking)
    - pricing: Price-related feedback (cost, value, billing)
    
    It also determines the urgency of the feedback:
    - critical: Immediate attention required (safety issues, legal threats, public relations disaster)
    - high: Time-sensitive issues affecting use (broken functionality, missing parts, severe delay)
    - medium: Important but not blocking (general complaints, feature requests, minor delays)
    - low: No immediate action needed (praise, minor suggestions, general comments)
    """

    # Create a clear prompt for ChatGPT
    prompt = f"""Categorize this customer feedback into ONE of the categories and determine its urgency.

Categories:
- product: Issues about the product itself (quality, features, defects, functionality)
- service: Customer service issues (support staff, help, responsiveness)
- delivery: Shipping and delivery problems (speed, packaging, tracking, arrival)
- pricing: Price-related feedback (cost, value for money, billing issues)

Urgency Levels:
- critical: Immediate attention required (e.g., severe safety issues, threatening legal action)
- high: Time-sensitive issues affecting use (e.g., broken product, missing items, extreme delays)
- medium: Important but not blocking (e.g., minor complaints, feature requests, standard delays)
- low: No immediate action needed (e.g., praise, minor suggestions, general comments)

Customer Feedback: "{feedback_text}"

Respond in this exact format:
Category: [product/service/delivery/pricing]
Urgency: [critical/high/medium/low]
Confidence: [0.0 to 1.0]
Reasoning: [brief explanation]"""

    try:
        # Call ChatGPT API
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a customer feedback categorization expert. Determine category and urgency accurately."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=200
        )

        # Extract the response text
        result_text = response.choices[0].message.content.strip()

        # Parse the response
        category = "product"  # default
        urgency = "low"  # default
        confidence = 0.5  # default
        reasoning = "Unable to parse response"

        # Parse line by line
        for line in result_text.split('\n'):
            line = line.strip()
            if line.startswith('Category:'):
                category = line.split(':', 1)[1].strip().lower()
            elif line.startswith('Urgency:'):
                urgency = line.split(':', 1)[1].strip().lower()
            elif line.startswith('Confidence:'):
                try:
                    confidence = float(line.split(':', 1)[1].strip())
                except ValueError:
                    confidence = 0.5
            elif line.startswith('Reasoning:'):
                reasoning = line.split(':', 1)[1].strip()

        return {
            "category": category,
            "urgency": urgency,
            "confidence": confidence,
            "reasoning": reasoning
        }

    except Exception as e:
        # If something goes wrong, return default
        print(f"Error in categorization: {str(e)}")
        return {
            "category": "product",
            "urgency": "low",
            "confidence": 0.0,
            "reasoning": f"Error: {str(e)}"
        }