from flask import Blueprint, render_template, make_response, request
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET', 'POST'], strict_slashes=False)
def index():
    if request.method == 'POST':
        # Delegate to Omni ACP if needed, but blueprints should handle their own prefixes.
        # However, for root POST, we can keep it for legacy compatibility or redirect.
        # Actually, index.py would handle this if not refactored.
        pass
        
    resp = make_response(render_template('index.html'))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, public, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@main_bp.route('/kr', strict_slashes=False)
def kr_index():
    resp = make_response(render_template('kr_index.html'))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, public, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@main_bp.route('/dividend', strict_slashes=False)
def dividend_portfolio():
    resp = make_response(render_template('dividend_portfolio.html'))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return resp

@main_bp.route('/dashboard', strict_slashes=False)
def dashboard():
    resp = make_response(render_template('dashboard.html'))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, public, max-age=0'
    return resp

@main_bp.route('/omni', strict_slashes=False)
@main_bp.route('/omni-dashboard', strict_slashes=False)
def omni_dashboard():
    resp = make_response(render_template('omni_dashboard.html'))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, public, max-age=0'
    return resp

