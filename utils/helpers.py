import os
import secrets
from werkzeug.utils import secure_filename
from flask import current_app

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_uploaded_file(file):
    if file and file.filename and allowed_file(file.filename):
        # Generate a secure random filename
        filename = secure_filename(file.filename)
        if '.' in filename:
            file_ext = filename.rsplit('.', 1)[1].lower()
            random_name = secrets.token_hex(16) + '.' + file_ext
            
            # Ensure upload directory exists with proper permissions
            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            
            # Set directory permissions (especially for /image on Linux)
            if os.name == 'posix':  # Linux/Unix
                os.chmod(upload_folder, 0o755)
            
            file_path = os.path.join(upload_folder, random_name)
            file.save(file_path)
            
            # Set file permissions (readable by web server)
            if os.name == 'posix':  # Linux/Unix
                os.chmod(file_path, 0o644)
                
            return random_name
    return None

def format_datetime(dt):
    return dt.strftime('%Y-%m-%d %H:%M') if dt else ''

def get_user_status_text(status):
    status_map = {
        'pending': '待审核',
        'approved': '已通过',
        'rejected': '已拒绝'
    }
    return status_map.get(status, status)