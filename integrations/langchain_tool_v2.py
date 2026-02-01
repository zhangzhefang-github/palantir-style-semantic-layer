#!/usr/bin/env python3
"""
LangChain 集成 v2 - 使用最新的 @tool 装饰器和 ToolRuntime

基于 LangChain 最新文档：https://docs.langchain.com/tools

使用方法:
    pip install langchain langchain-openai langgraph
    export OPENAI_API_KEY=your_key
    python integrations/langchain_tool_v2.py
"""

import os
import sys
from typing import Optional, Literal
from datetime import datetime
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Check dependencies
try:
    from pydantic import BaseModel, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    # 创建占位类
    class BaseModel:
        pass
    def Field(*args, **kwargs):
        return None

try:
    from langchain.tools import tool
    from langchain_openai import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    # 创建占位装饰器
    def tool(*args, **kwargs):
        def decorator(func):
            func.invoke = lambda params: func(**params)
            return func
        if len(args) == 1 and callable(args[0]):
            return decorator(args[0])
        return decorator

if not PYDANTIC_AVAILABLE or not LANGCHAIN_AVAILABLE:
    print("⚠️  依赖未完全安装，运行: pip install langchain langchain-openai langgraph pydantic")
    print("   当前仍可运行基础演示...")

from semantic_layer import SemanticOrchestrator
from semantic_layer.models import ExecutionContext


# ============================================================
# 1️⃣ 定义 Pydantic Schema（输入参数）
# ============================================================

class SemanticQueryInput(BaseModel):
    """语义查询的输入参数 Schema"""
    
    question: str = Field(
        description="用户的业务问题，如'上月华东区毛利率是多少？'或'昨天产线A的一次合格率'"
    )
    department: Optional[Literal["finance", "sales"]] = Field(
        default=None,
        description="部门上下文，影响指标版本选择。finance=财务口径，sales=销售口径"
    )
    region: Optional[str] = Field(
        default=None,
        description="区域，如'华东'、'华北'"
    )
    period: Optional[str] = Field(
        default=None,
        description="时间周期，如'2026-01'"
    )
    line: Optional[str] = Field(
        default=None,
        description="产线，如'A'、'B'"
    )
    start_date: Optional[str] = Field(
        default=None,
        description="开始日期，如'2026-01-27'"
    )
    end_date: Optional[str] = Field(
        default=None,
        description="结束日期，如'2026-01-27'"
    )


class AuditQueryInput(BaseModel):
    """审计查询的输入参数"""
    
    audit_id: str = Field(
        description="审计记录ID，如'20260201_143022_a8f3e2b1'"
    )


# ============================================================
# 2️⃣ 初始化 Orchestrator（全局单例）
# ============================================================

_orchestrator: Optional[SemanticOrchestrator] = None

def get_orchestrator(db_path: str = "data/semantic_layer.db") -> SemanticOrchestrator:
    """获取或创建 Orchestrator 单例"""
    global _orchestrator
    
    if _orchestrator is None:
        # 确保数据库存在
        if not os.path.exists(db_path):
            import sqlite3
            os.makedirs('data', exist_ok=True)
            conn = sqlite3.connect(db_path)
            
            # 找到 schema 和 seed 文件
            root = os.path.dirname(os.path.dirname(__file__))
            with open(os.path.join(root, 'schema.sql'), 'r') as f:
                conn.executescript(f.read())
            with open(os.path.join(root, 'seed_data.sql'), 'r') as f:
                conn.executescript(f.read())
            conn.close()
            print("✅ 数据库已自动初始化")
        
        _orchestrator = SemanticOrchestrator(db_path)
    
    return _orchestrator


# ============================================================
# 3️⃣ 定义 Tools（使用 @tool 装饰器）
# ============================================================

@tool("semantic_query", args_schema=SemanticQueryInput)
def semantic_query(
    question: str,
    department: Optional[str] = None,
    region: Optional[str] = None,
    period: Optional[str] = None,
    line: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> str:
    """查询企业业务指标。
    
    这个工具可以：
    1. 自动识别用户问的是什么指标（如毛利率、一次合格率）
    2. 根据部门上下文自动选择正确的计算口径
    3. 返回可追溯的结果（包含 Audit ID）
    
    重要提示：
    - 财务部和销售部查询毛利率会得到不同口径的结果
    - 每个查询都有 audit_id，可用于追溯完整决策链
    
    Args:
        question: 用户的业务问题
        department: 部门（影响版本选择）
        region: 区域
        period: 时间周期
        line: 产线
        start_date: 开始日期
        end_date: 结束日期
    """
    orchestrator = get_orchestrator()
    
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
        user_id=1,
        role=f'{department}_manager' if department else 'operator',
        parameters=parameters,
        timestamp=datetime.now()
    )
    
    # 执行查询
    result = orchestrator.query(
        question=question,
        parameters=parameters,
        context=context
    )
    
    # 格式化返回
    if result.get('status') == 'success':
        data = result.get('data', [])
        version = result.get('version_name', 'unknown')
        audit_id = result.get('audit_id', 'N/A')
        
        if data and len(data) > 0:
            first_row = data[0]
            for key, value in first_row.items():
                if isinstance(value, (int, float)):
                    if 'margin' in key.lower():
                        return f"""
查询成功！
- 指标: 毛利率
- 结果: {value * 100:.1f}%
- 使用版本: {version}
- 审计ID: {audit_id}
- 说明: 此结果基于「{version}」口径计算。完整决策链可通过 audit_id 追溯。
"""
                    elif 'fpy' in key.lower():
                        return f"""
查询成功！
- 指标: 一次合格率 (FPY)
- 结果: {value * 100:.2f}%
- 使用版本: {version}
- 审计ID: {audit_id}
"""
                    else:
                        return f"""
查询成功！
- 结果: {value:.4f}
- 使用版本: {version}
- 审计ID: {audit_id}
"""
        return f"查询成功，但无数据返回。版本: {version}, Audit ID: {audit_id}"
    else:
        error = result.get('error', '未知错误')
        return f"查询失败: {error}"


@tool("list_available_metrics")
def list_available_metrics() -> str:
    """列出系统中所有可用的业务指标。
    
    返回系统支持的所有语义对象（指标），包括名称、描述和所属领域。
    """
    orchestrator = get_orchestrator()
    objects = orchestrator.list_semantic_objects()
    
    result = "系统支持的业务指标：\n\n"
    for obj in objects:
        name = obj.get('name', 'unknown')
        desc = obj.get('description', 'N/A')
        domain = obj.get('domain', 'N/A')
        aliases = obj.get('aliases', [])
        
        result += f"📊 {name}\n"
        result += f"   描述: {desc}\n"
        result += f"   领域: {domain}\n"
        result += f"   别名: {', '.join(aliases[:3]) if aliases else 'N/A'}\n\n"
    
    return result


@tool("get_audit_trail", args_schema=AuditQueryInput)
def get_audit_trail(audit_id: str) -> str:
    """查询指定的审计记录，获取完整决策链。
    
    每个查询都会生成一个 audit_id，可以用这个 ID 追溯完整的决策过程，
    包括：语义解析、版本选择、权限检查、SQL 生成和执行等所有步骤。
    
    Args:
        audit_id: 审计记录ID
    """
    orchestrator = get_orchestrator()
    history = orchestrator.get_audit_history(limit=100)
    
    for record in history:
        if record.get('audit_id') == audit_id:
            question = record.get('question', 'N/A')
            status = record.get('status', 'N/A')
            executed_at = record.get('executed_at', 'N/A')
            decision_trace = record.get('decision_trace', [])
            
            result = f"""
审计记录详情
============
- Audit ID: {audit_id}
- 问题: {question}
- 状态: {status}
- 执行时间: {executed_at}

决策链 ({len(decision_trace)} 步):
"""
            for i, step in enumerate(decision_trace[:10], 1):  # 最多显示 10 步
                step_name = step.get('step', 'unknown')
                result += f"  {i}. {step_name}\n"
            
            if len(decision_trace) > 10:
                result += f"  ... 还有 {len(decision_trace) - 10} 步\n"
            
            return result
    
    return f"未找到 audit_id 为 {audit_id} 的审计记录"


# ============================================================
# 4️⃣ 创建 Agent（使用 create_agent）
# ============================================================

def create_semantic_agent(model_name: str = "gpt-4o"):
    """
    创建带有语义控制面能力的 Agent
    
    Args:
        model_name: OpenAI 模型名称
    
    Returns:
        可以处理业务查询的 Agent
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("请先安装 LangChain: pip install langchain langchain-openai langgraph")
    
    try:
        from langchain.agents import create_agent
    except ImportError:
        # 兼容旧版本
        from langchain.agents import create_openai_functions_agent, AgentExecutor
        from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
        
        llm = ChatOpenAI(model=model_name, temperature=0)
        tools = [semantic_query, list_available_metrics, get_audit_trail]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个企业数据分析助手，负责帮助用户查询业务指标。

你有以下工具可用：
1. semantic_query - 查询业务指标（如毛利率、一次合格率）
2. list_available_metrics - 列出所有可用指标
3. get_audit_trail - 查询审计记录

重要提示：
- 从用户问题中提取部门、区域、时间等上下文
- 不同部门查询同一指标可能得到不同结果（口径不同）
- 每个查询都有 Audit ID，可用于追溯决策链
- 如果用户问"为什么结果不一样"，检查是否使用了不同的部门口径
"""),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_functions_agent(llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)
    
    # 使用新版 create_agent（如果可用）
    llm = ChatOpenAI(model=model_name, temperature=0)
    tools = [semantic_query, list_available_metrics, get_audit_trail]
    
    return create_agent(
        llm,
        tools=tools,
        system_prompt="""你是一个企业数据分析助手，负责帮助用户查询业务指标。

重要提示：
- 从用户问题中提取部门、区域、时间等上下文
- 不同部门查询同一指标可能得到不同结果（口径不同）
- 每个查询都有 Audit ID，可用于追溯决策链
"""
    )


# ============================================================
# 5️⃣ 演示
# ============================================================

def demo_tools_directly():
    """直接调用 Tool（不需要 API Key）"""
    print("=" * 80)
    print("🔧 直接调用 Tool 演示（无需 API Key）")
    print("=" * 80)
    
    # 切换到项目根目录
    os.chdir(os.path.dirname(os.path.dirname(__file__)))
    
    # 1. 列出可用指标
    print("\n📋 调用 list_available_metrics:")
    print("-" * 60)
    result = list_available_metrics.invoke({})
    print(result)
    
    # 2. 财务视角查询毛利率
    print("\n💰 调用 semantic_query（财务视角）:")
    print("-" * 60)
    result = semantic_query.invoke({
        "question": "上月华东区毛利率是多少？",
        "department": "finance",
        "region": "华东",
        "period": "2026-01"
    })
    print(result)
    
    # 3. 销售视角查询毛利率
    print("\n📈 调用 semantic_query（销售视角）:")
    print("-" * 60)
    result = semantic_query.invoke({
        "question": "上月华东区毛利率是多少？",
        "department": "sales",
        "region": "华东",
        "period": "2026-01"
    })
    print(result)
    
    # 4. 查询 FPY
    print("\n🏭 调用 semantic_query（一次合格率）:")
    print("-" * 60)
    result = semantic_query.invoke({
        "question": "昨天产线A的一次合格率是多少？",
        "line": "A",
        "start_date": "2026-01-27",
        "end_date": "2026-01-27"
    })
    print(result)


def demo_with_agent():
    """使用 Agent 演示（需要 API Key）"""
    print("\n" + "=" * 80)
    print("🤖 使用 Agent 演示")
    print("=" * 80)
    
    if not LANGCHAIN_AVAILABLE:
        print("\n⚠️  LangChain 未安装")
        print("请运行: pip install langchain langchain-openai langgraph")
        print("\n以下是安装后的调用示例：\n")
        print("""
from integrations.langchain_tool_v2 import create_semantic_agent

agent = create_semantic_agent()
result = agent.invoke({"input": "帮我查一下上月华东区的毛利率，我是财务部的"})
print(result["output"])
""")
        return
    
    if not os.environ.get("OPENAI_API_KEY"):
        print("\n⚠️  未设置 OPENAI_API_KEY")
        print("请运行: export OPENAI_API_KEY=your_key")
        print("\n以下是 Agent 调用示例代码：\n")
        print("""
from integrations.langchain_tool_v2 import create_semantic_agent

agent = create_semantic_agent()

# 对话 1
result = agent.invoke({
    "input": "帮我查一下上月华东区的毛利率，我是财务部的"
})
print(result["output"])

# 对话 2
result = agent.invoke({
    "input": "销售部那边说毛利率是 28%，怎么跟你说的不一样？"
})
print(result["output"])
""")
        return
    
    agent = create_semantic_agent()
    
    queries = [
        "帮我查一下上月华东区的毛利率，我是财务部的",
        "销售部那边说毛利率是 28%，怎么跟你说的不一样？",
        "系统支持查询哪些指标？",
    ]
    
    for query in queries:
        print(f"\n📝 用户: {query}")
        print("-" * 60)
        result = agent.invoke({"input": query})
        print(f"🤖 Agent: {result['output']}")


if __name__ == "__main__":
    demo_tools_directly()
    demo_with_agent()
