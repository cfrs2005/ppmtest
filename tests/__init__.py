"""
Bilibili视频分析系统 - 测试工具和配置
"""

import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 测试配置
TEST_CONFIG = {
    'TEST_BVID': 'BV1BW411j7y4',  # 一个公开的测试视频
    'TEST_TIMEOUT': 30,
    'TEST_DELAY': 1
}

def create_test_app():
    """创建测试应用"""
    from bilibili_analyzer import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    return app

def setup_test_database(app):
    """设置测试数据库"""
    with app.app_context():
        from bilibili_analyzer import db
        db.create_all()

def teardown_test_database(app):
    """清理测试数据库"""
    with app.app_context():
        from bilibili_analyzer import db
        db.drop_all()

class IntegrationTestCase(unittest.TestCase):
    """集成测试基类"""
    
    def setUp(self):
        """测试前准备"""
        self.app = create_test_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        setup_test_database(self.app)
        
    def tearDown(self):
        """测试后清理"""
        teardown_test_database(self.app)
        self.app_context.pop()

if __name__ == '__main__':
    unittest.main()