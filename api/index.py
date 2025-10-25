import os
from pathlib import Path
from fastapi import FastAPI, Depends
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi_clerk_auth import ClerkConfig, ClerkHTTPBearer, HTTPAuthorizationCredentials
from openai import AzureOpenAI

app = FastAPI()

# Add CORS middleware (allows frontend to call backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Clerk authentication setup
clerk_config = ClerkConfig(jwks_url=os.getenv("CLERK_JWKS_URL"))
clerk_guard = ClerkHTTPBearer(clerk_config)

class Visit(BaseModel):
    patient_name: str
    date_of_visit: str
    notes: str

system_prompt = """
You are provided with notes written by a doctor from a patient's visit.
Your job is to summarize the visit for the doctor and provide an email.
Reply with exactly three sections with the headings:
### Summary of visit for the doctor's records
### Next steps for the doctor
### Draft of email to patient in patient-friendly language
"""

def user_prompt_for(visit: Visit) -> str:
    return f"""Create the summary, next steps and draft email for:
Patient Name: {visit.patient_name}
Date of Visit: {visit.date_of_visit}
Notes:
{visit.notes}"""

@app.post("/api/consultation")
def consultation_summary(
    visit: Visit,
     creds: HTTPAuthorizationCredentials = Depends(clerk_guard),
):
    try:
        user_id = creds.decoded["sub"]
        
        # Get Azure AI Foundry environment variables
        api_key = os.getenv("AZURE_OPENAI_KEY_GPT_5_NANO")
        endpoint = os.getenv("AI_FOUNDRY_ENDPOINT_GPT_5_NANO")
        
        print(f"API Key present: {bool(api_key)}")
        print(f"Endpoint: {endpoint}")
        
        if not api_key or not endpoint:
            error_msg = "Missing Azure AI Foundry environment variables"
            print(error_msg)
            def error_stream():
                yield f"data: {error_msg}\n\n"
            return StreamingResponse(error_stream(), media_type="text/event-stream")
        
        # Create Azure OpenAI client
        client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version="2025-01-01-preview",
        )
        
        user_prompt = user_prompt_for(visit)
        prompt = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        print("Creating Azure AI Foundry completion stream...")
        
        stream = client.chat.completions.create(
            model="gpt-5-nano",
            messages=prompt,
            stream=True,
        )
        
        def event_stream():
            try:
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content is not None:
                        text = chunk.choices[0].delta.content
                        print(f"Sending: {text}")
                        lines = text.split("\n")
                        for line in lines[:-1]:
                            yield f"data: {line}\n\n"
                            yield "data:  \n"
                        yield f"data: {lines[-1]}\n\n"
            except Exception as e:
                error_msg = f"Stream error: {str(e)}"
                print(error_msg)
                yield f"data: {error_msg}\n\n"
        
        return StreamingResponse(event_stream(), media_type="text/event-stream")
    
    except Exception as e:
        error_msg = f"API setup error: {str(e)}"
        print(error_msg)
        import traceback
        print(traceback.format_exc())
        def error_stream():
            yield f"data: {error_msg}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")

@app.get("/health")
def health_check():
    """Health check endpoint for AWS App Runner"""
    return {"status": "healthy"}

# Serve static files (our Next.js export) - MUST BE LAST!
static_path = Path("static")
if static_path.exists():
    # Serve index.html for the root path
    @app.get("/")
    async def serve_root():
        return FileResponse(static_path / "index.html")
    
    # Mount static files for all other routes
    app.mount("/", StaticFiles(directory="static", html=True), name="static")