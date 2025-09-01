import pymysql
from flask import current_app, g
import sys

def get_db():
    if 'db' not in g:
        try:
            g.db = pymysql.connect(
                host=current_app.config['MYSQL_HOST'],
                user=current_app.config['MYSQL_USER'],
                password=current_app.config['MYSQL_PASSWORD'],
                database=current_app.config['MYSQL_DB'],
                port=current_app.config['MYSQL_PORT'],
                charset='utf8mb4',
                autocommit=False,
                connect_timeout=5,
                read_timeout=10,
                write_timeout=10
            )
        except pymysql.Error as e:
            print(f"Database connection error: {e}", file=sys.stderr)
            return None
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    if db is None:
        return False
    
    cursor = db.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            group_type VARCHAR(10) NOT NULL,
            group_name VARCHAR(100) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')
    
    # Create venue_submissions table (for submission groups)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS venue_submissions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            venue_date DATE NOT NULL,
            registration_name VARCHAR(100) NOT NULL,
            is_free_submission BOOLEAN DEFAULT FALSE,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status ENUM('active', 'deleted') DEFAULT 'active',
            approval_status ENUM('approved', 'pending') DEFAULT 'approved',
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')
    
    # Add approval_status column if it doesn't exist (for existing databases)
    try:
        cursor.execute('''
            ALTER TABLE venue_submissions 
            ADD COLUMN approval_status ENUM('approved', 'pending') DEFAULT 'approved'
        ''')
    except pymysql.Error:
        # Column already exists or other error, ignore
        pass
    
    # Create venues table (individual venues within a submission)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS venues (
            id INT AUTO_INCREMENT PRIMARY KEY,
            submission_id INT NOT NULL,
            venue_number INT NOT NULL,
            time_slot VARCHAR(20) NOT NULL,
            plus_one_name VARCHAR(100),
            venue_screenshot VARCHAR(255),
            FOREIGN KEY (submission_id) REFERENCES venue_submissions(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')
    
    # Create admins table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')
    
    # Insert default admin users
    # Password hash for 'mmyq123' using werkzeug
    from werkzeug.security import generate_password_hash
    admin_password = generate_password_hash('mmyq123')
    
    admin_users = [
        ('admin', generate_password_hash('admin123')),  # 保留原有的admin账号
        ('ww', admin_password),
        ('daxia', admin_password), 
        ('xiaoxiong', admin_password),
        ('molly', admin_password),
        ('limou', admin_password)
    ]
    
    for username, password_hash in admin_users:
        cursor.execute('''
            INSERT IGNORE INTO admins (username, password_hash)
            VALUES (%s, %s)
        ''', (username, password_hash))
    
    db.commit()
    cursor.close()
    return True

def execute_query(query, params=None, fetch=False):
    db = get_db()
    if db is None:
        return None
    
    cursor = db.cursor()
    try:
        cursor.execute(query, params or ())
        if fetch:
            if fetch == 'one':
                result = cursor.fetchone()
            else:
                result = cursor.fetchall()
        else:
            result = cursor.rowcount
            db.commit()
        return result
    except pymysql.Error as e:
        print(f"Database query error: {e}", file=sys.stderr)
        db.rollback()
        return None
    finally:
        cursor.close()