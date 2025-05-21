import os
import json
import time
import google.generativeai as genai
from app.utils.logger import setup_logger
from app.utils.config import load_config

logger = setup_logger()
config = load_config()

def generate_text(prompt, max_tokens=1500, return_json=False, max_retries=3):
    """
    Generate text using Google Gemini model
    
    Args:
        prompt (str): Text prompt for generation
        max_tokens (int): Maximum tokens to generate
        return_json (bool): If True, parse response as JSON
        max_retries (int): Maximum number of retries on failure
        
    Returns:
        str or dict: Generated text or parsed JSON
    """
    api_key = os.environ.get('GOOGLE_GEMINI_API_KEY') or config.get('GOOGLE_GEMINI_API_KEY')
    
    if not api_key:
        logger.warning("No Google Gemini API key found. Cannot generate text.")
        return None
    
    logger.info(f"Generating text with Gemini (return_json={return_json})")
    
    # Configure the API key
    genai.configure(api_key=api_key)
    
    try:
        # Create the generation config (using the appropriate method based on your version)
        generation_config = {
            "max_output_tokens": max_tokens,
            "temperature": 0.7
        }
        
        # Create the model
        model = genai.GenerativeModel(model_name='gemini-pro')
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Generation attempt {attempt + 1}/{max_retries}")
                
                # Modify prompt for JSON if needed
                effective_prompt = prompt
                if return_json:
                    effective_prompt = f"""
                    {prompt}
                    
                    Important: Your response must be a properly formatted JSON object with no additional text, 
                    explanations, or markdown formatting before or after the JSON. 
                    The response should be able to be parsed directly by json.loads().
                    """
                
                # Generate content
                response = model.generate_content(
                    contents=effective_prompt
                )
                
                # Extract the generated text
                generated_text = response.text
                
                # Parse JSON if requested
                if return_json:
                    try:
                        # Clean the response - sometimes there are markdown code blocks
                        if "```json" in generated_text:
                            json_text = generated_text.split("```json")[1].split("```")[0].strip()
                        elif "```" in generated_text:
                            json_text = generated_text.split("```")[1].strip()
                        else:
                            json_text = generated_text
                            
                        return json.loads(json_text)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON response: {str(e)}")
                        logger.debug(f"Raw response: {generated_text}")
                        if attempt < max_retries - 1:
                            logger.info(f"Retrying JSON generation (attempt {attempt + 2}/{max_retries})")
                            time.sleep(1)  # Brief pause before retry
                            continue
                        return None
                
                return generated_text
                
            except Exception as e:
                logger.error(f"Error generating text (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed after {max_retries} attempts")
                    return None
    
    except Exception as e:
        logger.error(f"Error initializing Gemini text generation: {str(e)}", exc_info=True)
        return None