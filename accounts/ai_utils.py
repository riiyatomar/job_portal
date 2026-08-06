import os
import json
import logging
from google import genai
import PyPDF2

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path):
    text = ""
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def analyze_resume(file_path, job_description=None):
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is not set.")
    
    model_name = os.environ.get('GEMINI_MODEL', 'gemini-1.5-pro')
    client = genai.Client(api_key=api_key)

    if file_path.lower().endswith('.pdf'):
        resume_text = extract_text_from_pdf(file_path)
    else:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                resume_text = f.read()
        except Exception:
            resume_text = ""

    if not resume_text.strip():
        raise ValueError("Could not extract text from the resume. Please ensure it is a valid PDF containing text.")

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
    
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        
        # Clean response in case there are markdown blocks
        cleaned_text = response.text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        if cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
            
        result = json.loads(cleaned_text.strip())
        return result
    except json.JSONDecodeError as e:
        logger.error(f"AI JSON Decode Error: {e}", exc_info=True)
        raise ValueError("AI returned malformed data. Please try again.")
    except Exception as e:
        logger.error(f"AI Analysis Exception: {e}", exc_info=True)
        raise Exception(f"AI Analysis failed: {str(e)}")
