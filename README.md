# CustomerLens

**AI-Powered Customer Feedback Intelligence Platform**

## 🎯 Overview

CustomerLens analyzes customer feedback using AI to provide sentiment analysis, categorization, and intelligent response generation.

## 🚀 Features

- **Sentiment Analysis** using ChatGPT (positive/negative/neutral/mixed)
- **Smart Categorization** using Gemini (product/service/delivery/pricing)
- **RAG-based Response Generation** with company guidelines
- **Automated Workflows** via n8n integration
- **RESTful API** with FastAPI

## 🛠️ Tech Stack

- Python 3.12
- FastAPI
- SQLite
- ChatGPT API (OpenAI)
- Gemini API (Google)
- LangChain + ChromaDB
- n8n

## 📦 Installation
```bash
# Clone repository
git clone https://github.com/yourusername/customer-lens.git
cd customer-lens

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

## 🚀 Running the Application
```bash
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for API documentation.

## 📝 API Endpoints

- `POST /feedback` - Submit feedback
- `GET /feedback/{id}` - Get feedback
- `GET /feedback` - List all feedback
- `PUT /feedback/{id}` - Update feedback
- `DELETE /feedback/{id}` - Delete feedback
- `POST /feedback/{id}/analyze` - Analyze feedback

## 👨‍💻 Author

Victor von Reiche - AI Engineering Student at Masterschool

## 📄 License

MIT License