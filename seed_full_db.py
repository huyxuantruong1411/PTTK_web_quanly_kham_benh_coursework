import random
from datetime import datetime, timedelta, date
from faker import Faker
from app import create_app, db
from app.models import (
    NguoiDung, VaiTro, NguoiDung_VaiTro, BenhNhan, Thuoc, 
    LichHen, KetQuaKham, ChiSoSinhTon, DonThuoc, ChiTietDon, 
    HoaDon, TuongTacThuoc, GiaoDichKho, TinNhan, BenhNhanDiUng,
    BaoCao, CauHinhBaoCao
)
from werkzeug.security import generate_password_hash

# Cấu hình Faker tiếng Việt
fake = Faker('vi_VN')

app = create_app()

# --- CẤU HÌNH SỐ LƯỢNG DỮ LIỆU ---
NUM_DOCTORS = 10
NUM_NURSES = 15
NUM_PHARMACISTS = 5
NUM_RECEPTIONISTS = 5
NUM_PATIENTS = 2000     # Tạo 2000 bệnh nhân
NUM_APPOINTMENTS = 5000 # Tạo 5000 lịch khám/hồ sơ bệnh án

# Danh sách thuốc mẫu thực tế để dữ liệu nhìn "thật" hơn
SAMPLE_DRUGS = [
    ("Panadol Extra", "Viên", "Paracetamol", 2000),
    ("Efferalgan 500mg", "Viên", "Paracetamol", 3000),
    ("Amoxicillin 500mg", "Viên", "Amoxicillin", 5000),
    ("Augmentin 625mg", "Viên", "Amoxicillin + Clavulanate", 15000),
    ("Ibuprofen 400mg", "Viên", "Ibuprofen", 4000),
    ("Omeprazol 20mg", "Viên", "Omeprazole", 2500),
    ("Berberin", "Viên", "Berberin", 1000),
    ("Vitamin C 500mg", "Viên", "Ascorbic Acid", 1500),
    ("Gaviscon", "Gói", "Sodium alginate", 8000),
    ("Smecta", "Gói", "Diosmectite", 5000),
    ("Eugica", "Viên", "Tinh dầu tràm", 2000),
    ("Decolgen", "Viên", "Paracetamol + Phenylephrine", 3000),
    ("Zyrtec 10mg", "Viên", "Cetirizine", 7000),
    ("Fugacar", "Viên", "Mebendazole", 20000),
    ("Oresol", "Gói", "Glucose + Electrolytes", 3000),
    ("Glucophage", "Viên", "Metformin", 4500),
    ("Lipitor", "Viên", "Atorvastatin", 12000),
    ("Plavix", "Viên", "Clopidogrel", 18000),
    ("Ventolin", "Chai", "Salbutamol", 85000),
    ("Neurontin", "Viên", "Gabapentin", 11000)
]

CHUYEN_KHOA = ["Nội tổng quát", "Nhi khoa", "Tai Mũi Họng", "Tim mạch", "Tiêu hóa", "Da liễu", "Xương khớp"]

def seed_roles():
    """1. Tạo Vai Trò (Nếu chưa có)"""
    print("--- Đang tạo Vai Trò ---")
    roles = ['Admin', 'BacSi', 'YTa', 'DuocSi', 'LeTan', 'BenhNhan']
    existing_roles = {r.TenVaiTro for r in VaiTro.query.all()}
    
    new_roles = []
    for r in roles:
        if r not in existing_roles:
            new_roles.append(VaiTro(TenVaiTro=r, MoTa=f'Vai trò {r} trong hệ thống'))
    
    if new_roles:
        db.session.add_all(new_roles)
        db.session.commit()
    print(f"Đã đảm bảo các vai trò: {roles}")

def create_staff(role_name, count, prefix):
    """Hàm phụ trợ tạo nhân viên"""
    role = VaiTro.query.filter_by(TenVaiTro=role_name).first()
    staff_ids = []
    
    print(f"--- Đang tạo {count} {role_name} ---")
    for i in range(count):
        username = f"{prefix}_{i+1}"
        if not NguoiDung.query.filter_by(TenDangNhap=username).first():
            user = NguoiDung(
                TenDangNhap=username,
                HoTen=fake.name(),
                Email=f"{username}@antam.com",
                SDT=fake.phone_number()[:15],
                ChuyenKhoa=random.choice(CHUYEN_KHOA) if role_name == 'BacSi' else None,
                TrangThai=True
            )
            user.set_password('123')
            db.session.add(user)
            db.session.flush() # Để lấy ID
            
            # Gán vai trò
            ur = NguoiDung_VaiTro(MaND=user.MaND, MaVaiTro=role.MaVaiTro)
            db.session.add(ur)
            staff_ids.append(user.MaND)
    
    db.session.commit()
    # Nếu không tạo mới (do đã tồn tại), query lại ID
    if not staff_ids:
        staff_users = NguoiDung.query.join(NguoiDung_VaiTro).filter(NguoiDung_VaiTro.MaVaiTro == role.MaVaiTro).all()
        staff_ids = [u.MaND for u in staff_users]
        
    return staff_ids

def seed_drugs():
    """2. Tạo Thuốc và Tương tác thuốc"""
    print("--- Đang tạo Thuốc ---")
    if Thuoc.query.count() < 5:
        for name, unit, active, price in SAMPLE_DRUGS:
            t = Thuoc(
                TenThuoc=name, DonVi=unit, HoatChat=active, Gia=price,
                SoLuongTon=random.randint(100, 2000),
                SoLuongCanhBao=50,
                HanDung=fake.date_between(start_date='+6M', end_date='+3y')
            )
            db.session.add(t)
        db.session.commit()
    
    # Tạo tương tác thuốc (ngẫu nhiên)
    print("--- Đang tạo Tương tác thuốc ---")
    all_drugs = Thuoc.query.all()
    drug_ids = [d.MaThuoc for d in all_drugs]
    if TuongTacThuoc.query.count() == 0 and len(drug_ids) > 2:
        for _ in range(10):
            d1, d2 = random.sample(drug_ids, 2)
            tt = TuongTacThuoc(
                MaThuoc1=d1, MaThuoc2=d2,
                MucDo=random.choice(['Nhẹ', 'Trung bình', 'Nghiêm trọng']),
                MoTa=fake.sentence()
            )
            db.session.add(tt)
        db.session.commit()
    return drug_ids

def seed_patients_mass(count):
    """3. Tạo Bệnh nhân số lượng lớn"""
    print(f"--- Đang tạo {count} Bệnh nhân (Có thể mất vài giây) ---")
    role_bn = VaiTro.query.filter_by(TenVaiTro='BenhNhan').first()
    existing_count = BenhNhan.query.count()
    needed = count - existing_count
    
    patient_ids = []
    
    if needed > 0:
        for i in range(needed):
            # Tạo User
            username = f"bn_{existing_count + i + 1}_{random.randint(1000,9999)}"
            ho_ten = fake.name()
            user = NguoiDung(
                TenDangNhap=username,
                HoTen=ho_ten,
                Email=fake.email(),
                SDT=fake.phone_number()[:15],
                TrangThai=True
            )
            user.set_password('123')
            db.session.add(user)
            db.session.flush()
            
            # Gán role
            db.session.add(NguoiDung_VaiTro(MaND=user.MaND, MaVaiTro=role_bn.MaVaiTro))
            
            # Tạo Bệnh nhân
            bn = BenhNhan(
                MaND=user.MaND,
                HoTen=ho_ten,
                NgaySinh=fake.date_of_birth(minimum_age=1, maximum_age=90),
                GioiTinh=random.choice(['Nam', 'Nữ']),
                SDT=user.SDT,
                DiaChi=fake.address(),
                Email=user.Email
            )
            db.session.add(bn)
            db.session.flush()
            patient_ids.append(bn.MaBN)
            
            # Tạo Dị ứng (10% bệnh nhân bị dị ứng)
            if random.random() < 0.1:
                du = BenhNhanDiUng(
                    MaBN=bn.MaBN,
                    TenChat=random.choice(['Paracetamol', 'Phấn hoa', 'Hải sản', 'Penicillin']),
                    PhanUng='Nổi mẩn đỏ, khó thở nhẹ'
                )
                db.session.add(du)
                
            if i % 100 == 0:
                db.session.commit()
                print(f"   -> Đã tạo {i} bệnh nhân...")
                
        db.session.commit()
    
    # Lấy lại toàn bộ ID bệnh nhân
    all_bns = db.session.query(BenhNhan.MaBN).all()
    return [x[0] for x in all_bns]

def seed_clinical_process(num_visits, doc_ids, nurse_ids, patient_ids, drug_ids, recep_ids):
    """4. Tạo quy trình khám chữa bệnh (Lịch hẹn -> KQ -> Đơn thuốc -> Hóa đơn -> Kho)"""
    print(f"--- Đang tạo {num_visits} Lượt khám bệnh (Quy trình đầy đủ) ---")
    
    for i in range(num_visits):
        # Chọn ngẫu nhiên
        ma_bn = random.choice(patient_ids)
        ma_bs = random.choice(doc_ids)
        ma_yt = random.choice(nurse_ids) if nurse_ids else ma_bs
        
        # Ngày hẹn (trong vòng 1 năm qua)
        visit_date = fake.date_time_between(start_date='-1y', end_date='now')
        
        # Trạng thái Lịch hẹn
        rand = random.random()
        if visit_date > datetime.now():
            status_lh = 'Chờ khám'
        elif rand < 0.1:
            status_lh = 'Hủy'
        else:
            status_lh = 'Đã khám'
            
        # A. TẠO LỊCH HẸN
        lh = LichHen(
            MaBN=ma_bn, MaBS=ma_bs, MaYT=ma_yt,
            NgayGio=visit_date, TrangThai=status_lh
        )
        db.session.add(lh)
        db.session.flush()
        
        # Nếu đã khám thì sinh tiếp dữ liệu
        if status_lh == 'Đã khám':
            # B. TẠO KẾT QUẢ KHÁM
            kq = KetQuaKham(
                MaLH=lh.MaLH, MaBS=ma_bs,
                ChanDoan=fake.sentence(nb_words=6),
                HuongDieuTri=fake.sentence(nb_words=10),
                NgayKham=visit_date.date(),
                DaTaiKham=random.choice([True, False])
            )
            if random.random() < 0.3: # 30% cần tái khám
                kq.CanhBaoTaiKham = (visit_date + timedelta(days=7)).date()
                kq.GhiChuTaiKham = "Tái khám theo dõi"
            db.session.add(kq)
            db.session.flush()
            
            # C. TẠO CHỈ SỐ SINH TỒN
            cs = ChiSoSinhTon(
                MaKQ=kq.MaKQ, MaYT=ma_yt,
                HuyetAp=f"{random.randint(110,140)}/{random.randint(70,90)}",
                NhietDo=round(random.uniform(36.5, 38.5), 1),
                CanNang=random.randint(40, 90),
                NhipTim=random.randint(60, 100)
            )
            db.session.add(cs)
            
            # D. TẠO ĐƠN THUỐC & CHI TIẾT (70% có thuốc)
            tong_tien_thuoc = 0
            ma_dt = None
            
            if random.random() < 0.7:
                # --- LOGIC MỚI: Random trạng thái 'Chờ phát' ---
                # Nếu ngày khám là 2 ngày gần đây hoặc random 20% => Chờ phát
                is_recent = visit_date.date() >= (datetime.now() - timedelta(days=2)).date()
                
                if is_recent or random.random() < 0.2:
                    trang_thai_don = 'Chờ phát'
                else:
                    trang_thai_don = 'Đã phát'

                dt = DonThuoc(
                    MaKQ=kq.MaKQ,
                    NgayKe=visit_date.date(),
                    TrangThai=trang_thai_don
                )
                db.session.add(dt)
                db.session.flush()
                ma_dt = dt.MaDT
                
                # Thêm thuốc vào đơn
                num_drugs_in_prescription = random.randint(1, 4)
                chosen_drugs = random.sample(drug_ids, num_drugs_in_prescription)
                
                for d_id in chosen_drugs:
                    qty = random.randint(5, 20)
                    drug_obj = Thuoc.query.get(d_id)
                    
                    ct = ChiTietDon(
                        MaDT=dt.MaDT, MaThuoc=d_id,
                        SoLuong=qty,
                        LieuDung="Sáng 1 viên, Tối 1 viên",
                        GhiChu="Uống sau ăn"
                    )
                    db.session.add(ct)
                    tong_tien_thuoc += float(drug_obj.Gia) * qty
                    
                    # E. TẠO GIAO DỊCH KHO 
                    # Chỉ trừ kho nếu đơn ĐÃ PHÁT
                    if trang_thai_don == 'Đã phát':
                        gd = GiaoDichKho(
                            MaThuoc=d_id,
                            MaND=ma_bs, 
                            Loai='Xuất (Kê đơn)',
                            SoLuong=qty,
                            Ngay=visit_date.date()
                        )
                        db.session.add(gd)

            # F. TẠO HÓA ĐƠN
            tien_kham = 150000
            
            # Logic thanh toán: Nếu đơn thuốc 'Chờ phát' -> 'Chưa thanh toán' (tùy quy trình, ở đây giả sử chưa)
            trang_thai_hd = 'Đã thanh toán'
            if ma_dt and dt.TrangThai == 'Chờ phát' and random.random() < 0.5:
                 trang_thai_hd = 'Chưa thanh toán'

            hd = HoaDon(
                MaLH=lh.MaLH,
                MaDT=ma_dt,
                TongTien=tien_kham + tong_tien_thuoc,
                NgayThanhToan=visit_date.date(),
                TrangThai=trang_thai_hd
            )
            db.session.add(hd)
            
        if i % 100 == 0:
            db.session.commit()
            print(f"   -> Đã xử lý {i} lượt khám...")
            
    db.session.commit()

def seed_todays_queue(doc_ids, patient_ids):
    """Tạo dữ liệu hàng chờ khám CHO HÔM NAY (để bác sĩ có việc làm ngay)"""
    print("--- Đang tạo Hàng chờ khám cho hôm nay ---")
    
    today = datetime.now().replace(hour=7, minute=0, second=0, microsecond=0)
    count = 0
    
    # Duyệt qua từng bác sĩ, mỗi người cho 5-10 bệnh nhân chờ
    for doc_id in doc_ids:
        # Tạo 5-10 bệnh nhân đang chờ khám cho mỗi bác sĩ
        num_patients = random.randint(5, 10)
        
        for i in range(num_patients):
            ma_bn = random.choice(patient_ids)
            
            # Thời gian hẹn: rải rác từ sáng đến giờ hiện tại + 2 tiếng
            # Để giả lập có người hẹn sáng, người hẹn chiều
            minutes_offset = random.randint(0, 480) # Trong vòng 8 tiếng làm việc
            appt_time = today + timedelta(minutes=minutes_offset)
            
            # 80% là Chờ khám (để hiện lên danh sách), 20% là Đang khám (nếu có trạng thái này)
            status = 'Chờ khám'
            
            lh = LichHen(
                MaBN=ma_bn,
                MaBS=doc_id,
                MaYT=None, # Chưa có y tá nhận hoặc có thể random
                NgayGio=appt_time,
                TrangThai=status
            )
            db.session.add(lh)
            count += 1
            
    db.session.commit()
    print(f"   -> Đã thêm {count} bệnh nhân vào hàng chờ hôm nay.")

def seed_messages(users_ids):
    """5. Tạo tin nhắn nội bộ"""
    print("--- Đang tạo Tin nhắn nội bộ ---")
    if TinNhan.query.count() < 50:
        for _ in range(100):
            sender = random.choice(users_ids)
            # 50% tin nhắn riêng, 50% tin nhắn nhóm
            if random.random() < 0.5:
                receiver = random.choice(users_ids)
                room = None
            else:
                receiver = None
                room = random.choice(['general', 'medical_team'])
            
            tn = TinNhan(
                NguoiGui_ID=sender,
                NguoiNhan_ID=receiver,
                NoiDung=fake.sentence(),
                ThoiGian=fake.date_time_between(start_date='-1M', end_date='now'),
                PhongChat=room
            )
            db.session.add(tn)
        db.session.commit()

def seed_reports(admin_id):
    """6. Tạo dữ liệu Báo cáo"""
    print("--- Đang tạo Báo cáo mẫu ---")
    if BaoCao.query.count() < 5:
        for _ in range(5):
            bc = BaoCao(
                MaND=admin_id,
                LoaiBaoCao='DoanhThu',
                TuNgay=fake.date_between(start_date='-3M', end_date='-2M'),
                DenNgay=fake.date_between(start_date='-1M', end_date='today'),
                TongSo=random.randint(100, 500),
                DoanhThu=random.randint(10000000, 50000000),
                NgayLap=datetime.now().date()
            )
            db.session.add(bc)
            db.session.flush()
            
            ch = CauHinhBaoCao(
                MaBC=bc.MaBC,
                KyBaoCao='Tháng',
                TieuChi='Tổng doanh thu theo tháng'
            )
            db.session.add(ch)
        db.session.commit()

def run_seeding():
    with app.app_context():
        print("🚀 BẮT ĐẦU QUÁ TRÌNH SEEDING DATA LỚN...")
        
        # 1. Roles
        seed_roles()
        
        # 2. Staff Users
        doc_ids = create_staff('BacSi', NUM_DOCTORS, 'bs')
        nurse_ids = create_staff('YTa', NUM_NURSES, 'yta')
        phar_ids = create_staff('DuocSi', NUM_PHARMACISTS, 'ds')
        recep_ids = create_staff('LeTan', NUM_RECEPTIONISTS, 'letan')
        admin_ids = create_staff('Admin', 1, 'admin')
        
        all_staff_ids = doc_ids + nurse_ids + phar_ids + recep_ids + admin_ids
        
        # 3. Drugs & Interactions
        drug_ids = seed_drugs()
        
        # 4. Patients (Large volume)
        patient_ids = seed_patients_mass(NUM_PATIENTS)
        
        # 5. Clinical Process (Lịch sử quá khứ)
        seed_clinical_process(
            NUM_APPOINTMENTS, 
            doc_ids, nurse_ids, patient_ids, drug_ids, recep_ids
        )

        # --- BỔ SUNG: TẠO HÀNG CHỜ CHO HÔM NAY ---
        seed_todays_queue(doc_ids, patient_ids)
        # -----------------------------------------
        
        # 6. Messages
        seed_messages(all_staff_ids)
        
        # 7. Reports
        if admin_ids:
            seed_reports(admin_ids[0])
            
        print("\n✅ HOÀN TẤT! DATABASE ĐÃ ĐƯỢC LẤP ĐẦY DỮ LIỆU MẪU.")

if __name__ == '__main__':
    run_seeding()