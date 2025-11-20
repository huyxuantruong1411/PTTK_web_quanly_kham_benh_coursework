import os
from datetime import datetime, timedelta
from app import create_app, db
from app.models import LichHen
from app.utils import send_appointment_reminder
from sqlalchemy import text
from apscheduler.schedulers.background import BackgroundScheduler

def send_daily_reminders():
    """Gửi email nhắc lịch cho các cuộc hẹn vào ngày mai"""
    app = create_app()
    with app.app_context():
        tomorrow = datetime.now() + timedelta(days=1)
        start_of_tomorrow = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_tomorrow = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        appointments = LichHen.query.filter(
            LichHen.NgayGio >= start_of_tomorrow,
            LichHen.NgayGio <= end_of_tomorrow,
            LichHen.TrangThai == 'Chờ khám'
        ).all()
        
        for appointment in appointments:
            if appointment.benh_nhan.Email:  # Chỉ gửi nếu có email
                send_appointment_reminder(appointment)
        
        print(f"Đã gửi {len(appointments)} email nhắc lịch cho ngày mai.")

def auto_backup():
    """Thực hiện backup tự động theo cấu hình"""
    app = create_app()
    with app.app_context():
        # Tạo thư mục backup nếu chưa có
        backup_dir = os.path.join(os.getcwd(), 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Tạo tên file backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'AnTamClinicDB_{timestamp}.bak')
        
        # Thực hiện backup
        try:
            with db.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
                connection.execute(text(f"BACKUP DATABASE [AnTamClinicDB] TO DISK = '{backup_file}' WITH INIT, NAME = 'AnTamClinicDB-Auto Backup', STATS = 10"))
            
            print(f"Auto backup successful: {backup_file}")
            
            # Xóa các file backup cũ (giữ lại 7 ngày gần nhất)
            keep_days = 7
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            
            for filename in os.listdir(backup_dir):
                if filename.endswith('.bak'):
                    file_path = os.path.join(backup_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        print(f"Deleted old backup: {filename}")
            
            return True
        except Exception as e:
            print(f"Auto backup failed: {str(e)}")
            return False

# Khởi tạo scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(send_daily_reminders, 'cron', hour=8, minute=0)  # Chạy lúc 8:00 mỗi ngày
scheduler.add_job(auto_backup, 'cron', hour=2, minute=0)  # Chạy lúc 2:00 mỗi ngày
scheduler.start()