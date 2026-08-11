import os
import json
import logging
from google import genai
from google.genai import errors as genai_errors
import httpx
import PyPDF2

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path):
    """Extract text from a PDF file using PyPDF2."""
    text = ""
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        logger.error(f"Error reading PDF '{file_path}': {e}", exc_info=True)
    return text


def extract_text_from_docx(file_path):
    """Extract text from a DOCX file by parsing its XML content.
    
    DOCX is a ZIP archive containing XML files. We parse word/document.xml
    to extract paragraph text without requiring python-docx as a dependency.
    """
    import zipfile
    import xml.etree.ElementTree as ET

    text = ""
    try:
        with zipfile.ZipFile(file_path, 'r') as z:
            # The main document content is in word/document.xml
            if 'word/document.xml' not in z.namelist():
                logger.error(f"DOCX file '{file_path}' does not contain word/document.xml")
                return ""
            
            with z.open('word/document.xml') as f:
                tree = ET.parse(f)
                root = tree.getroot()
                
                # Define the Word XML namespace
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                
                # Extract text from all paragraph > run > text elements
                paragraphs = []
                for para in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                    para_text = ""
                    for run in para.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r'):
                        for t in run.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
                            if t.text:
                                para_text += t.text
                    if para_text.strip():
                        paragraphs.append(para_text)
                
                text = "\n".join(paragraphs)
    except zipfile.BadZipFile:
        logger.error(f"File '{file_path}' is not a valid DOCX (bad ZIP archive)")
    except Exception as e:
        logger.error(f"Error reading DOCX '{file_path}': {e}", exc_info=True)
    return text


def analyze_resume(file_path, job_description=None):
    """Analyze a resume using the Google Gemini API.
    
    Supports PDF and DOCX files. Extracts text first, then sends to Gemini
    for analysis. Never sends raw binary data to the API.
    """
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is not set in your environment. Please configure it in the .env file.")

    model_name = os.environ.get('GEMINI_MODEL', 'gemini-3.5-flash')
    
    logger.info(f"Starting resume analysis: file='{os.path.basename(file_path)}', model='{model_name}'")

    client = genai.Client(api_key=api_key)

    # --- Text extraction based on file type ---
    lower_path = file_path.lower()
    if lower_path.endswith('.pdf'):
        resume_text = extract_text_from_pdf(file_path)
    elif lower_path.endswith('.docx'):
        resume_text = extract_text_from_docx(file_path)
    elif lower_path.endswith('.doc'):
        # .doc (legacy binary format) - attempt plain text read as best-effort
        logger.warning(f"Legacy .doc format detected for '{file_path}'. Text extraction may be incomplete.")
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                resume_text = f.read()
        except Exception:
            resume_text = ""
    else:
        # Unknown format - try reading as text
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                resume_text = f.read()
        except Exception:
            resume_text = ""

    if not resume_text.strip():
        raise ValueError(
            "Could not extract text from the resume. "
            "Please ensure your file is a valid PDF or DOCX containing readable text (not a scanned image)."
        )

    logger.info(f"Extracted {len(resume_text)} characters from resume")

    # --- Build the prompt ---
    prompt = f"""
You are an expert ATS (Applicant Tracking System) and Senior Technical Recruiter.
Analyze the following resume text.

Resume Text:
'''
{resume_text}
'''
"""

    if job_description:
        prompt += f"""
Compare the resume against the following job description:
'''
{job_description}
'''
"""

    prompt += """
Provide a detailed analysis in strictly valid JSON format matching the structure below.
Do not use markdown formatting like ```json. Return ONLY raw JSON.

{
    "resume_score": <int 0-100>,
    "ats_score": <int 0-100>,
    "summary_review": "<string>",
    "skills_detected": ["<string>", "<string>"],
    "missing_skills": ["<string>", "<string>"],
    "strengths": ["<string>", "<string>"],
    "weaknesses": ["<string>", "<string>"],
    "grammar_suggestions": ["<string>", "<string>"],
    "formatting_suggestions": ["<string>", "<string>"],
    "actionable_improvements": ["<string>", "<string>"]
"""

    if job_description:
        prompt += """,
    "match_percentage": <int 0-100>,
    "matching_skills": ["<string>", "<string>"],
    "job_missing_skills": ["<string>", "<string>"],
    "job_recommendations": ["<string>", "<string>"]
"""

    prompt += "\n}"

    # --- Call Gemini API ---
    try:
        logger.info(f"Sending request to Gemini model '{model_name}'...")
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )

        # Guard against empty response
        if not response.text:
            logger.error("Gemini API returned an empty response (response.text is None/empty).")
            raise ValueError("AI returned an empty response. Please try again.")

        logger.info(f"Received response from Gemini ({len(response.text)} chars)")

        # Clean response in case Gemini wraps it in markdown code blocks
        cleaned_text = response.text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        if cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]

        result = json.loads(cleaned_text.strip())
        logger.info(f"Successfully parsed AI analysis: resume_score={result.get('resume_score')}, ats_score={result.get('ats_score')}")
        return result

    except json.JSONDecodeError as e:
        raw_preview = response.text[:500] if response and response.text else 'None'
        logger.error(f"AI JSON Decode Error: {e}. Raw text preview: {raw_preview}", exc_info=True)
        raise ValueError("AI returned malformed data. Please try again.")

    except httpx.TimeoutException as e:
        logger.error(f"Gemini API timeout: {e}", exc_info=True)
        raise ValueError("The AI service timed out. Please try again in a moment.")

    except genai_errors.ClientError as e:
        error_msg = str(e)
        logger.error(f"Gemini ClientError: {error_msg}", exc_info=True)
        if 'API_KEY_INVALID' in error_msg or 'API key not valid' in error_msg:
            raise ValueError(
                "The Google API key is invalid. Please generate a new key at "
                "https://aistudio.google.com/apikey and update your .env file."
            )
        elif '429' in error_msg or 'RESOURCE_EXHAUSTED' in error_msg:
            raise ValueError("AI rate limit reached. Please wait a minute and try again.")
        elif '404' in error_msg or 'not found' in error_msg.lower():
            raise ValueError(f"AI model '{model_name}' is not available. Please check GEMINI_MODEL in .env.")
        else:
            raise ValueError(f"AI service error: {error_msg}")

    except genai_errors.ServerError as e:
        logger.error(f"Gemini ServerError: {e}", exc_info=True)
        raise ValueError("The AI service is temporarily unavailable. Please try again later.")

    except Exception as e:
        logger.error(f"Unexpected AI Analysis Exception ({type(e).__name__}): {e}", exc_info=True)
        raise ValueError(f"AI Analysis failed: {str(e)}")
