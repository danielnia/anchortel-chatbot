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
import sqlite3
from datetime import datetime

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
async def handle_query(session_id: str, user_input: str, logs: list[str]) -> str:
    try:
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        memory = get_session_memory(session_id, llm)


        from rag_store import retriever
        rag_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)
        rag_tool = Tool(
            name="AnchortelKnowledgeBase",
            func=rag_chain.run,
            description="Useful for answering customer questions about AnchorTel's services, plans, and policies."
        )

        tools = build_tools() + [rag_tool]

        system_message = SystemMessage(
            content=(
                """You are an intelligent assistant for AnchorTel. You have access to:
                - Tools for account actions (create, reset, billing)
                - A document retriever for questions about AnchorTel services

                Instructions:
                - If you're unsure or don’t have enough information to answer, reply with: 
                  "I’m not sure about that. Let me note it down for follow-up."
                - Never make up facts or hallucinate.
                - If a required field is missing (e.g., email), ask for it before using a tool.
                - Use tools or the retriever only when necessary to complete the user's request.
                - If the answer may be unclear or incomplete, ask a clarifying question.
                - Use the AnchortelKnowledgeBase tool when the user asks general questions about services, plans, 
                  or policies."""
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

        # If output is empty, fall back to RAG
        if not output or "i don't know" in output.lower() or "not sure" in output.lower():
            # Optionally add a fallback like RAG or a logged message
            rag_answer = rag_chain.run(user_input).strip()
            if rag_answer:
                return rag_answer

            log_unhandled(session_id, user_input)
            return "I'm not sure I have that information right now. Could you rephrase or give more details?"

        return output

    except Exception as e:
        logging.error(f"Error in handle_query: {e}", exc_info=True)
        return "An internal error occurred while handling your request."

