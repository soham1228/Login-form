from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import csv
import os
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Configure paths
BASE_DIR = Path(__file__).parent
CSV_FILE = BASE_DIR / 'data' / 'form_submissions.csv'

def init_app():
    """Initialize application resources"""
    # Create data directory if needed
    (BASE_DIR / 'data').mkdir(exist_ok=True)
    
    # Initialize CSV file if needed
    if not CSV_FILE.exists():
        CSV_FILE.parent.mkdir(exist_ok=True)
        with open(CSV_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'name', 'gender', 'email', 
                'phone', 'address', 'instagram', 'education'
            ])
            writer.writeheader()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/api/submit', methods=['POST'])
def submit():
    try:
        data = request.json
        
        # Validate required fields
        required = ['name', 'email', 'phone']
        if not all(field in data for field in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Save to CSV
        with open(CSV_FILE, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'name', 'gender', 'email', 
                'phone', 'address', 'instagram', 'education'
            ])
            writer.writerow({
                'timestamp': datetime.now().isoformat(),
                'name': data.get('name'),
                'gender': data.get('gender'),
                'email': data.get('email'),
                'phone': data.get('phone'),
                'address': data.get('address'),
                'instagram': data.get('instagram'),
                'education': data.get('education')
            })
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data')
def get_data():
    try:
        with open(CSV_FILE, 'r') as f:
            reader = csv.DictReader(f)
            return jsonify({'data': list(reader)})
    except FileNotFoundError:
        return jsonify({'data': []})

@app.route('/api/export')
def export_data():
    return send_file(
        CSV_FILE,
        as_attachment=True,
        download_name='form_submissions.csv',
        mimetype='text/csv'
    )

if __name__ == '__main__':
    init_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)