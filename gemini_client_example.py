"""
Example client script for testing Gemini API Proxy.

This script demonstrates how to use the proxy server to access Google Generative AI
from a client machine without direct internet access.

Requirements:
    pip install langchain-google-genai

Usage:
    python gemini_client_example.py
"""

from langchain_google_genai import ChatGoogleGenerativeAI

# Configuration
PROXY_HOST = "192.168.1.100"  # Change to your proxy server IP
PROXY_PORT = 80               # Proxy server port

print("=" * 60)
print("Gemini API Proxy - Example Client")
print("=" * 60)
print(f"Connecting to proxy server: {PROXY_HOST}:{PROXY_PORT}")
print()

# Initialize LLM with proxy configuration
llm = ChatGoogleGenerativeAI(
    model="dummy",  # Any model name works - server will replace it
    temperature=0,
    api_key="dummy",  # Dummy API key - server has the real one
    client_options={"api_endpoint": f"http://{PROXY_HOST}:{PROXY_PORT}"}
)

# Example 1: Simple question
print("Example 1: Simple Question")
print("-" * 60)
try:
    response = llm.invoke("Xin chào! Bạn là ai?")
    print(f"Response: {response.content}")
    print()
except Exception as e:
    print(f"Error: {e}")
    print()

# Example 2: Code explanation
print("Example 2: Code Explanation")
print("-" * 60)
try:
    response = llm.invoke("Giải thích code này: def factorial(n): return 1 if n <= 1 else n * factorial(n-1)")
    print(f"Response: {response.content}")
    print()
except Exception as e:
    print(f"Error: {e}")
    print()

# Example 3: Streaming response
print("Example 3: Streaming Response")
print("-" * 60)
print("Streaming: ", end="", flush=True)
try:
    for chunk in llm.stream("Kể một câu chuyện ngắn về Python"):
        print(chunk.content, end="", flush=True)
    print("\n")
except Exception as e:
    print(f"\nError: {e}\n")

# Example 4: Translation
print("Example 4: Translation")
print("-" * 60)
try:
    response = llm.invoke("Translate to English: Tôi yêu lập trình Python")
    print(f"Response: {response.content}")
    print()
except Exception as e:
    print(f"Error: {e}")
    print()

print("=" * 60)
print("All examples completed!")
print("=" * 60)
