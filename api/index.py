import os
import sys
from flask import Flask, session

# Robust path resolution
API_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(API_DIR)

if API_DIR not in sys.path:
    sys.path.append(API_DIR)
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from utils import get_data_dir

# Initialize Flask with specific template and static folders
TEMPLATE_DIR = os.path.join(API_DIR, 'templates')
if not os.path.exists(TEMPLATE_DIR):
    TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

app = Flask(__name__, 
            template_folder=TEMPLATE_DIR,
            static_folder=os.path.join(BASE_DIR, 'assets'),
            static_url_path='/assets')

app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'vibecoding_secret_key')

# Register Blueprints
from routes.main import main_bp
from routes.kr_market import kr_market_bp
from routes.us_market import us_market_bp
from routes.omni import omni_bp
from routes.common import common_bp

app.register_blueprint(main_bp)
app.register_blueprint(kr_market_bp)
app.register_blueprint(us_market_bp)
app.register_blueprint(omni_bp, url_prefix='/api/acp')
app.register_blueprint(common_bp)

# Global Handlers
from flask import request
@app.before_request
def debug_all_requests():
    path = request.path.lower()
    if 'acp' in path or request.method == 'POST':
        print(f"!!! [{request.method}] {request.path} detected !!!")

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    app.run(debug=True, port=5000)
