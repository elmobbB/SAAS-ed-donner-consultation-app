from fastapi import FastAPI  
from fastapi.responses import PlainTextResponse  
from openai import OpenAI  
import os

app = FastAPI()

@app.get("/api", response_class=PlainTextResponse)
def idea():
    client = OpenAI(
        base_url=os.getenv("AI_FOUNDRY_ENDPOINT"),
        api_key=os.getenv("AI_FOUNDRY_KEY")
    )
    prompt = [{"role": "user", "content": "Come up with a new business idea for AI Agents"}]
    response = client.chat.completions.create(model="DeepSeek-R1", messages=prompt)
    return response.choices[0].message.content