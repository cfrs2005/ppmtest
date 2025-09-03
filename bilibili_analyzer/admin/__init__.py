"""
Admin蓝图 - 管理后台
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from bilibili_analyzer.models import Channel, Video, AnalysisResult, User
from bilibili_analyzer import db

# 简化版本，暂时不使用flask_login
def login_required(f):
    """临时装饰器"""
    return f

class CurrentUser:
    """临时用户类"""
    def __init__(self):
        self.is_admin = True

current_user = CurrentUser()

bp = Blueprint('admin', __name__)

@bp.route('/')
@login_required
def dashboard():
    """管理后台首页"""
    if not current_user.is_admin:
        flash('需要管理员权限', 'danger')
        return redirect(url_for('main.index'))
    
    # 统计数据
    channel_count = Channel.query.count()
    video_count = Video.query.count()
    analysis_count = AnalysisResult.query.count()
    user_count = User.query.count()
    
    # 最近的活动
    recent_channels = Channel.query.order_by(Channel.created_at.desc()).limit(5).all()
    recent_videos = Video.query.order_by(Video.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         channel_count=channel_count,
                         video_count=video_count,
                         analysis_count=analysis_count,
                         user_count=user_count,
                         recent_channels=recent_channels,
                         recent_videos=recent_videos)

@bp.route('/channels')
@login_required
def channels():
    """频道管理"""
    if not current_user.is_admin:
        flash('需要管理员权限', 'danger')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    channels = Channel.query.paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/channels.html', channels=channels)

@bp.route('/videos')
@login_required
def videos():
    """视频管理"""
    if not current_user.is_admin:
        flash('需要管理员权限', 'danger')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    videos = Video.query.order_by(Video.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/videos.html', videos=videos)

@bp.route('/analysis')
@login_required
def analysis():
    """分析结果管理"""
    if not current_user.is_admin:
        flash('需要管理员权限', 'danger')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    results = AnalysisResult.query.order_by(AnalysisResult.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/analysis.html', results=results)

@bp.route('/users')
@login_required
def users():
    """用户管理"""
    if not current_user.is_admin:
        flash('需要管理员权限', 'danger')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/users.html', users=users)

@bp.route('/settings')
@login_required
def settings():
    """系统设置"""
    if not current_user.is_admin:
        flash('需要管理员权限', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('admin/settings.html')