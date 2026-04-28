from openai import OpenAI
from django.conf import settings

client = OpenAI(
    api_key=settings.API_KEY,   #  from environment
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "https://djangoblood.onrender.com",  # your live URL
        "X-Title": "Health App"
    }
)

def get_health_ai_response(user_message):
    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[
                {"role": "system", "content": "Give very short health tips (1 line only)."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=50
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print("AI ERROR:", str(e))
        return "Server busy. Try again."