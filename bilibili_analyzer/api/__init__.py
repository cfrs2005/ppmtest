"""
API蓝图 - RESTful API接口
"""

from flask import Blueprint, jsonify, request
from bilibili_analyzer.models import Channel, Video, AnalysisResult
from bilibili_analyzer import db

bp = Blueprint('api', __name__)

@bp.route('/channels', methods=['GET'])
def get_channels():
    """获取频道列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    channels = Channel.query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'channels': [channel.to_dict() for channel in channels.items],
        'total': channels.total,
        'pages': channels.pages,
        'current_page': channels.page
    })

@bp.route('/channels/<int:channel_id>', methods=['GET'])
def get_channel(channel_id):
    """获取单个频道"""
    channel = Channel.query.get_or_404(channel_id)
    return jsonify(channel.to_dict())

@bp.route('/channels', methods=['POST'])
def create_channel():
    """创建频道"""
    data = request.get_json()
    
    if not data or 'channel_id' not in data or 'name' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    channel = Channel(
        channel_id=data['channel_id'],
        name=data['name'],
        description=data.get('description', ''),
        avatar_url=data.get('avatar_url', '')
    )
    
    db.session.add(channel)
    db.session.commit()
    
    return jsonify(channel.to_dict()), 201

@bp.route('/channels/<int:channel_id>', methods=['PUT'])
def update_channel(channel_id):
    """更新频道"""
    channel = Channel.query.get_or_404(channel_id)
    data = request.get_json()
    
    if 'name' in data:
        channel.name = data['name']
    if 'description' in data:
        channel.description = data['description']
    if 'avatar_url' in data:
        channel.avatar_url = data['avatar_url']
    if 'follower_count' in data:
        channel.follower_count = data['follower_count']
    if 'video_count' in data:
        channel.video_count = data['video_count']
    
    channel.updated_at = db.func.current_timestamp()
    db.session.commit()
    
    return jsonify(channel.to_dict())

@bp.route('/channels/<int:channel_id>', methods=['DELETE'])
def delete_channel(channel_id):
    """删除频道"""
    channel = Channel.query.get_or_404(channel_id)
    db.session.delete(channel)
    db.session.commit()
    
    return jsonify({'message': 'Channel deleted successfully'})

@bp.route('/videos', methods=['GET'])
def get_videos():
    """获取视频列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    channel_id = request.args.get('channel_id', type=int)
    
    query = Video.query
    if channel_id:
        query = query.filter_by(channel_id=channel_id)
    
    videos = query.order_by(Video.published_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'videos': [video.to_dict() for video in videos.items],
        'total': videos.total,
        'pages': videos.pages,
        'current_page': videos.page
    })

@bp.route('/videos/<int:video_id>', methods=['GET'])
def get_video(video_id):
    """获取单个视频"""
    video = Video.query.get_or_404(video_id)
    return jsonify(video.to_dict())

@bp.route('/videos', methods=['POST'])
def create_video():
    """创建视频"""
    data = request.get_json()
    
    if not data or 'bvid' not in data or 'title' not in data or 'channel_id' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    video = Video(
        bvid=data['bvid'],
        title=data['title'],
        channel_id=data['channel_id'],
        description=data.get('description', ''),
        cover_url=data.get('cover_url', ''),
        duration=data.get('duration'),
        play_count=data.get('play_count', 0),
        like_count=data.get('like_count', 0),
        coin_count=data.get('coin_count', 0),
        favorite_count=data.get('favorite_count', 0),
        share_count=data.get('share_count', 0),
        comment_count=data.get('comment_count', 0)
    )
    
    db.session.add(video)
    db.session.commit()
    
    return jsonify(video.to_dict()), 201

@bp.route('/analysis/<int:video_id>', methods=['GET'])
def get_analysis_results(video_id):
    """获取视频分析结果"""
    results = AnalysisResult.query.filter_by(video_id=video_id).all()
    return jsonify([result.to_dict() for result in results])

@bp.route('/analysis', methods=['POST'])
def create_analysis_result():
    """创建分析结果"""
    data = request.get_json()
    
    if not data or 'video_id' not in data or 'analysis_type' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    result = AnalysisResult(
        video_id=data['video_id'],
        analysis_type=data['analysis_type'],
        result_data=data.get('result_data', {}),
        confidence=data.get('confidence')
    )
    
    db.session.add(result)
    db.session.commit()
    
    return jsonify(result.to_dict()), 201

@bp.route('/stats', methods=['GET'])
def get_stats():
    """获取统计信息"""
    channel_count = Channel.query.count()
    video_count = Video.query.count()
    analysis_count = AnalysisResult.query.count()
    
    return jsonify({
        'channel_count': channel_count,
        'video_count': video_count,
        'analysis_count': analysis_count
    })