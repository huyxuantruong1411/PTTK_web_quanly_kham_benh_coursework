# app/routes/doctor.py (Cập nhật hoàn chỉnh)
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from app import db
from app.models import BenhNhan, LichHen, KetQuaKham, ChiSoSinhTon, DonThuoc, ChiTietDon, Thuoc, TinNhan, TuongTacThuoc, BenhNhanDiUng
from app.utils import check_drug_interactions, check_allergy_warnings, get_follow_up_patients
from datetime import datetime, timedelta

doctor_bp = Blueprint('doctor', __name__)

@doctor_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.has_role('BacSi'):
        flash('Bạn không có quyền truy cập!', 'danger')
        return redirect(url_for('auth.login'))
    
    # Lấy các lịch hẹn hôm nay của bác sĩ
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    today_appointments = LichHen.query.filter(
        LichHen.MaBS == current_user.MaND,
        LichHen.NgayGio.between(today_start, today_end)
    ).order_by(LichHen.NgayGio).all()
    
    # Lấy các lịch hẹn trong tuần
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    week_appointments = LichHen.query.filter(
        LichHen.MaBS == current_user.MaND,
        LichHen.NgayGio.between(week_start, week_end)
    ).order_by(LichHen.NgayGio).all()
    
    # Thống kê lượt khám trong tháng
    month_start = today.replace(day=1)
    month_exams = LichHen.query.filter(
        LichHen.MaBS == current_user.MaND,
        LichHen.NgayGio >= month_start,
        LichHen.TrangThai == 'Đã khám'
    ).count()
    
    # Thống kê theo ngày trong tuần
    daily_stats = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        
        day_appointments = LichHen.query.filter(
            LichHen.MaBS == current_user.MaND,
            LichHen.NgayGio.between(day_start, day_end),
            LichHen.TrangThai == 'Đã khám'
        ).count()
        
        daily_stats.append({
            'day': day.strftime('%a'),
            'count': day_appointments
        })
    
    # Lấy các bệnh nhân cần tái khám
    follow_up_patients = get_follow_up_patients(current_user.MaND)
    
    return render_template(
        'doctor/dashboard.html',
        today_appointments=today_appointments,
        week_appointments=week_appointments,
        month_exams=month_exams,
        daily_stats=daily_stats,
        follow_up_patients=follow_up_patients
    )

@doctor_bp.route('/history_search', methods=['GET', 'POST'])
@login_required
def history_search():
    patients = []
    if request.method == 'POST':
        keyword = request.form.get('keyword')
        patients = BenhNhan.query.filter(
            or_(BenhNhan.HoTen.contains(keyword), BenhNhan.SDT.contains(keyword))
        ).all()
    return render_template('doctor/history_search.html', patients=patients)

@doctor_bp.route('/history/<int:patient_id>')
@login_required
def patient_history(patient_id):
    if not current_user.has_role('BacSi'):
        flash('Không có quyền truy cập', 'danger')
        return redirect(url_for('auth.login'))

    # 1. Lấy thông tin bệnh nhân
    bn = BenhNhan.query.get_or_404(patient_id)

    # 2. Lấy lịch sử khám (để hiển thị bảng)
    history = db.session.query(KetQuaKham).join(LichHen).filter(
        LichHen.MaBN == patient_id,
        LichHen.TrangThai == 'Đã khám'
    ).order_by(KetQuaKham.NgayKham.desc()).all()
    
    # 3. Lấy dữ liệu chỉ số sinh tồn (để vẽ biểu đồ)
    # Join các bảng: ChiSo -> KetQua -> LichHen để lấy đúng bệnh nhân
    vitals = db.session.query(ChiSoSinhTon).join(KetQuaKham).join(LichHen).filter(
        LichHen.MaBN == patient_id,
        LichHen.TrangThai == 'Đã khám'
    ).order_by(KetQuaKham.NgayKham.asc()).all()

    # 4. Xử lý dữ liệu list ngay tại Python (Thay vì làm ở HTML gây lỗi)
    dates = [v.ket_qua.NgayKham.strftime('%d/%m') for v in vitals]
    nhiptim = [v.NhipTim if v.NhipTim else 0 for v in vitals]
    cannang = [v.CanNang if v.CanNang else 0 for v in vitals]
    
    return render_template(
        'doctor/history.html', 
        history=history, 
        bn=bn, 
        dates=dates,        # Truyền list ngày
        nhiptim=nhiptim,    # Truyền list nhịp tim
        cannang=cannang     # Truyền list cân nặng
    )

@doctor_bp.route('/exam-list')
@login_required
def exam_list():
    if not current_user.has_role('BacSi'):
        flash('Bạn không có quyền truy cập!', 'danger')
        return redirect(url_for('auth.login'))
    
    # Lấy danh sách và kiểm tra xem đã có chỉ số sinh tồn chưa
    queue_query = LichHen.query.filter_by(MaBS=current_user.MaND, TrangThai='Chờ khám').all()
    
    queue_data = []
    for item in queue_query:
        # Kiểm tra chỉ số sinh tồn thông qua KetQuaKham
        has_vitals = False
        if item.ket_qua:
            # Check if any vital signs exist for this exam result
            vitals = ChiSoSinhTon.query.filter_by(MaKQ=item.ket_qua.MaKQ).first()
            if vitals:
                has_vitals = True
        
        queue_data.append({
            'appt': item,
            'has_vitals': has_vitals
        })

    return render_template('doctor/exam_list.html', queue=queue_data)

@doctor_bp.route('/exam/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def exam_detail(appointment_id):
    if not current_user.has_role('BacSi'):
        flash('Bạn không có quyền truy cập!', 'danger')
        return redirect(url_for('auth.login'))
    
    appointment = LichHen.query.get_or_404(appointment_id)
    drugs = Thuoc.query.all()
    
    # Tạo hoặc lấy kết quả khám
    kq = KetQuaKham.query.filter_by(MaLH=appointment_id).first()
    if not kq:
        kq = KetQuaKham(MaLH=appointment_id, MaBS=current_user.MaND, NgayKham=datetime.now().date())
        db.session.add(kq)
        db.session.commit()
    
    # Lấy chỉ số sinh tồn nếu có
    vitals = ChiSoSinhTon.query.filter_by(MaKQ=kq.MaKQ).first()
    
    # Lấy danh sách dị ứng của bệnh nhân
    allergies = BenhNhanDiUng.query.filter_by(MaBN=appointment.MaBN).all()
    
    if request.method == 'POST':
        # Lưu kết quả khám
        kq.ChanDoan = request.form['chandoan']
        kq.HuongDieuTri = request.form['huongdieutri']
        
        # Lưu thông tin tái khám
        if request.form.get('canhbao_taikham'):
            try:
                kq.CanhBaoTaiKham = datetime.strptime(request.form.get('canhbao_taikham'), '%Y-%m-%d').date()
                kq.DaTaiKham = False
                kq.GhiChuTaiKham = request.form.get('ghichu_taikham', '')
            except ValueError:
                flash('Định dạng ngày tái khám không hợp lệ!', 'danger')
        
        db.session.commit()
        
        # Lưu chỉ số sinh tồn (nếu form có gửi lên)
        if vitals:
            # Cập nhật chỉ số sinh tồn đã tồn tại
            vitals.HuyetAp = request.form.get('huyetap')
            vitals.NhietDo = request.form.get('nhietdo')
            vitals.CanNang = request.form.get('cannang')
            vitals.NhipTim = request.form.get('nhiptim')
        else:
            # Tạo mới chỉ số sinh tồn
            vitals = ChiSoSinhTon(
                MaKQ=kq.MaKQ,
                HuyetAp=request.form.get('huyetap'),
                NhietDo=request.form.get('nhietdo'),
                CanNang=request.form.get('cannang'),
                NhipTim=request.form.get('nhiptim'),
                MaYT=current_user.MaND  # Giả sử người nhập là User hiện tại
            )
            db.session.add(vitals)
        
        # Kê đơn thuốc
        drug_ids = request.form.getlist('thuoc_id')
        quantities = request.form.getlist('soluong')
        usages = request.form.getlist('lieudung')
        
        if drug_ids:
            # Xóa đơn thuốc cũ nếu có
            old_dt = DonThuoc.query.filter_by(MaKQ=kq.MaKQ).first()
            if old_dt:
                # Xóa chi tiết đơn cũ
                ChiTietDon.query.filter_by(MaDT=old_dt.MaDT).delete()
                db.session.delete(old_dt)
            
            # Tạo đơn thuốc mới
            dt = DonThuoc(MaKQ=kq.MaKQ, TrangThai='Chờ phát')
            db.session.add(dt)
            db.session.flush()
            
            for i in range(len(drug_ids)):
                if drug_ids[i] and quantities[i]:
                    detail = ChiTietDon(
                        MaDT=dt.MaDT,
                        MaThuoc=int(drug_ids[i]),
                        SoLuong=int(quantities[i]),
                        LieuDung=usages[i]
                    )
                    db.session.add(detail)
        
        # Cập nhật trạng thái lịch hẹn
        appointment.TrangThai = 'Đã khám'
        db.session.commit()
        flash('Hoàn tất khám bệnh!', 'success')
        return redirect(url_for('doctor.exam_list'))

    return render_template(
        'doctor/exam_detail.html', 
        appt=appointment, 
        drugs=drugs, 
        kq=kq, 
        vitals=vitals,
        allergies=allergies
    )

@doctor_bp.route('/check_drug_interactions', methods=['POST'])
@login_required
def check_interactions():
    if not current_user.has_role('BacSi'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    drug_ids = request.json.get('drug_ids', [])
    if not drug_ids:
        return jsonify({'interactions': []})
    
    # Chuyển đổi string IDs sang integers
    drug_ids = [int(id) for id in drug_ids]
    
    # Kiểm tra tương tác thuốc
    interactions = check_drug_interactions(drug_ids)
    
    return jsonify({'interactions': interactions})

@doctor_bp.route('/check_allergy_warnings', methods=['POST'])
@login_required
def check_allergies():
    if not current_user.has_role('BacSi'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    drug_ids = request.json.get('drug_ids', [])
    patient_id = request.json.get('patient_id')
    
    if not drug_ids or not patient_id:
        return jsonify({'warnings': []})
    
    # Chuyển đổi string IDs sang integers
    drug_ids = [int(id) for id in drug_ids]
    
    # Kiểm tra dị ứng
    warnings = check_allergy_warnings(drug_ids, patient_id)
    
    return jsonify({'warnings': warnings})

@doctor_bp.route('/chat')
@login_required
def chat():
    # Lấy 50 tin nhắn gần nhất
    history = TinNhan.query.order_by(TinNhan.ThoiGian.asc()).limit(50).all()
    return render_template('chat/medical_chat.html', history_messages=history)

# API Gửi tin nhắn (AJAX)
@doctor_bp.route('/api/send_message', methods=['POST'])
@login_required
def api_send_message():
    data = request.json
    content = data.get('message')
    if content:
        msg = TinNhan(
            NguoiGui_ID=current_user.MaND,
            NoiDung=content,
            PhongChat='medical_team'
        )
        db.session.add(msg)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

# API Lấy tin nhắn (AJAX Polling)
@doctor_bp.route('/api/get_messages')
@login_required
def api_get_messages():
    # Lấy 50 tin nhắn gần nhất
    messages = TinNhan.query.order_by(TinNhan.ThoiGian.asc()).limit(50).all()
    results = []
    for msg in messages:
        results.append({
            'user': msg.nguoi_gui.HoTen,
            'content': msg.NoiDung,
            'time': msg.ThoiGian.strftime('%H:%M'),
            'is_me': msg.NguoiGui_ID == current_user.MaND
        })
    return jsonify(results)