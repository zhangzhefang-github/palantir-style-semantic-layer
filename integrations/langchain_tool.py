#!/usr/bin/env python3
"""
LangChain 集成 - 将语义控制面封装为 LangChain Tool

使用方法:
    pip install langchain langchain-openai
    export OPENAI_API_KEY=your_key
    python integrations/langchain_tool.py
"""

import os
import sys
from typing import Optional, Type
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pydantic import BaseModel, Field

# LangChain imports (需要安装: pip install langchain langchain-openai)
try:
    from langchain.tools import BaseTool
    from langchain.agents import AgentExecutor, create_openai_functions_agent
    from langchain_openai import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("⚠️  LangChain 未安装，运行: pip install langchain langchain-openai")

from semantic_layer import SemanticOrchestrator
from semantic_layer.models import ExecutionContext


class SemanticQueryInput(BaseModel):
    """语义查询输入参数"""
    question: str = Field(description="用户的业务问题，如'上月华东区毛利率是多少？'")
    department: Optional[str] = Field(default=None, description="部门上下文，如 'finance' 或 'sales'")
    region: Optional[str] = Field(default=None, description="区域，如 '华东'")
    period: Optional[str] = Field(default=None, description="时间周期，如 '2026-01'")


class SemanticQueryTool(BaseTool):
    """
    语义控制面查询工具
    
    这个工具将用户的业务问题转换为可执行的 SQL 查询，
    并根据上下文自动选择正确的指标版本。
    """
    name: str = "semantic_query"
    description: str = """
    查询企业业务指标。这个工具可以：
    1. 自动识别用户问的是什么指标（如毛利率、一次合格率）
    2. 根据用户的部门自动选择正确的计算口径
    3. 返回可追溯的结果（包含 Audit ID）
    
    使用场景：
    - 查询毛利率时，财务部和销售部会得到不同口径的结果
    - 查询生产指标时，会根据是否考虑返工选择不同版本
    
    输入参数：
    - question: 用户的业务问题
    - department: 部门（可选，影响版本选择）
    - region: 区域（可选）
    - period: 时间周期（可选）
    """
    args_schema: Type[BaseModel] = SemanticQueryInput
    
    # 类属性
    orchestrator: SemanticOrchestrator = None
    db_path: str = "data/semantic_layer.db"
    
    def __init__(self, db_path: str = "data/semantic_layer.db"):
        super().__init__()
        self.db_path = db_path
        self._init_orchestrator()
    
    def _init_orchestrator(self):
        """初始化 Orchestrator"""
        if not os.path.exists(self.db_path):
            # 自动初始化数据库
            from setup_database import setup_database
            setup_database()
        self.orchestrator = SemanticOrchestrator(self.db_path)
    
    def _run(
        self,
        question: str,
        department: Optional[str] = None,
        region: Optional[str] = None,
        period: Optional[str] = None,
    ) -> str:
        """执行语义查询"""
        # 构建参数
        parameters = {}
        if region:
            parameters['region'] = region
        if period:
            parameters['period'] = period
        if department:
            parameters['scenario'] = {'department': department}
        
        # 构建上下文
        context = ExecutionContext(
            user_id=1,
            role=f'{department}_manager' if department else 'operator',
            parameters=parameters,
            timestamp=datetime.now()
        )
        
        # 执行查询
        result = self.orchestrator.query(
            question=question,
            parameters=parameters,
            context=context
        )
        
        # 格式化返回结果
        if result.get('status') == 'success':
            data = result.get('data', [])
            version = result.get('version_name', 'unknown')
            audit_id = result.get('audit_id', 'N/A')
            
            # 提取主要指标值
            if data and len(data) > 0:
                first_row = data[0]
                # 找到数值字段
                for key, value in first_row.items():
                    if isinstance(value, (int, float)):
                        if 'margin' in key.lower() or 'rate' in key.lower():
                            return f"""
查询结果：
- 指标值: {value * 100:.1f}%
- 使用版本: {version}
- 审计ID: {audit_id}
- 说明: 此结果基于 {version} 口径计算，完整决策链可通过 audit_id 追溯
"""
                        else:
                            return f"""
查询结果：
- 指标值: {value:.4f}
- 使用版本: {version}
- 审计ID: {audit_id}
"""
            return f"查询成功，但无数据返回。版本: {version}, Audit ID: {audit_id}"
        else:
            error = result.get('error', '未知错误')
            return f"查询失败: {error}"
    
    async def _arun(self, *args, **kwargs) -> str:
        """异步执行（目前使用同步实现）"""
        return self._run(*args, **kwargs)


def create_semantic_agent(db_path: str = "data/semantic_layer.db"):
    """
    创建一个带有语义查询能力的 LangChain Agent
    
    Returns:
        AgentExecutor: 可以处理业务查询的 Agent
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("请先安装 LangChain: pip install langchain langchain-openai")
    
    # 创建工具
    semantic_tool = SemanticQueryTool(db_path=db_path)
    tools = [semantic_tool]
    
    # 创建 LLM
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    
    # 创建 Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个企业数据分析助手。你可以使用 semantic_query 工具来查询业务指标。

当用户询问业务指标时，你应该：
1. 识别用户想查询的指标（如毛利率、一次合格率等）
2. 从问题中提取部门、区域、时间等上下文
3. 使用 semantic_query 工具执行查询
4. 解释结果，说明使用了哪个版本的计算口径

重要提示：
- 不同部门可能有不同的计算口径，工具会自动选择
- 每个查询都有 Audit ID，可以用于追溯决策链
- 如果用户没有指定部门，系统会使用默认版本
"""),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # 创建 Agent
    agent = create_openai_functions_agent(llm, tools, prompt)
    
    # 创建 Executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True
    )
    
    return agent_executor


def demo_langchain_integration():
    """演示 LangChain 集成"""
    print("=" * 80)
    print("🔗 LangChain 集成演示")
    print("=" * 80)
    
    if not LANGCHAIN_AVAILABLE:
        print("\n⚠️  LangChain 未安装")
        print("请运行: pip install langchain langchain-openai")
        print("\n以下是集成代码示例：\n")
        print("""
from integrations.langchain_tool import create_semantic_agent

# 创建 Agent
agent = create_semantic_agent()

# 执行查询
result = agent.invoke({
    "input": "上月华东区毛利率是多少？我是财务部的。"
})
print(result["output"])
""")
        return
    
    if not os.environ.get("OPENAI_API_KEY"):
        print("\n⚠️  未设置 OPENAI_API_KEY")
        print("请运行: export OPENAI_API_KEY=your_key")
        return
    
    # 创建 Agent
    agent = create_semantic_agent()
    
    # 测试查询
    test_queries = [
        "上月华东区毛利率是多少？我是财务部的。",
        "销售部视角，华东区上月的毛利率是多少？",
    ]
    
    for query in test_queries:
        print(f"\n📝 用户问题: {query}")
        print("-" * 60)
        result = agent.invoke({"input": query})
        print(f"\n🤖 回答: {result['output']}")
        print("=" * 80)


if __name__ == "__main__":
    demo_langchain_integration()
