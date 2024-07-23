from pathlib import Path
import requests
from io import BytesIO
from PIL import Image
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from jsonschema import validate, ValidationError
from flask_cors import CORS
from datetime import datetime, timezone, timedelta
import os
import openai
import uuid
import pyodbc # KEEP IN SCRIPT

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

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Determine the root directory of your project
project_root = Path(__file__).parent.parent

# from dotenv import load_dotenv
# import os

# # Load environment variables from .env file
# load_dotenv()

# # Access variables
# app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
# openai.api_key = os.getenv('OPENAI_API_KEY')
# STABILITY_KEY = os.getenv('STABILITY_KEY')

# Configure the SQLAlchemy URI for SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 's'

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Directory to save generated images
IMAGE_DIR = os.path.join(app.root_path, 'generated_images')
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

# OpenAI API Endpoint
openai.api_key = 's' # ENSURE THIS IS SET ON MACHINE
STABILITY_KEY = 's'

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

    def __repr__(self):
        return f"<ImageMetadata {self.id}>"

# Function to delete old images and metadata
def delete_old_images_and_metadata():
    # Calculate the cutoff time dynamically as the current time minus 48 hours
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=48)
    
    # Query the database for metadata entries older than the cutoff time
    old_metadata = ImageMetadata.query.filter(ImageMetadata.timestamp < cutoff_time).all()
    
    for metadata in old_metadata:
        try:
            # Delete the image file associated with the metadata
            image_path = os.path.join(IMAGE_DIR, metadata.filename)
            if os.path.exists(image_path):
                os.remove(image_path)
            
            # Delete the metadata entry from the database
            db.session.delete(metadata)
        except Exception as e:
            print(f"Error deleting file {metadata.filename}: {str(e)}")
    
    # Commit the transaction to finalize the deletions
    db.session.commit()
    print("Old images and metadata deleted.")

# Schedule the cleanup task to run every 48 hours
scheduler = BackgroundScheduler()
scheduler.add_job(delete_old_images_and_metadata, 'interval', hours=48)
scheduler.start()

# Route to generate art
@app.route('/generate-art/<model>', methods=['POST'])
def generate_art(model):
    try:
        data = request.json
        print(f"Received JSON data: {data}")
        
        if data is None:
            return jsonify({'error': 'Invalid JSON data received'}), 400

        # Choose schema based on the model
        if model == 'dalle':
            schema = dalle_schema
        else:
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
        else:
            return jsonify({'error': 'Invalid model'}), 400

        return jsonify(results), 200

    except ValidationError as e:
        return jsonify({'error': f'Invalid JSON format: {e.message}'}), 400

    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
# Route to serve images    
@app.route('/images/<filename>', methods=['GET'])
def serve_image(filename):
    return send_from_directory(IMAGE_DIR, filename)
    
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

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai.api_key}"
        }

        # Generate images using OpenAI's API
        response = requests.post("https://api.openai.com/v1/images/generations", headers=headers, json=image_params)
        images_response = response.json()  # Parse the JSON response
        print(f"Response Status: {response.status_code}")
        print(f"Response JSON: {response.json()}")

        # Check if 'data' key exists in the response
        if 'data' in images_response:
            images_dt = datetime.now(timezone.utc)
            img_filename_prefix = images_dt.strftime('DALLE_%Y%m%d_%H%M%S')

            image_urls = []

            for i, image_data in enumerate(images_response['data']):
                if 'url' in image_data:
                    try:
                        img_url = image_data['url']

                        # Fetch the image from the URL
                        img_response = requests.get(img_url)
                        img_data = img_response.content
                        img = Image.open(BytesIO(img_data))

                        # Save image as png/jpg/jpeg
                        img_filename = f"{img_filename_prefix}_{i}.png"
                        img_path = os.path.join(IMAGE_DIR, img_filename)
                        print(f"Image path: {img_path}")
                        
                        # Save image to disk
                        with open(img_path, 'wb') as img_file:
                            img_file.write(img_data)

                        # Create metadata entry
                        metadata = ImageMetadata(
                            filename=img_filename,
                            timestamp=images_dt,
                            model='dalle',
                            prompt=prompt,
                            width=width,
                            height=height,
                            quality=quality,
                            style=style,
                            user=user
                        )

                        db.session.add(metadata)

                        image_urls.append({
                            'url': f"/images/{img_filename}",
                            'metadata': metadata
                        })

                    except Exception as e:
                        print(f"Error saving image {i}: {e}")

            db.session.commit()  # Commit after processing all images
            return {"images": image_urls}

        else:
            print(f"Unexpected response format from OpenAI API: {images_response}")
            return {"images": []}

    except requests.RequestException as e:
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
        print(f"Response Status: {response.status_code}")
        print(f"Response JSON: {images_response}")

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
                        img_response = requests.get(img_url)
                        img_data = img_response.content
                        img = Image.open(BytesIO(img_data))

                        # Save image as JPEG
                        img_filename = f"{img_filename_prefix}_{i}.png"
                        img_path = os.path.join(IMAGE_DIR, img_filename)
                        print(f"Image path: {img_path}")
                        
                        # Save image to disk
                        with open(img_path, 'wb') as img_file:
                            img_file.write(img_data)

                        metadata = ImageMetadata(
                            filename=img_filename,
                            timestamp=images_dt,
                            model='stable-diffusion',
                            prompt=prompt,
                            negative_prompt=negative_prompt,
                            seed=seed,
                            style_preset=style_preset
                        )

                        db.session.add(metadata)

                        image_urls.append({
                                    'url': f"/images/{img_filename}",
                                    'metadata': metadata
                                })
                    
                    except Exception as e:
                        print(f"Error saving image {i}: {e}")

            db.session.commit()  # Commit after processing all images
            return {"images": image_urls}

        else:
            print(f"Unexpected response format from Stable Diffusion API: {images_response}")
            return {"images": []}

    except requests.RequestException as e:
        print(f"Request Error: {e}")
        return {"images": []}

# Route to upload images
@app.route('/upload', methods=['POST'])
def upload_images():
    data = request.get_json()
    images = data.get('images')

    if not images or not isinstance(images, list):
        return jsonify({'message': 'Invalid request. "images" should be a list of objects with "imageUrl" and "generatedImageFilename"'}), 400

    response_data = []

    try:
        folder_path = os.path.join(app.root_path, 'uploaded_images')
        os.makedirs(folder_path, exist_ok=True)

        for image_data in images:
            imageUrl = image_data.get('imageUrl')
            generated_image_filename = image_data.get('generatedImageFilename')

            if not imageUrl or not generated_image_filename:
                return jsonify({'message': 'Invalid request. Each image object must contain "imageUrl" and "generatedImageFilename"'}), 400

            # Retrieve metadata from the generated image
            generated_metadata = ImageMetadata.query.filter_by(filename=generated_image_filename).first()
            if not generated_metadata:
                return jsonify({'message': f'Metadata for the generated image {generated_image_filename} not found'}), 404

            # Generate a unique filename using UUID
            unique_filename = str(uuid.uuid4()) + '.jpg'
            filename = os.path.join(folder_path, unique_filename)

            # Download the image from the provided URL
            response = requests.get(imageUrl)
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(response.content)

                # Create new metadata entry for the uploaded image, copying from the generated image metadata
                uploaded_metadata = ImageMetadata(
                    filename=unique_filename,
                    timestamp=datetime.now(timezone.utc),
                    model=generated_metadata.model,
                    prompt=generated_metadata.prompt,
                    width=generated_metadata.width,
                    height=generated_metadata.height,
                    quality=generated_metadata.quality,
                    style=generated_metadata.style,
                    user=generated_metadata.user
                )

                db.session.add(uploaded_metadata)

                response_data.append({
                    'uploaded_filename': unique_filename,
                    'message': 'Image uploaded successfully'
                })
                
            else:
                response_data.append({
                    'uploaded_filename': None,
                    'message': f'Failed to download image from {imageUrl}. URL may be invalid'
                })

        db.session.commit()
        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({'message': f'Error uploading images: {str(e)}'}), 500
    
# Endpoint to fetch list of uploaded images
@app.route('/api/uploaded_images')
def get_uploaded_images():
    images_dir = os.path.join(app.root_path, 'backend', 'uploaded_images')
    images = os.listdir(images_dir)
    image_list = [image for image in images if image.lower().endswith(('.jpg', '.png'))]

    return jsonify({'images': image_list})

# Route to fetch metadata based on filename
@app.route('/api/metadata', methods=['GET'])
def get_metadata():
    filename = request.args.get('filename')

    if not filename:
        return jsonify({'error': 'Filename parameter is required'}), 400

    try:
        # Query metadata from the database
        metadata = ImageMetadata.query.filter_by(filename=filename).first()

        if not metadata:
            return jsonify({'error': 'Metadata not found for the given filename'}), 404

        # Construct JSON response
        metadata_dict = {
            'filename': metadata.filename,
            'timestamp': metadata.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'model': metadata.model,
            'prompt': metadata.prompt,
            'width': metadata.width,
            'height': metadata.height,
            'quality': metadata.quality,
            'style': metadata.style,
            'user': metadata.user
        }

        return jsonify(metadata_dict), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8001)
    
