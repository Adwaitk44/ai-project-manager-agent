from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
model = os.getenv("GROQ_MODEL")

if not api_key:
    raise ValueError("Groq API key not found in .env")

client = Groq(api_key=api_key)

response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "system",
            "content": "You are an AI Project Manager Assistant."
        },
        {
            "role": "user",
            "content": "Explain an AI Project Manager Agent in 3 sentences."
        }
    ],
    temperature=0.2
)

print("\nGroq Response:\n")
print(response.choices[0].message.content)