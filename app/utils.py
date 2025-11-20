from flask_mail import Mail, Message
from flask import current_app
from datetime import datetime, timedelta
from sqlalchemy import or_, and_
from app.models import BenhNhan, KetQuaKham, LichHen, NguoiDung, Thuoc, DonThuoc, ChiTietDon, TuongTacThuoc, BenhNhanDiUng
from app import db

mail = Mail()

def send_reminder_email(email, subject, body):
    msg = Message(subject, recipients=[email])
    msg.body = body
    mail.send(msg)

def send_appointment_reminder(appointment):
    """Gửi email nhắc lịch hẹn cho bệnh nhân"""
    patient = appointment.benh_nhan
    doctor = appointment.bac_si
    
    subject = "Nhắc nhở lịch hẹn khám bệnh"
    body = f"""
    Kính gửi {patient.HoTen},
    
    Đây là email nhắc nhở về lịch hẹn khám bệnh của bạn:
    
    Bác sĩ: {doctor.HoTen}
    Chuyên khoa: {doctor.ChuyenKhoa}
    Thời gian: {appointment.NgayGio.strftime('%H:%M ngày %d/%m/%Y')}
    
    Vui lòng đến trước 15 phút để hoàn tất thủ tục.
    
    Trân trọng,
    Phòng khám An Tâm
    """
    
    send_reminder_email(patient.Email, subject, body)

def send_appointment_confirmation(appointment):
    """Gửi email xác nhận lịch hẹn cho bệnh nhân"""
    patient = appointment.benh_nhan
    doctor = appointment.bac_si
    
    subject = "Xác nhận lịch hẹn khám bệnh"
    body = f"""
    Kính gửi {patient.HoTen},
    
    Lịch hẹn khám bệnh của bạn đã được xác nhận:
    
    Bác sĩ: {doctor.HoTen}
    Chuyên khoa: {doctor.ChuyenKhoa}
    Thời gian: {appointment.NgayGio.strftime('%H:%M ngày %d/%m/%Y')}
    
    Vui lòng đến trước 15 phút để hoàn tất thủ tục.
    
    Trân trọng,
    Phòng khám An Tâm
    """
    
    send_reminder_email(patient.Email, subject, body)

def send_appointment_cancellation(appointment):
    """Gửi email thông báo hủy lịch hẹn cho bệnh nhân"""
    patient = appointment.benh_nhan
    
    subject = "Thông báo hủy lịch hẹn khám bệnh"
    body = f"""
    Kính gửi {patient.HoTen},
    
    Lịch hẹn khám bệnh của bạn vào lúc {appointment.NgayGio.strftime('%H:%M ngày %d/%m/%Y')} đã bị hủy.
    
    Nếu bạn có thắc mắc, vui lòng liên hệ với phòng khám.
    
    Trân trọng,
    Phòng khám An Tâm
    """
    
    send_reminder_email(patient.Email, subject, body)

def send_prescription_ready(prescription):
    """Gửi email thông báo đơn thuốc đã sẵn sàng"""
    appointment = prescription.ket_qua.lich_hen
    patient = appointment.benh_nhan
    
    subject = "Thông báo đơn thuốc đã sẵn sàng"
    body = f"""
    Kính gửi {patient.HoTen},
    
    Đơn thuốc từ lịch khám vào ngày {appointment.NgayGio.strftime('%d/%m/%Y')} đã sẵn sàng để nhận.
    
    Vui lòng đến quầy dược để nhận thuốc theo đơn.
    
    Trân trọng,
    Phòng khám An Tâm
    """
    
    send_reminder_email(patient.Email, subject, body)

def search_patients(query):
    """Tìm kiếm bệnh nhân theo tên, SĐT hoặc email"""
    return BenhNhan.query.filter(
        or_(
            BenhNhan.HoTen.contains(query),
            BenhNhan.SDT.contains(query),
            BenhNhan.Email.contains(query)
        )
    ).all()

def search_appointments(query, user_role=None, user_id=None):
    """Tìm kiếm lịch hẹn theo tên bệnh nhân, tên bác sĩ hoặc ngày"""
    appointments = LichHen.query.join(BenhNhan).join(NguoiDung, LichHen.MaBS == NguoiDung.MaND).filter(
        or_(
            BenhNhan.HoTen.contains(query),
            NguoiDung.HoTen.contains(query),
            LichHen.NgayGio.like(f'%{query}%')
        )
    )
    
    # Nếu là bác sĩ, chỉ hiển thị lịch hẹn của bác sĩ đó
    if user_role == 'BacSi':
        appointments = appointments.filter(LichHen.MaBS == user_id)
    
    return appointments.all()

def search_medicines(query):
    """Tìm kiếm thuốc theo tên hoặc đơn vị"""
    return Thuoc.query.filter(
        or_(
            Thuoc.TenThuoc.contains(query),
            Thuoc.DonVi.contains(query)
        )
    ).all()

def search_prescriptions(query):
    """Tìm kiếm đơn thuốc theo tên bệnh nhân hoặc tên thuốc"""
    return DonThuoc.query.join(KetQuaKham).join(LichHen).join(BenhNhan).filter(
        or_(
            BenhNhan.HoTen.contains(query),
            DonThuoc.NgayKe.like(f'%{query}%')
        )
    ).all()

def search_users(query, role=None):
    """Tìm kiếm người dùng theo tên, tên đăng nhập hoặc email"""
    users = NguoiDung.query.filter(
        or_(
            NguoiDung.HoTen.contains(query),
            NguoiDung.TenDangNhap.contains(query),
            NguoiDung.Email.contains(query)
        )
    )
    
    if role:
        users = users.filter(NguoiDung.VaiTro == role)
    
    return users.all()

def check_drug_interactions(drug_ids):
    """Kiểm tra tương tác thuốc giữa các thuốc trong danh sách"""
    if len(drug_ids) < 2:
        return []
    
    interactions = []
    
    # Lấy tất cả các cặp thuốc có thể tương tác
    for i in range(len(drug_ids)):
        for j in range(i+1, len(drug_ids)):
            drug1_id = drug_ids[i]
            drug2_id = drug_ids[j]
            
            # Kiểm tra tương tác theo cả hai hướng
            interaction = TuongTacThuoc.query.filter(
                or_(
                    and_(TuongTacThuoc.MaThuoc1 == drug1_id, TuongTacThuoc.MaThuoc2 == drug2_id),
                    and_(TuongTacThuoc.MaThuoc1 == drug2_id, TuongTacThuoc.MaThuoc2 == drug1_id)
                )
            ).first()
            
            if interaction:
                drug1 = Thuoc.query.get(drug1_id)
                drug2 = Thuoc.query.get(drug2_id)
                interactions.append({
                    'drug1': drug1.TenThuoc,
                    'drug2': drug2.TenThuoc,
                    'severity': interaction.MucDo,
                    'description': interaction.MoTa
                })
    
    return interactions

def check_expiry_warnings():
    """Kiểm tra thuốc sắp hết hạn (trong 30 ngày tới)"""
    from datetime import date, timedelta
    
    thirty_days_from_now = date.today() + timedelta(days=30)
    
    expiring_medicines = Thuoc.query.filter(
        Thuoc.HanDung <= thirty_days_from_now,
        Thuoc.SoLuongTon > 0
    ).all()
    
    return expiring_medicines

def check_stock_warnings():
    """Kiểm tra thuốc sắp hết hàng (dưới ngưỡng cảnh báo)"""
    low_stock_medicines = Thuoc.query.filter(
        Thuoc.SoLuongTon <= Thuoc.SoLuongCanhBao
    ).all()
    
    return low_stock_medicines

def get_patient_allergies(patient_id):
    """Lấy danh sách dị ứng của bệnh nhân"""
    return BenhNhanDiUng.query.filter_by(MaBN=patient_id).all()

def check_allergy_warnings(drug_ids, patient_id):
    """Kiểm tra thuốc có gây dị ứng cho bệnh nhân không"""
    allergies = get_patient_allergies(patient_id)
    if not allergies:
        return []
    
    warnings = []
    for drug_id in drug_ids:
        drug = Thuoc.query.get(drug_id)
        for allergy in allergies:
            # Kiểm tra nếu hoạt chất của thuốc trùng với chất gây dị ứng
            if drug.HoatChat and drug.HoatChat.lower() == allergy.TenChat.lower():
                warnings.append({
                    'drug': drug.TenThuoc,
                    'allergen': allergy.TenChat,
                    'reaction': allergy.PhanUng
                })
    
    return warnings

def get_follow_up_patients(doctor_id):
    """Lấy danh sách bệnh nhân cần tái khám cho bác sĩ"""
    today = datetime.now().date()
    
    # SỬA LỖI AMBIGUOUS JOIN:
    # 1. Bắt đầu từ KetQuaKham
    # 2. Join LichHen (qua FK trong KQKB)
    # 3. Join BenhNhan (qua FK trong LichHen)
    follow_ups = db.session.query(
        KetQuaKham,
        BenhNhan
    ).join(LichHen, KetQuaKham.MaLH == LichHen.MaLH) \
    .join(BenhNhan, LichHen.MaBN == BenhNhan.MaBN) \
    .filter(
        KetQuaKham.MaBS == doctor_id,
        KetQuaKham.CanhBaoTaiKham <= today,
        KetQuaKham.DaTaiKham == False
    ).all()
    
    # Cần định dạng lại kết quả trả về để phù hợp với doctor/dashboard.html
    # File doctor/dashboard.html sử dụng: HoTen, NgayKham, GhiChu
    # Dữ liệu hiện tại là list of tuples: [(KetQuaKham_obj, BenhNhan_obj), ...]

    results = []
    for kq, bn in follow_ups:
        results.append({
            'HoTen': bn.HoTen,
            'NgayKham': kq.NgayKham,
            'GhiChu': kq.GhiChuTaiKham,  # Sử dụng GhiChuTaiKham thay vì GhiChu
            'MaBN': bn.MaBN
        })
    
    # return follow_ups # Thay thế bằng results đã được định dạng
    return results