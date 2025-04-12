import streamlit as st
from dotenv import load_dotenv
from typing import Any, Dict, List, Optional
import asyncio
import nest_asyncio
from agents import get_narrator, get_observer
from utils import CUSTOM_CSS

nest_asyncio.apply() # Allows nesting of event loops

load_dotenv()

st.set_page_config(page_title="PokeStory", page_icon="pokeball.png",layout="wide")
st.title("📚 PokeStory")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
col1, col2 = st.columns([2, 1],border=True)

with col1:
    tab1, tab2 = st.tabs([":material/stylus: **Lượt hiện tại**", ":material/history: **Xem lại**"])

with col2:
    st.subheader("Bảng thông tin")

with st.sidebar:
    st.markdown("# :material/list_alt: Menu")
    st.session_state.observer_output_container = st.container()

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
    if "narrator" not in st.session_state:
        print("--- Initializing narrator for this session ---")
        st.session_state.narrator = get_narrator()

    if "observer" not in st.session_state:
        print("--- Initializing observer for this session ---")
        st.session_state.observer = get_observer()

    # Use the agents stored in session state
    narrator = st.session_state.narrator
    observer = st.session_state.observer

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    with col1:
        with tab1:
            current_container = st.container()
            if prompt := tab1.chat_input("Bạn muốn làm gì tiếp theo?"):
                await add_message("user", prompt)
            last_message = st.session_state["messages"][-1] if st.session_state["messages"] else None

            if last_message and last_message["role"] == "user":
                user_prompt = last_message["content"]

                with current_container.chat_message("user"):
                    st.markdown(user_prompt)

                with current_container.chat_message("assistant"):
                    response = ""
                    resp_container = st.empty()
                    assistant_error = None
                    with st.spinner("Suy nghĩ..."):
                        try:
                            run_response = await narrator.arun(user_prompt, stream=True)
                            async for _resp_chunk in run_response:
                                if _resp_chunk.content is not None:
                                    response += _resp_chunk.content
                                    resp_container.markdown(response)
                            await add_message("assistant", response)

                        except Exception as e:
                            assistant_error = e # Store the error
                            error_message = f"Xin lỗi, tôi gặp lỗi: {str(e)}"
                            resp_container.error(error_message) # Display error in chat
                            await add_message("assistant", error_message)

                    if response and not assistant_error:
                        with col2:
                            with st.spinner("Cập nhật thông tin..."):
                                try:
                                    observer_update = await observer.arun(response)
                                    print(observer_update.content)
                                    st.markdown(observer_update.content)
                                except Exception as e:
                                    error_message_obs = f"Lỗi cập nhật thông tin: {str(e)}"
                                    st.error(error_message_obs)
                    elif assistant_error:
                         print(f"Skipping observer due to narrator error: {assistant_error}")


            elif last_message and last_message["role"] == "assistant":
                second_last_message = st.session_state["messages"][-2] if len(st.session_state["messages"]) > 1 else None
                if second_last_message and second_last_message["role"] == "user":
                    with current_container.chat_message("user"):
                        st.markdown(second_last_message["content"])

                with current_container.chat_message("assistant"):
                    st.markdown(last_message["content"])

            elif not st.session_state["messages"]:
                 current_container.write("Chào mừng bạn đến với PokeStory! Bắt đầu cuộc phiêu lưu nào!")

        with tab2:
            messages_container_full = st.container(height=450)
            for message in st.session_state["messages"]:
                if message["role"] in ["user", "assistant"]:
                    _content = message["content"]
                    if _content is not None:
                        with messages_container_full.chat_message(message["role"]):
                            st.markdown(_content)

if __name__ == "__main__":
    asyncio.run(main())