# app/routes/auth.py (Cập nhật hoàn chỉnh)
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_user, logout_user, login_required
from app.models import NguoiDung
from app import login_manager

auth_bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return NguoiDung.query.get(int(user_id))

@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = NguoiDung.query.filter_by(TenDangNhap=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            # Điều hướng dựa trên vai trò
            if user.has_role('BacSi'): 
                return redirect(url_for('doctor.dashboard'))
            if user.has_role('LeTan'): 
                return redirect(url_for('reception.dashboard'))
            if user.has_role('DuocSi'): 
                return redirect(url_for('pharmacist.dashboard'))
            if user.has_role('YTa'): 
                return redirect(url_for('nurse.dashboard'))
            if user.has_role('Admin'): 
                return redirect(url_for('admin.dashboard'))
            if user.has_role('BenhNhan'): 
                return redirect(url_for('patient.dashboard'))
            return redirect(url_for('reception.dashboard'))  # Mặc định
        
        flash('Sai thông tin đăng nhập!', 'danger')
    return render_template('login.html')

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    # Điều hướng đến dashboard phù hợp với vai trò
    if current_user.has_role('BacSi'):
        return redirect(url_for('doctor.dashboard'))
    elif current_user.has_role('LeTan'):
        return redirect(url_for('reception.dashboard'))
    elif current_user.has_role('DuocSi'):
        return redirect(url_for('pharmacist.dashboard'))
    elif current_user.has_role('YTa'):
        return redirect(url_for('nurse.dashboard'))
    elif current_user.has_role('Admin'):
        return redirect(url_for('admin.dashboard'))
    elif current_user.has_role('BenhNhan'):
        return redirect(url_for('patient.dashboard'))
    else:
        return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))