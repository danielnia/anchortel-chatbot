from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor
from langchain.agents.openai_functions_agent.agent_token_buffer_memory import AgentTokenBufferMemory
from langchain.agents.openai_functions_agent.base import OpenAIFunctionsAgent
from tools import create_account, reset_password, get_billing_info
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage
import logging
from langchain.chains import RetrievalQA
from langchain.agents import Tool
import sqlite3
from datetime import datetime
import itertools


memory_store = {}

def build_tools():
    return [create_account, reset_password, get_billing_info]

# Get or create memory per user
def get_session_memory(session_id: str, llm) -> AgentTokenBufferMemory:
    if session_id not in memory_store:
        memory_store[session_id] = AgentTokenBufferMemory(
            memory_key="chat_history",  # key used inside the prompt
            llm=llm,
            max_token_limit=2000
        )
    return memory_store[session_id]



# Log unhandled queries for support wit8h Metadata

def log_unhandled(user_id: str, message: str):
    conn = sqlite3.connect("nhandled_queries.db")  # relative path
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO unhandled_queries (user_id, message, timestamp)
        VALUES (?, ?, ?)
    ''', (user_id, message, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


# Async query handler with persistent memory
async def handle_query(session_id: str, user_input: str, logs: list[str], return_docs: bool = False) -> dict | str:
    try:
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        memory = get_session_memory(session_id, llm)

        from rag_store import retriever
        rag_chain = RetrievalQA.from_chain_type(llm=llm,
                                                retriever=retriever,
                                                return_source_documents=return_docs )

        def rag_tool_func(query):
            result = rag_chain({"query": query})
            return {
                "answer": result.get("result", "").strip(),
                "source_documents": result.get("source_documents", [])
            }

        rag_tool = Tool(
            name="AnchortelKnowledgeBase",
            func=rag_tool_func,
            description="Useful for answering customer questions about AnchorTel's services, plans, and policies."
        )

        tools = build_tools() + [rag_tool]

        system_message = SystemMessage(
            content=(
                """You are an intelligent assistant for AnchorTel. ..."""
            )
        )

        prompt = ChatPromptTemplate.from_messages([
            system_message,
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        agent = OpenAIFunctionsAgent(
            llm=llm,
            tools=tools,
            prompt=prompt
        )

        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            verbose=True,
            return_intermediate_steps=True,
            handle_parsing_errors=True
        )
        logs.append("Agent created, calling execution.")
        result = await agent_executor.ainvoke({"input": user_input})

        output = result.get("output", "").strip()

        # Extract source_documents from intermediate_steps if RAG tool was used
        source_documents = []
        print(result.keys())

        if return_docs and "intermediate_steps" in result:
            # print("intermediate_steps found in result: ", result["intermediate_steps"])
            for action, observation in result["intermediate_steps"]:
                if getattr(action, "tool", None) == "AnchortelKnowledgeBase":
                    # observation is the return value of rag_tool_func
                    docs = observation.get("source_documents", [])
                    source_documents.extend(docs)
            # Remove duplicates if needed
            source_documents = list({id(doc): doc for doc in source_documents}.values())

        if return_docs:
            return {
                "answer": output,
                "source_documents": source_documents
            }

        return output

    except Exception as e:
        logging.error(f"Error in handle_query: {e}", exc_info=True)
        return "An internal error occurred while handling your request."

