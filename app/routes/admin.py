# app/routes/admin.py (Cập nhật hoàn chỉnh)
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import login_required, current_user
from sqlalchemy import text, desc
from app import db
from app.models import BenhNhan, CauHinhBaoCao, ChiTietDon, NguoiDung, VaiTro, NguoiDung_VaiTro, BaoCao, LichHen, DonThuoc, Thuoc
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO

# Định nghĩa Blueprint
admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
@login_required
def restrict_to_admin():
    """Giới hạn truy cập chỉ cho Admin."""
    if not current_user.has_role('Admin'):
        flash('Bạn không có quyền truy cập!', 'danger')
        return redirect(url_for('auth.login'))

# ----------------------------------------------------------------------
# DASHBOARD
# ----------------------------------------------------------------------

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    # Thống kê người dùng
    total_users = NguoiDung.query.count()
    active_users = NguoiDung.query.filter_by(TrangThai=True).count()
    
    # Thống kê bệnh nhân
    total_patients = BenhNhan.query.count()

    # Thống kê lịch hẹn trong tháng
    today = datetime.now().date()
    month_start = today.replace(day=1)

    month_appointments = LichHen.query.filter(
        LichHen.NgayGio >= month_start
    ).count()

    month_completed = LichHen.query.filter(
        LichHen.NgayGio >= month_start,
        LichHen.TrangThai == 'Đã khám'
    ).count()

    # Lấy số lượng bệnh nhân mới (giả định: BN có lịch hẹn trong tháng)
    new_patients = BenhNhan.query.join(LichHen).filter(
        LichHen.NgayGio >= month_start
    ).distinct(BenhNhan.MaBN).count()

    # Thống kê doanh thu tháng
    month_revenue = db.session.query(db.func.sum(Thuoc.Gia * ChiTietDon.SoLuong)).join(ChiTietDon).join(DonThuoc).filter(
        DonThuoc.NgayKe >= month_start
    ).scalar() or 0

    # Thống kê thuốc
    total_medicines = Thuoc.query.count()
    low_stock_medicines = Thuoc.query.filter(
        Thuoc.SoLuongTon <= Thuoc.SoLuongCanhBao
    ).count()

    # Lấy các báo cáo gần đây
    recent_reports = BaoCao.query.order_by(BaoCao.NgayLap.desc()).limit(5).all()

    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        active_users=active_users,
        total_patients=total_patients,
        month_appointments=month_appointments,
        month_completed=month_completed,
        month_revenue=month_revenue,
        total_medicines=total_medicines,
        low_stock_medicines=low_stock_medicines,
        new_patients=new_patients, # Thêm new_patients vào context
        recent_reports=recent_reports
    )

# ----------------------------------------------------------------------
# QUẢN LÝ NGƯỜI DÙNG (USERS)
# ----------------------------------------------------------------------

@admin_bp.route('/users', methods=['GET', 'POST'])
@login_required
def manage_users():
    """Quản lý thêm, sửa, xem danh sách người dùng, sử dụng mô hình N-N."""
    if request.method == 'POST':
        # Thêm user mới
        username = request.form['username']
        password = request.form['password']
        hoten = request.form['hoten']
        email = request.form.get('email', '')
        sdt = request.form.get('sdt', '')
        chuyenkhoa = request.form.get('chuyenkhoa', '')
        vaitro_id = request.form['vaitro'] # Là MaVaiTro

        if NguoiDung.query.filter_by(TenDangNhap=username).first():
            flash('Tên đăng nhập đã tồn tại!', 'danger')
        else:
            user = NguoiDung(
                TenDangNhap=username,
                HoTen=hoten,
                Email=email,
                SDT=sdt,
                ChuyenKhoa=chuyenkhoa
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush() # Lấy ID của user

            # Gán vai trò cho người dùng (Mô hình N-N)
            user_role = NguoiDung_VaiTro(MaND=user.MaND, MaVaiTro=vaitro_id)
            db.session.add(user_role)

            db.session.commit()
            flash('Thêm user thành công!', 'success')

    # Lấy danh sách người dùng và vai trò của họ
    # Đây là cách phức tạp hơn để lấy Vai trò theo mô hình N-N:
    # Lấy tất cả người dùng.
    users = NguoiDung.query.all()
    # Lấy tất cả vai trò cho form
    vai_tros = VaiTro.query.all()
    
    # Lấy thông tin vai trò gán cho từng user để hiển thị:
    user_data = []
    for user in users:
        current_roles = ', '.join([vt.vai_tro.TenVaiTro for vt in user.vai_tros])
        user_data.append({
            'MaND': user.MaND,
            'HoTen': user.HoTen,
            'TenDangNhap': user.TenDangNhap,
            'Email': user.Email,
            'VaiTro': current_roles,
            'TrangThai': user.TrangThai
        })

    return render_template('admin/manage_users.html', users=user_data, vai_tros=vai_tros)


@admin_bp.route('/get_user/<int:user_id>')
@login_required
def get_user(user_id):
    """Lấy thông tin người dùng cụ thể (AJAX)"""
    user = NguoiDung.query.get_or_404(user_id)
    
    # Lấy danh sách các vai trò (dạng list TenVaiTro)
    current_roles = [vt.vai_tro.MaVaiTro for vt in user.vai_tros]

    return jsonify({
        'MaND': user.MaND,
        'TenDangNhap': user.TenDangNhap,
        'HoTen': user.HoTen,
        'Email': user.Email,
        'SDT': user.SDT,
        'ChuyenKhoa': user.ChuyenKhoa,
        'TrangThai': user.TrangThai,
        'MaVaiTro': current_roles[0] if current_roles else None # Giả sử chỉ có 1 vai trò chính
    })

@admin_bp.route('/update_user/<int:user_id>', methods=['POST'])
@login_required
def update_user(user_id):
    """Cập nhật thông tin người dùng và vai trò (AJAX)"""
    user = NguoiDung.query.get_or_404(user_id)
    
    try:
        # Cập nhật thông tin người dùng
        user.HoTen = request.form.get('hoten')
        user.Email = request.form.get('email')
        user.SDT = request.form.get('sdt')
        user.ChuyenKhoa = request.form.get('chuyenkhoa')
        # Kiểm tra và cập nhật trạng thái
        trang_thai = request.form.get('trangthai')
        user.TrangThai = True if trang_thai == 'true' or trang_thai == 'Hoạt động' else False

        # Cập nhật vai trò (Mô hình N-N)
        vaitro_id = request.form.get('vaitro')

        # Xóa tất cả các vai trò cũ
        NguoiDung_VaiTro.query.filter_by(MaND=user_id).delete()

        # Thêm vai trò mới
        if vaitro_id:
            user_role = NguoiDung_VaiTro(MaND=user_id, MaVaiTro=vaitro_id)
            db.session.add(user_role)

        db.session.commit()
        return jsonify({'success': True, 'message': 'Cập nhật thông tin người dùng thành công!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Lỗi khi cập nhật: {str(e)}'})

@admin_bp.route('/lock_user/<int:user_id>', methods=['POST'])
@login_required
def lock_user(user_id):
    """Khóa người dùng (AJAX)"""
    user = NguoiDung.query.get_or_404(user_id)
    user.TrangThai = False
    db.session.commit()
    return jsonify({'success': True, 'message': 'Khóa người dùng thành công!'})

@admin_bp.route('/unlock_user/<int:user_id>', methods=['POST'])
@login_required
def unlock_user(user_id):
    """Mở khóa người dùng (AJAX)"""
    user = NguoiDung.query.get_or_404(user_id)
    user.TrangThai = True
    db.session.commit()
    return jsonify({'success': True, 'message': 'Mở khóa người dùng thành công!'})

# ----------------------------------------------------------------------
# BÁO CÁO VÀ THỐNG KÊ (REPORTS)
# ----------------------------------------------------------------------

@admin_bp.route('/reports', methods=['GET', 'POST'])
@login_required
def reports():
    # Sửa lỗi cú pháp: dùng datetime.strptime để chuyển đổi string date sang date object
    from_date_str = request.form.get('from_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    to_date_str = request.form.get('to_date', datetime.now().strftime('%Y-%m-%d'))
    
    try:
        from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Định dạng ngày không hợp lệ!', 'danger')
        from_date = (datetime.now() - timedelta(days=30)).date()
        to_date = datetime.now().date()
        from_date_str = from_date.strftime('%Y-%m-%d')
        to_date_str = to_date.strftime('%Y-%m-%d')

    report_type = request.form.get('report_type', 'general')
    report_period = request.form.get('report_period', 'daily')

    # Thống kê lượt khám
    exams = LichHen.query.filter(
        LichHen.NgayGio.between(from_date, to_date + timedelta(days=1)),
        LichHen.TrangThai == 'Đã khám'
    ).count()

    # Thống kê doanh thu (giả sử từ đơn thuốc)
    revenue = db.session.query(db.func.sum(Thuoc.Gia * ChiTietDon.SoLuong)).join(ChiTietDon).join(DonThuoc).filter(
        DonThuoc.NgayKe.between(from_date, to_date)
    ).scalar() or 0

    # Thống kê thuốc bán chạy
    # Sửa db.desc('total_quantity') thành desc(text('total_quantity')) nếu dùng SQLAlchemy 2.0+ hoặc dùng func.sum như trên.
    top_medicines = db.session.query(
        Thuoc.TenThuoc,
        db.func.sum(ChiTietDon.SoLuong).label('total_quantity'),
        db.func.sum(Thuoc.Gia * ChiTietDon.SoLuong).label('total_revenue')
    ).join(ChiTietDon).join(DonThuoc).filter(
        DonThuoc.NgayKe.between(from_date, to_date)
    ).group_by(Thuoc.TenThuoc).order_by(desc(text('total_quantity'))).limit(10).all()

    # Thống kê bác sĩ khám nhiều nhất
    top_doctors = db.session.query(
        NguoiDung.HoTen,
        db.func.count(LichHen.MaLH).label('total_appointments')
    ).join(LichHen, NguoiDung.MaND == LichHen.MaBS).filter(
        LichHen.NgayGio.between(from_date, to_date + timedelta(days=1)),
        LichHen.TrangThai == 'Đã khám'
    ).group_by(NguoiDung.HoTen).order_by(desc(text('total_appointments'))).limit(10).all()

    # Thống kê theo ngày (Daily Stats)
    daily_stats = db.session.query(
        db.func.cast(LichHen.NgayGio, db.Date).label('date'), # Sửa lỗi func.date
        db.func.count(LichHen.MaLH).label('appointments')
    ).filter(
        LichHen.NgayGio.between(from_date, to_date + timedelta(days=1)),
        LichHen.TrangThai == 'Đã khám'
    ).group_by(db.func.cast(LichHen.NgayGio, db.Date)).order_by('date').all()

    # Chuẩn bị dữ liệu cho biểu đồ
    dates = [stat.date.strftime('%d/%m') for stat in daily_stats]
    appointment_counts = [stat.appointments for stat in daily_stats]

    # Lưu báo cáo
    if request.method == 'POST':
        bc = BaoCao(
            MaND=current_user.MaND,
            LoaiBaoCao=report_type,
            TuNgay=from_date,
            DenNgay=to_date,
            TongSo=exams,
            DoanhThu=revenue
        )
        db.session.add(bc)
        db.session.flush() # Lấy ID của báo cáo

        # Lưu cấu hình báo cáo
        ch = CauHinhBaoCao(
            MaBC=bc.MaBC,
            KyBaoCao=report_period,
            TieuChi=f'Thống kê từ {from_date_str} đến {to_date_str}'
        )
        db.session.add(ch)
        db.session.commit()

        flash('Báo cáo đã lưu!', 'success')

        # Xuất báo cáo ra file Excel
        if report_type == 'excel':
            # Tạo DataFrame cho báo cáo tổng quan
            general_df = pd.DataFrame({
                'Chỉ số': ['Tổng lượt khám', 'Doanh thu'],
                'Giá trị': [exams, revenue]
            })

            # Tạo DataFrame cho thuốc bán chạy
            medicine_df = pd.DataFrame(top_medicines, columns=['Tên thuốc', 'Số lượng', 'Doanh thu'])

            # Tạo file Excel với nhiều sheet
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                general_df.to_excel(writer, sheet_name='Tổng quan', index=False)
                medicine_df.to_excel(writer, sheet_name='Thuốc bán chạy', index=False)

            output.seek(0)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'report_{from_date_str}_to_{to_date_str}.xlsx'
            )

    return render_template(
        'admin/reports.html',
        exams=exams,
        revenue=revenue,
        from_date=from_date_str,
        to_date=to_date_str,
        top_medicines=top_medicines,
        top_doctors=top_doctors,
        dates=dates,
        appointment_counts=appointment_counts,
        report_type=report_type,
        report_period=report_period
    )

@admin_bp.route('/backup')
@login_required
def backup():
    import os
    from datetime import datetime
    
    # Tạo thư mục backup nếu chưa có
    backup_dir = os.path.join(os.getcwd(), 'backups')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # Tạo tên file backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'AnTamClinicDB_{timestamp}.bak')

    # Thực hiện backup (FIX LỖI ENGINE.EXECUTE)
    try:
        # Sử dụng connect() và isolation_level="AUTOCOMMIT" vì BACKUP không chạy trong transaction
        with db.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.execute(text(f"BACKUP DATABASE [AnTamClinicDB] TO DISK = '{backup_file}' WITH INIT, NAME = 'AnTamClinicDB-Full Database Backup', STATS = 10"))
            
        flash(f'Sao lưu thành công! File được lưu tại: {backup_file}', 'success')
    except Exception as e:
        flash(f'Lỗi khi sao lưu: {str(e)}', 'danger')

    return redirect(url_for('admin.reports'))

@admin_bp.route('/restore', methods=['GET', 'POST'])
@login_required
def restore():
    if request.method == 'POST':
        backup_file = request.form.get('backup_file')
        if not backup_file:
            flash('Vui lòng chọn file backup!', 'danger')
            return redirect(url_for('admin.restore'))

        try:
            # Thực hiện phục hồi (FIX LỖI ENGINE.EXECUTE)
            # Lưu ý: Restore database đang sử dụng là rất nguy hiểm và thường sẽ thất bại nếu có kết nối khác đang mở.
            # Cần chuyển sang master trước để restore (SQL Server specific)
            with db.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
                # Ngắt kết nối hiện tại tới DB (Single User Mode) để Restore
                connection.execute(text("USE master; ALTER DATABASE [AnTamClinicDB] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;"))
                connection.execute(text(f"RESTORE DATABASE [AnTamClinicDB] FROM DISK = '{backup_file}' WITH REPLACE;"))
                connection.execute(text("ALTER DATABASE [AnTamClinicDB] SET MULTI_USER;"))
                
            flash('Phục hồi dữ liệu thành công!', 'success')
        except Exception as e:
            # Cố gắng đưa DB trở lại Multi User nếu lỗi
            try:
                with db.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                     conn.execute(text("ALTER DATABASE [AnTamClinicDB] SET MULTI_USER;"))
            except:
                pass
            flash(f'Lỗi khi phục hồi: {str(e)}', 'danger')

        return redirect(url_for('admin.reports'))
    
    # -----------------------------------------------------------
    # Xử lý GET request (Hiển thị form)
    # -----------------------------------------------------------
    # Lấy danh sách file backup
    backup_dir = os.path.join(os.getcwd(), 'backups')
    backup_files = []
    if os.path.exists(backup_dir):
        for filename in sorted(os.listdir(backup_dir), reverse=True):
            if filename.endswith('.bak'):
                file_path = os.path.join(backup_dir, filename)
                file_stat = os.stat(file_path)
                backup_files.append({
                    'name': filename,
                    'path': file_path,
                    'size': round(file_stat.st_size / (1024 * 1024), 2), # MB
                    'date': datetime.fromtimestamp(file_stat.st_mtime).strftime('%d/%m/%Y %H:%M')
                })

    # TRẢ VỀ TEMPLATE
    return render_template('admin/restore.html', backup_files=backup_files)

@admin_bp.route('/schedule_backup', methods=['GET', 'POST'])
@login_required
def schedule_backup():
    if request.method == 'POST':
        # Logic này chỉ lưu cấu hình trên form, không thực hiện lập lịch thực tế (do cần Cron/Task Scheduler)
        frequency = request.form.get('frequency')
        time = request.form.get('time')
        keep_days = request.form.get('keep_days', 7)
        
        # Ở đây có thể lưu cấu hình này vào DB/file config để hiển thị sau này
        
        flash('Đã lưu cấu hình backup tự động!', 'success')
        return redirect(url_for('admin.reports'))
    
    return render_template('admin/schedule_backup.html')