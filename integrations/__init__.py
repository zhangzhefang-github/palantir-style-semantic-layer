"""
语义控制面集成模块

提供多种集成方式:
- LangChain Tool 集成
- REST API 服务
- 直接客户端调用

使用示例:
    from integrations.demo_integration import SemanticLayerClient
    
    client = SemanticLayerClient()
    result = client.query(
        question="上月华东区毛利率是多少？",
        department="finance",
        region="华东",
        period="2026-01"
    )
"""

from .demo_integration import SemanticLayerClient

__all__ = ['SemanticLayerClient']
