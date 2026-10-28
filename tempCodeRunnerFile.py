import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types

# Load the API key from the .env file in this project folder
load_dotenv(Path(__file__).resolve().parent / ".env")

app = FastAPI(
    title="Construction Intelligence Platform",
    description="Backend API for construction intelligence features",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Development only; restrict for production
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


@app.get("/")
def home():
    return {"message": "Construction Intelligence Platform API is running!"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/analyze-safety")
async def analyze_safety(image: UploadFile = File(...)):
    if client is None:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY is missing. Check your .env file.",
        )

    if image.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a JPG, PNG, or WebP image.",
        )

    image_bytes = await image.read()

    if not image_bytes:
        raise HTTPException(status_code=400, detail="The uploaded image is empty.")

    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Image must be smaller than 10 MB.",
        )

    prompt = """
    Analyze this construction-site image for visible occupational safety concerns.

    Return a clear report with:
    1. Visible hazards, if any.
    2. Possible risks to workers or visitors.
    3. Practical safety improvements.
    4. Items that cannot be confirmed from the image.

    Do not claim that protective equipment is missing unless it is clearly visible
    that the relevant equipment is absent. Do not assume the image shows the
    entire site. State that this is a preliminary visual assessment, not a
    substitute for an on-site inspection by a qualified safety professional.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=image.content_type,
                ),
                prompt,
            ],
        )

        report = response.text
        if not report:
            raise HTTPException(
                status_code=502,
                detail="The AI returned an empty report. Please try again.",
            )

        return {
            "feature": "Site Safety Monitoring",
            "report": report,
            "notice": (
                "Preliminary visual assessment only; "
                "confirm findings with a qualified safety professional."
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        print("AI ERROR:", repr(e))
        raise HTTPException(
            status_code=502,
            detail="AI analysis failed. Check the VS Code terminal for details.",
        )
    