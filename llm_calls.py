import os
import google.generativeai as genai
import json
from typing import List, Dict


def call_gemini_flash(llm_input: str, system_prompt: str) -> List[Dict]:
    """
    Calls the Gemini Flash API to generate a response to the given input.

    Args:
        llm_input (str): The input text for the language model.
        system_prompt (str): The system prompt for the language model.

    Returns:
        List[Dict]: The parsed response generated by the language model.
    """

    # Get the API key from the environment variables.
    api_key = os.environ["GEMINI_API_KEY"]

    # Configure the API key for the Gemini Flash API.
    genai.configure(api_key=api_key)

    # Generation configuration for the language model.
    generation_config = {
        "temperature": 0,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "application/json",
    }

    # Initialize the GenerativeModel with the specified model and generation configuration.
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        system_instruction=system_prompt,
    )

    # Start a new chat session and send the input to the language model.
    chat_session = model.start_chat(history=[])

    # Send the input to the language model and receive the response.
    response = chat_session.send_message(llm_input)

    # Convert the response to a JSON object.
    parsed_response = json.loads(response.text)

    # Return the parsed response.
    return parsed_response
