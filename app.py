from flask import Flask, request, jsonify, render_template_string, send_file
from flask_cors import CORS
import pandas as pd
import os
import tempfile
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Excel file configuration - Use proper temp directory for cross-platform compatibility
# For local development, use current directory; for production, use temp directory
if os.environ.get('RENDER'):  # Running on Render
    EXCEL_FILE = '/tmp/form_submissions.xlsx'
else:  # Local development or other platforms
    # Use current directory for local development
    EXCEL_FILE = os.path.join(os.getcwd(), 'form_submissions.xlsx')
    
    # Alternative: Use system temp directory
    # EXCEL_FILE = os.path.join(tempfile.gettempdir(), 'form_submissions.xlsx')

def initialize_excel_file():
    """Initialize Excel file with headers if it doesn't exist"""
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(EXCEL_FILE), exist_ok=True)
        
        if not os.path.exists(EXCEL_FILE):
            # Create DataFrame with column headers
            df = pd.DataFrame(columns=[
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
            df.to_excel(EXCEL_FILE, index=False)
            print(f"Created new Excel file: {EXCEL_FILE}")
        else:
            print(f"Excel file already exists: {EXCEL_FILE}")
    except Exception as e:
        print(f"Error initializing Excel file: {str(e)}")
        raise

def save_to_excel(form_data):
    """Save form data to Excel file"""
    try:
        # Read existing data
        try:
            df = pd.read_excel(EXCEL_FILE)
        except FileNotFoundError:
            initialize_excel_file()
            df = pd.read_excel(EXCEL_FILE)
        
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
        
        # Add new row to DataFrame
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        
        # Save to Excel
        df.to_excel(EXCEL_FILE, index=False)
        
        return True, f"Data saved successfully. Total records: {len(df)}"
    
    except Exception as e:
        return False, f"Error saving to Excel: {str(e)}"

@app.route('/')
def index():
    """Serve the main landing page"""
    # Read and serve the index.html content
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
    """Handle form submission and save to Excel"""
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
        
        # Save to Excel
        success, message = save_to_excel(form_data)
        
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
        if not os.path.exists(EXCEL_FILE):
            return jsonify({
                'success': False,
                'message': 'No data file found'
            })
        
        df = pd.read_excel(EXCEL_FILE)
        
        # Convert DataFrame to HTML table
        html_table = df.to_html(
            classes='table table-striped table-bordered',
            table_id='dataTable',
            escape=False,
            index=False
        )
        
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
                <p><strong>Total Submissions:</strong> {len(df)}</p>
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

@app.route('/download-excel')
def download_excel():
    """Download the Excel file"""
    try:
        if os.path.exists(EXCEL_FILE):
            return send_file(EXCEL_FILE, as_attachment=True)
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
        if not os.path.exists(EXCEL_FILE):
            return jsonify({
                'success': True,
                'stats': {
                    'total_submissions': 0,
                    'gender_distribution': {},
                    'education_distribution': {}
                }
            })
        
        df = pd.read_excel(EXCEL_FILE)
        
        # Calculate statistics
        stats = {
            'total_submissions': len(df),
            'gender_distribution': df['Gender'].value_counts().to_dict(),
            'education_distribution': df['Education Level'].value_counts().to_dict(),
            'recent_submissions': df.tail(5).to_dict('records')
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
    # Initialize Excel file
    initialize_excel_file()
    
    print("Starting Flask server...")
    print(f"Excel file will be stored at: {EXCEL_FILE}")
    print("Available endpoints:")
    print("  - / : Main form")
    print("  - /view-data : View all data")
    print("  - /stats : Get statistics")
    print("  - /download-excel : Download Excel file")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)