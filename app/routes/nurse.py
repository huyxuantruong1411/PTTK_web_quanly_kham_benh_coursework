# app/routes/nurse.py (Cập nhật hoàn chỉnh)
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import LichHen, ChiSoSinhTon, KetQuaKham
from datetime import datetime

nurse_bp = Blueprint('nurse', __name__)

@nurse_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.has_role('YTa'):
        flash('Bạn không có quyền truy cập!', 'danger')
        return redirect(url_for('auth.login'))
    
    # Lấy các lịch hẹn hôm nay
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    today_appointments = LichHen.query.filter(
        LichHen.NgayGio.between(today_start, today_end)
    ).order_by(LichHen.NgayGio).all()
    
    # Lấy các bệnh nhân chờ nhập chỉ số
    waiting_vitals = []
    for appointment in today_appointments:
        kq = KetQuaKham.query.filter_by(MaLH=appointment.MaLH).first()
        if not kq or not ChiSoSinhTon.query.filter_by(MaKQ=kq.MaKQ).first():
            waiting_vitals.append(appointment)
    
    # Thống kê lượt nhập chỉ số trong tháng
    month_start = today.replace(day=1)
    month_vitals = ChiSoSinhTon.query.join(KetQuaKham).filter(
        KetQuaKham.NgayKham >= month_start
    ).count()
    
    # Lấy các bệnh nhân đã nhập chỉ số hôm nay
    today_vitals = ChiSoSinhTon.query.join(KetQuaKham).filter(
        KetQuaKham.NgayKham == today
    ).count()
    
    return render_template(
        'nurse/dashboard.html',
        today_appointments=today_appointments,
        waiting_vitals=waiting_vitals,
        month_vitals=month_vitals,
        today_vitals=today_vitals
    )

@nurse_bp.route('/exam-list')
@login_required
def exam_list():
    if not current_user.has_role('YTa'):
        flash('Bạn không có quyền truy cập!', 'danger')
        return redirect(url_for('auth.login'))
    
    queue = LichHen.query.filter_by(TrangThai='Chờ khám').all()  # Y tá thấy toàn bộ
    return render_template('nurse/exam_list.html', queue=queue)

@nurse_bp.route('/vitals/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def enter_vitals(appointment_id):
    if not current_user.has_role('YTa'):
        flash('Bạn không có quyền truy cập!', 'danger')
        return redirect(url_for('auth.login'))
    
    appointment = LichHen.query.get_or_404(appointment_id)
    
    # Tạo hoặc lấy kết quả khám
    kq = KetQuaKham.query.filter_by(MaLH=appointment_id).first()
    if not kq:
        kq = KetQuaKham(MaLH=appointment_id, MaBS=appointment.MaBS, NgayKham=datetime.now().date())
        db.session.add(kq)
        db.session.commit()
    
    # Lấy chỉ số sinh tồn nếu có
    vitals = ChiSoSinhTon.query.filter_by(MaKQ=kq.MaKQ).first()
    
    if request.method == 'POST':
        if vitals:
            # Cập nhật chỉ số sinh tồn đã tồn tại
            vitals.HuyetAp = request.form['huyetap']
            vitals.NhietDo = float(request.form['nhietdo'])
            vitals.CanNang = float(request.form['cannang'])
            vitals.NhipTim = int(request.form['nhiptim'])
        else:
            # Tạo mới chỉ số sinh tồn
            vitals = ChiSoSinhTon(
                MaKQ=kq.MaKQ,
                MaYT=current_user.MaND,
                HuyetAp=request.form['huyetap'],
                NhietDo=float(request.form['nhietdo']),
                CanNang=float(request.form['cannang']),
                NhipTim=int(request.form['nhiptim'])
            )
            db.session.add(vitals)
        
        db.session.commit()
        flash('Nhập chỉ số thành công! Chuyển cho bác sĩ.', 'success')
        return redirect(url_for('nurse.exam_list'))
    
    return render_template('nurse/enter_vitals.html', appt=appointment, vitals=vitals)