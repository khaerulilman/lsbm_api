from flask import Flask, request, jsonify, send_file
from flask_cors import CORS  # Import CORS
from PIL import Image
import random
import hashlib
import os
import io
import base64
from werkzeug.utils import secure_filename
import tempfile
import cloudinary
import cloudinary.uploader
import cloudinary.api
from datetime import datetime

app = Flask(__name__)

# Configure CORS to allow all domains
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization", "Access-Control-Allow-Origin"],
        "expose_headers": ["Content-Type", "Authorization", "Access-Control-Allow-Origin"],
        "supports_credentials": True
    }
})

# Configure Cloudinary
cloudinary.config(
    cloud_name="dsv5gqxsv",
    api_key="885774276796484",
    api_secret="wwL1QGMTiZVhpJRDPK2y2sK50Rw"
)

# Configure upload settings
ALLOWED_EXTENSIONS = {'png', 'bmp'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper function: get pixel order based on password
def get_pixel_order(width, height, password):
    seed = int(hashlib.sha256(password.encode()).hexdigest(), 16) % (10 ** 8)
    coords = [(x, y) for y in range(height) for x in range(width)]
    random.seed(seed)
    random.shuffle(coords)
    return coords

# Encoding function
def embed_message(image_file, message, password):
    img = Image.open(image_file).convert('RGB')
    pixels = img.load()
    width, height = img.size

    message_bin = ''.join(format(ord(c), '08b') for c in message)
    length_bin = format(len(message_bin), '032b')
    total_bin = length_bin + message_bin

    coords = get_pixel_order(width, height, password)
    if len(total_bin) > len(coords):
        raise ValueError("Pesan terlalu panjang untuk gambar ini.")

    # Set random seed for consistent channel selection during encoding/decoding
    random.seed(int(hashlib.sha256(password.encode()).hexdigest(), 16) % (10 ** 8))
    
    for i, bit in enumerate(total_bin):
        x, y = coords[i]
        r, g, b = pixels[x, y]
        channel = random.choice([0, 1, 2])
        color = [r, g, b]

        current_lsb = color[channel] % 2
        bit = int(bit)
        if current_lsb != bit:
            color[channel] = color[channel] + 1 if color[channel] < 255 else color[channel] - 1
        pixels[x, y] = tuple(color)

    # Save to BytesIO instead of file
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes

def upload_to_cloudinary_from_bytes(img_bytes, folder="steganography", filename="stego_image"):
    """Upload file from BytesIO to Cloudinary and return the URL"""
    try:
        # Upload with specific folder and resource type
        result = cloudinary.uploader.upload(
            img_bytes,
            folder=folder,
            resource_type="image",
            public_id=filename,
            unique_filename=True
        )
        return result.get('secure_url'), result.get('public_id')
    except Exception as e:
        raise Exception(f"Failed to upload to Cloudinary: {str(e)}")

# Decoding function - Enhanced for Cloudinary
def extract_message_from_url(image_url, password):
    """Extract message from Cloudinary URL"""
    import urllib.request
    
    # Download image to BytesIO
    img_bytes = io.BytesIO()
    
    try:
        with urllib.request.urlopen(image_url) as response:
            img_bytes.write(response.read())
        img_bytes.seek(0)
        
        message = extract_message_from_bytes(img_bytes, password)
        return message
    except Exception as e:
        raise e

# Decoding function
def extract_message_from_bytes(image_bytes, password):
    img = Image.open(image_bytes).convert('RGB')
    pixels = img.load()
    width, height = img.size
    coords = get_pixel_order(width, height, password)

    # Set random seed for consistent channel selection during encoding/decoding
    random.seed(int(hashlib.sha256(password.encode()).hexdigest(), 16) % (10 ** 8))

    bits = ""
    for i in range(32):
        x, y = coords[i]
        r, g, b = pixels[x, y]
        bits += str([r, g, b][random.choice([0, 1, 2])] % 2)
    msg_len = int(bits, 2)

    bits = ""
    for i in range(32, 32 + msg_len):
        x, y = coords[i]
        r, g, b = pixels[x, y]
        bits += str([r, g, b][random.choice([0, 1, 2])] % 2)

    chars = [chr(int(bits[i:i + 8], 2)) for i in range(0, len(bits), 8)]
    return ''.join(chars)

@app.route('/api/encode', methods=['POST', 'OPTIONS'])
def encode_message():
    """
    API endpoint untuk encoding pesan ke dalam gambar
    
    Expected form data:
    - image: file (PNG/BMP)
    - message: string
    - password: string
    
    Returns:
    - JSON response dengan Cloudinary URL atau error
    """
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'success': True})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    try:
        # Validate request
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image file provided'
            }), 400
        
        if 'message' not in request.form or 'password' not in request.form:
            return jsonify({
                'success': False,
                'error': 'Message and password are required'
            }), 400

        file = request.files['image']
        message = request.form['message']
        password = request.form['password']

        # Validate inputs
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        if not message.strip():
            return jsonify({
                'success': False,
                'error': 'Message cannot be empty'
            }), 400

        if not password.strip():
            return jsonify({
                'success': False,
                'error': 'Password cannot be empty'
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'File type not allowed. Only PNG and BMP files are supported.'
            }), 400

        try:
            # Embed message - work with BytesIO directly
            img_bytes = embed_message(file, message, password)
            
            # Upload result to Cloudinary
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(secure_filename(file.filename))[0]
            output_filename = f"stego_{base_name}_{timestamp}"
            
            cloudinary_url, public_id = upload_to_cloudinary_from_bytes(
                img_bytes.getvalue(), 
                "steganography/encoded", 
                output_filename
            )
            
            response = jsonify({
                'success': True,
                'message': 'Pesan berhasil disisipkan ke dalam gambar dan diupload ke Cloudinary',
                'cloudinary_url': cloudinary_url,
                'public_id': public_id,
                'output_filename': output_filename,
                'original_filename': file.filename
            })
            
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

        except ValueError as ve:
            response = jsonify({
                'success': False,
                'error': str(ve)
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        except Exception as e:
            response = jsonify({
                'success': False,
                'error': f'Error processing image: {str(e)}'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 500

    except Exception as e:
        response = jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@app.route('/api/decode', methods=['POST', 'OPTIONS'])
def decode_message():
    """
    API endpoint untuk decoding pesan dari gambar
    
    Expected form data:
    - image_decode: file (PNG/BMP)
    - password: string
    
    Returns:
    - JSON response dengan extracted message atau error
    """
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'success': True})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    try:
        # Check if password is provided
        if 'password' not in request.form:
            response = jsonify({
                'success': False,
                'error': 'Password is required'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        password = request.form['password']

        if not password.strip():
            response = jsonify({
                'success': False,
                'error': 'Password cannot be empty'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        # Check if image file is uploaded
        if 'image_decode' not in request.files:
            response = jsonify({
                'success': False,
                'error': 'No image file provided'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        file = request.files['image_decode']
        
        # Validate inputs
        if file.filename == '':
            response = jsonify({
                'success': False,
                'error': 'No file selected'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        if not allowed_file(file.filename):
            response = jsonify({
                'success': False,
                'error': 'File type not allowed. Only PNG and BMP files are supported.'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        try:
            # Extract message from uploaded file directly
            extracted_message = extract_message_from_bytes(file, password)
            
            response = jsonify({
                'success': True,
                'message': 'Pesan berhasil diekstrak dari gambar',
                'extracted_message': extracted_message,
                'original_filename': file.filename
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

        except Exception as e:
            response = jsonify({
                'success': False,
                'error': f'Error extracting message: {str(e)}. Pastikan password benar dan gambar mengandung pesan tersembunyi.'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

    except Exception as e:
        response = jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health_check():
    """Health check endpoint"""
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'success': True})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        return response
    
    response = jsonify({
        'status': 'healthy',
        'message': 'LSB Steganography API is running'
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/', methods=['GET', 'OPTIONS'])
def index():
    """API documentation endpoint"""
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'success': True})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        return response
    
    docs = {
        'name': 'LSB Matching Steganography API',
        'version': '1.0.0',
        'description': 'API untuk menyembunyikan dan mengekstrak pesan dalam gambar menggunakan LSB Matching',
        'endpoints': {
            'POST /api/encode': {
                'description': 'Menyisipkan pesan ke dalam gambar dan upload ke Cloudinary',
                'parameters': {
                    'image': 'file (PNG/BMP)',
                    'message': 'string - pesan yang akan disembunyikan',
                    'password': 'string - password untuk enkripsi'
                },
                'response': 'JSON dengan Cloudinary URL'
            },
            'POST /api/decode': {
                'description': 'Mengekstrak pesan dari gambar',
                'parameters': {
                    'image': 'file (PNG/BMP) - OR',
                    'cloudinary_url': 'string - Cloudinary image URL',
                    'password': 'string - password untuk dekripsi'  
                },
                'response': 'JSON dengan extracted_message'
            },
            'GET /api/health': {
                'description': 'Health check endpoint',
                'response': 'Status API'
            }
        },
        'supported_formats': ['PNG', 'BMP'],
        'max_file_size': '16MB',
        'cloudinary_integration': True,
        'note': 'Images are automatically uploaded to Cloudinary for storage and sharing'
    }
    response = jsonify(docs)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

# Vercel requires this
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# For Vercel deployment
if __name__ == '__main__':
    app.run(debug=False)
