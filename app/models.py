from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# LƯU Ý: Đã xóa import NVARCHAR của MSSQL để tương thích với PostgreSQL/SQLite

class NguoiDung(db.Model, UserMixin):
    __tablename__ = 'NguoiDung'
    MaND = db.Column(db.Integer, primary_key=True, autoincrement=True)
    TenDangNhap = db.Column(db.String(100), unique=True, nullable=False)
    MatKhau = db.Column(db.String(255), nullable=False)
    Email = db.Column(db.String(100))
    # Sử dụng db.String (Unicode) thay cho NVARCHAR
    HoTen = db.Column(db.String(100), nullable=False)
    SDT = db.Column(db.String(15))
    ChuyenKhoa = db.Column(db.String(100))  # Thêm cho bác sĩ
    TrangThai = db.Column(db.Boolean, default=True)  # 1: Hoạt động, 0: Khóa

    def set_password(self, password):
        self.MatKhau = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.MatKhau, password)

    @property
    def id(self):
        return self.MaND
    
    def has_role(self, role_name):
        """Kiểm tra người dùng có vai trò cụ thể không"""
        # Lấy tất cả vai trò của người dùng
        user_roles = [vai_tro.vai_tro.TenVaiTro for vai_tro in self.vai_tros]
        return role_name in user_roles

# Bảng VaiTro
class VaiTro(db.Model):
    __tablename__ = 'VaiTro'
    MaVaiTro = db.Column(db.Integer, primary_key=True, autoincrement=True)
    TenVaiTro = db.Column(db.String(50), nullable=False)
    MoTa = db.Column(db.Text) # db.Text tương đương NVARCHAR(MAX)

# Bảng trung gian NguoiDung_VaiTro
class NguoiDung_VaiTro(db.Model):
    __tablename__ = 'NguoiDung_VaiTro'
    MaND = db.Column(db.Integer, db.ForeignKey('NguoiDung.MaND'), primary_key=True)
    MaVaiTro = db.Column(db.Integer, db.ForeignKey('VaiTro.MaVaiTro'), primary_key=True)
    NgayGan = db.Column(db.Date, default=datetime.utcnow)
    
    # Quan hệ
    nguoi_dung = db.relationship('NguoiDung', backref='vai_tros')
    vai_tro = db.relationship('VaiTro', backref='nguoi_dungs')

class BenhNhan(db.Model):
    __tablename__ = 'BenhNhan'
    MaBN = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MaND = db.Column(db.Integer, db.ForeignKey('NguoiDung.MaND'), nullable=True)  # Liên kết với người dùng
    HoTen = db.Column(db.String(100), nullable=False)
    NgaySinh = db.Column(db.Date, nullable=False)
    GioiTinh = db.Column(db.String(10), nullable=False) # Nam/Nữ
    SDT = db.Column(db.String(15))
    DiaChi = db.Column(db.String(200))
    Email = db.Column(db.String(100))
    
    # Quan hệ với người dùng
    user = db.relationship('NguoiDung', foreign_keys=[MaND], backref='patient_profile')

# Bảng BenhNhanDiUng
class BenhNhanDiUng(db.Model):
    __tablename__ = 'BenhNhanDiUng'
    MaBN = db.Column(db.Integer, db.ForeignKey('BenhNhan.MaBN'), primary_key=True)
    TenChat = db.Column(db.String(100), nullable=False)
    PhanUng = db.Column(db.String(255))
    
    # Quan hệ
    benh_nhan = db.relationship('BenhNhan', backref='di_ung')

class LichHen(db.Model):
    __tablename__ = 'LichHen'
    MaLH = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MaBN = db.Column(db.Integer, db.ForeignKey('BenhNhan.MaBN'), nullable=False)
    MaBS = db.Column(db.Integer, db.ForeignKey('NguoiDung.MaND'), nullable=False)
    MaYT = db.Column(db.Integer, db.ForeignKey('NguoiDung.MaND'))
    NgayGio = db.Column(db.DateTime, nullable=False)
    TrangThai = db.Column(db.String(50), default='Chờ khám')

    benh_nhan = db.relationship('BenhNhan', backref='lich_hen')
    bac_si = db.relationship('NguoiDung', foreign_keys=[MaBS], backref='lich_hen_bs')
    y_ta = db.relationship('NguoiDung', foreign_keys=[MaYT], backref='lich_hen_yt')

class KetQuaKham(db.Model):
    __tablename__ = 'KetQuaKham'
    MaKQ = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MaLH = db.Column(db.Integer, db.ForeignKey('LichHen.MaLH'), unique=True, nullable=False)
    MaBS = db.Column(db.Integer, db.ForeignKey('NguoiDung.MaND'), nullable=False)
    ChanDoan = db.Column(db.Text, nullable=False) # db.Text cho nội dung dài
    HuongDieuTri = db.Column(db.Text)
    NgayKham = db.Column(db.Date, default=datetime.utcnow)
    CanhBaoTaiKham = db.Column(db.Date)
    DaTaiKham = db.Column(db.Boolean, default=False)
    GhiChuTaiKham = db.Column(db.Text)

    lich_hen = db.relationship('LichHen', backref='ket_qua')
    bac_si = db.relationship('NguoiDung', backref='ket_qua')

class ChiSoSinhTon(db.Model):
    __tablename__ = 'ChiSoSinhTon'
    MaKQ = db.Column(db.Integer, db.ForeignKey('KetQuaKham.MaKQ'), primary_key=True)
    MaYT = db.Column(db.Integer, db.ForeignKey('NguoiDung.MaND'), nullable=False)
    HuyetAp = db.Column(db.String(10))
    NhietDo = db.Column(db.Float)
    CanNang = db.Column(db.Float)
    NhipTim = db.Column(db.Integer)

    ket_qua = db.relationship('KetQuaKham', backref='chi_so')
    y_ta = db.relationship('NguoiDung', backref='chi_so')

class DonThuoc(db.Model):
    __tablename__ = 'DonThuoc'
    MaDT = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MaKQ = db.Column(db.Integer, db.ForeignKey('KetQuaKham.MaKQ'), nullable=False)
    NgayKe = db.Column(db.Date, default=datetime.utcnow)
    TrangThai = db.Column(db.String(50), default='Chờ phát')

    ket_qua = db.relationship('KetQuaKham', backref='don_thuoc')

class ChiTietDon(db.Model):
    __tablename__ = 'ChiTietDon'
    MaDT = db.Column(db.Integer, db.ForeignKey('DonThuoc.MaDT'), primary_key=True)
    MaThuoc = db.Column(db.Integer, db.ForeignKey('Thuoc.MaThuoc'), primary_key=True)
    SoLuong = db.Column(db.Integer, nullable=False)
    LieuDung = db.Column(db.String(100))
    GhiChu = db.Column(db.String(200))

    don_thuoc = db.relationship('DonThuoc', backref='chi_tiet')
    thuoc = db.relationship('Thuoc', backref='chi_tiet')

class Thuoc(db.Model):
    __tablename__ = 'Thuoc'
    MaThuoc = db.Column(db.Integer, primary_key=True, autoincrement=True)
    TenThuoc = db.Column(db.String(100), nullable=False)
    DonVi = db.Column(db.String(20), nullable=False)
    HanDung = db.Column(db.Date, nullable=False)
    Gia = db.Column(db.Numeric(10, 2), nullable=False)
    SoLuongTon = db.Column(db.Integer, default=0)
    SoLuongCanhBao = db.Column(db.Integer, default=10)
    HoatChat = db.Column(db.String(100))

class GiaoDichKho(db.Model):
    __tablename__ = 'GiaoDichKho'
    MaGD = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MaThuoc = db.Column(db.Integer, db.ForeignKey('Thuoc.MaThuoc'), nullable=False)
    MaND = db.Column(db.Integer, db.ForeignKey('NguoiDung.MaND'), nullable=False)
    Loai = db.Column(db.String(50), nullable=False)
    SoLuong = db.Column(db.Integer, nullable=False)
    Ngay = db.Column(db.Date, default=datetime.utcnow)

    thuoc = db.relationship('Thuoc', backref='giao_dich')
    nguoi_dung = db.relationship('NguoiDung', backref='giao_dich')

class BaoCao(db.Model):
    __tablename__ = 'BaoCao'
    MaBC = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MaND = db.Column(db.Integer, db.ForeignKey('NguoiDung.MaND'), nullable=False)
    LoaiBaoCao = db.Column(db.String(50), nullable=False)
    TuNgay = db.Column(db.Date, nullable=False)
    DenNgay = db.Column(db.Date, nullable=False)
    TongSo = db.Column(db.Integer)
    DoanhThu = db.Column(db.Numeric(10, 2))
    NgayLap = db.Column(db.Date, default=datetime.utcnow)

    nguoi_dung = db.relationship('NguoiDung', backref='bao_cao')

class CauHinhBaoCao(db.Model):
    __tablename__ = 'CauHinhBaoCao'
    MaCH = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MaBC = db.Column(db.Integer, db.ForeignKey('BaoCao.MaBC'), nullable=False)
    KyBaoCao = db.Column(db.String(50), nullable=False)
    TieuChi = db.Column(db.String(100), nullable=False)

    bao_cao = db.relationship('BaoCao', backref='cau_hinh')

class TuongTacThuoc(db.Model):
    __tablename__ = 'TuongTacThuoc'
    MaTT = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MaThuoc1 = db.Column(db.Integer, db.ForeignKey('Thuoc.MaThuoc'), nullable=False)
    MaThuoc2 = db.Column(db.Integer, db.ForeignKey('Thuoc.MaThuoc'), nullable=False)
    MucDo = db.Column(db.String(50), nullable=False)
    MoTa = db.Column(db.Text)
    
    thuoc1 = db.relationship('Thuoc', foreign_keys=[MaThuoc1])
    thuoc2 = db.relationship('Thuoc', foreign_keys=[MaThuoc2])

class HoaDon(db.Model):
    __tablename__ = 'HoaDon'
    MaHD = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MaDT = db.Column(db.Integer, db.ForeignKey('DonThuoc.MaDT'))
    MaLH = db.Column(db.Integer, db.ForeignKey('LichHen.MaLH'))
    TongTien = db.Column(db.Numeric(10, 2), nullable=False)
    NgayThanhToan = db.Column(db.Date, default=datetime.utcnow)
    TrangThai = db.Column(db.String(50), default='Chưa thanh toán')

    don_thuoc = db.relationship('DonThuoc', backref='hoa_don')
    lich_hen = db.relationship('LichHen', backref='hoa_don')

class TinNhan(db.Model):
    __tablename__ = 'TinNhan'
    MaTN = db.Column(db.Integer, primary_key=True, autoincrement=True)
    NguoiGui_ID = db.Column(db.Integer, db.ForeignKey('NguoiDung.MaND'), nullable=False)
    NguoiNhan_ID = db.Column(db.Integer, db.ForeignKey('NguoiDung.MaND'), nullable=True)
    NoiDung = db.Column(db.Text, nullable=False) # db.Text hỗ trợ văn bản dài
    ThoiGian = db.Column(db.DateTime, default=datetime.utcnow)
    PhongChat = db.Column(db.String(50), default='general')

    nguoi_gui = db.relationship('NguoiDung', foreign_keys=[NguoiGui_ID], backref='tin_nhan_gui')
    nguoi_nhan = db.relationship('NguoiDung', foreign_keys=[NguoiNhan_ID], backref='tin_nhan_nhan')