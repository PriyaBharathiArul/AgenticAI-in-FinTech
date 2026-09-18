import streamlit as st
from datetime import datetime

import config
from agents import run_single_agent, run_multi_agent


st.set_page_config(
    page_title="Agentic AI in FinTech",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Agentic AI in FinTech")
st.caption("Single Agent vs Multi-Agent with conversational memory")


def build_contextual_question(history, new_question, max_exchanges=3):
    if not history:
        return new_question

    recent_history = history[-(max_exchanges * 2):]

    lines = [
        "Use the conversation history below to answer the latest user question.",
        "Resolve follow-up references such as 'that', 'it', 'the two', etc.",
        "",
        "Conversation history:"
    ]

    for msg in recent_history:
        role = "User" if msg["role"] == "user" else "Assistant"
        lines.append(f"{role}: {msg['content']}")

    lines.append("")
    lines.append(f"Latest user question: {new_question}")
    lines.append("Answer the latest user question using the conversation context above.")

    return "\n".join(lines)


def set_active_model(model_label: str):
    if model_label == "gpt-4o-mini":
        config.set_active_model(config.MODEL_SMALL)
    else:
        config.set_active_model(config.MODEL_LARGE)


def run_selected_agent(agent_mode: str, contextual_question: str):
    if agent_mode == "Single Agent":
        result = run_single_agent(contextual_question, verbose=False)

        answer_text = result.answer if isinstance(result.answer, str) else str(result.answer)
        metadata = {
            "architecture": "Single Agent",
            "model": config.ACTIVE_MODEL,
            "tools_used": result.tools_called,
            "tool_count": len(result.tools_called),
            "confidence": getattr(result, "confidence", None),
        }
        return answer_text, metadata

    else:
        result = run_multi_agent(contextual_question, verbose=False)

        answer_text = result.get("final_answer", "")
        if not isinstance(answer_text, str):
            answer_text = str(answer_text)

        agent_results = result.get("agent_results", [])
        all_tools = []
        for r in agent_results:
            if hasattr(r, "tools_called"):
                all_tools.extend(r.tools_called)

        metadata = {
            "architecture": result.get("architecture", "Multi Agent"),
            "model": config.ACTIVE_MODEL,
            "tools_used": list(dict.fromkeys(all_tools)),
            "tool_count": len(all_tools),
            "elapsed_sec": result.get("elapsed_sec", None),
            "agents_used": [r.agent_name for r in agent_results if hasattr(r, "agent_name")],
        }
        return answer_text, metadata


def render_metadata(meta: dict):
    architecture = meta.get("architecture", "Unknown")
    model = meta.get("model", "Unknown")
    tool_count = meta.get("tool_count", 0)

    st.caption(f"Architecture: {architecture}  |  Model: {model}  |  Tool calls: {tool_count}")

    tools = meta.get("tools_used", [])
    if tools:
        st.caption("Tools used: " + ", ".join(tools))

    agents_used = meta.get("agents_used")
    if agents_used:
        st.caption("Agents activated: " + ", ".join(agents_used))


if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_agent_mode" not in st.session_state:
    st.session_state.last_agent_mode = "Single Agent"

if "last_model_choice" not in st.session_state:
    st.session_state.last_model_choice = "gpt-4o-mini"


with st.sidebar:
    st.header("Controls")

    agent_mode = st.selectbox(
        "Agent selector",
        ["Single Agent", "Multi-Agent"],
        index=0 if st.session_state.last_agent_mode == "Single Agent" else 1,
    )

    model_choice = st.selectbox(
        "Model selector",
        ["gpt-4o-mini", "gpt-4o"],
        index=0 if st.session_state.last_model_choice == "gpt-4o-mini" else 1,
    )

    if st.button("Clear conversation", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

    st.markdown("---")
    st.subheader("Current settings")
    st.write(f"**Architecture:** {agent_mode}")
    st.write(f"**Model:** {model_choice}")

    st.markdown("---")
    st.subheader("Memory behavior")
    st.write(
        "This app passes recent conversation history to the selected agent so follow-up "
        "questions like 'that', 'it', or 'the two' can be resolved."
    )

st.session_state.last_agent_mode = agent_mode
st.session_state.last_model_choice = model_choice

set_active_model(model_choice)


for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if msg["role"] == "assistant" and "metadata" in msg:
            render_metadata(msg["metadata"])


user_input = st.chat_input("Ask a finance question...")

if user_input:
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now().isoformat()
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    contextual_question = build_contextual_question(
        st.session_state.chat_history,
        user_input,
        max_exchanges=3
    )

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                answer_text, metadata = run_selected_agent(agent_mode, contextual_question)

                st.markdown(answer_text)
                render_metadata(metadata)

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer_text,
                    "metadata": metadata,
                    "timestamp": datetime.now().isoformat()
                })

            except Exception as e:
                error_text = f"An error occurred while running the agent:\n\n`{e}`"
                st.error(error_text)

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": error_text,
                    "metadata": {
                        "architecture": agent_mode,
                        "model": config.ACTIVE_MODEL,
                        "tools_used": [],
                        "tool_count": 0,
                    },
                    "timestamp": datetime.now().isoformat()
                })
