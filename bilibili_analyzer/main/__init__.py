"""
Main蓝图 - 主要页面路由
"""

from flask import Blueprint, render_template, jsonify, request
from bilibili_analyzer.models import Channel, Video, AnalysisResult
from bilibili_analyzer import db

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """首页"""
    return render_template('index.html')

@bp.route('/dashboard')
def dashboard():
    """仪表板"""
    # 获取统计数据
    channel_count = Channel.query.count()
    video_count = Video.query.count()
    analysis_count = AnalysisResult.query.count()
    
    return render_template('dashboard.html', 
                         channel_count=channel_count,
                         video_count=video_count,
                         analysis_count=analysis_count)

@bp.route('/channels')
def channels():
    """频道列表"""
    page = request.args.get('page', 1, type=int)
    channels = Channel.query.paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('channels.html', channels=channels)

@bp.route('/channels/<int:channel_id>')
def channel_detail(channel_id):
    """频道详情"""
    channel = Channel.query.get_or_404(channel_id)
    videos = Video.query.filter_by(channel_id=channel_id).order_by(Video.published_at.desc()).limit(10).all()
    return render_template('channel_detail.html', channel=channel, videos=videos)

@bp.route('/videos')
def videos():
    """视频列表"""
    page = request.args.get('page', 1, type=int)
    videos = Video.query.order_by(Video.published_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('videos.html', videos=videos)

@bp.route('/videos/<int:video_id>')
def video_detail(video_id):
    """视频详情"""
    video = Video.query.get_or_404(video_id)
    analysis_results = AnalysisResult.query.filter_by(video_id=video_id).all()
    return render_template('video_detail.html', video=video, analysis_results=analysis_results)

@bp.route('/about')
def about():
    """关于页面"""
    return render_template('about.html')