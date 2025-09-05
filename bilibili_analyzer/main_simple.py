"""
简化版仪表板路由
"""

from flask import Blueprint, render_template, session, redirect, url_for
from bilibili_analyzer.auth_simple import login_required

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """首页"""
    if 'logged_in' in session and session['logged_in']:
        return redirect('/dashboard')
    else:
        return redirect('/login')

@bp.route('/dashboard')
@login_required
def dashboard():
    """仪表板"""
    username = session.get('username', '用户')
    return f'''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>仪表板 - Bilibili视频分析系统</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background: #f5f5f5;
            }}
            .navbar {{
                background: white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                padding: 1rem 2rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .navbar-brand {{
                font-size: 1.5rem;
                font-weight: bold;
                color: #667eea;
                text-decoration: none;
            }}
            .navbar-user {{
                display: flex;
                align-items: center;
                gap: 1rem;
            }}
            .user-info {{
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}
            .user-avatar {{
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
            }}
            .logout-btn {{
                background: #dc3545;
                color: white;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 5px;
                cursor: pointer;
                text-decoration: none;
                font-size: 0.9rem;
            }}
            .logout-btn:hover {{
                background: #c82333;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
            }}
            .welcome-section {{
                background: white;
                border-radius: 10px;
                padding: 2rem;
                margin-bottom: 2rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1.5rem;
                margin-bottom: 2rem;
            }}
            .stat-card {{
                background: white;
                border-radius: 10px;
                padding: 1.5rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
            }}
            .stat-icon {{
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 1rem;
                font-size: 1.5rem;
                color: white;
            }}
            .stat-number {{
                font-size: 2rem;
                font-weight: bold;
                color: #333;
                margin-bottom: 0.5rem;
            }}
            .stat-label {{
                color: #666;
                font-size: 0.9rem;
            }}
        </style>
    </head>
    <body>
        <nav class="navbar">
            <a href="#" class="navbar-brand">Bilibili视频分析系统</a>
            <div class="navbar-user">
                <div class="user-info">
                    <div class="user-avatar">{username[0].upper()}</div>
                    <span>{username}</span>
                </div>
                <a href="/logout" class="logout-btn">退出登录</a>
            </div>
        </nav>

        <div class="container">
            <div class="welcome-section">
                <h1>欢迎回来，{username}！</h1>
                <p>您已成功登录Bilibili视频分析系统。在这里您可以分析B站视频数据、获取热门视频信息、进行内容分析等操作。</p>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon">📊</div>
                    <div class="stat-number">0</div>
                    <div class="stat-label">今日分析</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">🎬</div>
                    <div class="stat-number">0</div>
                    <div class="stat-label">总视频数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">⭐</div>
                    <div class="stat-number">0</div>
                    <div class="stat-label">收藏视频</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">📈</div>
                    <div class="stat-number">0</div>
                    <div class="stat-label">趋势分析</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

@bp.route('/logout')
def logout():
    """登出"""
    session.clear()
    return redirect('/login')