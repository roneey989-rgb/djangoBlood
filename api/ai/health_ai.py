from openai import OpenAI

# Create client (no settings.py needed if you put key here)
client = OpenAI(
    api_key="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",
    base_url="https://openrouter.ai/api/v1"
)

def get_health_ai_response(user_message):
    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat",  # free model
            messages=[
                {
                    "role": "system",
                    "content": "You are a health assistant. Give very short health tips (1-2 lines only). No explanation."
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            max_tokens=50  
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"ERROR: {str(e)}"
    