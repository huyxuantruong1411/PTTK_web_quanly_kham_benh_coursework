# app/setup_db.py (Cập nhật hoàn chỉnh)
from app import create_app, db
from app.models import *

app = create_app()

with app.app_context():
    # 1. Tạo toàn bộ bảng
    db.create_all()
    print("Đã tạo Database Schema thành công!")

    # 2. Tạo dữ liệu mẫu cho vai trò
    if not VaiTro.query.first():
        vai_tros = [
            VaiTro(TenVaiTro='Admin', MoTa='Quản trị viên hệ thống'),
            VaiTro(TenVaiTro='BacSi', MoTa='Bác sĩ'),
            VaiTro(TenVaiTro='YTa', MoTa='Y tá'),
            VaiTro(TenVaiTro='DuocSi', MoTa='Dược sĩ'),
            VaiTro(TenVaiTro='LeTan', MoTa='Nhân viên lễ tân'),
            VaiTro(TenVaiTro='BenhNhan', MoTa='Bệnh nhân')
        ]
        db.session.add_all(vai_tros)
        db.session.commit()
        print("Đã thêm dữ liệu mẫu VaiTro!")

    # 3. Tạo dữ liệu mẫu nếu chưa có
    if not NguoiDung.query.first():
        # Admin
        admin = NguoiDung(TenDangNhap='admin', HoTen='Quản trị viên', Email='admin@antamclinic.com')
        admin.set_password('123')
        db.session.add(admin)
        db.session.flush()  # Lấy ID của admin
        
        # Gán vai trò Admin
        admin_role = NguoiDung_VaiTro(MaND=admin.MaND, MaVaiTro=1)  # Giả sử Admin có MaVaiTro = 1
        db.session.add(admin_role)
        
        # Bác sĩ
        bs = NguoiDung(TenDangNhap='bacsi', HoTen='BS. Nguyen Van A', Email='bacsi@antamclinic.com', ChuyenKhoa='Noi Khoa')
        bs.set_password('123')
        db.session.add(bs)
        db.session.flush()  # Lấy ID của bác sĩ
        
        # Gán vai trò Bác sĩ
        bs_role = NguoiDung_VaiTro(MaND=bs.MaND, MaVaiTro=2)  # Giả sử BacSi có MaVaiTro = 2
        db.session.add(bs_role)
        
        # Lễ tân
        lt = NguoiDung(TenDangNhap='letan', HoTen='Le Tan B', Email='letan@antamclinic.com')
        lt.set_password('123')
        db.session.add(lt)
        db.session.flush()  # Lấy ID của lễ tân
        
        # Gán vai trò Lễ tân
        lt_role = NguoiDung_VaiTro(MaND=lt.MaND, MaVaiTro=5)  # Giả sử LeTan có MaVaiTro = 5
        db.session.add(lt_role)
        
        # Dược sĩ
        ds = NguoiDung(TenDangNhap='duocsi', HoTen='Duoc Si C', Email='duocsi@antamclinic.com')
        ds.set_password('123')
        db.session.add(ds)
        db.session.flush()  # Lấy ID của dược sĩ
        
        # Gán vai trò Dược sĩ
        ds_role = NguoiDung_VaiTro(MaND=ds.MaND, MaVaiTro=4)  # Giả sử DuocSi có MaVaiTro = 4
        db.session.add(ds_role)
        
        # Y tá
        yt = NguoiDung(TenDangNhap='yta', HoTen='Y Ta D', Email='yta@antamclinic.com')
        yt.set_password('123')
        db.session.add(yt)
        db.session.flush()  # Lấy ID của y tá
        
        # Gán vai trò Y tá
        yt_role = NguoiDung_VaiTro(MaND=yt.MaND, MaVaiTro=3)  # Giả sử YTa có MaVaiTro = 3
        db.session.add(yt_role)
        
        db.session.commit()
        print("Đã thêm dữ liệu mẫu User!")
    
    # 4. Tạo dữ liệu mẫu cho thuốc và tương tác thuốc
    if not Thuoc.query.first():
        # Tạo thuốc mẫu
        thuocs = [
            Thuoc(TenThuoc='Paracetamol', DonVi='Viên', HanDung=datetime(2025, 12, 31).date(), Gia=5000, SoLuongTon=100, HoatChat='Paracetamol'),
            Thuoc(TenThuoc='Amoxicillin', DonVi='Viên', HanDung=datetime(2025, 6, 30).date(), Gia=8000, SoLuongTon=50, HoatChat='Amoxicillin'),
            Thuoc(TenThuoc='Ibuprofen', DonVi='Viên', HanDung=datetime(2025, 10, 15).date(), Gia=6000, SoLuongTon=30, HoatChat='Ibuprofen'),
            Thuoc(TenThuoc='Vitamin C', DonVi='Viên', HanDung=datetime(2026, 3, 20).date(), Gia=3000, SoLuongTon=200, HoatChat='Ascorbic acid'),
            Thuoc(TenThuoc='Omeprazole', DonVi='Viên', HanDung=datetime(2025, 8, 10).date(), Gia=12000, SoLuongTon=40, HoatChat='Omeprazole')
        ]
        db.session.add_all(thuocs)
        db.session.commit()
        print("Đã thêm dữ liệu mẫu Thuoc!")
        
        # Tạo tương tác thuốc mẫu
        if not TuongTacThuoc.query.first():
            # Paracetamol và Ibuprofen có thể gây tương tác
            tt1 = TuongTacThuoc(MaThuoc1=1, MaThuoc2=3, MucDo='Trung bình', MoTa='Sử dụng đồng thời có thể tăng nguy cơ tác dụng phụ trên dạ dày')
            db.session.add(tt1)
            
            # Amoxicillin và Omeprazole có thể tương tác
            tt2 = TuongTacThuoc(MaThuoc1=2, MaThuoc2=5, MucDo='Nhẹ', MoTa='Omeprazole có thể làm giảm hấp thu Amoxicillin')
            db.session.add(tt2)
            
            db.session.commit()
            print("Đã thêm dữ liệu mẫu TuongTacThuoc!")