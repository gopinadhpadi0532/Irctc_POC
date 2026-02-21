from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import GOOGLE_API_KEY
from app.config import GROQ_API_KEY


from langchain_groq import ChatGroq


def get_llm():
    # return ChatGoogleGenerativeAI(
    #     model="gemini-2.0-flash",
    #     google_api_key=GOOGLE_API_KEY,
    #     temperature=0.3
    # )
    return ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    groq_api_key=GROQ_API_KEY,
    # Groq is very fast, but we'll keep retries just in case
    max_retries=3, 
)
