from openai import OpenAI

from core.settings import settings

client = OpenAI(api_key=settings.openai_api_key)

response = client.responses.create(
    model="gpt-4o-mini",
    input="Write a one-sentence bedtime story about a unicorn.",
)

print(response.output_text)
