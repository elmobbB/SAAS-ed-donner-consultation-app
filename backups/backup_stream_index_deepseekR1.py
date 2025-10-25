from fastapi import FastAPI  
from fastapi.responses import StreamingResponse  
from openai import OpenAI  
import os
import json

app = FastAPI()

@app.get("/api")
def idea():
    try:
        # Check if environment variables are set
        ai_endpoint = os.getenv("AI_FOUNDRY_ENDPOINT")
        ai_key = os.getenv("AI_FOUNDRY_KEY")
        
        if not ai_endpoint or not ai_key:
            print("Missing environment variables")
            def error_stream():
                yield "data: " + json.dumps("Error: Missing API configuration") + "\n\n"
            return StreamingResponse(error_stream(), media_type="text/event-stream")
        
        client = OpenAI(
            base_url=ai_endpoint,
            api_key=ai_key
        )
         
        prompt = [{"role": "user", "content": "Reply with a new business idea for AI Agents, formatted with headings, sub-headings and bullet points"}]        
        print("Making API call to DeepSeek...")
        stream = client.chat.completions.create(
            model="DeepSeek-R1", 
            messages=prompt,
            max_tokens=50,      
            temperature=0.7,
            stream=True
        )

        def event_stream():
            try:
                for chunk in stream:
                    if (chunk.choices and 
                        len(chunk.choices) > 0 and 
                        chunk.choices[0].delta and 
                        chunk.choices[0].delta.content is not None):
                        
                        text = chunk.choices[0].delta.content
                        print(f"Sending chunk: {text}")
                        yield f"data: {json.dumps(text)}\n\n"
            except Exception as e:
                print(f"Stream error: {e}")
                yield f"data: {json.dumps(f'Stream error: {str(e)}')}\n\n"
        
        return StreamingResponse(event_stream(), media_type="text/event-stream")
    
    except Exception as e:
        print(f"API error: {e}")
        def error_stream():
            yield f"data: {json.dumps(f'API Error: {str(e)}')}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")