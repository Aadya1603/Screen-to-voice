import os
import time
import requests
import base64
from PIL import ImageGrab, Image
from dotenv import load_dotenv
import openai
import keyboard
import pygame

# Load environment variables from .env file
load_dotenv()
api_key = os.getenv('openai_apikey')

# Debugging: Print the api_key to verify it is being loaded
print(f"API Key: {api_key}")

if not api_key:
    raise ValueError("API key not found. Please set the 'openai_apikey' in the .env file.")

# Initialize Pygame mixer
pygame.mixer.init()

# Ensure the "images" and "audio" folders exist
if not os.path.exists('images'):
    os.makedirs('images')

if not os.path.exists('audio'):
    os.makedirs('audio')

temp_image_path = 'images/temp_img.jpg'
temp_audio_path = 'audio/temp_audio.wav'

def take_screenshot():
    screenshot = ImageGrab.grab()
    screenshot = screenshot.resize((512, 512))
    screenshot.save(temp_image_path, 'JPEG')
    return temp_image_path

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_image(image_path):
    encoded_image = encode_image(image_path)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    message = {
        "role": "user",
        "content": f"IF YOU SEE A QUESTION ON THE SCREEN, ANSWER IT - Keep it SHORT and conversational. [image: {encoded_image}]"
    }

    payload = {
        "model": "gpt-4o",
        "temperature": 0.5,
        "messages": [message],
        "max_tokens": 1000
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to analyze image: {response.status_code} - {response.text}")
        return None

def generate_speech(text):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "input": text,
        "voice": "alloy",
        "output_format": "wav"
    }

    response = requests.post("https://api.openai.com/v1/audio/speech", headers=headers, json=payload)
    if response.status_code == 200:
        with open(temp_audio_path, "wb") as audio_file:
            audio_file.write(response.content)
    else:
        print(f"Failed to generate speech: {response.status_code} - {response.text}")

def play_audio(file_path):
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)

def execute_once():
    image_path = take_screenshot()
    response = analyze_image(image_path)
    if response:
        text_response = response['choices'][0]['message']['content']
        print(text_response)

        generate_speech(text_response)
        play_audio(temp_audio_path)

        os.remove(image_path)

#capture screen 
print("Press 'Ctrl+Spacebar' to capture and analyze the screen.")
while True:
    if keyboard.is_pressed('ctrl+space'):
        execute_once()
        while keyboard.is_pressed('ctrl+space'):
            time.sleep(0.1)
    time.sleep(0.1)
