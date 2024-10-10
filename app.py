import streamlit as st
import requests

# Initialize session state
if 'conversation_id' not in st.session_state:
    st.session_state['conversation_id'] = None  # No conversation selected yet

if 'conversations' not in st.session_state:
    st.session_state['conversations'] = []  # List of conversations

if 'messages' not in st.session_state:
    st.session_state['messages'] = []

if 'messages_loaded' not in st.session_state:
    st.session_state['messages_loaded'] = False

def load_conversations():
    try:
        response = requests.get("http://localhost:8000/conversations")
        response.raise_for_status()
        conversations = response.json()
        st.session_state['conversations'] = conversations
    except requests.exceptions.RequestException as e:
        st.error(f"Error loading conversations: {e}")

load_conversations()

with st.sidebar:
    st.title("Conversations")
    if st.button("New Conversation"):
        # Create a new conversation
        try:
            response = requests.post("http://localhost:8000/conversations", json={})
            response.raise_for_status()
            data = response.json()
            st.session_state['conversation_id'] = data['conversation_id']
            st.session_state['messages'] = []
            st.session_state['messages_loaded'] = True  # No messages to load
            # Reload conversations
            load_conversations()
        except requests.exceptions.RequestException as e:
            st.error(f"Error creating conversation: {e}")
    st.write("")

    # List of conversations
    conversation_names = []
    conversation_ids = []
    for conv in st.session_state['conversations']:
        name = conv['name'] or f"Conversation {conv['conversation_id']}"
        conversation_names.append(name)
        conversation_ids.append(conv['conversation_id'])

    if conversation_names:
        selected_index = 0
        if st.session_state['conversation_id'] in conversation_ids:
            selected_index = conversation_ids.index(st.session_state['conversation_id'])

        selected_conversation = st.selectbox(
            "Select a conversation",
            options=conversation_names,
            index=selected_index,
            key='conversation_select'
        )
        # Update the conversation_id based on selection
        selected_conv_id = conversation_ids[conversation_names.index(selected_conversation)]
        if st.session_state['conversation_id'] != selected_conv_id:
            st.session_state['conversation_id'] = selected_conv_id
            st.session_state['messages_loaded'] = False
            st.session_state['messages'] = []

st.title("RAG Chatbot")

# If a conversation is selected, load its messages
if st.session_state['conversation_id'] is not None and not st.session_state['messages_loaded']:
    try:
        response = requests.get(f"http://localhost:8000/conversations/{st.session_state['conversation_id']}/messages")
        response.raise_for_status()
        messages = response.json()
        st.session_state['messages'] = messages
        st.session_state['messages_loaded'] = True
    except requests.exceptions.RequestException as e:
        st.error(f"Error loading messages: {e}")

# Display chat messages from history on app rerun
for message in st.session_state['messages']:
    with st.chat_message(message['role']):
        st.write(message['content'])

if st.session_state['conversation_id'] is not None:
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to history
        st.session_state['messages'].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # Prepare payload
        payload = {
            "question": prompt,
            "conversation_id": st.session_state['conversation_id']
        }

        # Send request to backend
        try:
            response = requests.post("http://localhost:8000/generate", json=payload)
            response.raise_for_status()
            answer = response.json().get('answer', '')

            # Add assistant message to history
            st.session_state['messages'].append({"role": "assistant", "content": answer})
            with st.chat_message("assistant"):
                st.write(answer)
        except requests.exceptions.RequestException as e:
            st.error(f"Error: {e}")
else:
    st.info("Please select or create a conversation to start chatting.")
