#!/usr/bin/env python3
"""
LangChain 多模型集成 - 支持 Gemini 和 Groq

使用方法:
    1. pip install langchain langchain-google-genai langchain-groq python-dotenv
    2. cp .env.example .env
    3. 编辑 .env 填入你的 API Key
    4. python integrations/langchain_multimodel.py

支持的模型:
    - Gemini: gemini-2.5-flash-lite, gemini-2.5-flash, gemini-2.5-pro
    - Groq: llama-3.3-70b-versatile, mixtral-8x7b-32768, gemma2-9b-it
"""

import os
import sys
from typing import Optional, Literal
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

# 自动加载 .env 文件
try:
    from dotenv import load_dotenv
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ 已从 {env_path} 加载环境变量")
    else:
        # 尝试从当前目录加载
        if Path('.env').exists():
            load_dotenv('.env')
            print("✅ 已从 .env 加载环境变量")
except ImportError:
    pass  # python-dotenv 未安装，依赖手动 export

# ============================================================
# 1️⃣ 检查依赖
# ============================================================

GEMINI_AVAILABLE = False
GROQ_AVAILABLE = False
LANGCHAIN_AVAILABLE = False

try:
    from langchain.chat_models import init_chat_model
    LANGCHAIN_AVAILABLE = True
except ImportError:
    print("⚠️  LangChain 未安装，运行: pip install langchain")

try:
    import langchain_google_genai
    GEMINI_AVAILABLE = True
except ImportError:
    print("⚠️  Gemini 集成未安装，运行: pip install langchain-google-genai")

try:
    import langchain_groq
    GROQ_AVAILABLE = True
except ImportError:
    print("⚠️  Groq 集成未安装，运行: pip install langchain-groq")

from semantic_layer import SemanticOrchestrator
from semantic_layer.models import ExecutionContext


# ============================================================
# 2️⃣ 模型配置
# ============================================================

# 推荐的模型配置
MODEL_CONFIGS = {
    # Gemini 模型（Google）- 适合复杂推理
    "gemini-flash": {
        "model": "gemini-2.5-flash-lite",
        "provider": "google_genai",
        "description": "Gemini 2.5 Flash Lite - 快速响应，适合简单查询",
        "env_key": "GOOGLE_API_KEY"
    },
    "gemini-pro": {
        "model": "gemini-2.5-pro",
        "provider": "google_genai", 
        "description": "Gemini 2.5 Pro - 高质量推理，适合复杂分析",
        "env_key": "GOOGLE_API_KEY"
    },
    
    # Groq 模型 - 超快推理速度
    "groq-llama": {
        "model": "llama-3.3-70b-versatile",
        "provider": "groq",
        "description": "Llama 3.3 70B on Groq - 超快速度，免费额度",
        "env_key": "GROQ_API_KEY"
    },
    "groq-mixtral": {
        "model": "mixtral-8x7b-32768",
        "provider": "groq",
        "description": "Mixtral 8x7B on Groq - 平衡速度与质量",
        "env_key": "GROQ_API_KEY"
    },
    "groq-gemma": {
        "model": "gemma2-9b-it",
        "provider": "groq",
        "description": "Gemma 2 9B on Groq - 轻量级，适合简单任务",
        "env_key": "GROQ_API_KEY"
    },
}


def get_available_models() -> list[str]:
    """获取当前可用的模型列表"""
    available = []
    for name, config in MODEL_CONFIGS.items():
        env_key = config["env_key"]
        if os.environ.get(env_key):
            if config["provider"] == "google_genai" and GEMINI_AVAILABLE:
                available.append(name)
            elif config["provider"] == "groq" and GROQ_AVAILABLE:
                available.append(name)
    return available


def create_model(model_name: str = "groq-llama", temperature: float = 0):
    """
    创建指定的模型实例
    
    Args:
        model_name: 模型名称（见 MODEL_CONFIGS）
        temperature: 温度参数
    
    Returns:
        LangChain ChatModel 实例
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("请安装 LangChain: pip install langchain")
    
    if model_name not in MODEL_CONFIGS:
        raise ValueError(f"未知模型: {model_name}，可用: {list(MODEL_CONFIGS.keys())}")
    
    config = MODEL_CONFIGS[model_name]
    
    # 检查 API Key
    env_key = config["env_key"]
    if not os.environ.get(env_key):
        raise ValueError(f"请设置环境变量: export {env_key}=your_key")
    
    # 使用 init_chat_model 创建模型
    return init_chat_model(
        model=config["model"],
        model_provider=config["provider"],
        temperature=temperature,
    )


def create_configurable_model(default_model: str = "groq-llama"):
    """
    创建可配置的模型（运行时可切换）
    
    使用示例:
        model = create_configurable_model()
        
        # 使用 Groq
        model.invoke("Hello", config={"configurable": {"model": "llama-3.3-70b-versatile", "model_provider": "groq"}})
        
        # 切换到 Gemini
        model.invoke("Hello", config={"configurable": {"model": "gemini-2.5-flash-lite", "model_provider": "google_genai"}})
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("请安装 LangChain: pip install langchain")
    
    config = MODEL_CONFIGS.get(default_model, MODEL_CONFIGS["groq-llama"])
    
    return init_chat_model(
        model=config["model"],
        model_provider=config["provider"],
        temperature=0,
        configurable_fields=("model", "model_provider", "temperature"),
    )


# ============================================================
# 3️⃣ 语义控制面 Tool 集成
# ============================================================

_orchestrator: Optional[SemanticOrchestrator] = None

def get_orchestrator(db_path: str = "data/semantic_layer.db") -> SemanticOrchestrator:
    """获取或创建 Orchestrator 单例"""
    global _orchestrator
    
    if _orchestrator is None:
        if not os.path.exists(db_path):
            import sqlite3
            os.makedirs('data', exist_ok=True)
            conn = sqlite3.connect(db_path)
            root = os.path.dirname(os.path.dirname(__file__))
            with open(os.path.join(root, 'schema.sql'), 'r') as f:
                conn.executescript(f.read())
            with open(os.path.join(root, 'seed_data.sql'), 'r') as f:
                conn.executescript(f.read())
            conn.close()
            print("✅ 数据库已自动初始化")
        _orchestrator = SemanticOrchestrator(db_path)
    return _orchestrator


def semantic_query_func(
    question: str,
    department: Optional[str] = None,
    region: Optional[str] = None,
    period: Optional[str] = None,
    line: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> str:
    """执行语义查询的核心函数"""
    orchestrator = get_orchestrator()
    
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
    
    context = ExecutionContext(
        user_id=1,
        role=f'{department}_manager' if department else 'operator',
        parameters=parameters,
        timestamp=datetime.now()
    )
    
    result = orchestrator.query(
        question=question,
        parameters=parameters,
        context=context
    )
    
    if result.get('status') == 'success':
        data = result.get('data', [])
        version = result.get('version_name', 'unknown')
        audit_id = result.get('audit_id', 'N/A')
        
        if data and len(data) > 0:
            for key, value in data[0].items():
                if isinstance(value, (int, float)):
                    if 'margin' in key.lower():
                        return f"毛利率: {value * 100:.1f}% (版本: {version}, Audit: {audit_id})"
                    elif 'fpy' in key.lower():
                        return f"一次合格率: {value * 100:.2f}% (版本: {version}, Audit: {audit_id})"
                    else:
                        return f"结果: {value:.4f} (版本: {version}, Audit: {audit_id})"
        return f"查询成功，无数据。版本: {version}"
    return f"查询失败: {result.get('error', '未知错误')}"


def create_semantic_tools():
    """创建语义控制面工具列表"""
    try:
        from langchain.tools import tool
        from pydantic import BaseModel, Field
    except ImportError:
        print("⚠️  请安装: pip install langchain pydantic")
        return []
    
    class SemanticQueryInput(BaseModel):
        """语义查询输入"""
        question: str = Field(description="业务问题，如'上月华东区毛利率是多少？'")
        department: Optional[Literal["finance", "sales"]] = Field(
            default=None, description="部门：finance=财务口径，sales=销售口径"
        )
        region: Optional[str] = Field(default=None, description="区域，如'华东'")
        period: Optional[str] = Field(default=None, description="时间周期，如'2026-01'")
        line: Optional[str] = Field(default=None, description="产线，如'A'")
        start_date: Optional[str] = Field(default=None, description="开始日期")
        end_date: Optional[str] = Field(default=None, description="结束日期")
    
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
        """查询企业业务指标。根据部门自动选择计算口径，返回可追溯的结果。"""
        return semantic_query_func(question, department, region, period, line, start_date, end_date)
    
    @tool("list_metrics")
    def list_metrics() -> str:
        """列出系统支持的所有业务指标。"""
        orchestrator = get_orchestrator()
        objects = orchestrator.list_semantic_objects()
        result = "可用指标：\n"
        for obj in objects:
            result += f"- {obj['name']}: {obj.get('description', 'N/A')[:50]}...\n"
        return result
    
    return [semantic_query, list_metrics]


def create_agent_with_tools(model_name: str = "groq-llama"):
    """
    创建带语义控制面能力的 Agent
    
    Args:
        model_name: 使用的模型（见 MODEL_CONFIGS）
    
    Returns:
        AgentExecutor
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("请安装: pip install langchain")
    
    try:
        from langchain.agents import create_openai_functions_agent, AgentExecutor
        from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    except ImportError:
        raise ImportError("请安装: pip install langchain")
    
    model = create_model(model_name, temperature=0)
    tools = create_semantic_tools()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是企业数据分析助手。使用 semantic_query 工具查询业务指标。

重要提示：
- 财务部和销售部查询毛利率会得到不同结果（口径不同）
- 每个查询都有 Audit ID 可追溯
- 如果用户问"为什么结果不一样"，检查部门口径差异
"""),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # 注意：Groq 和 Gemini 都支持 OpenAI 兼容的 function calling
    agent = create_openai_functions_agent(model, tools, prompt)
    
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True
    )


# ============================================================
# 4️⃣ 演示
# ============================================================

def demo_direct_query():
    """直接使用语义控制面查询（无需 LLM）"""
    print("=" * 80)
    print("🔧 直接调用语义控制面（无需 LLM API Key）")
    print("=" * 80)
    
    os.chdir(os.path.dirname(os.path.dirname(__file__)))
    
    print("\n💰 财务视角查询毛利率:")
    result = semantic_query_func(
        question="上月华东区毛利率是多少？",
        department="finance",
        region="华东",
        period="2026-01"
    )
    print(f"   {result}")
    
    print("\n📈 销售视角查询毛利率:")
    result = semantic_query_func(
        question="上月华东区毛利率是多少？",
        department="sales",
        region="华东",
        period="2026-01"
    )
    print(f"   {result}")
    
    print("\n🏭 查询一次合格率:")
    result = semantic_query_func(
        question="昨天产线A的一次合格率是多少？",
        line="A",
        start_date="2026-01-27",
        end_date="2026-01-27"
    )
    print(f"   {result}")


def demo_with_llm():
    """使用 LLM Agent 进行对话"""
    print("\n" + "=" * 80)
    print("🤖 使用 LLM Agent（需要 API Key）")
    print("=" * 80)
    
    # 检查可用模型
    available = get_available_models()
    if not available:
        print("\n⚠️  未找到可用的模型 API Key")
        print("\n请设置以下环境变量之一：")
        print("   export GOOGLE_API_KEY=your_gemini_key")
        print("   export GROQ_API_KEY=your_groq_key")
        print("\n推荐使用 Groq（免费额度，速度极快）：")
        print("   1. 访问 https://console.groq.com/keys")
        print("   2. 创建 API Key")
        print("   3. export GROQ_API_KEY=your_key")
        return
    
    print(f"\n✅ 可用模型: {available}")
    
    # 优先使用 Groq（免费且快）
    model_name = "groq-llama" if "groq-llama" in available else available[0]
    print(f"📌 使用模型: {model_name}")
    
    try:
        agent = create_agent_with_tools(model_name)
        
        queries = [
            "帮我查一下上月华东区的毛利率，我是财务部的",
            "系统支持查询哪些指标？",
        ]
        
        for query in queries:
            print(f"\n📝 用户: {query}")
            print("-" * 60)
            result = agent.invoke({"input": query})
            print(f"🤖 Agent: {result['output']}")
    except Exception as e:
        print(f"\n❌ 错误: {e}")


def show_setup_guide():
    """显示配置指南"""
    print("\n" + "=" * 80)
    print("📋 配置指南")
    print("=" * 80)
    print("""
1. 安装依赖：
   pip install langchain langchain-google-genai langchain-groq pydantic

2. 设置 API Key（二选一）：

   【推荐】Groq（免费 + 超快）：
   - 访问 https://console.groq.com/keys 获取 Key
   - export GROQ_API_KEY=gsk_xxx
   
   【可选】Gemini：
   - 访问 https://aistudio.google.com/apikey 获取 Key
   - export GOOGLE_API_KEY=AIza_xxx

3. 运行测试：
   python integrations/langchain_multimodel.py

4. 在代码中使用：

   from integrations.langchain_multimodel import create_agent_with_tools
   
   # 使用 Groq（推荐，免费且快）
   agent = create_agent_with_tools("groq-llama")
   result = agent.invoke({"input": "上月华东区毛利率是多少？我是财务部的"})
   
   # 或使用 Gemini
   agent = create_agent_with_tools("gemini-flash")
""")


if __name__ == "__main__":
    show_setup_guide()
    demo_direct_query()
    demo_with_llm()
