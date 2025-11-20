from app import create_app, db
from app.models import LichHen, BenhNhan, NguoiDung
from datetime import datetime

app = create_app()

with app.app_context():
    # 1. Tạo bệnh nhân mẫu nếu chưa có
    bn = BenhNhan.query.first()
    if not bn:
        bn = BenhNhan(HoTen="Nguyễn Văn A", NgaySinh=datetime(1990, 1, 1).date(), GioiTinh="Nam", SDT="0909123456", DiaChi="Bình Dương")
        db.session.add(bn)
        db.session.commit()
        print("Đã tạo Bệnh nhân mẫu.")

    # 2. Lấy bác sĩ mẫu (ID thường là 2 theo setup_db.py cũ)
    bs = NguoiDung.query.filter_by(TenDangNhap='bacsi').first()
    
    if bn and bs:
        # 3. Tạo lịch hẹn mẫu
        lh = LichHen(
            MaBN=bn.MaBN, 
            MaBS=bs.MaND, 
            NgayGio=datetime.now(), 
            TrangThai='Chờ khám'
        )
        db.session.add(lh)
        db.session.commit()
        print(f"Đã tạo Lịch hẹn mẫu với ID: {lh.MaLH}")
    else:
        print("Cần chạy setup_db.py trước để có User và Bệnh nhân!")