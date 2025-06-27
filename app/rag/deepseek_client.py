import os
import httpx
import asyncio
from typing import Dict, Any, Optional
import json


BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "deepseek/deepseek-chat"


def get_headers() -> Dict[str, str]:
    """Get headers for OpenRouter API requests"""
    api_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY or DEEPSEEK_API_KEY environment variable is not set")
    
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://questionpapergenerator.ai",  # Optional for rankings
        "X-Title": "Question Paper Generator"  # Optional for rankings
    }


async def chat_async(
    prompt: str, 
    model: str = DEFAULT_MODEL,
    max_tokens: int = 4000,
    temperature: float = 0.7,
    timeout: int = 120
) -> str:
    """
    Send a chat completion request to DeepSeek API
    
    Args:
        prompt: The prompt to send to the model
        model: Model name to use
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        timeout: Request timeout in seconds
    
    Returns:
        Generated text response
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                BASE_URL,
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": False
                },
                headers=get_headers()
            )
            
            response.raise_for_status()
            data = response.json()
            
            if "choices" not in data or not data["choices"]:
                raise ValueError("No choices in response")
                
            return data["choices"][0]["message"]["content"]
            
    except httpx.TimeoutException:
        raise TimeoutError(f"Request timed out after {timeout} seconds")
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"HTTP error {e.response.status_code}: {e.response.text}")
    except Exception as e:
        raise RuntimeError(f"Error calling DeepSeek API: {str(e)}")


def chat_sync(
    prompt: str, 
    model: str = DEFAULT_MODEL,
    max_tokens: int = 4000,
    temperature: float = 0.7,
    timeout: int = 120
) -> str:
    """
    Synchronous wrapper for chat_async using thread-based approach
    """
    import threading
    import queue
    
    result_queue = queue.Queue()
    
    def run_async():
        try:
            # Create new event loop in this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    chat_async(prompt, model, max_tokens, temperature, timeout)
                )
                result_queue.put(('success', result))
            except Exception as e:
                result_queue.put(('error', e))
            finally:
                loop.close()
                
        except Exception as e:
            result_queue.put(('error', e))
    
    # Run in separate thread
    thread = threading.Thread(target=run_async)
    thread.start()
    thread.join(timeout=timeout + 10)  # Give some extra time
    
    if thread.is_alive():
        raise TimeoutError(f"Request timed out after {timeout} seconds")
    
    try:
        result_type, result_value = result_queue.get_nowait()
        if result_type == 'error':
            raise result_value
        return result_value
    except queue.Empty:
        raise RuntimeError("No result received from async function")


async def streaming_chat_async(
    prompt: str, 
    model: str = DEFAULT_MODEL,
    max_tokens: int = 4000,
    temperature: float = 0.7,
    timeout: int = 120
):
    """
    Streaming chat completion (generator)
    
    Args:
        prompt: The prompt to send
        model: Model name
        max_tokens: Maximum tokens
        temperature: Sampling temperature
        timeout: Request timeout
        
    Yields:
        str: Incremental response chunks
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                'POST',
                BASE_URL,
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": True
                },
                headers=get_headers()
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        if data_str.strip() == "[DONE]":
                            break
                            
                        try:
                            data = json.loads(data_str)
                            if "choices" in data and data["choices"]:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
                            
    except Exception as e:
        raise RuntimeError(f"Error in streaming chat: {str(e)}")


def test_connection() -> bool:
    """Test if OpenRouter API is accessible"""
    try:
        response = chat_sync("Hello, this is a test.", max_tokens=10, timeout=30)
        return bool(response.strip())
    except Exception as e:
        print(f"OpenRouter API test failed: {e}")
        return False


def estimate_tokens(text: str) -> int:
    """Rough estimation of token count"""
    # Simple heuristic: ~4 characters per token
    return len(text) // 4


def validate_prompt_length(prompt: str, max_tokens: int = 4000) -> bool:
    """Check if prompt is within reasonable length limits"""
    estimated_tokens = estimate_tokens(prompt)
    # Leave room for response
    return estimated_tokens < (max_tokens * 0.7)


def generate_response(prompt: str, **kwargs) -> str:
    """
    Generate response function used by the worker
    
    Args:
        prompt: The prompt for question paper generation
        **kwargs: Additional parameters (temperature, max_tokens, etc.)
    
    Returns:
        Generated question paper text
    """
    # Extract parameters
    temperature = kwargs.get('temperature', 0.3)  # Lower temperature for more consistent formatting
    max_tokens = kwargs.get('max_tokens', 4000)
    timeout = kwargs.get('timeout', 180)  # Longer timeout for complex generation
    
    # Validate prompt length
    if not validate_prompt_length(prompt, max_tokens):
        raise ValueError("Prompt too long - please reduce textbook content or sample paper length")
    
    try:
        print(f"🤖 Generating question paper with DeepSeek API...")
        response = chat_sync(
            prompt=prompt,
            model=DEFAULT_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout
        )
        
        print(f"✅ Question paper generated successfully! Length: {len(response)} characters")
        return response
        
    except Exception as e:
        print(f"❌ Error generating question paper: {e}")
        print(f"🔄 Using fallback mock response for testing...")
        
        # Fallback mock response for testing when API is not available
        mock_response = """
SAMPLE UNIVERSITY
DEPARTMENT OF COMPUTER SCIENCE
Bachelor of Science - Computer Science
Semester V Examination - June 2024
Subject: Data Structures and Algorithms
Time: 3 Hours                                                                Max. Marks: 100

INSTRUCTIONS:
1. Answer ALL questions from Section A and any FOUR from Section B.
2. Each question in Section A carries 5 marks.
3. Each question in Section B carries 15 marks.
4. Use of calculators is permitted.

SECTION A (Answer ALL questions)                                           [5 × 8 = 40 marks]

1. Define Big O notation and explain its significance in algorithm analysis.                [5 marks]

2. Write an algorithm to find the maximum element in an array.                             [5 marks]

3. Explain the difference between stack and queue data structures.                         [5 marks]

4. What is a binary search tree? State its properties.                                     [5 marks]

5. Define recursion and write a recursive function to calculate factorial.                 [5 marks]

6. Explain the concept of hashing and collision resolution techniques.                     [5 marks]

7. What is dynamic programming? Give one example.                                          [5 marks]

8. Describe the breadth-first search algorithm for graph traversal.                       [5 marks]

SECTION B (Answer any FOUR questions)                                      [4 × 15 = 60 marks]

9. a) Implement bubble sort algorithm and analyze its time complexity.                     [8 marks]
   b) Compare bubble sort with quick sort in terms of performance.                        [7 marks]

10. a) Explain linked list implementation with insertion and deletion operations.          [10 marks]
    b) Write a program to reverse a linked list.                                          [5 marks]

11. a) Describe various tree traversal methods with examples.                              [8 marks]
    b) Implement binary search tree insertion and search operations.                      [7 marks]

12. a) Explain Dijkstra's shortest path algorithm with an example.                         [10 marks]
    b) What are the limitations of Dijkstra's algorithm?                                  [5 marks]

13. a) Describe merge sort algorithm and analyze its time complexity.                      [8 marks]
    b) Implement heap sort and compare it with merge sort.                                [7 marks]

14. a) Explain graph representation using adjacency matrix and adjacency list.            [8 marks]
    b) Write an algorithm for depth-first search traversal of a graph.                    [7 marks]

END OF PAPER
"""
        return mock_response.strip() 