from flask import Flask, request, jsonify, render_template_string, send_file
from flask_cors import CORS
import csv
import os
import tempfile
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# CSV file configuration
if os.environ.get('RENDER'):  # Running on Render
    CSV_FILE = '/tmp/form_submissions.csv'
else:  # Local development or other platforms
    CSV_FILE = os.path.join(os.getcwd(), 'form_submissions.csv')

def initialize_csv_file():
    """Initialize CSV file with headers if it doesn't exist"""
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
        
        if not os.path.exists(CSV_FILE):
            # Create CSV with headers
            with open(CSV_FILE, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=[
                    'Timestamp',
                    'Full Name',
                    'Gender',
                    'Email',
                    'Mobile Number',
                    'Address',
                    'Instagram Handle',
                    'Education Level',
                    'Submission ID'
                ])
                writer.writeheader()
            print(f"Created new CSV file: {CSV_FILE}")
        else:
            print(f"CSV file already exists: {CSV_FILE}")
    except Exception as e:
        print(f"Error initializing CSV file: {str(e)}")
        raise

def save_to_csv(form_data):
    """Save form data to CSV file"""
    try:
        # Prepare new row data
        new_row = {
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Full Name': form_data.get('name', ''),
            'Gender': form_data.get('gender', ''),
            'Email': form_data.get('email', ''),
            'Mobile Number': form_data.get('contact', ''),
            'Address': form_data.get('address', ''),
            'Instagram Handle': form_data.get('instagram', ''),
            'Education Level': form_data.get('education', ''),
            'Submission ID': f"SUB_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        # Count existing records
        record_count = 0
        if os.path.exists(CSV_FILE):
            with open(CSV_FILE, 'r') as f:
                record_count = sum(1 for _ in f) - 1  # Subtract header row
        
        # Append new row to CSV
        with open(CSV_FILE, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=new_row.keys())
            writer.writerow(new_row)
        
        return True, f"Data saved successfully. Total records: {record_count + 1}"
    
    except Exception as e:
        return False, f"Error saving to CSV: {str(e)}"

@app.route('/')
def index():
    """Serve the main landing page"""
    try:
        with open('index.html', 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return "index.html file not found", 404

@app.route('/form.html')
def form_page():
    """Serve the form page with modified JavaScript"""
    try:
        with open('form.html', 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Replace the form submission JavaScript with server integration
        modified_content = content.replace(
            '// Store form data (in a real app, this would be sent to a server)\n          console.log(\'Form submitted:\', formData);',
            '''// Send form data to server
          fetch('/submit-form', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
          })
          .then(response => response.json())
          .then(data => {
            if (data.success) {
              console.log('Form submitted successfully:', data.message);
            } else {
              console.error('Form submission failed:', data.message);
            }
          })
          .catch(error => {
            console.error('Error submitting form:', error);
          });'''
        )
        
        return modified_content
    except FileNotFoundError:
        return "form.html file not found", 404

@app.route('/submit-form', methods=['POST'])
def submit_form():
    """Handle form submission and save to CSV"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['personalInfo', 'contactInfo']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Extract form data
        form_data = {
            'name': data['personalInfo'].get('name', ''),
            'gender': data['personalInfo'].get('gender', ''),
            'email': data['contactInfo'].get('email', ''),
            'contact': data['contactInfo'].get('contact', ''),
            'address': data['contactInfo'].get('address', ''),
            'instagram': data['socialEducational'].get('instagram', ''),
            'education': data['socialEducational'].get('education', '')
        }
        
        # Validate email and contact
        if not form_data['email'] or not form_data['contact']:
            return jsonify({
                'success': False,
                'message': 'Email and contact number are required'
            }), 400
        
        # Save to CSV
        success, message = save_to_csv(form_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'submission_id': f"SUB_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500

@app.route('/view-data')
def view_data():
    """View all submitted data in a table format"""
    try:
        if not os.path.exists(CSV_FILE):
            return jsonify({
                'success': False,
                'message': 'No data file found'
            })
        
        # Read CSV data
        rows = []
        with open(CSV_FILE, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Generate HTML table
        html_table = '<table class="table table-striped table-bordered" id="dataTable">'
        
        # Add headers
        if rows:
            html_table += '<thead><tr>'
            for header in rows[0].keys():
                html_table += f'<th>{header}</th>'
            html_table += '</tr></thead>'
        
        # Add rows
        html_table += '<tbody>'
        for row in rows:
            html_table += '<tr>'
            for value in row.values():
                html_table += f'<td>{value}</td>'
            html_table += '</tr>'
        html_table += '</tbody></table>'
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Form Submissions Data</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .table {{ width: 100%; border-collapse: collapse; }}
                .table th, .table td {{ padding: 8px; text-align: left; border: 1px solid #ddd; }}
                .table th {{ background-color: #f2f2f2; }}
                .stats {{ background: #e8f4f8; padding: 15px; margin-bottom: 20px; border-radius: 5px; }}
                .back-btn {{ display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <h1>Form Submissions Data</h1>
            <a href="/" class="back-btn">← Back to Form</a>
            <div class="stats">
                <h3>Statistics</h3>
                <p><strong>Total Submissions:</strong> {len(rows)}</p>
                <p><strong>Last Updated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            {html_table}
        </body>
        </html>
        """
        
        return html_template
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error reading data: {str(e)}'
        }), 500

@app.route('/download-csv')
def download_csv():
    """Download the CSV file"""
    try:
        if os.path.exists(CSV_FILE):
            return send_file(CSV_FILE, as_attachment=True)
        else:
            return jsonify({
                'success': False,
                'message': 'No data file found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error downloading file: {str(e)}'
        }), 500

@app.route('/stats')
def get_stats():
    """Get submission statistics"""
    try:
        if not os.path.exists(CSV_FILE):
            return jsonify({
                'success': True,
                'stats': {
                    'total_submissions': 0,
                    'gender_distribution': {},
                    'education_distribution': {}
                }
            })
        
        # Read CSV data and calculate stats
        gender_counts = {}
        education_counts = {}
        total_submissions = 0
        
        with open(CSV_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_submissions += 1
                gender = row.get('Gender', 'Unknown')
                education = row.get('Education Level', 'Unknown')
                
                gender_counts[gender] = gender_counts.get(gender, 0) + 1
                education_counts[education] = education_counts.get(education, 0) + 1
        
        # Get recent submissions (last 5)
        recent_submissions = []
        with open(CSV_FILE, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            recent_submissions = rows[-5:] if len(rows) > 5 else rows
        
        stats = {
            'total_submissions': total_submissions,
            'gender_distribution': gender_counts,
            'education_distribution': education_counts,
            'recent_submissions': recent_submissions
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error calculating stats: {str(e)}'
        }), 500

if __name__ == '__main__':
    # Initialize CSV file
    initialize_csv_file()
    
    print("Starting Flask server...")
    print(f"CSV file will be stored at: {CSV_FILE}")
    print("Available endpoints:")
    print("  - / : Main form")
    print("  - /view-data : View all data")
    print("  - /stats : Get statistics")
    print("  - /download-csv : Download CSV file")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)