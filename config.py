import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'mmyq-venue-booking-system-2024'
    
    # MySQL Database Configuration
    MYSQL_HOST = 'hkg1.clusters.zeabur.com'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'ToN9sfU57neVx8lm0OzAFP43r2Kp1dZ6'
    MYSQL_DB = 'zeabur'
    MYSQL_PORT = 32360
    
    # File Upload Configuration
    # 在云端使用 /image 持久化存储，本地开发时使用 static/uploads
    # 通过检查环境变量或特定条件来判断是否在云端
    is_cloud = os.environ.get('PORT') or os.path.exists('/app')  # Zeabur cloud indicators
    UPLOAD_FOLDER = '/image' if is_cloud and os.path.exists('/image') else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Application Settings
    GROUPS = ['一群', '二群']
    
    # Venue Configuration  
    TIME_SLOTS = [
        ('12:00-13:00', '12点-13点'),
        ('13:00-14:00', '13点-14点'),
        ('14:00-15:00', '14点-15点')
    ]
    
    VENUE_NUMBERS = list(range(1, 25))  # 1-24场地
    
    # Multi-venue Settings
    FREE_VENUE_COUNT = 2  # 贡献2个场地免单
    
class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}