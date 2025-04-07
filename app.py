import streamlit as st
from dotenv import load_dotenv
from typing import Any, Dict, List, Optional
import asyncio
from agents import get_agent, get_observer

async def add_message(
    role: str, content: str, tool_calls: Optional[List[Dict[str, Any]]] = None
) -> None:
    """Safely add a message to the session state."""
    if "messages" not in st.session_state or not isinstance(
        st.session_state["messages"], list
    ):
        st.session_state["messages"] = []
    st.session_state["messages"].append(
        {"role": role, "content": content, "tool_calls": tool_calls}
    )

async def main() -> None:
    load_dotenv()
    st.set_page_config(page_title="PokeStory", page_icon="pokeball.png")
    st.title("📚 PokeStory")

    with st.sidebar:
        st.markdown("# :material/list_alt: Pokemon của bạn")
    agent = get_agent()
    # observer = get_observer()

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if prompt := st.chat_input("Placeholder"):
        await add_message("user", prompt)
    # Display chat history
    for message in st.session_state["messages"]:
        if message["role"] in ["user", "assistant"]:
            _content = message["content"]
            if _content is not None:
                with st.chat_message(message["role"]):
                    st.markdown(_content)

    last_message = (
        st.session_state["messages"][-1] if st.session_state["messages"] else None
    )
    if last_message and last_message.get("role") == "user":
        prompt = last_message["content"]
        with st.chat_message("assistant"):
            response = ""
            resp_container = st.empty()
            with st.spinner("Suy nghĩ..."):
                try:
                    # Run the agent and stream the response
                    run_response = await agent.arun(prompt, stream=True)
                    async for _resp_chunk in run_response:
                        if _resp_chunk.content is not None:
                            response += _resp_chunk.content
                            resp_container.markdown(response)
                    await add_message("assistant", response)
                except Exception as e:
                    error_message = f"Sorry, I encountered an error: {str(e)}"
                    await add_message("assistant", error_message)
                    st.error(error_message)

            # with st.spinner("Cập nhật thông tin..."):
            #     last_n_messages = [msg["content"] for msg in st.session_state["messages"][-5:] if "content" in msg]
            #     last_n_str = "\n".join(last_n_messages)
            #     observer_update = await observer.arun(last_n_str)
            #     # print(observer_update.content)
            #     st.sidebar.markdown(observer_update.content)

if __name__ == "__main__":
    asyncio.run(main())