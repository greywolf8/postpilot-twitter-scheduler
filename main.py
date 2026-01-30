from flask import Flask, request, jsonify, send_from_directory
import subprocess
import sys
import os
from werkzeug.utils import secure_filename
import tempfile

app = Flask(__name__)

@app.route('/scrape', methods=['POST'])
def scrape_user():
    try:
        data = request.get_json()
        
        if not data or 'username' not in data:
            return jsonify({'error': 'Username is required'}), 400
        
        username = data['username']
        
        # Validate username
        if not username or len(username) < 3 or len(username) > 20:
            return jsonify({'error': 'Invalid username format'}), 400
        
        print(f"[INFO] Starting scrape for user: {username}")
        
        # Step 1: Run user-scrapper.py with the username
        print("[INFO] Running user-scrapper.py...")
        scraper_result = subprocess.run([
            sys.executable, 'user-scrapper.py', username
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        if scraper_result.returncode != 0:
            print(f"[ERROR] Scraper failed: {scraper_result.stderr}")
            return jsonify({
                'error': 'Scraping failed',
                'details': scraper_result.stderr
            }), 500
        
        print("[INFO] Scraper completed successfully")
        
        # Step 2: Run analytics.py on the generated data
        print("[INFO] Running analytics.py...")
        analytics_result = subprocess.run([
            sys.executable, 'analytics.py'
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        if analytics_result.returncode != 0:
            print(f"[ERROR] Analytics failed: {analytics_result.stderr}")
            return jsonify({
                'error': 'Analytics failed',
                'details': analytics_result.stderr
            }), 500
        
        print("[INFO] Analytics completed successfully")
        
        # Check if output files were created
        output_files = []
        expected_files = ['user_analytics.csv', 'analytics_report.txt', 'analytics_report.json', 'hour_engagement.png', 'day_engagement.png']
        
        for file in expected_files:
            if os.path.exists(file):
                output_files.append(file)
        
        return jsonify({
            'success': True,
            'message': f'Successfully scraped and analyzed data for u/{username}',
            'username': username,
            'output_files': output_files,
            'scraper_output': scraper_result.stdout,
            'analytics_output': analytics_result.stdout
        })
        
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        return jsonify({
            'error': 'Unexpected error occurred',
            'details': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'reddit-scraper'})

@app.route('/test')
def test_page():
    return send_from_directory('.', 'test.html')

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'service': 'Reddit User Scraper & Analytics',
        'version': '1.0',
        'endpoints': {
            'POST /scrape': {
                'description': 'Scrape and analyze Reddit user data',
                'body': {'username': 'string'},
                'example': {'username': 'Reasonable_Cod_8762'}
            },
            'GET /health': 'Health check endpoint',
            'GET /': 'This information'
        }
    })

if __name__ == '__main__':
    print("[INFO] Starting Reddit Scraper API server...")
    print("[INFO] Available endpoints:")
    print("  POST /scrape - Scrape and analyze user data")
    print("  GET /health - Health check")
    print("  GET / - Service information")
    app.run(host='0.0.0.0', port=5000, debug=True)
