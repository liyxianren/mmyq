from werkzeug.security import check_password_hash, generate_password_hash
from utils.database import execute_query

class Admin:
    def __init__(self, id=None, username=None, password_hash=None, created_at=None):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.created_at = created_at
    
    @staticmethod
    def find_by_username(username):
        result = execute_query(
            'SELECT id, username, password_hash, created_at FROM admins WHERE username = %s',
            (username,),
            fetch='one'
        )
        if result:
            return Admin(*result)
        return None
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def create(username, password):
        password_hash = generate_password_hash(password)
        result = execute_query(
            'INSERT INTO admins (username, password_hash) VALUES (%s, %s)',
            (username, password_hash)
        )
        return result is not None and result > 0