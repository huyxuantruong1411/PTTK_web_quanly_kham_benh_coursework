import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import DonThuoc, Thuoc, GiaoDichKho, ChiTietDon
from app.utils import check_allergy_warnings, check_drug_interactions, check_expiry_warnings, check_stock_warnings

pharmacist_bp = Blueprint('pharmacist', __name__)

@pharmacist_bp.route('/prescriptions')
@login_required
def prescription_list():
    # Lấy danh sách đơn thuốc chưa phát
    # JOIN để kiểm tra trạng thái thanh toán của Lịch hẹn tương ứng
    # Logic: DonThuoc -> KetQuaKham -> LichHen -> HoaDon
    from app.models import HoaDon, LichHen, KetQuaKham
    
    prescriptions_query = db.session.query(DonThuoc).join(KetQuaKham).join(LichHen).filter(
        DonThuoc.TrangThai == 'Chờ phát'
    ).all()
    
    prescriptions_data = []
    for p in prescriptions_query:
        # Kiểm tra xem lịch hẹn này đã có hóa đơn thanh toán chưa
        hoa_don = HoaDon.query.filter_by(MaLH=p.ket_qua.MaLH, TrangThai='Đã thanh toán').first()
        is_paid = True if hoa_don else False
        
        prescriptions_data.append({
            'obj': p,
            'is_paid': is_paid
        })

    # Lấy các cảnh báo (giữ nguyên code cũ)
    expiring_medicines = check_expiry_warnings()
    low_stock_medicines = check_stock_warnings()
    
    return render_template(
        'pharmacist/prescription_list.html', 
        prescriptions=prescriptions_data, # Truyền danh sách đã xử lý logic thanh toán
        expiring_medicines=expiring_medicines,
        low_stock_medicines=low_stock_medicines
    )

@pharmacist_bp.route('/prescription_detail/<int:dt_id>')
@login_required
def prescription_detail(dt_id):
    dt = DonThuoc.query.get_or_404(dt_id)
    
    # Lấy danh sách ID thuốc trong đơn
    drug_ids = [detail.MaThuoc for detail in dt.chi_tiet]
    
    # Kiểm tra tương tác thuốc
    interactions = check_drug_interactions(drug_ids)
    
    # Kiểm tra dị ứng (nếu có thông tin bệnh nhân)
    patient_id = dt.ket_qua.lich_hen.MaBN
    allergy_warnings = check_allergy_warnings(drug_ids, patient_id)
    
    return render_template(
        'pharmacist/prescription_detail.html',
        prescription=dt,
        interactions=interactions,
        allergy_warnings=allergy_warnings
    )

@pharmacist_bp.route('/dispense/<int:dt_id>')
@login_required
def dispense(dt_id):
    dt = DonThuoc.query.get_or_404(dt_id)
    
    # BƯỚC 1: Kiểm tra tồn kho cho TOÀN BỘ danh sách thuốc trước
    for detail in dt.chi_tiet:
        drug = Thuoc.query.get(detail.MaThuoc)
        if drug.SoLuongTon < detail.SoLuong:
            flash(f'Lỗi: Thuốc "{drug.TenThuoc}" không đủ tồn kho (Còn: {drug.SoLuongTon}, Cần: {detail.SoLuong})', 'danger')
            return redirect(url_for('pharmacist.prescription_list'))

    # BƯỚC 2: Nếu tất cả đều đủ, mới tiến hành trừ kho
    try:
        for detail in dt.chi_tiet:
            drug = Thuoc.query.get(detail.MaThuoc)
            drug.SoLuongTon -= detail.SoLuong
            
            # Ghi log giao dịch kho
            gd = GiaoDichKho(
                MaThuoc=drug.MaThuoc,
                MaND=current_user.MaND,
                Loai='Xuất (Kê đơn)',
                SoLuong=detail.SoLuong
            )
            db.session.add(gd)
            
        dt.TrangThai = 'Đã phát'
        db.session.commit()
        flash('Cấp thuốc thành công!', 'success')
        
    except Exception as e:
        db.session.rollback() # Hoàn tác nếu có lỗi hệ thống
        flash(f'Có lỗi xảy ra: {str(e)}', 'danger')

    return redirect(url_for('pharmacist.prescription_list'))

@pharmacist_bp.route('/inventory', methods=['GET', 'POST'])
@login_required
def inventory():
    if request.method == 'POST':
        # Thêm thuốc mới hoặc nhập kho
        if 'add_drug' in request.form:
            thuoc = Thuoc(
                TenThuoc=request.form['ten_thuoc'],
                DonVi=request.form['donvi'],
                HanDung=datetime.strptime(request.form['handung'], '%Y-%m-%d'),
                Gia=float(request.form['gia']),
                SoLuongTon=int(request.form['soluong'])
            )
            db.session.add(thuoc)
            db.session.commit()
            flash('Thêm thuốc thành công!', 'success')
        
        elif 'import' in request.form:
            ma_thuoc = int(request.form['ma_thuoc'])
            soluong = int(request.form['soluong'])
            thuoc = Thuoc.query.get(ma_thuoc)
            thuoc.SoLuongTon += soluong
            gd = GiaoDichKho(MaThuoc=ma_thuoc, MaND=current_user.MaND, Loai='Nhập', SoLuong=soluong)
            db.session.add(gd)
            db.session.commit()
            flash('Nhập kho thành công!', 'success')
    
    drugs = Thuoc.query.all()
    return render_template('pharmacist/inventory.html', drugs=drugs)

@pharmacist_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.has_role('DuocSi'):
        flash('Bạn không có quyền truy cập!', 'danger')
        return redirect(url_for('auth.login'))
    
    # Lấy các đơn thuốc chờ phát
    pending_prescriptions = DonThuoc.query.filter_by(TrangThai='Chờ phát').count()
    
    # Lấy các đơn thuốc đã phát hôm nay
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    today_dispensed = DonThuoc.query.filter(
        DonThuoc.NgayKe.between(today_start, today_end),
        DonThuoc.TrangThai == 'Đã phát'
    ).count()
    
    # Thống kê thuốc sắp hết
    low_stock_medicines = Thuoc.query.filter(
        Thuoc.SoLuongTon <= Thuoc.SoLuongCanhBao
    ).count()
    
    # Thống kê thuốc sắp hết hạn
    thirty_days_from_now = today + datetime.timedelta(days=30)
    expiring_medicines = Thuoc.query.filter(
        Thuoc.HanDung <= thirty_days_from_now,
        Thuoc.SoLuongTon > 0
    ).count()
    
    # Lấy các đơn thuốc gần đây
    recent_prescriptions = DonThuoc.query.order_by(DonThuoc.NgayKe.desc()).limit(10).all()
    
    # Lấy các thuốc sắp hết
    low_stock_list = Thuoc.query.filter(
        Thuoc.SoLuongTon <= Thuoc.SoLuongCanhBao
    ).limit(5).all()
    
    return render_template(
        'pharmacist/dashboard.html',
        pending_prescriptions=pending_prescriptions,
        today_dispensed=today_dispensed,
        low_stock_medicines=low_stock_medicines,
        expiring_medicines=expiring_medicines,
        recent_prescriptions=recent_prescriptions,
        low_stock_list=low_stock_list
    )