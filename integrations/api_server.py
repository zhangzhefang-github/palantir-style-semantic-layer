#!/usr/bin/env python3
"""
REST API 服务 - 供 ChatBI / 前端调用

使用方法:
    pip install flask flask-cors
    python integrations/api_server.py
    
API 端点:
    POST /api/query - 执行语义查询
    GET /api/objects - 列出所有语义对象
    GET /api/audit/<audit_id> - 查询审计记录
"""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("⚠️  Flask 未安装，运行: pip install flask flask-cors")

from semantic_layer import SemanticOrchestrator
from semantic_layer.models import ExecutionContext


def create_app(db_path: str = "data/semantic_layer.db"):
    """创建 Flask 应用"""
    app = Flask(__name__)
    CORS(app)  # 允许跨域
    
    # 初始化 Orchestrator
    if not os.path.exists(db_path):
        # 自动初始化数据库
        import sqlite3
        os.makedirs('data', exist_ok=True)
        conn = sqlite3.connect(db_path)
        with open('schema.sql', 'r') as f:
            conn.executescript(f.read())
        with open('seed_data.sql', 'r') as f:
            conn.executescript(f.read())
        conn.close()
    
    orchestrator = SemanticOrchestrator(db_path)
    
    @app.route('/api/query', methods=['POST'])
    def query():
        """
        执行语义查询
        
        Request Body:
        {
            "question": "上月华东区毛利率是多少？",
            "department": "finance",  // 可选
            "region": "华东",         // 可选
            "period": "2026-01",      // 可选
            "user_id": 1,             // 可选
            "role": "finance_manager" // 可选
        }
        
        Response:
        {
            "status": "success",
            "data": [...],
            "version": "GrossMargin_v1_finance",
            "audit_id": "20260201_xxx",
            "decision_trace": [...]
        }
        """
        try:
            data = request.get_json()
            
            question = data.get('question', '')
            if not question:
                return jsonify({'error': 'question is required'}), 400
            
            # 构建参数
            parameters = {}
            if data.get('region'):
                parameters['region'] = data['region']
            if data.get('period'):
                parameters['period'] = data['period']
            if data.get('department'):
                parameters['scenario'] = {'department': data['department']}
            if data.get('line'):
                parameters['line'] = data['line']
            if data.get('start_date'):
                parameters['start_date'] = data['start_date']
            if data.get('end_date'):
                parameters['end_date'] = data['end_date']
            
            # 构建上下文
            context = ExecutionContext(
                user_id=data.get('user_id', 1),
                role=data.get('role', 'operator'),
                parameters=parameters,
                timestamp=datetime.now()
            )
            
            # 执行查询
            result = orchestrator.query(
                question=question,
                parameters=parameters,
                context=context
            )
            
            return jsonify(result)
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/objects', methods=['GET'])
    def list_objects():
        """
        列出所有语义对象
        
        Response:
        {
            "objects": [
                {"id": 1, "name": "FPY", "domain": "production", ...},
                ...
            ]
        }
        """
        try:
            objects = orchestrator.list_semantic_objects()
            return jsonify({'objects': objects})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/audit/<audit_id>', methods=['GET'])
    def get_audit(audit_id):
        """
        查询审计记录
        
        Response:
        {
            "audit_id": "20260201_xxx",
            "question": "...",
            "decision_trace": [...],
            "executed_at": "..."
        }
        """
        try:
            history = orchestrator.get_audit_history(limit=100)
            for record in history:
                if record.get('audit_id') == audit_id:
                    return jsonify(record)
            return jsonify({'error': 'Audit record not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/health', methods=['GET'])
    def health():
        """健康检查"""
        return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})
    
    return app


def main():
    """启动 API 服务"""
    print("=" * 80)
    print("🌐 语义控制面 REST API 服务")
    print("=" * 80)
    
    if not FLASK_AVAILABLE:
        print("\n⚠️  Flask 未安装")
        print("请运行: pip install flask flask-cors")
        print("\n安装后运行: python integrations/api_server.py")
        return
    
    app = create_app()
    
    print("""
📡 API 端点:
   POST /api/query    - 执行语义查询
   GET  /api/objects  - 列出语义对象
   GET  /api/audit/<id> - 查询审计记录
   GET  /api/health   - 健康检查

📝 示例请求:
   curl -X POST http://localhost:5000/api/query \\
     -H "Content-Type: application/json" \\
     -d '{"question": "上月华东区毛利率是多少？", "department": "finance", "region": "华东", "period": "2026-01"}'

🔗 ChatBI 集成:
   在你的 ChatBI 中，将此 API 作为后端数据源调用即可。
   每个查询都会返回 audit_id，可用于追溯决策链。
""")
    
    print("🚀 启动服务: http://localhost:5000")
    print("-" * 80)
    
    app.run(host='0.0.0.0', port=5000, debug=True)


if __name__ == "__main__":
    main()
