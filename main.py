
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types

# Load the API key from the .env file beside main.py
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini
client = genai.Client(api_key=API_KEY) if API_KEY else None

MODEL_NAME = "gemini-3.8-flash"
MAX_IMAGE_SIZE = 10 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}

app = FastAPI(
    title="AI-Powered Construction Intelligence Platform",
    description="AI-assisted construction safety and crack analysis",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Construction Intelligence Platform API is running!"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "gemini_configured": client is not None,
    }


async def read_image(image: UploadFile):
    """Validate and read an uploaded construction image."""

    if client is None:
        raise HTTPException(
            status_code=500,
            detail="Gemini API key is missing. Check GEMINI_API_KEY in .env.",
        )

    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Upload a JPG, PNG, or WebP image.",
        )

    image_bytes = await image.read()

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded image is empty.",
        )

    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Image must be 10 MB or smaller.",
        )

    return image_bytes


async def analyze_image(image: UploadFile, prompt: str):
    """Send an image and prompt to Gemini and return its report."""

    image_bytes = await read_image(image)

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=image.content_type,
                ),
                prompt,
            ],
        )

        report = response.text

        if not report or not report.strip():
            raise HTTPException(
                status_code=502,
                detail="Gemini returned an empty report. Try another image.",
            )

        return report

    except HTTPException:
        raise

    except Exception as error:
        # Detailed information appears in the VS Code terminal.
        print(
            f"Gemini analysis error ({image.filename}): "
            f"{type(error).__name__}: {error}"
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "Gemini image analysis failed. Check the backend terminal "
                "for the detailed error. Verify model access, API quota, "
                "network connection, and API key configuration."
            ),
        )


@app.post("/analyze-safety")
async def analyze_safety(image: UploadFile = File(...)):
    prompt = """
You are assisting with preliminary construction-site safety monitoring.

Analyze the provided image and organize your report under these headings:

1. Visible observations
2. Potential safety hazards
3. Possible risks to workers or visitors
4. Recommended safety improvements
5. Items that cannot be confirmed from the image

Describe only what is visibly supported by the image. Do not claim that
protective equipment is missing unless the image clearly supports that
observation. Do not assume the image shows the entire site.

This is a preliminary visual assessment, not a substitute for an on-site
inspection by a qualified safety professional.
"""

    report = await analyze_image(image, prompt)

    return {
        "feature": "Site Safety Monitoring",
        "report": report,
        "notice": (
            "Preliminary visual assessment only. Confirm findings with "
            "a qualified safety professional."
        ),
    }


@app.post("/analyze-cracks")
async def analyze_cracks(image: UploadFile = File(...)):
    prompt = """
You are assisting with preliminary visual inspection of construction
materials. Examine the uploaded image for visible cracks or surface defects
in walls, concrete, columns, beams, floors, or other construction elements.

Organize your report under these headings:

1. Visible observations
   Describe only features actually visible in the photograph.

2. Crack characteristics
   If a crack is visible, describe its apparent location, direction,
   pattern, and visible extent. Do not invent measurements.

3. Possible explanations
   Give cautious possibilities. Do not state an unconfirmed cause as fact.

4. Preliminary concern level
   Use low, moderate, or high concern only when supported by visible
   evidence. Explain the uncertainty. This is not a structural safety rating.

5. Recommended next steps
   Suggest practical steps such as taking a clearer close-up photograph,
   documenting changes, and arranging an appropriate professional inspection.

6. Image limitations
   Explain what cannot be determined from this photograph.

If no crack is clearly visible, explicitly say so. Never invent cracks,
measurements, crack depth, structural integrity, load capacity, or a
building's safety status from an image alone.

This AI-assisted visual review is not a structural engineering assessment.
Suspected significant or growing cracks, displacement, falling material,
or other signs of possible structural distress should be assessed promptly
by a qualified structural engineer. If immediate danger is suspected,
keep people away from the affected area and contact site safety personnel.
"""

    report = await analyze_image(image, prompt)

    return {
        "feature": "Crack Detection and Analysis",
        "report": report,
        "notice": (
            "Preliminary visual review only. A qualified structural "
            "engineer must assess structural concerns."
        ),
    }
