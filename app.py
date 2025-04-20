import streamlit as st
from dotenv import load_dotenv
from typing import Any, Dict, List, Optional
import asyncio
import nest_asyncio
import pokebase as pb
from agents import get_narrator, get_observer
from utils import CUSTOM_CSS, create_pokemon_name_dict, translate_pokemon_name, get_pokemon_info_with_sprites
from PIL import Image
import requests
from io import BytesIO


nest_asyncio.apply() # Allows nesting of event loops

load_dotenv()

### Setup streamlit UI
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
###

### Create 2 Pokemon name dicts with English as key and Japanese as key
eng_to_jap = create_pokemon_name_dict(2,3)
jap_to_eng = create_pokemon_name_dict(3,2)
###

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

    # Initialize session state for storing Pokemon names
    if 'pokemon_names_str' not in st.session_state:
        st.session_state.pokemon_names_str = ""
    if 'translated_names' not in st.session_state:
        st.session_state.translated_names = []

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
                                    if(observer_update.content == "Nope"):
                                        # If observer returns "Nope", clear or show no info
                                        st.session_state.pokemon_names_str = ""
                                        st.session_state.translated_names = []
                                    elif st.session_state.pokemon_names_str != observer_update.content:
                                        # Update if the list of names has changed
                                        st.session_state.pokemon_names_str = observer_update.content
                                        pokemon_names = observer_update.content.strip('\n').split(',')
                                        st.session_state.translated_names = [] # Clear previous translated names
                                        for name in pokemon_names:
                                            clean_name = name.replace(" ", "")
                                            translated_name = translate_pokemon_name(eng_to_jap, clean_name)
                                            st.session_state.translated_names.append(translated_name)

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
    with col2:
        if st.session_state.translated_names:
            num_cols = 3
            for i, jap_name in enumerate(st.session_state.translated_names):
                # Check if it's the start of a new row (index 0, 3, 6, ...)
                if i % num_cols == 0:
                    # Create a new set of columns for this row
                    cols = st.columns(num_cols)
                col_index = i % num_cols
                try:
                    eng_name = translate_pokemon_name(jap_to_eng, jap_name)
                    pokemon = get_pokemon_info_with_sprites(eng_name)
                    img_link = pokemon['sprites']['other']['official-artwork']['front_default']
                    cols[col_index].image(image=img_link, caption=eng_to_jap[eng_name],width=65)
                except Exception as e:
                    with cols[col_index]:
                        st.error(f"Lỗi fetch API: {jap_name}: {e}")

if __name__ == "__main__":
    asyncio.run(main())