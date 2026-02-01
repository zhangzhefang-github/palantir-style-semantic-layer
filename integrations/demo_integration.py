#!/usr/bin/env python3
"""
集成演示脚本 - 无需 API Key 即可运行

演示如何将语义控制面集成到你的系统中。
"""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from semantic_layer import SemanticOrchestrator
from semantic_layer.models import ExecutionContext


class SemanticLayerClient:
    """
    语义控制面客户端
    
    这个类封装了与语义控制面的所有交互，
    可以直接集成到你的 ChatBI 或 Agent 系统中。
    """
    
    def __init__(self, db_path: str = "data/semantic_layer.db"):
        """初始化客户端"""
        self.db_path = db_path
        self._ensure_database()
        self.orchestrator = SemanticOrchestrator(db_path)
    
    def _ensure_database(self):
        """确保数据库已初始化"""
        if not os.path.exists(self.db_path):
            import sqlite3
            os.makedirs('data', exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            
            # 查找 schema 和 seed 文件
            root = os.path.dirname(os.path.dirname(__file__))
            schema_path = os.path.join(root, 'schema.sql')
            seed_path = os.path.join(root, 'seed_data.sql')
            
            with open(schema_path, 'r') as f:
                conn.executescript(f.read())
            with open(seed_path, 'r') as f:
                conn.executescript(f.read())
            conn.close()
            print("✅ 数据库已自动初始化")
    
    def query(
        self,
        question: str,
        department: str = None,
        region: str = None,
        period: str = None,
        line: str = None,
        start_date: str = None,
        end_date: str = None,
        user_id: int = 1,
        role: str = "operator"
    ) -> dict:
        """
        执行语义查询
        
        Args:
            question: 用户的业务问题
            department: 部门（影响版本选择）
            region: 区域
            period: 时间周期
            line: 产线
            start_date: 开始日期
            end_date: 结束日期
            user_id: 用户 ID
            role: 用户角色
        
        Returns:
            dict: 包含查询结果、版本信息和审计 ID
        """
        # 构建参数
        parameters = {}
        if region:
            parameters['region'] = region
        if period:
            parameters['period'] = period
        if department:
            parameters['scenario'] = {'department': department}
        if line:
            parameters['line'] = line
        if start_date:
            parameters['start_date'] = start_date
        if end_date:
            parameters['end_date'] = end_date
        
        # 构建上下文
        context = ExecutionContext(
            user_id=user_id,
            role=role,
            parameters=parameters,
            timestamp=datetime.now()
        )
        
        # 执行查询
        return self.orchestrator.query(
            question=question,
            parameters=parameters,
            context=context
        )
    
    def list_metrics(self) -> list:
        """列出所有可用指标"""
        return self.orchestrator.list_semantic_objects()
    
    def get_audit(self, audit_id: str) -> dict:
        """获取审计记录"""
        history = self.orchestrator.get_audit_history(limit=100)
        for record in history:
            if record.get('audit_id') == audit_id:
                return record
        return None


def demo_chatbi_integration():
    """模拟 ChatBI 集成场景"""
    print("=" * 80)
    print("🤖 模拟 ChatBI 集成场景")
    print("=" * 80)
    
    # 创建客户端（这就是你在 ChatBI 中要做的）
    client = SemanticLayerClient()
    
    # 模拟用户对话
    conversations = [
        {
            "user": "帮我查一下上月华东区的毛利率",
            "context": {"department": "finance", "region": "华东", "period": "2026-01"}
        },
        {
            "user": "销售部那边说毛利率是 28%，怎么跟你说的不一样？",
            "context": {"department": "sales", "region": "华东", "period": "2026-01"}
        },
        {
            "user": "昨天产线A的一次合格率是多少？",
            "context": {"line": "A", "start_date": "2026-01-27", "end_date": "2026-01-27"}
        },
    ]
    
    for i, conv in enumerate(conversations, 1):
        print(f"\n{'='*60}")
        print(f"📝 用户问题 {i}: {conv['user']}")
        print("-" * 60)
        
        # 调用语义控制面
        ctx = conv['context']
        result = client.query(
            question=conv['user'],
            department=ctx.get('department'),
            region=ctx.get('region'),
            period=ctx.get('period'),
            line=ctx.get('line'),
            start_date=ctx.get('start_date'),
            end_date=ctx.get('end_date')
        )
        
        # 处理结果（这是 ChatBI 需要做的）
        if result.get('status') == 'success':
            data = result.get('data', [])
            version = result.get('version_name', 'unknown')
            audit_id = result.get('audit_id', 'N/A')
            
            print(f"\n🤖 ChatBI 回答:")
            print(f"   使用版本: {version}")
            
            if data and len(data) > 0:
                for key, value in data[0].items():
                    if isinstance(value, (int, float)):
                        if 'margin' in key.lower() or 'fpy' in key.lower():
                            print(f"   结果: {value * 100:.1f}%")
                        else:
                            print(f"   结果: {value:.4f}")
            
            print(f"   Audit ID: {audit_id}")
            print(f"   (决策链可通过 audit_id 追溯)")
        else:
            print(f"   ⚠️ 错误: {result.get('error', '未知错误')}")
    
    print("\n" + "=" * 80)
    print("💡 集成要点")
    print("=" * 80)
    print("""
1. 创建 SemanticLayerClient 实例
2. 从用户输入中提取上下文（部门、区域、时间等）
3. 调用 client.query() 获取结果
4. 将结果格式化返回给用户
5. 保存 audit_id 用于后续追溯

关键价值：
- 系统自动选择正确的指标版本
- 每个查询都有完整的决策链
- 不同用户/部门看到一致的、正确的结果
""")


def demo_langchain_style():
    """展示 LangChain 风格的调用方式"""
    print("\n" + "=" * 80)
    print("🔗 LangChain 风格调用示例")
    print("=" * 80)
    
    client = SemanticLayerClient()
    
    # 模拟 LangChain Agent 的 Tool 调用
    def semantic_query_tool(question: str, department: str = None, region: str = None, period: str = None) -> str:
        """这是 LangChain Tool 的函数签名"""
        result = client.query(
            question=question,
            department=department,
            region=region,
            period=period
        )
        
        if result.get('status') == 'success':
            data = result.get('data', [])
            version = result.get('version_name', 'unknown')
            audit_id = result.get('audit_id')
            
            if data and len(data) > 0:
                for key, value in data[0].items():
                    if isinstance(value, (int, float)):
                        if 'margin' in key.lower():
                            return f"毛利率: {value * 100:.1f}% (版本: {version}, Audit: {audit_id})"
                        elif 'fpy' in key.lower():
                            return f"一次合格率: {value * 100:.2f}% (版本: {version}, Audit: {audit_id})"
            return f"查询成功，但无数据。版本: {version}"
        return f"查询失败: {result.get('error', '未知错误')}"
    
    # 测试调用
    print("\n📝 Tool 调用示例:")
    print("-" * 60)
    
    # 调用 1: 财务视角
    result1 = semantic_query_tool(
        question="毛利率是多少？",
        department="finance",
        region="华东",
        period="2026-01"
    )
    print(f"财务视角: {result1}")
    
    # 调用 2: 销售视角
    result2 = semantic_query_tool(
        question="毛利率是多少？",
        department="sales",
        region="华东",
        period="2026-01"
    )
    print(f"销售视角: {result2}")
    
    print("""
💡 LangChain 集成步骤:
1. pip install langchain langchain-openai
2. 将上述函数封装为 BaseTool
3. 创建 Agent 并注入 Tool
4. 详细代码见: integrations/langchain_tool.py
""")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(__file__)))
    demo_chatbi_integration()
    demo_langchain_style()
