# app/forms.py (Cập nhật hoàn chỉnh)
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, SelectField, FloatField, IntegerField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, EqualTo, Email

class LoginForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[DataRequired(), Length(min=4, max=100)])
    password = PasswordField('Mật khẩu', validators=[DataRequired()])
    submit = SubmitField('Đăng nhập')

class PatientForm(FlaskForm):
    hoten = StringField('Họ tên', validators=[DataRequired()])
    ngaysinh = DateField('Ngày sinh', validators=[DataRequired()])
    gioitinh = SelectField('Giới tính', choices=[('Nam', 'Nam'), ('Nữ', 'Nữ')], validators=[DataRequired()])
    sdt = StringField('SĐT', validators=[DataRequired(), Length(min=10, max=15)])
    diachi = StringField('Địa chỉ', validators=[DataRequired()])
    submit = SubmitField('Thêm Bệnh Nhân')

class AppointmentForm(FlaskForm):
    mabn = SelectField('Bệnh nhân', coerce=int, validators=[DataRequired()])
    mabs = SelectField('Bác sĩ', coerce=int, validators=[DataRequired()])
    ngaygio = StringField('Ngày giờ', validators=[DataRequired()])  # Sử dụng datetime-local ở HTML
    submit = SubmitField('Đặt Lịch')

class VitalsForm(FlaskForm):
    huyetap = StringField('Huyết áp', validators=[DataRequired()])
    nhietdo = FloatField('Nhiệt độ', validators=[DataRequired(), NumberRange(min=30, max=45)])
    cannang = FloatField('Cân nặng', validators=[DataRequired(), NumberRange(min=1, max=200)])
    nhiptim = IntegerField('Nhịp tim', validators=[DataRequired(), NumberRange(min=1, max=300)])
    submit = SubmitField('Lưu')

class ExamForm(FlaskForm):
    chandoan = TextAreaField('Chẩn đoán', validators=[DataRequired()])
    huongdieutri = TextAreaField('Hướng điều trị')
    submit = SubmitField('Lưu Kết Quả & Kê Đơn')

class DrugForm(FlaskForm):
    ten_thuoc = StringField('Tên thuốc', validators=[DataRequired()])
    donvi = StringField('Đơn vị', validators=[DataRequired()])
    handung = DateField('Hạn dùng', validators=[DataRequired()])
    gia = FloatField('Giá', validators=[DataRequired(), NumberRange(min=0)])
    soluong = IntegerField('Số lượng', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Thêm Thuốc')

class UserForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[DataRequired()])
    password = PasswordField('Mật khẩu', validators=[DataRequired()])
    hoten = StringField('Họ tên', validators=[DataRequired()])
    vaitro = SelectField('Vai trò', choices=[('Admin', 'Admin'), ('BacSi', 'Bác sĩ'), ('YTa', 'Y tá'), ('DuocSi', 'Dược sĩ'), ('LeTan', 'Lễ tân')], validators=[DataRequired()])
    submit = SubmitField('Thêm User')

class PatientRegistrationForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[DataRequired(), Length(min=4, max=100)])
    password = PasswordField('Mật khẩu', validators=[DataRequired(), Length(min=6, max=100)])
    confirm_password = PasswordField('Xác nhận mật khẩu', validators=[DataRequired(), EqualTo('password')])
    hoten = StringField('Họ tên', validators=[DataRequired()])
    ngaysinh = DateField('Ngày sinh', validators=[DataRequired()])
    gioitinh = SelectField('Giới tính', choices=[('Nam', 'Nam'), ('Nữ', 'Nữ')], validators=[DataRequired()])
    sdt = StringField('SĐT', validators=[DataRequired(), Length(min=10, max=15)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    diachi = StringField('Địa chỉ', validators=[DataRequired()])
    submit = SubmitField('Đăng ký')