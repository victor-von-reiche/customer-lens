import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


async def categorize_feedback(feedback_text: str) -> dict:
    """
    Categorize customer feedback using Gemini.

    This function analyzes feedback and determines which category it belongs to:
    - product: Issues with the product itself (quality, features, functionality)
    - service: Customer service related (support, help, communication)
    - delivery: Shipping and delivery issues (speed, packaging, tracking)
    - pricing: Price-related feedback (cost, value, billing)
    """

    # Create a clear prompt for Gemini
    prompt = f"""Categorize this customer feedback into ONE of these categories:

Categories:
- product: Issues about the product itself (quality, features, defects, functionality)
- service: Customer service issues (support staff, help, responsiveness)
- delivery: Shipping and delivery problems (speed, packaging, tracking, arrival)
- pricing: Price-related feedback (cost, value for money, billing issues)

Customer Feedback: "{feedback_text}"

Respond in this exact format:
Category: [product/service/delivery/pricing]
Confidence: [0.0 to 1.0]
Reasoning: [brief explanation of why this category fits]"""

    try:
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Generate response
        response = model.generate_content(prompt)
        result_text = response.text.strip()

        # Parse the response
        category = "product"  # default
        confidence = 0.5  # default
        reasoning = "Unable to parse response"

        # Parse line by line
        for line in result_text.split('\n'):
            line = line.strip()
            if line.startswith('Category:'):
                category = line.split(':', 1)[1].strip().lower()
            elif line.startswith('Confidence:'):
                try:
                    confidence = float(line.split(':', 1)[1].strip())
                except ValueError:
                    confidence = 0.5
            elif line.startswith('Reasoning:'):
                reasoning = line.split(':', 1)[1].strip()

        return {
            "category": category,
            "confidence": confidence,
            "reasoning": reasoning
        }

    except Exception as e:
        # If something goes wrong, return default
        print(f"Error in categorization: {str(e)}")
        return {
            "category": "product",
            "confidence": 0.0,
            "reasoning": f"Error: {str(e)}"
        }