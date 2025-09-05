"""
登录页面路由
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import json
from datetime import datetime, timedelta

bp = Blueprint('auth', __name__)

# 模拟用户数据库
USERS = {
    'admin': {
        'username': 'admin',
        'password': generate_password_hash('admin'),
        'email': 'admin@example.com',
        'created_at': datetime.now(),
        'last_login': None
    },
    'user': {
        'username': 'user',
        'password': generate_password_hash('user'),
        'email': 'user@example.com',
        'created_at': datetime.now(),
        'last_login': None
    }
}

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'GET':
        return render_template('login.html')
    
    if request.method == 'POST':
        # 处理AJAX请求
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            remember = data.get('remember', False)
        else:
            # 处理表单提交
            username = request.form.get('username')
            password = request.form.get('password')
            remember = request.form.get('remember', False)
        
        # 验证用户
        user = USERS.get(username)
        
        if user and check_password_hash(user['password'], password):
            # 登录成功
            session['user_id'] = username
            session['username'] = username
            session['email'] = user['email']
            session['logged_in'] = True
            
            # 更新最后登录时间
            user['last_login'] = datetime.now()
            
            # 设置记住我
            if remember:
                session.permanent = True
                # 设置session过期时间为30天
                session['expires'] = (datetime.now() + timedelta(days=30)).isoformat()
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': '登录成功',
                    'redirect': url_for('main.dashboard')
                })
            else:
                return redirect(url_for('main.dashboard'))
        else:
            # 登录失败
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': '用户名或密码错误'
                }), 401
            else:
                return render_template('login.html', error='用户名或密码错误')

@bp.route('/logout')
def logout():
    """登出"""
    session.clear()
    return redirect(url_for('auth.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    if request.method == 'GET':
        return render_template('register.html')
    
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            confirm_password = data.get('confirm_password')
        else:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
        
        # 验证
        if not username or not email or not password:
            error_msg = '请填写完整信息'
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg}), 400
            else:
                return render_template('register.html', error=error_msg)
        
        if password != confirm_password:
            error_msg = '两次密码输入不一致'
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg}), 400
            else:
                return render_template('register.html', error=error_msg)
        
        if username in USERS:
            error_msg = '用户名已存在'
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg}), 400
            else:
                return render_template('register.html', error=error_msg)
        
        # 创建用户
        USERS[username] = {
            'username': username,
            'password': generate_password_hash(password),
            'email': email,
            'created_at': datetime.now(),
            'last_login': None
        }
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': '注册成功，请登录',
                'redirect': url_for('auth.login')
            })
        else:
            return redirect(url_for('auth.login'))

@bp.route('/api/check-auth')
def check_auth():
    """检查登录状态"""
    if 'logged_in' in session and session['logged_in']:
        return jsonify({
            'logged_in': True,
            'username': session.get('username'),
            'email': session.get('email')
        })
    else:
        return jsonify({
            'logged_in': False
        })

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """忘记密码"""
    if request.method == 'GET':
        return render_template('forgot_password.html')
    
    if request.method == 'POST':
        email = request.form.get('email')
        
        # 模拟发送重置邮件
        return render_template('forgot_password.html', 
                             success='密码重置邮件已发送到您的邮箱')

# 登录验证装饰器
def login_required(f):
    """登录验证装饰器"""
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function