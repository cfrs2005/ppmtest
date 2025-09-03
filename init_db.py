#!/usr/bin/env python3
"""
手动数据库迁移脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from bilibili_analyzer import db

def init_db():
    """初始化数据库"""
    with app.app_context():
        print("正在创建数据库表...")
        db.create_all()
        print("✅ 数据库表创建成功！")
        
        # 创建测试数据
        from bilibili_analyzer.models import Channel, Video, User
        
        # 创建测试用户
        if not User.query.first():
            admin_user = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            print("✅ 创建管理员用户")
        
        # 创建测试频道
        if not Channel.query.first():
            test_channel = Channel(
                channel_id='test001',
                name='测试频道',
                description='这是一个测试频道',
                follower_count=1000,
                video_count=10
            )
            db.session.add(test_channel)
            print("✅ 创建测试频道")
        
        db.session.commit()
        print("✅ 数据库初始化完成！")

if __name__ == '__main__':
    init_db()