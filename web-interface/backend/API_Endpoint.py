import os
import requests
import datetime
from datetime import timezone
from io import BytesIO
from pathlib import Path
from PIL import Image
import openai
from jsonschema import validate, ValidationError
from flask import Flask, request, jsonify, send_from_directory, redirect, url_for, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
import logging

dalle_schema = {
    "type": "object",
    "properties": {
        "prompt": {"type": "string"},
        "n": {"type": "integer"},
        "width": {"type": "integer"},
        "height": {"type": "integer"},
        "quality": {"type": "string"},
        "style": {"type": "string"},
        "user": {"type": "string"}
    },
    "required": ["prompt", "user"]
}

# Determine the root directory of the project
project_root = Path(__file__).parent.parent

load_dotenv()

# # Access variables
sqlalchemy_database_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
openai_api_key = os.getenv('OPENAI_API_KEY')
stability_key = os.getenv('STABILITY_KEY')
okta_secret_key = os.getenv('OKTA_SECRET_KEY')
okta_client_id = os.getenv('OKTA_CLIENT_ID')
okta_client_secret = os.getenv('OKTA_CLIENT_SECRET')
okta_domain = os.getenv('OKTA_DOMAIN')
server_domain = os.getenv('SERVER_DOMAIN')

# Initialize Flask
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = sqlalchemy_database_uri
db = SQLAlchemy(app)
logging.info(f"Server Initialized.")

# Set the values in the app configuration
openai.api_key = openai_api_key
STABILITY_KEY = stability_key

class ImageMetadata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    model = db.Column(db.String(50), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    quality = db.Column(db.String(50))
    style = db.Column(db.String(50))
    user = db.Column(db.String(50))
    is_generated = db.Column(db.SmallInteger, default=0)

# Define the network share path
NETWORK_SHARE_PATH = r'\\callisto\Data'

app.secret_key = okta_secret_key

# Okta settings
OKTA_CLIENT_ID = okta_client_id
OKTA_CLIENT_SECRET = okta_client_secret
OKTA_AUTH_SERVER = f"https://{okta_domain}/oauth2/default"
OKTA_REDIRECT_URI = f"http://{server_domain}/login/callback"


@app.route('/')
def home():
    return 'Welcome to OAuth with Okta in Flask!'

@app.route('/login')
def login():
    okta = OAuth2Session(OKTA_CLIENT_ID, redirect_uri=OKTA_REDIRECT_URI)
    authorization_url, state = okta.authorization_url(OKTA_AUTH_SERVER + '/v1/authorize')
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route('/login/callback')
def callback():
    okta = OAuth2Session(OKTA_CLIENT_ID, state=session['oauth_state'], redirect_uri=OKTA_REDIRECT_URI)
    token = okta.fetch_token(
        OKTA_AUTH_SERVER + '/v1/token',
        client_secret=OKTA_CLIENT_SECRET,
        authorization_response=request.url,
    )
    # Store the token securely, for example in session
    session['oauth_token'] = token
    return redirect(url_for('protected'))

@app.route('/protected')
def protected():
    if 'oauth_token' in session:
        # Use the token to access protected resources from Okta APIs
        return 'You are logged in!'
    else:
        return redirect(url_for('login'))


@app.route('/upload-data', methods=['POST'])
def upload_data():
    data = request.json
    # Insert data into the database
    for item in data:
        new_entry = ImageMetadata(
            id=item['id'],
            filename=item['filename'],
            prompt=item['prompt'],
            user=item['user'],
            quality=item['quality'],
            style=item['style'],
            model=item['model'],
            size=item['size'],
            is_generated = 1
        )
        db.session.add(new_entry)
    db.session.commit()
    return jsonify({'status': 'success'}), 200

@app.route('/api/metadata', methods=['GET'])
def get_metadata():
    metadata = ImageMetadata.query.all()
    metadata_list = [{
        'id': item.id,
        'filename': item.filename,
        'timestamp': item.timestamp,
        'model': item.model,
        'prompt': item.prompt,
        'width': item.width,
        'height': item.height,
        'quality': item.quality,
        'style': item.style,
        'user': item.user,
        'is_generated': item.is_generated
    } for item in metadata]
    return jsonify(metadata_list)

# Route to generate art
@app.route('/generate-art/<model>', methods=['POST'])
def generate_art(model):
    try:
        data = request.json
        logging.info(f"Received JSON data: {data}")
        
        if data is None:
            logging.info(f"Error: Invalid JSON data received.")
            return jsonify({'error': 'Invalid JSON data received'}), 400

        # Choose schema based on the model
        if model == 'dalle':
            schema = dalle_schema
            logging.info("DALL-E schema selected.")
        else:
            logging.info(f"Invalid Model")
            return jsonify({'error': 'Invalid model'}), 400

        # Validate against the chosen schema
        validate(data, schema)

        # If validation succeeds, continue processing
        prompt = data.get('prompt')
        n = int(data.get('n', 1))
        width = int(data.get('width', 1024))
        height = int(data.get('height', 1024))
        quality = data.get('quality', '')
        style = data.get('style', '')
        user = data.get('user', '')
        
        # Process based on the model type
        if model == 'dalle':
            results = dalle_generate(prompt, n, width, height, quality, style, user=user)
            logging.info("Using DALL-E to create image")
        else:
            logging.info("Invalid Model")
            return jsonify({'error': 'Invalid model'}), 400

        return jsonify(results), 200

    except ValidationError as e:
        logging.info(f"Invalid JSON format: {e.message}")
        return jsonify({'error': f'Invalid JSON format: {e.message}'}), 400

    except Exception as e:
        logging.info(f"Exception occurred: {str(e)}")
        print(f"Exception occurred: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
# Route to serve images    
@app.route('/images/<filename>', methods=['GET'])
def serve_image(filename):
    logging.info(f"Fetching {filename}")
    return send_from_directory(NETWORK_SHARE_PATH, filename)
    
# Function to generate images using DALL-E
def dalle_generate(prompt, n, width, height, quality, style, user=''):
    try:
        # Define parameters for DALL-E image generation
        image_params = {
            "model": "dall-e-3",        # DALL-E 3 model
            "prompt": prompt,           # Prompt for generation
            "n": n,                     # Number of images to generate
            "size": f"{width}x{height}",# Image dimensions
            "user": user,               # User parameter added
            "response_format": "url"
        }

        # Add optional parameters if they are provided
        if quality:
            image_params["quality"] = quality
        if style:
            image_params["style"] = style

        logging.info(f"Fetched image parameters for DALL-E")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai.api_key}"
        }

        # Generate images using OpenAI's API
        response = requests.post("https://api.openai.com/v1/images/generations", headers=headers, json=image_params)
        images_response = response.json()  # Parse the JSON response
        logging.info(f"Response Status: {response.status_code}")

        # Check if 'data' key exists in the response
        if 'data' in images_response:
            images_dt = datetime.now(timezone.utc)
            img_filename_prefix = images_dt.strftime('DALLE_%Y%m%d_%H%M%S')

            image_details = []

            for i, image_data in enumerate(images_response['data']):
                if 'url' in image_data:
                    try:
                        img_url = image_data['url']

                        # Fetch the image from the URL
                        logging.info(f"Fetching the image from URL {img_url}")
                        img_response = requests.get(img_url)
                        img_data = img_response.content

                        # Save image as png/jpg/jpeg
                        img_filename = f"{img_filename_prefix}_{i}.jpg"
                        img_path = os.path.join(NETWORK_SHARE_PATH, img_filename)
                        logging.info(f"Image path: {img_path}")
                        print(f"Image path: {img_path}") # Test Statement Delete Later
                        
                        # Save image to disk
                        with open(img_path, 'wb') as img_file:
                            img_file.write(img_data)
                        logging.info("Image saved to disk.")

                        image_details.append({
                            'url': f"\\\\callisto\\Data\\{img_filename}",
                            'filename': img_filename,
                            'timestamp': images_dt,
                            'is_generated': 1
                        })
                        logging.info("Successfully appended details.")

                    except Exception as e:
                        logging.exception(f"Error saving image {i}: {e}")
                        print(f"Error saving image {i}: {e}")

            return {"images": image_details}

        else:
            logging.info(f"Unexpected response format from OpenAI API: {images_response}")
            print(f"Unexpected response format from OpenAI API: {images_response}")
            return {"images": []}

    except requests.RequestException as e:
        logging.exception(f"Request Error: {e}")
        print(f"Request Error: {e}")
        return {"images": []}
    
# Function to generate images using Stable Diffusion
def stable_diffusion_generate(prompt, negative_prompt, n, seed, style_preset):
    try:
        # Define parameters for Stable Diffusion image generation
        image_params = {
            "model": "stable-diffusion-v3",  # Stable Diffusion v3 model
            "prompt": prompt,                # Prompt for image generation
            "negative_prompt": negative_prompt,  # Negative prompt to exclude certain features
            "n": n,                          # Number of images to generate
            "seed": seed,                    # Seed for reproducibility
            "style_preset": style_preset,    # Style preset
        }

        headers = {
            "Content-Type": "application/json"
        }

        # Generate images using Stable Diffusion's API
        response = requests.post("https://api.stability.ai/v2beta/stable-image/generate/sd3", headers=headers, json=image_params)
        images_response = response.json()  # Parse the JSON response
        logging.info(f"Response Status: {response.status_code}")
        logging.info(f"Response JSON: {images_response}")

        # Check if 'data' key exists in the response
        if 'data' in images_response:
            images_dt = datetime.now(timezone.utc)
            img_filename_prefix = images_dt.strftime('STABLEDIFF_%Y%m%d_%H%M%S')

            image_urls = []

            for i, image_data in enumerate(images_response['data']):
                if 'url' in image_data:
                    try:
                        img_url = image_data['url']

                        # Fetch the image from the URL
                        logging.info(f"Fetching image url {img_url}")
                        img_response = requests.get(img_url)
                        img_data = img_response.content
                        img = Image.open(BytesIO(img_data))

                        # Save image as JPEG
                        img_filename = f"{img_filename_prefix}_{i}.png"
                        img_path = os.path.join(NETWORK_SHARE_PATH, img_filename)
                        logging.info(f"Image path {img_path}")
                        
                        # Save image to disk
                        with open(img_path, 'wb') as img_file:
                            img_file.write(img_data)
                        logging.info("Image saved to disk")

                        image_urls.append({
                                    'url': f"\\\\callisto\\Data\\{img_filename}",
                                })
                        logging.info("Successfully appended image urls in image_urls.")
                    
                    except Exception as e:
                        logging.info(f"Error saving image {i}: {e}")
                        print(f"Error saving image {i}: {e}")

            return {"images": image_urls}

        else:
            logging.info(f"Unexpected response format from Stable Diffusion API: {images_response}")
            print(f"Unexpected response format from Stable Diffusion API: {images_response}")
            return {"images": []}

    except requests.RequestException as e:
        logging.exception(f"Request Error: {e}")
        print(f"Request Error: {e}")
        return {"images": []}

#Route to create image variations
@app.route('/create-variations', methods=['POST'])
def create_variations():
    try:
        data = request.json
        logging.info(f"Received JSON data: {data}")

        if data is None:
            logging.info("Error: Invalid JSON data received.")
            return jsonify({'error': 'Invalid JSON data received'}), 400

        image_url = data.get('image_url')
        n = int(data.get('n', 1))
        width = int(data.get('width', 1024))
        height = int(data.get('height', 1024))
        user = data.get('user', '')

        # Validate input parameters
        if not image_url:
            logging.info("Error: image_url is required.")
            return jsonify({'error': 'image_url is required'}), 400

        # Create image variations
        results = dalle_create_variations(image_url, n, width, height, user=user)
        return jsonify(results), 200

    except Exception as e:
        logging.exception(f"Exception occurred: {str(e)}")
        print(f"Exception occurred: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
# Function to create image variations using DALL-E
def dalle_create_variations(image_url, n, width, height, user=''):
    try:
        # Define parameters for DALL-E image variation creation
        variation_params = {
            "model": "dall-e-3",        # DALL-E 3 model
            "image_url": image_url,     # URL of the image to create variations from
            "n": n,                     # Number of variations to create
            "size": f"{width}x{height}",# Image dimensions
            "user": user,               # User parameter added
            "response_format": "url"
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai.api_key}"
        }

        # Create image variations using OpenAI's API
        response = requests.post("https://api.openai.com/v1/images/variations", headers=headers, json=variation_params)
        variations_response = response.json()  # Parse the JSON response
        logging.info(f"Response Status: {response.status_code}")

        # Check if 'data' key exists in the response
        if 'data' in variations_response:
            variations_dt = datetime.now(timezone.utc)
            var_filename_prefix = variations_dt.strftime('VARIATION_%Y%m%d_%H%M%S')

            variation_urls = []

            for i, variation_data in enumerate(variations_response['data']):
                if 'url' in variation_data:
                    try:
                        var_url = variation_data['url']

                        # Fetch the image from the URL
                        logging.info(f"Fetched image from URL {var_url}")
                        var_response = requests.get(var_url)
                        var_data = var_response.content
                        var_img = Image.open(BytesIO(var_data))

                        # Save image as png/jpg/jpeg
                        var_filename = f"{var_filename_prefix}_{i}.png"
                        var_path = os.path.join(NETWORK_SHARE_PATH, var_filename)
                        logging.info(f"Variation path: {var_path}")

                        # Save image to disk
                        with open(var_path, 'wb') as var_file:
                            var_file.write(var_data)
                        logging.info(f"Image {var_data} saved to disk.")

                        variation_urls.append({
                            'url': f"\\\\callisto\\Data\\{var_filename}",
                        })
                        logging.info("Appended variation urls to variation_urls.")

                    except Exception as e:
                        logging.exception(f"Error saving variation {i}: {e}")
                        print(f"Error saving variation {i}: {e}")

            return {"variations": variation_urls}

        else:
            logging.info(f"Unexpected response format from OpenAI API: {variations_response}")
            print(f"Unexpected response format from OpenAI API: {variations_response}")
            return {"variations": []}

    except requests.RequestException as e:
        logging.exception(f"Request Error: {e}")
        print(f"Request Error: {e}")
        return {"variations": []}
    
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8001)