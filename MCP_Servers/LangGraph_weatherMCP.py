import asyncio
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition

load_dotenv()

async def main():
    OPEN_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENWEATHER_API_KEY  = os.getenv('OPENWEATHER_API_KEY')

    client = MultiServerMCPClient(
        {
            "weather": {
                "transport": "stdio",
                "command": "C:/Users/USER/PycharmProjects/test-orbit-ai/MCP_Servers/mcp-openweather/mcp-weather.exe",
                "args": [],
                "env": {"OPENWEATHER_API_KEY": OPENWEATHER_API_KEY}

            }
        }
    )

    tools = await client.get_tools()
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=OPEN_API_KEY)

    async def call_model(state: MessagesState):
        bound_model = model.bind_tools(tools)  # bind INSIDE node
        response = await bound_model.ainvoke(state["messages"])
        return {"messages": [response]}

    builder = StateGraph(MessagesState)
    builder.add_node("call_model", call_model)  #"call_model" - node name,  call_model - node function
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "call_model") # start connects to call_model
    builder.add_conditional_edges("call_model", tools_condition) # connects to tool node if tools required
    builder.add_edge("tools", "call_model") # connects back to call_model
    graph = builder.compile()

    result = await graph.ainvoke({"messages": [HumanMessage(content="What is the weather in Delhi today?")]})
    print(result["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(main())





