"""
Downloads server for APK and other resources.
Serves files from the apk directory for easy mobile app distribution.
"""

import os
from flask import Flask, send_file, jsonify, render_template_string
from pathlib import Path

app = Flask(__name__)

# Get the directory where APK files are stored
APK_DIR = Path(__file__).parent / "apk"
APK_DIR.mkdir(parents=True, exist_ok=True)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Anomaah Rider App - Download</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 12px;
            padding: 40px;
            max-width: 500px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            text-align: center;
        }
        
        .logo {
            font-size: 48px;
            margin-bottom: 20px;
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        
        .download-section {
            margin: 30px 0;
        }
        
        .app-name {
            font-size: 18px;
            font-weight: 600;
            color: #333;
            margin-bottom: 15px;
        }
        
        .file-info {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            font-size: 13px;
            color: #666;
        }
        
        .file-size {
            font-weight: 600;
            color: #333;
        }
        
        .download-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 14px 32px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            transition: transform 0.2s, box-shadow 0.2s;
            width: 100%;
        }
        
        .download-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        
        .download-btn:active {
            transform: translateY(0);
        }
        
        .requirements {
            background: #f0f4ff;
            padding: 20px;
            border-radius: 8px;
            margin-top: 30px;
            text-align: left;
        }
        
        .requirements h3 {
            color: #333;
            margin-bottom: 10px;
            font-size: 14px;
        }
        
        .requirements ul {
            list-style: none;
            font-size: 13px;
            color: #666;
        }
        
        .requirements li {
            margin-bottom: 8px;
            display: flex;
            align-items: center;
        }
        
        .requirements li:before {
            content: "✓";
            color: #667eea;
            font-weight: bold;
            margin-right: 8px;
            font-size: 16px;
        }
        
        .no-files {
            color: #e74c3c;
            padding: 20px;
            background: #fadbd8;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        .instructions {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
            text-align: left;
            font-size: 13px;
            color: #333;
        }
        
        .instructions strong {
            display: block;
            margin-bottom: 8px;
        }
        
        .footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 12px;
            color: #999;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">📱</div>
        <h1>Anomaah Rider App</h1>
        <p class="subtitle">Download the rider application for Android</p>
        
        <div class="download-section">
            {% if files %}
                {% for file in files %}
                    <div class="app-name">{{ file['name'] }}</div>
                    <div class="file-info">
                        <div class="file-size">{{ file['size_mb'] }} MB</div>
                        <div>{{ file['version'] }}</div>
                    </div>
                    <a href="/download/{{ file['filename'] }}" class="download-btn">
                        📥 Download APK
                    </a>
                {% endfor %}
            {% else %}
                <div class="no-files">
                    ⚠️ No APK files available for download yet.
                </div>
            {% endif %}
        </div>
        
        <div class="requirements">
            <h3>📋 System Requirements</h3>
            <ul>
                <li>Android 8.0 or higher</li>
                <li>Minimum 50 MB free storage</li>
                <li>Active internet connection</li>
            </ul>
        </div>
        
        {% if files %}
        <div class="instructions">
            <strong>Installation Instructions:</strong>
            <ol style="margin-left: 20px;">
                <li>Download the APK file using the button above</li>
                <li>Open your file manager and locate the downloaded file</li>
                <li>Tap the file to install</li>
                <li>If prompted, allow installation from unknown sources</li>
                <li>Follow the on-screen prompts to complete installation</li>
            </ol>
        </div>
        {% endif %}
        
        <div class="footer">
            <p>Anomaah Delivery Platform © 2026</p>
        </div>
    </div>
</body>
</html>
"""


def get_apk_files():
    """Get list of available APK files with metadata."""
    files = []
    if APK_DIR.exists():
        for apk_file in sorted(APK_DIR.glob("*.apk"), reverse=True):
            try:
                size_bytes = apk_file.stat().st_size
                size_mb = round(size_bytes / (1024 * 1024), 2)
                files.append({
                    'filename': apk_file.name,
                    'name': apk_file.stem.replace('-', ' ').title(),
                    'size_mb': size_mb,
                    'version': 'Debug Build',
                    'path': apk_file
                })
            except Exception as e:
                app.logger.error(f"Error processing {apk_file}: {e}")
    return files


@app.route('/', methods=['GET'])
def index():
    """Display APK download page."""
    files = get_apk_files()
    return render_template_string(HTML_TEMPLATE, files=files)


@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    """Download APK file."""
    # Security: ensure filename only contains safe characters
    if not filename.endswith('.apk'):
        return jsonify({'error': 'Invalid file type'}), 400
    
    # Prevent directory traversal
    if '..' in filename or '/' in filename:
        return jsonify({'error': 'Invalid filename'}), 400
    
    file_path = APK_DIR / filename
    
    if not file_path.exists():
        return jsonify({'error': 'File not found'}), 404
    
    try:
        return send_file(
            file_path,
            mimetype='application/vnd.android.package-archive',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        app.logger.error(f"Error downloading {filename}: {e}")
        return jsonify({'error': 'Download failed'}), 500


@app.route('/api/files', methods=['GET'])
def api_files():
    """Get list of available files as JSON."""
    files = get_apk_files()
    return jsonify({
        'files': [
            {
                'filename': f['filename'],
                'name': f['name'],
                'size_mb': f['size_mb'],
                'version': f['version'],
                'download_url': f"/download/{f['filename']}"
            }
            for f in files
        ]
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8700))
    app.run(host='0.0.0.0', port=port, debug=False)
