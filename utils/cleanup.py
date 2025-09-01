import os
import subprocess
from datetime import datetime, timedelta
from flask import current_app
from utils.database import execute_query

class DataCleanup:
    """数据和文件清理工具"""
    
    @staticmethod
    def get_expired_submissions(days_old=3):
        """获取过期的场地提交记录（默认3天前的数据）"""
        from datetime import date
        cutoff_date = date.today() - timedelta(days=days_old)
        
        query = '''
            SELECT vs.id, vs.venue_date, vs.registration_name, 
                   GROUP_CONCAT(v.venue_screenshot) as screenshots
            FROM venue_submissions vs
            LEFT JOIN venues v ON vs.id = v.submission_id
            WHERE vs.venue_date <= %s
            GROUP BY vs.id
            ORDER BY vs.venue_date DESC
        '''
        
        results = execute_query(query, (cutoff_date,), fetch=True)
        
        expired_data = []
        if results:
            for row in results:
                screenshots = []
                if row[3]:  # screenshots field
                    screenshots = [s.strip() for s in row[3].split(',') if s.strip()]
                
                expired_data.append({
                    'submission_id': row[0],
                    'venue_date': row[1], 
                    'registration_name': row[2],
                    'screenshots': screenshots
                })
        
        return expired_data
    
    @staticmethod
    def delete_image_files(screenshot_filenames):
        """删除图片文件 - 使用rm -rf命令"""
        if not screenshot_filenames:
            return {'success': True, 'deleted': 0, 'errors': []}
        
        upload_folder = current_app.config['UPLOAD_FOLDER']
        deleted_count = 0
        errors = []
        
        for filename in screenshot_filenames:
            if filename and filename.strip():
                file_path = os.path.join(upload_folder, filename.strip())
                try:
                    # 检查文件是否存在
                    if os.path.exists(file_path):
                        # 使用rm -rf删除文件（Linux环境）
                        if os.name == 'posix':  # Linux/Unix系统
                            result = subprocess.run(['rm', '-rf', file_path], 
                                                   capture_output=True, text=True)
                            if result.returncode == 0:
                                deleted_count += 1
                            else:
                                errors.append(f"删除 {filename} 失败: {result.stderr}")
                        else:
                            # Windows环境回退到Python删除
                            os.remove(file_path)
                            deleted_count += 1
                    else:
                        errors.append(f"文件不存在: {filename}")
                        
                except Exception as e:
                    errors.append(f"删除 {filename} 时出错: {str(e)}")
        
        return {
            'success': len(errors) == 0,
            'deleted': deleted_count, 
            'errors': errors
        }
    
    @staticmethod
    def delete_database_records(submission_ids):
        """删除数据库记录（级联删除venues表记录）"""
        if not submission_ids:
            return {'success': True, 'deleted': 0}
        
        # 转换为字符串，用于IN查询
        ids_str = ','.join(map(str, submission_ids))
        
        try:
            # 由于外键约束，删除venue_submissions时会自动删除相关的venues记录
            delete_query = f'''
                DELETE FROM venue_submissions 
                WHERE id IN ({ids_str})
            '''
            
            result = execute_query(delete_query)
            
            if result is not None:
                return {'success': True, 'deleted': result}
            else:
                return {'success': False, 'deleted': 0, 'error': '数据库删除失败'}
                
        except Exception as e:
            return {'success': False, 'deleted': 0, 'error': f'数据库操作失败: {str(e)}'}
    
    @staticmethod
    def cleanup_expired_data(days_old=3, dry_run=False):
        """
        清理过期数据
        
        Args:
            days_old: 清理多少天前的数据，默认3天
            dry_run: 是否仅测试运行（不实际删除）
            
        Returns:
            清理结果统计
        """
        # 获取过期数据
        expired_submissions = DataCleanup.get_expired_submissions(days_old)
        
        if not expired_submissions:
            return {
                'success': True,
                'message': '没有找到需要清理的过期数据',
                'stats': {
                    'submissions_deleted': 0,
                    'images_deleted': 0,
                    'errors': []
                }
            }
        
        # 收集所有图片文件名和提交ID
        all_screenshots = []
        submission_ids = []
        
        for submission in expired_submissions:
            submission_ids.append(submission['submission_id'])
            all_screenshots.extend(submission['screenshots'])
        
        # 如果是测试运行，只返回统计信息
        if dry_run:
            return {
                'success': True,
                'message': f'测试运行：将清理 {len(expired_submissions)} 个提交记录，{len(all_screenshots)} 个图片文件',
                'stats': {
                    'submissions_to_delete': len(expired_submissions),
                    'images_to_delete': len(all_screenshots),
                    'expired_submissions': expired_submissions
                }
            }
        
        # 实际执行清理
        errors = []
        
        # 1. 删除图片文件
        image_result = DataCleanup.delete_image_files(all_screenshots)
        if not image_result['success']:
            errors.extend(image_result['errors'])
        
        # 2. 删除数据库记录
        db_result = DataCleanup.delete_database_records(submission_ids)
        if not db_result['success']:
            errors.append(db_result.get('error', '数据库删除失败'))
        
        return {
            'success': len(errors) == 0,
            'message': f'清理完成：删除了 {db_result.get("deleted", 0)} 个提交记录，{image_result.get("deleted", 0)} 个图片文件',
            'stats': {
                'submissions_deleted': db_result.get('deleted', 0),
                'images_deleted': image_result.get('deleted', 0), 
                'errors': errors
            }
        }
    
    @staticmethod
    def get_cleanup_stats():
        """获取清理统计信息"""
        from datetime import date
        
        today = date.today()
        
        # 统计各个时间段的数据
        stats = {}
        
        for days in [1, 3, 7, 30]:
            cutoff_date = today - timedelta(days=days)
            
            count_query = '''
                SELECT COUNT(*) as submission_count,
                       COUNT(v.venue_screenshot) as image_count
                FROM venue_submissions vs
                LEFT JOIN venues v ON vs.id = v.submission_id
                WHERE vs.venue_date <= %s
            '''
            
            result = execute_query(count_query, (cutoff_date,), fetch='one')
            
            stats[f'{days}_days_old'] = {
                'submissions': result[0] if result else 0,
                'images': result[1] if result else 0,
                'cutoff_date': cutoff_date.strftime('%Y-%m-%d')
            }
        
        return stats