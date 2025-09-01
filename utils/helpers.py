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
            
            # Ensure upload directory exists
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], random_name)
            file.save(file_path)
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