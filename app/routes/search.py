# app/routes/search.py (Tạo file mới)
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.utils import (
    search_patients, search_appointments, 
    search_medicines, search_prescriptions, search_users
)

search_bp = Blueprint('search', __name__)

@search_bp.route('/patients')
@login_required
def search_patients_route():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    patients = search_patients(query)
    results = []
    for patient in patients:
        results.append({
            'id': patient.MaBN,
            'name': patient.HoTen,
            'phone': patient.SDT,
            'email': patient.Email,
            'url': f"/reception/patients/{patient.MaBN}"
        })
    
    return jsonify(results)

@search_bp.route('/appointments')
@login_required
def search_appointments_route():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    user_role = None
    if current_user.has_role('BacSi'):
        user_role = 'BacSi'

    appointments = search_appointments(query, user_role, current_user.MaND)
    results = []
    for appointment in appointments:
        results.append({
            'id': appointment.MaLH,
            'patient': appointment.benh_nhan.HoTen,
            'doctor': appointment.bac_si.HoTen,
            'datetime': appointment.NgayGio.strftime('%d/%m/%Y %H:%M'),
            'status': appointment.TrangThai,
            'url': f"/reception/appointments/{appointment.MaLH}"
        })
    
    return jsonify(results)

@search_bp.route('/medicines')
@login_required
def search_medicines_route():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    medicines = search_medicines(query)
    results = []
    for medicine in medicines:
        results.append({
            'id': medicine.MaThuoc,
            'name': medicine.TenThuoc,
            'unit': medicine.DonVi,
            'price': str(medicine.Gia),
            'stock': medicine.SoLuongTon,
            'url': f"/pharmacist/inventory/{medicine.MaThuoc}"
        })
    
    return jsonify(results)

@search_bp.route('/prescriptions')
@login_required
def search_prescriptions_route():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    prescriptions = search_prescriptions(query)
    results = []
    for prescription in prescriptions:
        results.append({
            'id': prescription.MaDT,
            'patient': prescription.ket_qua.lich_hen.benh_nhan.HoTen,
            'date': prescription.NgayKe.strftime('%d/%m/%Y'),
            'status': prescription.TrangThai,
            'url': f"/pharmacist/prescriptions/{prescription.MaDT}"
        })
    
    return jsonify(results)

@search_bp.route('/users')
@login_required
def search_users_route():
    query = request.args.get('q', '')
    role = request.args.get('role', '')
    if not query:
        return jsonify([])
    
    users = search_users(query, role if role else None)
    results = []
    for user in users:
        results.append({
            'id': user.MaND,
            'username': user.TenDangNhap,
            'name': user.HoTen,
            'role': user.VaiTro,
            'status': 'Hoạt động' if user.TrangThai else 'Đã khóa',
            'url': f"/admin/users/{user.MaND}"
        })
    
    return jsonify(results)