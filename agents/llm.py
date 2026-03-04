import os
import json
from litellm import completion
from pydantic import BaseModel
from typing import Type, TypeVar, Any

T = TypeVar('T', bound=BaseModel)

def get_llm_response(prompt: str, system_prompt: str = "You are a helpful AI assistant.", model: str = "gpt-4o", response_format: Type[T] = None) -> Any:
    """
    Calls the LLM using litellm.
    If response_format is provided (a Pydantic BaseModel), it enforces structured JSON output.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    kwargs = {
        "model": model,
        "messages": messages,
    }

    if response_format:
        kwargs["response_format"] = response_format
        
    try:
        response = completion(**kwargs)
        content = response.choices[0].message.content
        
        if response_format:
            # LiteLLM structured outputs return a JSON string matching the schema
            return response_format.model_validate_json(content)
        return content
    except Exception as e:
        print(f"[LLM] Error calling LiteLLM: {e}")
        raise
