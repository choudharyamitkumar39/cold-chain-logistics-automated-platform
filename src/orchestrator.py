import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

# ==========================================
# 1. SETUP & PATH RESOLUTION
# ==========================================
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

load_dotenv(project_root / ".env")

from src.agent_tools import query_telemetry_db, fetch_corridor_conditions, search_compliance_sop

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# ==========================================
# 2. FACTORY INITIALIZATION: AGENT REASONER LLM
# ==========================================
AGENT_LLM_SETTING = os.getenv("AGENT_LLM", "GEMINI").strip().upper()

if AGENT_LLM_SETTING == "GEMINI":
    google_key = os.getenv("GOOGLE_API_KEY")
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
    print(f"✨ Brain Mode: Utilizing Google Gemini Cloud Reasoner ({gemini_model})...")
    from langchain_google_genai import ChatGoogleGenerativeAI
    llm = ChatGoogleGenerativeAI(
        model=gemini_model,
        temperature=0,
        google_api_key=google_key,
        convert_system_message_to_human=True
    )

elif AGENT_LLM_SETTING == "OPENAI":
    print("🤖 Brain Mode: Utilizing Cloud OpenAI Reasoner (gpt-4o)...")
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

elif AGENT_LLM_SETTING == "DEEPSEEK":
    print("🐳 Brain Mode: Utilizing DeepSeek Cloud Reasoner...")
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(
        model="deepseek-v4-flash",
        temperature=0,
        openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
        max_tokens=2048
    )

else:
    print("🤗 Brain Mode: Local Fallback Activated (ChatOllama qwen2.5:7b)...")
    from langchain_community.chat_models import ChatOllama
    llm = ChatOllama(model="qwen2.5:7b", temperature=0, num_predict=1024)

fde_tools = [query_telemetry_db, fetch_corridor_conditions, search_compliance_sop]
llm_with_tools = llm.bind_tools(fde_tools)

# ==========================================
# 3. GRAPH ARCHITECTURE ASSEMBLY
# ==========================================
def reasoning_node(state: AgentState):
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

print("⚙️ Compiling LangGraph FDE Orchestrator...")
graph_builder = StateGraph(AgentState)
graph_builder.add_node("reasoner", reasoning_node)
graph_builder.add_node("tools", ToolNode(fde_tools))

graph_builder.add_edge(START, "reasoner")
graph_builder.add_conditional_edges("reasoner", tools_condition)
graph_builder.add_edge("tools", "reasoner")

fde_agent = graph_builder.compile(checkpointer=MemorySaver())

# ==========================================
# 4. CHAT LOOP TESTING PANEL
# ==========================================
if __name__ == "__main__":
    print("\n" + "="*55)
    print("🚀 FDE Cold-Chain Orchestrator State Machine Online")
    print(f"   Configured Execution: [LLM: {AGENT_LLM_SETTING}] -> [Embeddings: {os.getenv('EMBEDDINGS_MODEL', 'GEMINI')}]")
    print("="*55 + "\n")
    
    prompt_path = project_root / "src" / "prompts" / "system_prompt.txt"
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_instructions = f.read()
    except FileNotFoundError:
        print(f"Warning: Could not find {prompt_path}")
        system_instructions = "You are a helpful logistics AI assistant."

    system_prompt = SystemMessage(content=system_instructions)
    thread_config = {"configurable": {"thread_id": "cli_test_session"}}
    fde_agent.invoke({"messages": [system_prompt]}, config=thread_config)
    
    while True:
        try:
            user_input = input("\nDispatcher > ")
        except (KeyboardInterrupt, EOFError):
            break
            
        if user_input.lower() in ['exit', 'quit']:
            break
            
        events = fde_agent.stream({"messages": [("user", user_input)]}, config=thread_config, stream_mode="updates")
        for event in events:
            for node_name, node_state in event.items():
                if node_name == "tools":
                    print("   [System] 🔄 Retrieving external data elements via ToolNode...")
                elif node_name == "reasoner":
                    latest_msg = node_state["messages"][-1]
                    if latest_msg.content:
                        if isinstance(latest_msg.content, list):
                            text_out = "".join([c.get("text", "") if isinstance(c, dict) else str(c) for c in latest_msg.content])
                        else:
                            text_out = str(latest_msg.content)
                        print(f"\n🤖 FDE Agent:\n{text_out}")
