import os
import json
import time
from app.utils.logger import setup_logger
from app.utils.config import load_config

logger = setup_logger()
config = load_config()

# Import OpenAI
try:
    from openai import OpenAI
    openai_available = True
except ImportError:
    logger.warning("OpenAI package not available. Text generation will be limited.")
    openai_available = False

def generate_text(prompt, model="gpt-4o", max_tokens=1500, return_json=False, max_retries=3):
    """
    Generate text using AI model
    
    Args:
        prompt (str): Text prompt for generation
        model (str): AI model to use
        max_tokens (int): Maximum tokens to generate
        return_json (bool): If True, parse response as JSON
        max_retries (int): Maximum number of retries on failure
        
    Returns:
        str or dict: Generated text or parsed JSON
    """
    # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
    # do not change this unless explicitly requested by the user
    
    api_key = config.get('OPENAI_API_KEY') or config.get('AI_TEXT_GENERATION_API_KEY')
    
    if not api_key:
        logger.warning("No AI API key found. Cannot generate text.")
        return None
    
    if not openai_available:
        logger.warning("OpenAI package not available. Cannot generate text.")
        return None
    
    logger.info(f"Generating text with {model} (return_json={return_json})")
    
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Generation attempt {attempt + 1}/{max_retries}")
                
                # Create messages for the API call
                messages = [{"role": "user", "content": prompt}]
                
                # Add system message for JSON responses if needed
                if return_json:
                    messages.insert(0, {
                        "role": "system",
                        "content": "You are a helpful assistant that responds in valid JSON format. Your response should be properly formatted JSON that can be parsed."
                    })
                
                # Set up the API call arguments
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                }
                
                # Add response format for JSON if needed
                if return_json:
                    kwargs["response_format"] = {"type": "json_object"}
                
                # Make the API call
                response = client.chat.completions.create(**kwargs)
                
                # Extract the generated text
                generated_text = response.choices[0].message.content
                
                # Parse JSON if requested
                if return_json:
                    try:
                        return json.loads(generated_text)
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
        logger.error(f"Error initializing AI text generation: {str(e)}", exc_info=True)
        return None
