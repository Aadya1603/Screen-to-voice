import os
import time
import requests
import base64
from PIL import ImageGrab
from dotenv import load_dotenv
import openai
import pygame
import keyboard
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Load environment variables from .env file
load_dotenv()

# Fetch the OpenAI API key from the .env file
api_key = os.getenv('openai_apikey')

# Ensure the "images" and "audio" folders exist
if not os.path.exists('images'):
    os.makedirs('images')

if not os.path.exists('audio'):
    os.makedirs('audio')

temp_image_path = 'images/temp_img.jpg'
temp_audio_path = 'audio/temp_audio.wav'

# Function to take a screenshot, resize it, and save it
def take_screenshot():
    screenshot = ImageGrab.grab()
    screenshot = screenshot.resize((512, 512))
    screenshot.save(temp_image_path, 'JPEG')
    return temp_image_path

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Function to create a requests session with retry logic
def create_session():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

# Function to analyze the image using GPT-4o
def analyze_image(image_path):
    encoded_image = encode_image(image_path)
    session = create_session()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    message = {
        "role": "user",
        "content": [
            {"type": "text", "text": '''System Prompt: You are a screen assistant. Your task is to read and interpret questions or prompts visible on the screen, providing short and conversational answers.
             You are a screen assistant. Your primary role is to assist the user by answering any questions or prompts that appear on their computer screen. Here’s how you should perform your task:

            Answer Prompt: If you see a question on the screen, answer it concisely and conversationally.
           
            Stay Informative: Provide accurate and useful information. If you don’t know the answer, it’s better to admit it rather than providing a wrong or nonsensical response.
           
            Versatile Expertise: You can assist with various domains and topics, acting as an expert in everything displayed on the computer screen environment.
            
            '''},
            {"type": "image_url", "image_url": {"url": f"data:image/jpg;base64,{encoded_image}", "detail": "low"}}
        ]
    }

    payload = {
        "model": "gpt-4o",
        "temperature": 0.5,
        "messages": [message],
        "max_tokens": 1000
    }

    response = session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
    return response.json()

# Function to generate speech from text using TTS API
def generate_speech(text):
    session = create_session()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "tts-1",
        "voice": "alloy",
        "input": text,
        "response_format": "wav"
    }

    response = session.post("https://api.openai.com/v1/audio/speech", headers=headers, json=payload, timeout=30)
    if response.status_code == 200:
        with open(temp_audio_path, "wb") as audio_file:
            audio_file.write(response.content)
    else:
        print(f"Failed to generate speech: {response.status_code} - {response.text}")

# Function to play audio file using pygame
def play_audio(file_path):
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)

# Function to execute the main logic once
def execute_once():
    image_path = take_screenshot()
    response = analyze_image(image_path)
    text_response = response['choices'][0]['message']['content']
    print(text_response)

    generate_speech(text_response)
    play_audio(temp_audio_path)

    os.remove(image_path)

# Main loop to wait for the trigger key combination
print("Press 'Ctrl+Spacebar' to capture and analyze the screen.")
while True:
    if keyboard.is_pressed('ctrl+space'):
        execute_once()
        while keyboard.is_pressed('ctrl+space'):
            time.sleep(0.1)  # Wait until the key is released to avoid multiple triggers
    time.sleep(0.1)  # Slight delay to prevent high CPU usage
