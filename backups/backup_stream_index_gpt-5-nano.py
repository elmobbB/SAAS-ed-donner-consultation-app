from fastapi import FastAPI  # type: ignore
from fastapi.responses import StreamingResponse  # type: ignore
from openai import AzureOpenAI  # type: ignore
import os
import traceback

app = FastAPI()

@app.get("/api")
def idea():
    try:
        # Get environment variables
        api_key = os.getenv("AZURE_OPENAI_KEY_GPT_5_NANO")
        endpoint = os.getenv("AI_FOUNDRY_ENDPOINT_GPT_5_NANO")
        
        print(f"API Key present: {bool(api_key)}")
        print(f"Endpoint: {endpoint}")
        
        if not api_key or not endpoint:
            error_msg = "Missing environment variables"
            print(error_msg)
            def error_stream():
                yield f"data: {error_msg}\n\n"
            return StreamingResponse(error_stream(), media_type="text/event-stream")
        
        client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version="2025-01-01-preview",
        )
        
        prompt = [{"role": "user", "content": "What is the capital of France?"}]
        print("Creating completion stream...")
        
        stream = client.chat.completions.create(
            model="gpt-5-nano", 
            messages=prompt, 
            stream=True
        )

        def event_stream():
            try:
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content is not None:
                        text = chunk.choices[0].delta.content
                        print(f"Sending: {text}")
                        yield f"data: {text}\n\n"
            except Exception as e:
                error_msg = f"Stream error: {str(e)}"
                print(error_msg)
                yield f"data: {error_msg}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")
    
    except Exception as e:
        error_msg = f"API setup error: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        def error_stream():
            yield f"data: {error_msg}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")c