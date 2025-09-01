from utils.database import execute_query
from datetime import datetime, date

class VenueSubmission:
    """场地提交（一次提交可包含多个不同时间段的场地）"""
    def __init__(self, id=None, user_id=None, venue_date=None, registration_name=None,
                 is_free_submission=False, upload_time=None, status='active', approval_status='approved'):
        self.id = id
        self.user_id = user_id
        self.venue_date = venue_date
        self.registration_name = registration_name
        self.is_free_submission = is_free_submission
        self.upload_time = upload_time
        self.status = status
        self.approval_status = approval_status
        self.venues = []  # Will be populated with individual venues

    @staticmethod
    def create(user_id, venue_date, registration_name, is_free_submission=False, approval_status='approved'):
        result = execute_query('''
            INSERT INTO venue_submissions (user_id, venue_date, registration_name, is_free_submission, approval_status)
            VALUES (%s, %s, %s, %s, %s)
        ''', (user_id, venue_date, registration_name, is_free_submission, approval_status))
        
        if result and result > 0:
            # Get the last inserted submission ID
            last_id = execute_query('SELECT LAST_INSERT_ID()', fetch='one')
            return last_id[0] if last_id else None
        return None

    @staticmethod
    def get_by_user_id(user_id):
        results = execute_query('''
            SELECT id, user_id, venue_date, registration_name, is_free_submission, upload_time, status, approval_status
            FROM venue_submissions
            WHERE user_id = %s AND status = "active"
            ORDER BY venue_date DESC, upload_time DESC
        ''', (user_id,), fetch='all')
        
        submissions = []
        if results:
            for row in results:
                submission = VenueSubmission(*row)
                # Load venues for this submission
                submission.venues = Venue.get_by_submission_id(submission.id)
                submissions.append(submission)
        return submissions

    @staticmethod
    def get_all_active(venue_date=None):
        query = '''
            SELECT vs.id, vs.user_id, vs.venue_date, vs.registration_name, 
                   vs.is_free_submission, vs.upload_time, vs.status, vs.approval_status,
                   u.group_name, u.group_type
            FROM venue_submissions vs
            JOIN users u ON vs.user_id = u.id
            WHERE vs.status = "active" AND u.status = "approved"
        '''
        params = []
        
        if venue_date:
            query += ' AND vs.venue_date = %s'
            params.append(venue_date)
        
        query += ' ORDER BY vs.venue_date DESC, vs.upload_time DESC'
        
        results = execute_query(query, params, fetch='all')
        
        submissions = []
        if results:
            for row in results:
                submission = VenueSubmission(*row[:8])
                submission.group_name = row[8]
                submission.group_type = row[9]
                # Load venues for this submission
                submission.venues = Venue.get_by_submission_id(submission.id)
                submissions.append(submission)
        return submissions

    @staticmethod
    def get_by_id(submission_id):
        result = execute_query('''
            SELECT vs.id, vs.user_id, vs.venue_date, vs.registration_name, 
                   vs.is_free_submission, vs.upload_time, vs.status, vs.approval_status,
                   u.group_name, u.group_type
            FROM venue_submissions vs
            JOIN users u ON vs.user_id = u.id
            WHERE vs.id = %s
        ''', (submission_id,), fetch='one')
        
        if result:
            submission = VenueSubmission(*result[:8])
            submission.group_name = result[8]
            submission.group_type = result[9]
            submission.venues = Venue.get_by_submission_id(submission.id)
            return submission
        return None

    @staticmethod
    def delete_submission(submission_id):
        result = execute_query(
            'UPDATE venue_submissions SET status = "deleted" WHERE id = %s',
            (submission_id,)
        )
        return result is not None and result > 0
    
    @staticmethod
    def approve_submission(submission_id):
        result = execute_query(
            'UPDATE venue_submissions SET approval_status = "approved" WHERE id = %s',
            (submission_id,)
        )
        return result is not None and result > 0
    
    @staticmethod
    def get_pending_submissions():
        results = execute_query('''
            SELECT vs.id, vs.user_id, vs.venue_date, vs.registration_name, 
                   vs.is_free_submission, vs.upload_time, vs.status, vs.approval_status,
                   u.group_name, u.group_type
            FROM venue_submissions vs
            JOIN users u ON vs.user_id = u.id
            WHERE vs.status = "active" AND vs.approval_status = "pending" AND u.status = "approved"
            ORDER BY vs.upload_time ASC
        ''', fetch='all')
        
        submissions = []
        if results:
            for row in results:
                submission = VenueSubmission(*row[:8])
                submission.group_name = row[8]
                submission.group_type = row[9]
                submission.venues = Venue.get_by_submission_id(submission.id)
                submissions.append(submission)
        return submissions

    def get_venue_count(self):
        return len(self.venues)

    def is_multi_venue(self):
        return self.get_venue_count() > 1
        
    def get_time_slots(self):
        """获取此次提交涉及的所有时间段"""
        return list(set([venue.time_slot for venue in self.venues]))
        
    def get_total_plus_ones(self):
        """获取总共的+1人数"""
        return len([venue for venue in self.venues if venue.plus_one_name])

class Venue:
    """单个场地（包含场地号、时间段、+1等信息）"""
    def __init__(self, id=None, submission_id=None, venue_number=None, time_slot=None,
                 plus_one_name=None, venue_screenshot=None):
        self.id = id
        self.submission_id = submission_id
        self.venue_number = venue_number
        self.time_slot = time_slot
        self.plus_one_name = plus_one_name
        self.venue_screenshot = venue_screenshot

    @staticmethod
    def create(submission_id, venue_number, time_slot, plus_one_name=None, venue_screenshot=None):
        result = execute_query('''
            INSERT INTO venues (submission_id, venue_number, time_slot, plus_one_name, venue_screenshot)
            VALUES (%s, %s, %s, %s, %s)
        ''', (submission_id, venue_number, time_slot, plus_one_name, venue_screenshot))
        return result is not None and result > 0

    @staticmethod
    def get_by_submission_id(submission_id):
        results = execute_query('''
            SELECT id, submission_id, venue_number, time_slot, plus_one_name, venue_screenshot
            FROM venues WHERE submission_id = %s
            ORDER BY time_slot ASC, venue_number ASC
        ''', (submission_id,), fetch='all')
        return [Venue(*row) for row in results] if results else []

    @staticmethod
    def delete_venue(venue_id):
        result = execute_query('DELETE FROM venues WHERE id = %s', (venue_id,))
        return result is not None and result > 0
        
    @staticmethod
    def get_occupied_venues(venue_date, time_slot):
        """获取指定日期和时间段已被占用的场地号码"""
        results = execute_query('''
            SELECT v.venue_number
            FROM venues v
            JOIN venue_submissions vs ON v.submission_id = vs.id
            JOIN users u ON vs.user_id = u.id
            WHERE vs.venue_date = %s AND v.time_slot = %s 
                  AND vs.status = "active" AND u.status = "approved"
        ''', (venue_date, time_slot), fetch='all')
        
        return [row[0] for row in results] if results else []

# Utility functions for venue management
class VenueManager:
    @staticmethod
    def get_occupied_venue_numbers(venue_date, time_slot):
        """Get list of occupied venue numbers for a date/time slot"""
        return Venue.get_occupied_venues(venue_date, time_slot)

    @staticmethod
    def get_available_venue_numbers(venue_date, time_slot, max_venues=24):
        """Get list of available venue numbers"""
        occupied = VenueManager.get_occupied_venue_numbers(venue_date, time_slot)
        available = [i for i in range(1, max_venues + 1) if i not in occupied]
        return available

    @staticmethod
    def get_summary_by_date(venue_date):
        """Get venue summary organized by time slots for a specific date"""
        from flask import current_app
        time_slots = current_app.config['TIME_SLOTS']
        
        summary = {}
        for slot_key, slot_name in time_slots:
            # Get all venues for this time slot and date
            results = execute_query('''
                SELECT v.id, v.submission_id, v.venue_number, v.time_slot, 
                       v.plus_one_name, v.venue_screenshot,
                       vs.registration_name, vs.is_free_submission,
                       u.group_name, u.group_type
                FROM venues v
                JOIN venue_submissions vs ON v.submission_id = vs.id
                JOIN users u ON vs.user_id = u.id
                WHERE vs.venue_date = %s AND v.time_slot = %s 
                      AND vs.status = "active" AND vs.approval_status = "approved" AND u.status = "approved"
                ORDER BY v.venue_number ASC
            ''', (venue_date, slot_key), fetch='all')
            
            venues_list = []
            if results:
                for row in results:
                    venues_list.append({
                        'venue_id': row[0],
                        'submission_id': row[1],
                        'venue_number': row[2],
                        'time_slot': row[3],
                        'plus_one_name': row[4],
                        'screenshot': row[5],
                        'registration_name': row[6],
                        'is_free_submission': row[7],
                        'group_name': row[8],
                        'group_type': row[9]
                    })
            
            summary[slot_key] = {
                'name': slot_name,
                'venues': venues_list,
                'count': len(venues_list)
            }
        
        return summary
        
    @staticmethod
    def get_all_venues_by_date(venue_date):
        """Get all venues for a specific date (for admin overview)"""
        results = execute_query('''
            SELECT v.id, v.submission_id, v.venue_number, v.time_slot, 
                   v.plus_one_name, v.venue_screenshot,
                   vs.registration_name, vs.is_free_submission, vs.upload_time,
                   u.group_name, u.group_type
            FROM venues v
            JOIN venue_submissions vs ON v.submission_id = vs.id
            JOIN users u ON vs.user_id = u.id
            WHERE vs.venue_date = %s AND vs.status = "active" AND u.status = "approved"
            ORDER BY v.time_slot ASC, v.venue_number ASC
        ''', (venue_date,), fetch='all')
        
        venues = []
        if results:
            for row in results:
                venue_data = {
                    'venue_id': row[0],
                    'submission_id': row[1],
                    'venue_number': row[2],
                    'time_slot': row[3],
                    'plus_one_name': row[4],
                    'screenshot': row[5],
                    'registration_name': row[6],
                    'is_free_submission': row[7],
                    'upload_time': row[8],
                    'group_name': row[9],
                    'group_type': row[10]
                }
                venues.append(venue_data)
        
        return venues