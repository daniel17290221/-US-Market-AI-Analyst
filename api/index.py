import os
import sys
import json
import traceback
from flask import Flask, session, request

app = Flask(__name__) # Minimal app for error reporting
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'vibecoding_secret_key')

try:
    # Robust path resolution
    API_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.dirname(API_DIR)

    if API_DIR not in sys.path:
        sys.path.append(API_DIR)
    if BASE_DIR not in sys.path:
        sys.path.append(BASE_DIR)

    from utils import get_data_dir
    try:
        from x_agent import XMarketAgent
        print("X Agent Module Loaded")
    except:
        pass

    # Re-initialize Flask with proper folders
    TEMPLATE_DIR = os.path.join(API_DIR, 'templates')
    if not os.path.exists(TEMPLATE_DIR):
        TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

    app.template_folder = TEMPLATE_DIR
    app.static_folder = os.path.join(BASE_DIR, 'assets')
    app.static_url_path = '/assets'

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

except Exception as e:
    # Minimal logging for production safety
    print(f"CRITICAL APP STARTUP ERROR: {e}")
    import traceback
    traceback.print_exc()

# Global Handlers
from flask import request
@app.before_request
def check_options():
    if request.method == 'OPTIONS':
        return make_response()

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    app.run(debug=False, port=5000)
