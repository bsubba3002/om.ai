import csv
from flask import Flask, jsonify, render_template, request
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import logging

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Configure Gemini API (Replace with your actual API key)
genai.configure(api_key="AIzaSyCA71A8iPQjhKgyjE60JzKkIB7nHz_sZSo")
model = genai.GenerativeModel("gemini-1.5-flash")

# Read the CSV file for characters and topics
def read_csv():
    characters = []
    topics = []
    try:
        with open('iks_characters_and_topics.csv', mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                characters.append(row['Character'])
                topics.append(row['Topic'])
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
    return characters, topics

# Fetching relevant images using BeautifulSoup (Web Scraping)
def fetch_image_url(topic):
    search_query = topic.replace(" ", "+")
    url = f"https://www.google.com/search?hl=en&tbm=isch&q={search_query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        img_tags = soup.find_all('img')
        if img_tags:
            # Return the URL of the first image found
            return img_tags[1]['src']  # Skipping the first image (which is a Google logo)
        else:
            return None
    except Exception as e:
        logging.error(f"Error fetching image: {e}")
        return None

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/story_generation')
def story_generation():
    characters, topics = read_csv()
    return render_template('story_generation.html', characters=characters, topics=topics)

@app.route('/content_generation')
def content_generation():
    characters, topics = read_csv()
    return render_template('content_generation.html', characters=characters, topics=topics)

@app.route('/characters_and_topics', methods=['GET'])
def characters_and_topics():
    characters, topics = read_csv()
    return jsonify({"characters": characters, "topics": topics})

@app.route('/generate_story', methods=['POST'])
def generate_story():
    data = request.json
    topic = data.get('topic')
    child_name = data.get('child_name')

    # Build prompt for story generation
    prompt = (
        f"Create a fun, colorful, and silly children's story for ages 6 to 10 "
        f"that teaches something about '{topic}' from the Indian Knowledge System. "
        f"The story should feature a curious and hilarious child named '{child_name}' "
        f"who discovers or explores the topic in an adventurous and wacky way. "
        f"Include magical elements, ancient wisdom, and a cute moral at the end. "
        f"Make it joyful, surprising, and full of imagination!"
    )

    try:
        # Call Gemini API to generate the story
        response = model.generate_content(prompt)
        story = response.text

        # Fetch an image related to the topic
        image_url = fetch_image_url(topic)
        if not image_url:
            image_url = "https://via.placeholder.com/300"  # Provide a default image if no image is found

        return jsonify({"story": story, "image_url": image_url})
    except Exception as e:
        logging.error(f"Error generating story: {str(e)}")
        return jsonify({"error": f"Error generating story: {str(e)}"}), 500

@app.route('/generate_content', methods=['POST'])
def generate_content():
    data = request.json
    topic = data.get('topic')

    # Build prompt for content generation
    prompt = (
        f"Provide a detailed explanation of the topic '{topic}' from the Indian Knowledge System. "
        f"Include an introduction, brief history, key principles, conclusion, and summary at the end."
    )

    try:
        # Call Gemini API to generate content
        response = model.generate_content(prompt)
        content = response.text

        # Structure the content into sections (you can modify the structure as needed)
        content_sections = {
            "introduction": content.split('History:')[0].strip(),
            "history": "History section goes here...",
            "keyPrinciples": "Key Principles go here...",
            "conclusion": "Conclusion goes here...",
            "summary": "Summary goes here..."
        }

        # If the content has structured sections, try to update them
        if 'History' in content:
            content_sections['history'] = content.split('History:')[1].split('Key Principles:')[0].strip()
        
        if 'Key Principles' in content:
            content_sections['keyPrinciples'] = content.split('Key Principles:')[1].split('Conclusion:')[0].strip()

        if 'Conclusion' in content:
            content_sections['conclusion'] = content.split('Conclusion:')[1].split('Summary:')[0].strip()

        if 'Summary' in content:
            content_sections['summary'] = content.split('Summary:')[1].strip()

        return jsonify({"content": content_sections})

    except Exception as e:
        logging.error(f"Error generating content: {str(e)}")
        return jsonify({"error": f"Error generating content: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
