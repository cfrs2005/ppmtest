"""
简化版登录路由
"""

from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

bp = Blueprint('auth', __name__)

# 简化用户数据库
USERS = {
    'admin': {
        'username': 'admin',
        'password': generate_password_hash('admin'),
        'email': 'admin@example.com'
    },
    'user': {
        'username': 'user',
        'password': generate_password_hash('user'),
        'email': 'user@example.com'
    }
}

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'GET':
        return '''
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>登录 - Bilibili视频分析系统</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    margin: 0;
                    padding: 0;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .login-container {
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                    width: 100%;
                    max-width: 400px;
                }
                .login-header {
                    text-align: center;
                    margin-bottom: 30px;
                }
                .login-header h1 {
                    color: #333;
                    margin-bottom: 10px;
                }
                .form-group {
                    margin-bottom: 20px;
                }
                .form-group label {
                    display: block;
                    margin-bottom: 5px;
                    color: #333;
                    font-weight: bold;
                }
                .form-group input {
                    width: 100%;
                    padding: 12px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    font-size: 16px;
                    box-sizing: border-box;
                }
                .login-button {
                    width: 100%;
                    padding: 12px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 16px;
                    cursor: pointer;
                }
                .login-button:hover {
                    opacity: 0.9;
                }
                .error-message {
                    color: #d9534f;
                    background: #f2dede;
                    padding: 10px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }
                .success-message {
                    color: #3c763d;
                    background: #dff0d8;
                    padding: 10px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <div class="login-container">
                <div class="login-header">
                    <h1>Bilibili视频分析系统</h1>
                    <p>请登录您的账户</p>
                </div>
                
                % if error:
                <div class="error-message">{{ error }}</div>
                % endif
                
                % if success:
                <div class="success-message">{{ success }}</div>
                % endif
                
                <form method="POST" action="/login">
                    <div class="form-group">
                        <label for="username">用户名:</label>
                        <input type="text" id="username" name="username" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="password">密码:</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    
                    <div class="form-group">
                        <label>
                            <input type="checkbox" name="remember"> 记住我
                        </label>
                    </div>
                    
                    <button type="submit" class="login-button">登录</button>
                </form>
                
                <div style="text-align: center; margin-top: 20px;">
                    <p>测试账户: admin/admin 或 user/user</p>
                </div>
            </div>
        </body>
        </html>
        '''
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember')
        
        # 验证用户
        user = USERS.get(username)
        
        if user and check_password_hash(user['password'], password):
            # 登录成功
            session['user_id'] = username
            session['username'] = username
            session['email'] = user['email']
            session['logged_in'] = True
            
            if remember:
                session.permanent = True
            
            return redirect('/dashboard')
        else:
            # 登录失败
            return render_template_string('''
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>登录 - Bilibili视频分析系统</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        margin: 0;
                        padding: 0;
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }
                    .login-container {
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                        width: 100%;
                        max-width: 400px;
                    }
                    .login-header {
                        text-align: center;
                        margin-bottom: 30px;
                    }
                    .login-header h1 {
                        color: #333;
                        margin-bottom: 10px;
                    }
                    .form-group {
                        margin-bottom: 20px;
                    }
                    .form-group label {
                        display: block;
                        margin-bottom: 5px;
                        color: #333;
                        font-weight: bold;
                    }
                    .form-group input {
                        width: 100%;
                        padding: 12px;
                        border: 1px solid #ddd;
                        border-radius: 5px;
                        font-size: 16px;
                        box-sizing: border-box;
                    }
                    .login-button {
                        width: 100%;
                        padding: 12px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        border: none;
                        border-radius: 5px;
                        font-size: 16px;
                        cursor: pointer;
                    }
                    .login-button:hover {
                        opacity: 0.9;
                    }
                    .error-message {
                        color: #d9534f;
                        background: #f2dede;
                        padding: 10px;
                        border-radius: 5px;
                        margin-bottom: 20px;
                    }
                    .success-message {
                        color: #3c763d;
                        background: #dff0d8;
                        padding: 10px;
                        border-radius: 5px;
                        margin-bottom: 20px;
                    }
                </style>
            </head>
            <body>
                <div class="login-container">
                    <div class="login-header">
                        <h1>Bilibili视频分析系统</h1>
                        <p>请登录您的账户</p>
                    </div>
                    
                    <div class="error-message">用户名或密码错误，请重试</div>
                    
                    <form method="POST" action="/login">
                        <div class="form-group">
                            <label for="username">用户名:</label>
                            <input type="text" id="username" name="username" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="password">密码:</label>
                            <input type="password" id="password" name="password" required>
                        </div>
                        
                        <div class="form-group">
                            <label>
                                <input type="checkbox" name="remember"> 记住我
                            </label>
                        </div>
                        
                        <button type="submit" class="login-button">登录</button>
                    </form>
                    
                    <div style="text-align: center; margin-top: 20px;">
                        <p>测试账户: admin/admin 或 user/user</p>
                    </div>
                </div>
            </body>
            </html>
            ''', error='用户名或密码错误，请重试')

@bp.route('/logout')
def logout():
    """登出"""
    session.clear()
    return redirect('/login')

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

# 登录验证装饰器
def login_required(f):
    """登录验证装饰器"""
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect('/login')
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function