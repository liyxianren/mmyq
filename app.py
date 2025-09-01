import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime, date
from config import config
from utils.database import init_db, close_db, execute_query
from utils.helpers import save_uploaded_file, format_datetime, get_user_status_text
from models.user import User
from models.venue import VenueSubmission, Venue, VenueManager
from models.admin import Admin

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.getenv('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])
    
    # Initialize database
    with app.app_context():
        init_db()
    
    # Register teardown handler
    app.teardown_appcontext(close_db)
    
    # Template filters
    @app.template_filter('datetime')
    def datetime_filter(dt):
        return format_datetime(dt) if dt else ''
    
    @app.template_filter('user_status')
    def user_status_filter(status):
        return get_user_status_text(status)
    
    @app.template_filter('date_format')
    def date_format_filter(dt):
        if isinstance(dt, str):
            try:
                dt = datetime.strptime(dt, '%Y-%m-%d').date()
            except:
                return dt
        return dt.strftime('%Y年%m月%d日') if dt else ''
    
    # Routes
    @app.route('/')
    def index():
        if 'user_id' in session:
            # 验证session中的user_id是否有效
            from utils.database import execute_query
            user_exists = execute_query('SELECT id FROM users WHERE id = %s', (session['user_id'],), fetch='one')
            if user_exists:
                return redirect(url_for('venue_form'))
            else:
                # session无效，清除并跳转到登录页
                session.clear()
                flash('会话已过期，请重新登录', 'warning')
                return redirect(url_for('login'))
        return render_template('index.html')
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            group_type = request.form.get('group_type')
            group_name = request.form.get('group_name')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            # Validation
            if not all([group_type, group_name, password, confirm_password]):
                flash('所有字段都是必填的！', 'error')
                return render_template('register.html', groups=app.config['GROUPS'])
            
            if password != confirm_password:
                flash('密码确认不匹配！', 'error')
                return render_template('register.html', groups=app.config['GROUPS'])
            
            if len(password) < 6:
                flash('密码长度至少需要6位！', 'error')
                return render_template('register.html', groups=app.config['GROUPS'])
            
            # Check if group name exists
            existing_user = User.find_by_group_name(group_name)
            if existing_user:
                flash('该群名称已存在！', 'error')
                return render_template('register.html', groups=app.config['GROUPS'])
            
            # Create user
            if User.create(group_type, group_name, password):
                flash('注册成功！请等待管理员审核。', 'success')
                return redirect(url_for('login'))
            else:
                flash('注册失败，请重试。', 'error')
        
        return render_template('register.html', groups=app.config['GROUPS'])
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            group_name = request.form.get('group_name')
            password = request.form.get('password')
            
            if not group_name or not password:
                flash('请输入群名称和密码！', 'error')
                return render_template('login.html')
            
            user = User.find_by_group_name(group_name)
            
            if user and user.check_password(password):
                if user.is_approved():
                    session['user_id'] = user.id
                    session['group_name'] = user.group_name
                    session['group_type'] = user.group_type
                    flash(f'欢迎，{user.group_name}！', 'success')
                    return redirect(url_for('venue_form'))
                else:
                    status_text = get_user_status_text(user.status)
                    flash(f'账户状态：{status_text}', 'warning')
            else:
                flash('群名称或密码错误！', 'error')
        
        return render_template('login.html')
    
    @app.route('/logout')
    def logout():
        session.clear()
        flash('已退出登录。', 'info')
        return redirect(url_for('index'))
    
    @app.route('/venue-form', methods=['GET', 'POST'])
    def venue_form():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        # 验证session中的user_id是否有效
        from utils.database import execute_query
        user_exists = execute_query('SELECT id FROM users WHERE id = %s', (session['user_id'],), fetch='one')
        if not user_exists:
            session.clear()
            flash('会话已过期，请重新登录', 'warning')
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            venue_date = request.form.get('venue_date')
            registration_name = request.form.get('registration_name')
            
            
            # Get venues data - each venue can have different time slot and +1
            venues_data = []
            i = 0
            while True:
                venue_number = request.form.get(f'venues[{i}][number]')
                if not venue_number:
                    break
                    
                time_slot = request.form.get(f'venues[{i}][time_slot]')
                plus_one_name = request.form.get(f'venues[{i}][plus_one_name]')
                screenshot_file = request.files.get(f'venues[{i}][screenshot]')
                
                if venue_number and time_slot:
                    venues_data.append({
                        'number': int(venue_number),
                        'time_slot': time_slot,
                        'plus_one_name': plus_one_name if plus_one_name.strip() else None,
                        'screenshot_file': screenshot_file
                    })
                i += 1
            
            # Validation
            if not all([venue_date, registration_name]):
                flash('场地日期和报名名称是必填的！', 'error')
                return render_template('venue_form.html', 
                                     time_slots=app.config['TIME_SLOTS'],
                                     venue_numbers=app.config['VENUE_NUMBERS'])
            
            if not venues_data:
                flash('请至少添加一个场地！', 'error')
                return render_template('venue_form.html',
                                     time_slots=app.config['TIME_SLOTS'],
                                     venue_numbers=app.config['VENUE_NUMBERS'])
            
            try:
                venue_date_obj = datetime.strptime(venue_date, '%Y-%m-%d').date()
            except ValueError:
                flash('日期格式不正确！', 'error')
                return render_template('venue_form.html',
                                     time_slots=app.config['TIME_SLOTS'],
                                     venue_numbers=app.config['VENUE_NUMBERS'])
            
            # Check for conflicts
            for venue_data in venues_data:
                occupied = VenueManager.get_occupied_venue_numbers(venue_date_obj, venue_data['time_slot'])
                if venue_data['number'] in occupied:
                    flash(f'场地 {venue_data["number"]} 在 {dict(app.config["TIME_SLOTS"])[venue_data["time_slot"]]} 已被占用！', 'error')
                    return render_template('venue_form.html',
                                         time_slots=app.config['TIME_SLOTS'],
                                         venue_numbers=app.config['VENUE_NUMBERS'])
            
            # Check if providing 2+ venues for free submission
            is_free_submission = len(venues_data) >= app.config['FREE_VENUE_COUNT']
            
            # Check if it's after 10 PM (22:00)
            from datetime import datetime as dt
            current_time = dt.now().time()
            is_after_10pm = current_time.hour >= 22
            
            # If after 10 PM, submission needs approval
            approval_status = 'pending' if is_after_10pm else 'approved'
            
            # Create venue submission
            submission_id = VenueSubmission.create(
                session['user_id'], venue_date_obj, registration_name, is_free_submission, approval_status
            )
            
            if submission_id:
                # Add individual venues
                success_count = 0
                for venue_data in venues_data:
                    # Handle screenshot upload
                    screenshot_filename = None
                    if venue_data['screenshot_file'] and venue_data['screenshot_file'].filename:
                        screenshot_filename = save_uploaded_file(venue_data['screenshot_file'])
                    
                    if Venue.create(submission_id, venue_data['number'], venue_data['time_slot'], 
                                  venue_data['plus_one_name'], screenshot_filename):
                        success_count += 1
                
                if success_count > 0:
                    if approval_status == 'pending':
                        flash('场地信息提交成功！由于是晚上10点后提交，需要管理员审核后才会在统计页面显示。', 'warning')
                    else:
                        flash('场地信息提交成功！', 'success')
                    return redirect(url_for('venue_form'))
                else:
                    flash('场地添加失败，请重试。', 'error')
            else:
                flash('提交失败，请重试。', 'error')
        
        # Get today's date as default
        today = date.today().strftime('%Y-%m-%d')
        return render_template('venue_form.html',
                             time_slots=app.config['TIME_SLOTS'],
                             venue_numbers=app.config['VENUE_NUMBERS'],
                             default_date=today)
    
    
    @app.route('/get-available-venues')
    def get_available_venues():
        venue_date = request.args.get('date')
        time_slot = request.args.get('time_slot')
        
        if venue_date and time_slot:
            try:
                date_obj = datetime.strptime(venue_date, '%Y-%m-%d').date()
                available = VenueManager.get_available_venue_numbers(date_obj, time_slot)
                occupied = VenueManager.get_occupied_venue_numbers(date_obj, time_slot)
                return jsonify({
                    'available': available,
                    'occupied': occupied
                })
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400
        
        return jsonify({'available': list(range(1, 25)), 'occupied': []})
    
    # Admin routes
    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            admin = Admin.find_by_username(username)
            if admin and admin.check_password(password):
                session['admin_id'] = admin.id
                session['admin_username'] = admin.username
                flash(f'管理员登录成功！', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('用户名或密码错误！', 'error')
        
        return render_template('admin/login.html')
    
    @app.route('/admin/logout')
    def admin_logout():
        session.pop('admin_id', None)
        session.pop('admin_username', None)
        flash('已退出管理员登录。', 'info')
        return redirect(url_for('admin_login'))
    
    @app.route('/admin/dashboard')
    def admin_dashboard():
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        user_stats = User.get_user_stats()
        pending_users = User.get_pending_users()
        today = date.today()
        recent_submissions = VenueSubmission.get_all_active()[:10]  # Recent 10 submissions
        pending_submissions_count = len(VenueSubmission.get_pending_submissions())
        
        return render_template('admin/dashboard.html', 
                             user_stats=user_stats,
                             pending_users=pending_users, 
                             recent_submissions=recent_submissions,
                             pending_submissions_count=pending_submissions_count,
                             today=today,
                             time_slots=app.config['TIME_SLOTS'])
    
    @app.route('/admin/users')
    def admin_users():
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        status_filter = request.args.get('status', 'all')
        if status_filter == 'all':
            users = User.get_all_users()
        else:
            users = User.get_users_by_status(status_filter)
        
        user_stats = User.get_user_stats()
        return render_template('admin/users.html', 
                             users=users, 
                             user_stats=user_stats,
                             current_filter=status_filter)
    
    @app.route('/admin/user-actions', methods=['POST'])
    def admin_user_actions():
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        action = request.form.get('action')
        user_ids = request.form.getlist('user_ids[]')
        
        if not user_ids:
            flash('请选择要操作的用户！', 'error')
            return redirect(url_for('admin_users'))
        
        user_ids = [int(uid) for uid in user_ids]
        success = False
        
        if action == 'approve':
            success = User.batch_approve_users(user_ids)
            message = f'批准了 {len(user_ids)} 个用户'
        elif action == 'reject':
            success = User.batch_reject_users(user_ids)
            message = f'拒绝了 {len(user_ids)} 个用户'
        elif action == 'delete':
            success = User.batch_delete_users(user_ids)
            message = f'删除了 {len(user_ids)} 个用户'
        
        if success:
            flash(f'{message}！', 'success')
        else:
            flash('操作失败！', 'error')
        
        return redirect(url_for('admin_users'))
    
    @app.route('/admin/change-password/<int:user_id>', methods=['POST'])
    def admin_change_password(user_id):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        new_password = request.form.get('new_password')
        if not new_password or len(new_password) < 6:
            flash('密码长度至少需要6位！', 'error')
        else:
            user = User.find_by_id(user_id)
            if user and User.change_password(user_id, new_password):
                flash(f'已更改用户 {user.group_name} 的密码！', 'success')
            else:
                flash('密码修改失败！', 'error')
        
        return redirect(url_for('admin_users'))
    
    @app.route('/admin/approve-user/<int:user_id>')
    def approve_user(user_id):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        success = User.batch_approve_users([user_id])
        if success:
            flash('用户已批准！', 'success')
        else:
            flash('批准失败！', 'error')
        
        return redirect(url_for('admin_users'))
    
    @app.route('/admin/reject-user/<int:user_id>')
    def reject_user(user_id):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        success = User.batch_reject_users([user_id])
        if success:
            flash('用户已拒绝！', 'success')
        else:
            flash('拒绝失败！', 'error')
        
        return redirect(url_for('admin_users'))
    
    @app.route('/admin/venues-summary')
    def admin_venues_summary():
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        # Get date from query parameter, default to today
        selected_date = request.args.get('date')
        if selected_date:
            try:
                date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
            except ValueError:
                date_obj = date.today()
        else:
            date_obj = date.today()
        
        summary = VenueManager.get_summary_by_date(date_obj)
        pending_count = len(VenueSubmission.get_pending_submissions())
        
        return render_template('admin/venues_summary.html', 
                             summary=summary, 
                             selected_date=date_obj,
                             pending_count=pending_count,
                             time_slots=app.config['TIME_SLOTS'])
    
    @app.route('/admin/venue-details/<int:submission_id>')
    def admin_venue_details(submission_id):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        venue_submission = VenueSubmission.get_by_id(submission_id)
        if not venue_submission:
            flash('场地提交信息不存在！', 'error')
            return redirect(url_for('admin_venues_summary'))
        
        return render_template('admin/venue_details.html', 
                             venue_submission=venue_submission,
                             time_slots=app.config['TIME_SLOTS'])
    
    @app.route('/admin/delete-submission/<int:submission_id>')
    def admin_delete_submission(submission_id):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        if VenueSubmission.delete_submission(submission_id):
            flash('场地提交已删除！', 'success')
        else:
            flash('删除失败！', 'error')
        
        return redirect(url_for('admin_venues_summary'))
    
    @app.route('/admin/pending-submissions')
    def admin_pending_submissions():
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        pending_submissions = VenueSubmission.get_pending_submissions()
        return render_template('admin/pending_submissions.html', 
                             pending_submissions=pending_submissions,
                             time_slots=app.config['TIME_SLOTS'])
    
    @app.route('/admin/approve-submission/<int:submission_id>')
    def admin_approve_submission(submission_id):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        if VenueSubmission.approve_submission(submission_id):
            flash('场地提交已审核通过！', 'success')
        else:
            flash('审核失败！', 'error')
        
        return redirect(url_for('admin_pending_submissions'))
    
    @app.route('/admin/delete-venue/<int:venue_id>', methods=['POST'])
    def admin_delete_venue(venue_id):
        if 'admin_id' not in session:
            return jsonify({'success': False, 'message': '未授权'}), 401
        
        if Venue.delete_venue(venue_id):
            return jsonify({'success': True, 'message': '场地已删除！'})
        else:
            return jsonify({'success': False, 'message': '删除失败！'}), 500
    
    @app.route('/admin/venue-exchange')
    def admin_venue_exchange():
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        # 获取所有活跃的场地提交，按日期和时间段分组
        query = '''
            SELECT vs.id, vs.venue_date, vs.registration_name, vs.is_free_submission,
                   u.group_name, u.group_type, u.id as user_id,
                   GROUP_CONCAT(CONCAT(v.id, ':', v.venue_number, ':', v.time_slot, ':', IFNULL(v.plus_one_name, '')) SEPARATOR '|') as venues_data
            FROM venue_submissions vs
            JOIN users u ON vs.user_id = u.id
            JOIN venues v ON vs.id = v.submission_id
            WHERE vs.status = 'active' AND vs.approval_status = 'approved'
            GROUP BY vs.id
            ORDER BY vs.venue_date DESC, vs.upload_time DESC
            LIMIT 50
        '''
        submissions_data = execute_query(query, fetch=True)
        
        # 解析场地数据
        submissions = []
        for row in submissions_data or []:
            venues = []
            if row[7]:  # venues_data
                for venue_data in row[7].split('|'):
                    parts = venue_data.split(':')
                    if len(parts) >= 3:
                        venues.append({
                            'id': int(parts[0]),
                            'venue_number': int(parts[1]),
                            'time_slot': parts[2],
                            'plus_one_name': parts[3] if len(parts) > 3 and parts[3] else None
                        })
            
            submissions.append({
                'id': row[0],
                'venue_date': row[1],
                'registration_name': row[2],
                'is_free_submission': row[3],
                'group_name': row[4],
                'group_type': row[5],
                'user_id': row[6],
                'venues': venues
            })
        
        return render_template('admin/venue_exchange.html',
                             submissions=submissions,
                             time_slots=app.config['TIME_SLOTS'])
    
    @app.route('/admin/migrate-venue', methods=['POST'])
    def admin_migrate_venue():
        if 'admin_id' not in session:
            return jsonify({'success': False, 'message': '未授权'}), 401
        
        data = request.get_json()
        venue_id = data.get('venue_id')
        new_venue_number = data.get('new_venue_number')
        new_time_slot = data.get('new_time_slot')
        new_venue_date = data.get('new_venue_date')
        
        if not venue_id or not new_venue_number or not new_time_slot or not new_venue_date:
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400
        
        # 验证场地号范围
        try:
            new_venue_number = int(new_venue_number)
            if new_venue_number < 1 or new_venue_number > 24:
                return jsonify({'success': False, 'message': '场地号必须在1-24之间'}), 400
        except ValueError:
            return jsonify({'success': False, 'message': '场地号必须是数字'}), 400
        
        # 验证时间段
        if new_time_slot not in dict(app.config['TIME_SLOTS']):
            return jsonify({'success': False, 'message': '无效的时间段'}), 400
        
        # 验证日期格式
        try:
            from datetime import datetime
            venue_date_obj = datetime.strptime(new_venue_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': '无效的日期格式'}), 400
        
        # 获取原场地信息
        original_venue = execute_query('''
            SELECT v.id, v.venue_number, v.time_slot, v.plus_one_name, v.submission_id,
                   vs.venue_date, vs.registration_name, u.group_name, u.group_type
            FROM venues v
            JOIN venue_submissions vs ON v.submission_id = vs.id
            JOIN users u ON vs.user_id = u.id
            WHERE v.id = %s
        ''', (venue_id,), fetch='one')
        
        if not original_venue:
            return jsonify({'success': False, 'message': '场地不存在'}), 404
        
        # 检查目标位置是否已被占用
        conflict = execute_query('''
            SELECT v.id FROM venues v
            JOIN venue_submissions vs ON v.submission_id = vs.id
            WHERE v.venue_number = %s AND v.time_slot = %s AND vs.venue_date = %s 
            AND v.id != %s AND vs.status = 'active'
        ''', (new_venue_number, new_time_slot, new_venue_date, venue_id), fetch='one')
        
        if conflict:
            return jsonify({
                'success': False, 
                'message': f'目标位置已被占用：场地{new_venue_number}在{dict(app.config["TIME_SLOTS"])[new_time_slot]}时段({new_venue_date})已有预订'
            }), 409
        
        # 执行场地迁移
        try:
            # 如果迁移到不同日期，需要更新或创建新的submission
            if str(venue_date_obj) != str(original_venue[5]):
                # 需要创建新的submission或找到同日期的submission
                existing_submission = execute_query('''
                    SELECT vs.id FROM venue_submissions vs
                    JOIN users u ON vs.user_id = u.id
                    WHERE vs.venue_date = %s AND vs.registration_name = %s 
                    AND u.group_name = %s AND vs.status = 'active'
                ''', (new_venue_date, original_venue[6], original_venue[7]), fetch='one')
                
                if existing_submission:
                    # 找到同用户同日期的submission，更新venue的submission_id
                    new_submission_id = existing_submission[0]
                else:
                    # 创建新的submission
                    user_id = execute_query('''
                        SELECT u.id FROM users u
                        JOIN venue_submissions vs ON vs.user_id = u.id
                        WHERE vs.id = %s
                    ''', (original_venue[4],), fetch='one')[0]
                    
                    execute_query('''
                        INSERT INTO venue_submissions (user_id, venue_date, registration_name, is_free_submission, status, approval_status)
                        SELECT user_id, %s, registration_name, is_free_submission, 'active', 'approved'
                        FROM venue_submissions WHERE id = %s
                    ''', (new_venue_date, original_venue[4]))
                    
                    new_submission_id = execute_query('SELECT LAST_INSERT_ID()', fetch='one')[0]
                
                # 更新场地信息
                execute_query('''
                    UPDATE venues SET venue_number = %s, time_slot = %s, submission_id = %s WHERE id = %s
                ''', (new_venue_number, new_time_slot, new_submission_id, venue_id))
            else:
                # 同日期迁移，只更新场地号和时间段
                execute_query('''
                    UPDATE venues SET venue_number = %s, time_slot = %s WHERE id = %s
                ''', (new_venue_number, new_time_slot, venue_id))
            
            return jsonify({
                'success': True, 
                'message': f'场地迁移成功！{original_venue[7]}({original_venue[6]})的场地从{original_venue[1]}号({dict(app.config["TIME_SLOTS"])[original_venue[2]]}, {original_venue[5]})迁移到{new_venue_number}号({dict(app.config["TIME_SLOTS"])[new_time_slot]}, {new_venue_date})'
            })
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'迁移失败：{str(e)}'}), 500
    
    @app.route('/admin/get-venue-info/<int:venue_id>')
    def admin_get_venue_info(venue_id):
        if 'admin_id' not in session:
            return jsonify({'success': False, 'message': '未授权'}), 401
        
        venue_info = execute_query('''
            SELECT v.id, v.venue_number, v.time_slot, v.plus_one_name,
                   vs.venue_date, vs.registration_name, u.group_name, u.group_type, u.id as user_id
            FROM venues v
            JOIN venue_submissions vs ON v.submission_id = vs.id
            JOIN users u ON vs.user_id = u.id
            WHERE v.id = %s
        ''', (venue_id,), fetch='one')
        
        if not venue_info:
            return jsonify({'success': False, 'message': '场地不存在'}), 404
        
        return jsonify({
            'success': True,
            'venue': {
                'id': venue_info[0],
                'venue_number': venue_info[1],
                'time_slot': venue_info[2],
                'time_slot_name': dict(app.config['TIME_SLOTS']).get(venue_info[2], '未知'),
                'plus_one_name': venue_info[3],
                'venue_date': venue_info[4].strftime('%Y-%m-%d') if venue_info[4] else '',
                'registration_name': venue_info[5],
                'group_name': venue_info[6],
                'group_type': venue_info[7],
                'user_id': venue_info[8]
            }
        })
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)