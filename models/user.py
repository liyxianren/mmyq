from werkzeug.security import check_password_hash, generate_password_hash
from utils.database import execute_query

class User:
    def __init__(self, id=None, group_type=None, group_name=None, password_hash=None, status='pending', created_at=None):
        self.id = id
        self.group_type = group_type
        self.group_name = group_name
        self.password_hash = password_hash
        self.status = status
        self.created_at = created_at
    
    @staticmethod
    def create(group_type, group_name, password):
        password_hash = generate_password_hash(password)
        result = execute_query(
            'INSERT INTO users (group_type, group_name, password_hash) VALUES (%s, %s, %s)',
            (group_type, group_name, password_hash)
        )
        return result is not None and result > 0
    
    @staticmethod
    def find_by_group_name(group_name):
        result = execute_query(
            'SELECT id, group_type, group_name, password_hash, status, created_at FROM users WHERE group_name = %s',
            (group_name,),
            fetch='one'
        )
        if result:
            return User(*result)
        return None
    
    @staticmethod
    def find_by_id(user_id):
        result = execute_query(
            'SELECT id, group_type, group_name, password_hash, status, created_at FROM users WHERE id = %s',
            (user_id,),
            fetch='one'
        )
        if result:
            return User(*result)
        return None
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_approved(self):
        return self.status == 'approved'
    
    @staticmethod
    def get_pending_users():
        results = execute_query(
            'SELECT id, group_type, group_name, password_hash, status, created_at FROM users WHERE status = "pending" ORDER BY created_at DESC',
            fetch='all'
        )
        return [User(*row) for row in results] if results else []
    
    @staticmethod
    def approve_user(user_id):
        result = execute_query(
            'UPDATE users SET status = "approved" WHERE id = %s',
            (user_id,)
        )
        return result is not None and result > 0
    
    @staticmethod
    def reject_user(user_id):
        result = execute_query(
            'UPDATE users SET status = "rejected" WHERE id = %s',
            (user_id,)
        )
        return result is not None and result > 0
    
    @staticmethod
    def get_all_users():
        """Get all users regardless of status"""
        results = execute_query(
            'SELECT id, group_type, group_name, password_hash, status, created_at FROM users ORDER BY created_at DESC',
            fetch='all'
        )
        return [User(*row) for row in results] if results else []
    
    @staticmethod
    def get_users_by_status(status):
        """Get users by specific status"""
        results = execute_query(
            'SELECT id, group_type, group_name, password_hash, status, created_at FROM users WHERE status = %s ORDER BY created_at DESC',
            (status,),
            fetch='all'
        )
        return [User(*row) for row in results] if results else []
    
    @staticmethod
    def batch_approve_users(user_ids):
        """Batch approve multiple users"""
        if not user_ids:
            return False
        
        placeholders = ','.join(['%s'] * len(user_ids))
        result = execute_query(
            f'UPDATE users SET status = "approved" WHERE id IN ({placeholders})',
            tuple(user_ids)
        )
        return result is not None and result > 0
    
    @staticmethod
    def batch_reject_users(user_ids):
        """Batch reject multiple users"""
        if not user_ids:
            return False
        
        placeholders = ','.join(['%s'] * len(user_ids))
        result = execute_query(
            f'UPDATE users SET status = "rejected" WHERE id IN ({placeholders})',
            tuple(user_ids)
        )
        return result is not None and result > 0
    
    @staticmethod
    def delete_user(user_id):
        """Delete a user permanently"""
        result = execute_query(
            'DELETE FROM users WHERE id = %s',
            (user_id,)
        )
        return result is not None and result > 0
    
    @staticmethod
    def batch_delete_users(user_ids):
        """Batch delete multiple users"""
        if not user_ids:
            return False
        
        placeholders = ','.join(['%s'] * len(user_ids))
        result = execute_query(
            f'DELETE FROM users WHERE id IN ({placeholders})',
            tuple(user_ids)
        )
        return result is not None and result > 0
    
    @staticmethod
    def change_password(user_id, new_password):
        """Change user password"""
        password_hash = generate_password_hash(new_password)
        result = execute_query(
            'UPDATE users SET password_hash = %s WHERE id = %s',
            (password_hash, user_id)
        )
        return result is not None and result > 0
    
    def update_password(self, new_password):
        """Update current user's password"""
        success = User.change_password(self.id, new_password)
        if success:
            self.password_hash = generate_password_hash(new_password)
        return success
    
    @staticmethod
    def get_user_stats():
        """Get user statistics"""
        stats = {}
        
        # Count by status
        for status in ['pending', 'approved', 'rejected']:
            result = execute_query(
                'SELECT COUNT(*) FROM users WHERE status = %s',
                (status,),
                fetch='one'
            )
            stats[status] = result[0] if result else 0
        
        # Count by group type
        for group in ['一群', '二群']:
            result = execute_query(
                'SELECT COUNT(*) FROM users WHERE group_type = %s',
                (group,),
                fetch='one'
            )
            stats[f'group_{group}'] = result[0] if result else 0
        
        # Total count
        result = execute_query('SELECT COUNT(*) FROM users', fetch='one')
        stats['total'] = result[0] if result else 0
        
        return stats