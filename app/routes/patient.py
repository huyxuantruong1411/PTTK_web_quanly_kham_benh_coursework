from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user, login_user, logout_user
from app.forms import LoginForm, PatientRegistrationForm
from app.models import BenhNhan, BenhNhanDiUng, LichHen, KetQuaKham, ChiSoSinhTon, DonThuoc, NguoiDung, VaiTro, NguoiDung_VaiTro
from app import db # FIX: Import db
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

patient_bp = Blueprint('patient', __name__)

# FIX: Cập nhật restrict_to_patient để loại trừ register và login
@patient_bp.before_request
def restrict_to_patient():
    # 1. Cho phép truy cập register và login mà không cần login
    if request.endpoint in ['patient.register', 'patient.login']:
        return 

    # 2. Bắt buộc phải login để truy cập các route khác
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
        
    # 3. Nếu đã login, kiểm tra vai trò
    if not current_user.has_role('BenhNhan'):
        flash('Bạn không có quyền truy cập!', 'danger')
        return redirect(url_for('auth.login'))

@patient_bp.route('/register', methods=['GET', 'POST'])
# FIX: Đảm bảo không có @login_required
def register():
    # FIX: Kiểm tra nếu đã đăng nhập thì chuyển hướng đi
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    form = PatientRegistrationForm()
    
    # 🚨 LƯU Ý: Phải chạy "pip install email_validator" để fix lỗi WTForms Email validation
    if form.validate_on_submit():
        # Kiểm tra xem bệnh nhân đã tồn tại chưa
        existing_user = NguoiDung.query.filter_by(TenDangNhap=form.username.data).first()
        if existing_user:
            flash('Tên đăng nhập đã tồn tại!', 'danger')
            return render_template('patient/register.html', form=form)

        # Lấy MaVaiTro cho BenhNhan
        patient_role = VaiTro.query.filter_by(TenVaiTro='BenhNhan').first()
        if not patient_role:
             flash('Lỗi cấu hình hệ thống: Vai trò Bệnh nhân không tồn tại!', 'danger')
             return render_template('patient/register.html', form=form)
        
        try:
            # 1. Tạo người dùng mới
            user = NguoiDung(
                TenDangNhap=form.username.data,
                HoTen=form.hoten.data,
                Email=form.email.data,
                SDT=form.sdt.data
            )
            # Dùng form.password.data thay vì form.password
            user.set_password(form.password.data) 
            db.session.add(user)
            db.session.flush()

            # Gán vai trò BenhNhan (N-N model)
            user_role = NguoiDung_VaiTro(MaND=user.MaND, MaVaiTro=patient_role.MaVaiTro)
            db.session.add(user_role)
            
            # 2. Tạo hồ sơ bệnh nhân
            patient = BenhNhan(
                MaND=user.MaND,
                HoTen=form.hoten.data,
                NgaySinh=form.ngaysinh.data,
                GioiTinh=form.gioitinh.data,
                SDT=form.sdt.data,
                DiaChi=form.diachi.data,
                Email=form.email.data
            )
            db.session.add(patient)
            db.session.commit()
            
            flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
            # FIX LỖI 2: Chuyển hướng về trang đăng nhập chung (auth.login)
            return redirect(url_for('auth.login')) 
        
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi đăng ký hệ thống: {str(e)}', 'danger')
            return render_template('patient/register.html', form=form)
    
    return render_template('patient/register.html', form=form)

@patient_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Sử dụng LoginForm từ app.forms
    form = LoginForm() 
    
    # Nếu đã đăng nhập với vai trò Bệnh nhân
    if current_user.is_authenticated and current_user.has_role('BenhNhan'):
        return redirect(url_for('patient.dashboard'))
    
    # Nếu đã đăng nhập nhưng không phải Bệnh nhân, chuyển hướng đến dashboard chung
    if current_user.is_authenticated and not current_user.has_role('BenhNhan'):
        return redirect(url_for('auth.dashboard')) 
        
    if form.validate_on_submit():
        user = NguoiDung.query.filter_by(TenDangNhap=form.username.data).first()
        
        if user and user.check_password(form.password.data) and user.has_role('BenhNhan'):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('patient.dashboard'))
        else:
            flash('Đăng nhập không thành công. Vui lòng kiểm tra tên đăng nhập và mật khẩu.', 'danger')
    
    return render_template('patient/login.html', form=form)

@patient_bp.route('/dashboard')
# FIX LỖI 5: Loại bỏ @login_required vì nó đã được xử lý trong before_request
def dashboard():
    # Logic kiểm tra quyền đã nằm trong @before_request

    # Lấy thông tin bệnh nhân
    patient = BenhNhan.query.filter_by(MaND=current_user.MaND).first()
    
    # FIX LỖI 3: Kiểm tra NoneType
    if not patient:
        flash('Lỗi cấu hình: Hồ sơ bệnh nhân không tồn tại. Vui lòng liên hệ lễ tân.', 'danger')
        logout_user()
        return redirect(url_for('auth.login'))

    # Lấy các lịch hẹn sắp tới
    upcoming_appointments = LichHen.query.filter_by(MaBN=patient.MaBN)\
        .filter(LichHen.NgayGio >= datetime.now())\
        .order_by(LichHen.NgayGio).limit(5).all()
    
    # Lấy các lịch hẹn gần đây
    recent_appointments = LichHen.query.filter_by(MaBN=patient.MaBN)\
        .filter(LichHen.TrangThai == 'Đã khám')\
        .order_by(LichHen.NgayGio.desc()).all() 

    # Chỉ lấy 5 lịch khám gần nhất cho dashboard
    recent_appointments_limited = recent_appointments[:5]

    # Tính toán số lượng cần tái khám
    follow_ups = [
        appt for appt in recent_appointments 
        if appt.ket_qua and appt.ket_qua.CanhBaoTaiKham and not appt.ket_qua.DaTaiKham
    ]

    return render_template('patient/dashboard.html', 
                          patient=patient,
                          upcoming_appointments=upcoming_appointments,
                          recent_appointments=recent_appointments_limited,
                          follow_up_count=len(follow_ups))

@patient_bp.route('/appointments')
# FIX LỖI 5: Loại bỏ @login_required
def appointments():
    patient = BenhNhan.query.filter_by(MaND=current_user.MaND).first()
    if not patient: # Bổ sung kiểm tra an toàn
        return redirect(url_for('auth.dashboard')) 

    all_appointments = LichHen.query.filter_by(MaBN=patient.MaBN)\
        .order_by(LichHen.NgayGio.desc()).all()
    
    return render_template('patient/appointments.html', appts=all_appointments)

@patient_bp.route('/book_appointment', methods=['GET', 'POST'])
# FIX LỖI 5: Loại bỏ @login_required
def book_appointment():
    patient = BenhNhan.query.filter_by(MaND=current_user.MaND).first()
    if not patient:
        return redirect(url_for('auth.dashboard')) 
        
    # FIX: Lấy danh sách bác sĩ dùng mô hình N-N
    doctors = db.session.query(NguoiDung)\
                .join(NguoiDung_VaiTro)\
                .join(VaiTro)\
                .filter(VaiTro.TenVaiTro == 'BacSi').all()
    
    if request.method == 'POST':
        doctor_id = request.form.get('doctor_id')
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        
        try:
            appointment_datetime = datetime.strptime(f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            flash('Định dạng ngày giờ không hợp lệ!', 'danger')
            return render_template('patient/book_appointment.html', doctors=doctors)
        
        existing_appointment = LichHen.query.filter_by(
            MaBS=doctor_id,
            NgayGio=appointment_datetime
        ).first()
        
        if existing_appointment:
            flash('Bác sĩ đã có lịch hẹn vào thời điểm này. Vui lòng chọn thời gian khác!', 'danger')
        else:
            new_appointment = LichHen(
                MaBN=patient.MaBN,
                MaBS=doctor_id,
                NgayGio=appointment_datetime,
                TrangThai='Chờ khám'
            )
            db.session.add(new_appointment)
            db.session.commit()
            
            flash('Đặt lịch hẹn thành công!', 'success')
            return redirect(url_for('patient.appointments'))
    
    return render_template('patient/book_appointment.html', doctors=doctors)

@patient_bp.route('/results/<int:lh_id>')
# FIX LỖI 5: Loại bỏ @login_required
def results(lh_id):
    patient = BenhNhan.query.filter_by(MaND=current_user.MaND).first()
    if not patient:
        return redirect(url_for('auth.dashboard')) 
        
    # Kiểm tra xem lịch hẹn có thuộc về bệnh nhân này không
    appointment = LichHen.query.filter_by(MaLH=lh_id, MaBN=patient.MaBN).first_or_404()
    
    kq = KetQuaKham.query.filter_by(MaLH=lh_id).first()
    
    if not kq:
        flash('Lịch khám này chưa có kết quả.', 'info')
        return redirect(url_for('patient.dashboard'))
        
    dt = DonThuoc.query.filter_by(MaKQ=kq.MaKQ).first() if kq else None
    
    return render_template('patient/results.html', appointment=appointment, kq=kq, dt=dt, patient=patient)

@patient_bp.route('/get_health_data/<int:patient_id>')
# FIX LỖI 5: Loại bỏ @login_required
def get_health_data(patient_id):
    # Logic kiểm tra MaND có khớp với current_user không (Bổ sung kiểm tra an toàn)
    if not current_user.is_authenticated or BenhNhan.query.filter_by(MaND=current_user.MaND, MaBN=patient_id).first() is None:
        return jsonify({"error": "Unauthorized"}), 403

    appointments = db.session.query(LichHen, KetQuaKham, ChiSoSinhTon).join(KetQuaKham).join(ChiSoSinhTon, KetQuaKham.MaKQ == ChiSoSinhTon.MaKQ)\
        .filter(LichHen.MaBN == patient_id, LichHen.TrangThai == 'Đã khám')\
        .order_by(LichHen.NgayGio.asc()).all() 

    health_data = {
        'labels': [],
        'weight': [],
        'bloodPressure': [],
        'temperature': [],
        'heartRate': []
    }
    
    for lh, kq, cs in appointments:
        health_data['labels'].append(f"{lh.NgayGio.strftime('%d/%m/%Y')}")
        health_data['weight'].append(cs.CanNang if cs.CanNang else None)
        health_data['bloodPressure'].append(cs.HuyetAp if cs.HuyetAp else "0/0")
        health_data['temperature'].append(cs.NhietDo if cs.NhietDo else None)
        health_data['heartRate'].append(cs.NhipTim if cs.NhipTim else None)
    
    return jsonify(health_data)

@patient_bp.route('/profile')
# FIX LỖI 5: Loại bỏ @login_required
def profile():
    patient = BenhNhan.query.filter_by(MaND=current_user.MaND).first_or_404()
    
    allergies = BenhNhanDiUng.query.filter_by(MaBN=patient.MaBN).all()

    return render_template('patient/profile.html', patient=patient, allergies=allergies)