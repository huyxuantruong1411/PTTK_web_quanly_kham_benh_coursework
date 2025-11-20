# app/routes/reception.py (Cập nhật hoàn chỉnh)
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user, login_required
from app import db
from app.models import BenhNhan, DonThuoc, LichHen, NguoiDung, VaiTro
from app.utils import send_appointment_confirmation, send_appointment_cancellation
from datetime import datetime

reception_bp = Blueprint('reception', __name__)

@reception_bp.before_request
@login_required
def restrict_to_reception():
    if not current_user.has_role('LeTan'):
        flash('Bạn không có quyền truy cập!', 'danger')
        return redirect(url_for('auth.login'))

@reception_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.has_role('LeTan'):
        flash('Bạn không có quyền truy cập!', 'danger')
        return redirect(url_for('auth.login'))
    
    # Lấy các lịch hẹn hôm nay
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    today_appointments = LichHen.query.filter(
        LichHen.NgayGio.between(today_start, today_end)
    ).order_by(LichHen.NgayGio).all()
    
    # Thống kê lượt khám trong tháng
    month_start = today.replace(day=1)
    month_appointments = LichHen.query.filter(
        LichHen.NgayGio >= month_start
    ).count()
    
    month_completed = LichHen.query.filter(
        LichHen.NgayGio >= month_start,
        LichHen.TrangThai == 'Đã khám'
    ).count()
    
    # Thống kê bệnh nhân mới trong tháng
    new_patients = BenhNhan.query.filter(
        BenhNhan.MaBN.in_(
            db.session.query(LichHen.MaBN).filter(
                LichHen.NgayGio >= month_start
            )
        )
    ).distinct().count()
    
    # Lấy các lịch hẹn sắp tới
    upcoming_appointments = LichHen.query.filter(
        LichHen.NgayGio >= today_start,
        LichHen.TrangThai == 'Chờ khám'
    ).order_by(LichHen.NgayGio).limit(10).all()
    
    return render_template(
        'reception/dashboard.html',
        today_appointments=today_appointments,
        month_appointments=month_appointments,
        month_completed=month_completed,
        new_patients=new_patients,
        upcoming_appointments=upcoming_appointments
    )

@reception_bp.route('/patients', methods=['GET'])
@login_required
def patients():
    patients = BenhNhan.query.all()
    return render_template('reception/patients.html', patients=patients)

@reception_bp.route('/add_patient', methods=['POST'])
@login_required
def add_patient(): # Tên hàm mới
    if not current_user.has_role('LeTan'):
        return jsonify({'success': False, 'message': 'Không có quyền truy cập'}), 403

    try:
        # Lấy dữ liệu từ AJAX
        hoten = request.form.get('hoten') # [cite: 333]
        ngaysinh = request.form.get('ngaysinh') # [cite: 333]
        gioitinh = request.form.get('gioitinh') # [cite: 333]
        sdt = request.form.get('sdt') # [cite: 333]
        diachi = request.form.get('diachi') # [cite: 333]
        email = request.form.get('email') # [cite: 333]
        
        # Tạo bệnh nhân mới
        bn = BenhNhan(
            HoTen=hoten,
            NgaySinh=datetime.strptime(ngaysinh, '%Y-%m-%d').date(), # [cite: 333]
            GioiTinh=gioitinh,
            SDT=sdt,
            DiaChi=diachi,
            Email=email
        )
        db.session.add(bn)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Thêm bệnh nhân thành công!'})
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi khi thêm bệnh nhân: {e}") 
        return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'}), 500

@reception_bp.route('/get_patient/<int:patient_id>')
@login_required
def get_patient(patient_id):
    patient = BenhNhan.query.get_or_404(patient_id)
    return jsonify({
        'MaBN': patient.MaBN,
        'HoTen': patient.HoTen,
        'NgaySinh': patient.NgaySinh.strftime('%Y-%m-%d'),
        'GioiTinh': patient.GioiTinh,
        'SDT': patient.SDT,
        'DiaChi': patient.DiaChi,
        'Email': patient.Email
    })

@reception_bp.route('/update_patient/<int:patient_id>', methods=['POST'])
@login_required
def update_patient(patient_id):
    patient = BenhNhan.query.get_or_404(patient_id)
    
    # Cập nhật thông tin bệnh nhân
    patient.HoTen = request.form.get('hoten')
    patient.NgaySinh = datetime.strptime(request.form.get('ngaysinh'), '%Y-%m-%d').date()
    patient.GioiTinh = request.form.get('gioitinh')
    patient.SDT = request.form.get('sdt')
    patient.DiaChi = request.form.get('diachi')
    patient.Email = request.form.get('email')
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Cập nhật thông tin bệnh nhân thành công!'})

@reception_bp.route('/delete_patient/<int:patient_id>', methods=['POST'])
@login_required
def delete_patient(patient_id):
    patient = BenhNhan.query.get_or_404(patient_id)
    
    # Kiểm tra xem bệnh nhân có lịch hẹn không
    appointments = LichHen.query.filter_by(MaBN=patient_id).all()
    if appointments:
        return jsonify({'success': False, 'message': 'Không thể xóa bệnh nhân có lịch hẹn!'})
    
    db.session.delete(patient)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Xóa bệnh nhân thành công!'})

@reception_bp.route('/appointments', methods=['GET', 'POST'])
@login_required
def appointments():
    if request.method == 'GET':
        # Lấy danh sách bác sĩ cho form
        doctors = NguoiDung.query.filter(NguoiDung.vai_tros.any(VaiTro.TenVaiTro == 'BacSi')).all()
        # Lấy danh sách bệnh nhân cho form
        patients = BenhNhan.query.all()
        
        all_appointments = LichHen.query.order_by(LichHen.NgayGio.desc()).all()
        return render_template('reception/appointments.html', doctors=doctors, patients=patients, appointments=all_appointments)
    
    # Xử lý thêm/sửa lịch hẹn
    mabn = request.form.get('mabn')
    mabs = request.form.get('mabs')
    ngaygio = request.form.get('ngaygio')
    trangthai = request.form.get('trangthai', 'Chờ khám')
    lh_id = request.form.get('lh_id')  # ID lịch hẹn nếu là sửa
    
    try:
        # Chuyển đổi chuỗi thành datetime
        appointment_datetime = datetime.strptime(ngaygio, '%Y-%m-%dT%H:%M')
    except ValueError:
        return jsonify({'success': False, 'message': 'Định dạng ngày giờ không hợp lệ!'})
    
    # Kiểm tra trùng lịch hẹn (loại trừ lịch hẹn hiện tại nếu là sửa)
    existing_appointment = LichHen.query.filter(
        LichHen.MaBS == mabs,
        LichHen.NgayGio == appointment_datetime
    )
    
    if lh_id:
        existing_appointment = existing_appointment.filter(LichHen.MaLH != int(lh_id))
    
    if existing_appointment.first():
        return jsonify({'success': False, 'message': 'Bác sĩ đã có lịch hẹn vào thời điểm này. Vui lòng chọn thời gian khác!'})
    
    if lh_id:
        # Cập nhật lịch hẹn hiện tại
        appointment = LichHen.query.get_or_404(int(lh_id))
        appointment.MaBN = mabn
        appointment.MaBS = mabs
        appointment.NgayGio = appointment_datetime
        appointment.TrangThai = trangthai
        message = 'Cập nhật lịch hẹn thành công!'
    else:
        # Tạo lịch hẹn mới
        appointment = LichHen(
            MaBN=mabn,
            MaBS=mabs,
            NgayGio=appointment_datetime,
            TrangThai=trangthai
        )
        db.session.add(appointment)
        message = 'Đặt lịch hẹn thành công!'
    
    db.session.commit()
    
    # Gửi email xác nhận
    send_appointment_confirmation(appointment)
    
    return jsonify({'success': True, 'message': message})

@reception_bp.route('/cancel_appointment/<int:lh_id>', methods=['POST'])
@login_required
def cancel_appointment(lh_id):
    appointment = LichHen.query.get_or_404(lh_id)
    appointment.TrangThai = 'Hủy'
    db.session.commit()
    
    # Gửi email thông báo hủy
    send_appointment_cancellation(appointment)
    
    return jsonify({'success': True, 'message': 'Đã hủy lịch hẹn!'})

@reception_bp.route('/payment/<int:lh_id>', methods=['GET', 'POST'])
@login_required
def payment(lh_id):
    appointment = LichHen.query.get_or_404(lh_id)
    
    if request.method == 'POST':
        # Xử lý thanh toán
        payment_method = request.form.get('payment_method')
        amount = request.form.get('amount')
        
        # Tạo hóa đơn
        from app.models import HoaDon
        hd = HoaDon(
            MaLH=lh_id,
            TongTien=amount,
            TrangThai='Đã thanh toán'
        )
        db.session.add(hd)
        db.session.commit()
        
        flash('Thanh toán thành công!', 'success')
        return redirect(url_for('reception.appointments'))
    
    return render_template('reception/payment.html', appointment=appointment)

@reception_bp.route('/invoice/<int:lh_id>')
@login_required
def invoice_detail(lh_id):
    """Xem chi tiết hóa đơn để in"""
    appointment = LichHen.query.get_or_404(lh_id)
    
    # Tính tiền khám (Giả sử cố định 100k)
    kham_phi = 100000
    
    # Tính tiền thuốc
    thuoc_phi = 0
    don_thuoc = DonThuoc.query.filter_by(MaKQ=appointment.ket_qua.MaKQ).first() if appointment.ket_qua else None
    chi_tiet_thuoc = []
    
    if don_thuoc:
        for ct in don_thuoc.chi_tiet:
            thanh_tien = ct.SoLuong * ct.thuoc.Gia
            thuoc_phi += thanh_tien
            chi_tiet_thuoc.append({
                'TenThuoc': ct.thuoc.TenThuoc,
                'SoLuong': ct.SoLuong,
                'DonGia': ct.thuoc.Gia,
                'ThanhTien': thanh_tien
            })
            
    tong_tien = kham_phi + thuoc_phi
    
    return render_template(
        'reception/invoice.html',
        appt=appointment,
        kham_phi=kham_phi,
        thuoc_phi=thuoc_phi,
        tong_tien=tong_tien,
        chi_tiet_thuoc=chi_tiet_thuoc,
        today=datetime.now()
    )