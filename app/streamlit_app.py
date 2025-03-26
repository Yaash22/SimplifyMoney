import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd
from collections import Counter
import re
import time
import os

# Get API URL from environment variable or use default
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Chat Analysis Dashboard",
    page_icon="💬",
    layout="wide"
)

if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'pdf_chats' not in st.session_state:
    st.session_state.pdf_chats = []

st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Upload PDF", "Summarize Chats", "Search Chats", "Delete Chats", "Conversation Insights"]
)

st.sidebar.header("User Management")
with st.sidebar.form("create_user"):
    username = st.text_input("Username")
    email = st.text_input("Email")
    if st.form_submit_button("Create User"):
        try:
            if not username or not email:
                st.sidebar.error("Please enter both username and email")
            else:
                response = requests.post(
                    f"{API_URL}/users/",
                    json={"username": username, "email": email}
                )
                try:
                    response_data = response.json()
                    if response.status_code == 200:
                        st.sidebar.success("User created successfully!")
                        st.session_state.user_id = response_data['id']
                        st.sidebar.write(f"User ID: {response_data['id']}")
                    else:
                        error_detail = response_data.get('detail', 'Unknown error')
                        st.sidebar.error(f"Error creating user: {error_detail}")
                except json.JSONDecodeError:
                    st.sidebar.error(f"Server error: {response.text}")
        except requests.exceptions.ConnectionError:
            st.sidebar.error("Could not connect to the server. Make sure the FastAPI server is running.")
        except Exception as e:
            st.sidebar.error(f"Error: {str(e)}")

if st.session_state.user_id is None:
    user_id = st.sidebar.number_input("Enter User ID", min_value=1)
    st.session_state.user_id = user_id
else:
    user_id = st.session_state.user_id
    st.sidebar.write(f"Current User ID: {user_id}")

def fetch_user_chats():
    try:
        print(f"Fetching chats for user_id: {user_id}")
        response = requests.get(f"{API_URL}/users/{user_id}/pdf-chats")
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")
        
        if response.status_code == 200:
            chats = response.json()
            print(f"Retrieved {len(chats)} chats")
            st.session_state.pdf_chats = chats
            return chats
        else:
            error_msg = f"Error fetching chats: {response.text}"
            print(error_msg)
            st.error(error_msg)
            return []
    except requests.exceptions.ConnectionError:
        error_msg = "Could not connect to the server. Make sure the FastAPI server is running."
        print(error_msg)
        st.error(error_msg)
        return []
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(error_msg)
        st.error(error_msg)
        return []

if st.sidebar.button("Refresh Chats"):
    fetch_user_chats()

if page == "Upload PDF":
    st.title("📤 Upload PDF Chat")
    
    if st.session_state.user_id is None:
        st.warning("Please create a user or enter a user ID first")
    else:
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
        
        if uploaded_file is not None:
            if st.button("Upload PDF"):
                try:
                    files = {
                        "file": (uploaded_file.name, uploaded_file, "application/pdf")
                    }
                    
                    with st.spinner("Uploading PDF..."):
                        response = requests.post(
                            f"{API_URL}/pdf-chats/upload/?user_id={st.session_state.user_id}",
                            files=files
                        )
                        
                        if response.status_code == 200:
                            st.success("PDF uploaded successfully!")
                            chat_data = response.json()
                            st.write("File Details:")
                            st.json(chat_data)
                            fetch_user_chats()  
                        else:
                            error_msg = response.json().get('detail', 'Unknown error')
                            st.error(f"Error uploading PDF: {error_msg}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

elif page == "Summarize Chats":
    st.title("📝 Chat Summarization")
    
    pdf_chats = fetch_user_chats()
    
    if not pdf_chats:
        st.info("No PDF chats found.")
    else:
        chat_options = {f"{chat['filename']} (ID: {chat['id']})": chat['id'] for chat in pdf_chats}
        selected_chat = st.selectbox("Select a chat to summarize", options=list(chat_options.keys()))
        
        if selected_chat:
            chat_id = chat_options[selected_chat]
            
            chat = next(chat for chat in pdf_chats if chat['id'] == chat_id)
            st.write("Created at:", chat['created_at'])

            with st.expander("View Extracted Text"):
                st.text(chat['extracted_text'])
            
            if chat['summary']:
                st.subheader("Existing Summary")
                st.write(chat['summary'])
                
                if 'analysis' in chat:
                    analysis = chat['analysis']
                    st.subheader("Analysis")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Overall Sentiment", analysis['sentiment'])
                        st.metric("Message Count", analysis['message_count'])
                    with col2:
                        st.write("Participants:", ", ".join(analysis['participants']))
            
            if st.button("Generate New Summary"):
                try:
                    with st.spinner("Generating summary and analysis..."):
                        summary_response = requests.post(f"{API_URL}/pdf-chats/{chat_id}/summarize/")
                        if summary_response.status_code == 200:
                            st.success("Summary and analysis generated successfully!")
                            result = summary_response.json()
                            
                            st.subheader("Summary")
                            st.write(result["summary"])
                            
                            st.subheader("Analysis")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Overall Sentiment", result["sentiment"])
                                st.metric("Message Count", result["message_count"])
                            with col2:
                                st.write("Participants:", ", ".join(result["participants"]))
                            
                            fetch_user_chats() 
                            time.sleep(1) 
                            st.experimental_rerun()
                        else:
                            st.error(f"Error generating summary: {summary_response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

elif page == "Search Chats":
    st.title("🔍 Search Chats")
    search_term = st.text_input("Enter search term")
    search_type = st.radio("Search by", ["Filename", "Content", "Summary"])
    
    if st.button("Search"):
        pdf_chats = fetch_user_chats()
        
        if search_term:
            if search_type == "Filename":
                results = [chat for chat in pdf_chats if search_term.lower() in chat['filename'].lower()]
            elif search_type == "Content":
                results = [chat for chat in pdf_chats if search_term.lower() in chat['extracted_text'].lower()]
            else:  
                results = [chat for chat in pdf_chats if chat['summary'] and search_term.lower() in chat['summary'].lower()]
            
            if not results:
                st.info("No matching chats found.")
            else:
                for chat in results:
                    with st.expander(f"{chat['filename']} (ID: {chat['id']})"):
                        st.write("Created at:", chat['created_at'])
                        
                        if search_type == "Content":
                            text = chat['extracted_text']
                            matches = re.finditer(search_term, text, re.IGNORECASE)
                            highlighted_text = text
                            for match in matches:
                                start, end = match.span()
                                highlighted_text = highlighted_text[:start] + "**" + highlighted_text[start:end] + "**" + highlighted_text[end:]
                            st.markdown(highlighted_text)
                        
                        if chat['summary']:
                            st.subheader("Summary")
                            st.write(chat['summary'])
                            
                            if 'analysis' in chat:
                                analysis = chat['analysis']
                                st.subheader("Analysis")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Overall Sentiment", analysis['sentiment'])
                                    st.metric("Message Count", analysis['message_count'])
                                with col2:
                                    st.write("Participants:", ", ".join(analysis['participants']))
        else:
            st.warning("Please enter a search term")

elif page == "Delete Chats":
    st.title("🗑️ Delete Chats")
    
    pdf_chats = fetch_user_chats()
    
    if not pdf_chats:
        st.info("No PDF chats found.")
    else:
        chat_options = {f"{chat['filename']} (ID: {chat['id']})": chat['id'] for chat in pdf_chats}
        selected_chats = st.multiselect("Select chats to delete", options=list(chat_options.keys()))
        
        if selected_chats:
            if st.button("Delete Selected Chats"):
                try:
                    for chat_name in selected_chats:
                        chat_id = chat_options[chat_name]
                        delete_response = requests.delete(f"{API_URL}/pdf-chats/{chat_id}")
                        if delete_response.status_code == 200:
                            st.success(f"Successfully deleted {chat_name}")
                        else:
                            st.error(f"Error deleting {chat_name}: {delete_response.text}")
                    fetch_user_chats() 
                    time.sleep(1)  
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

elif page == "Conversation Insights":
    st.title("📊 Conversation Insights")
    
    pdf_chats = fetch_user_chats()
    
    if not pdf_chats:
        st.info("No PDF chats found.")
    else:
        chat_options = {f"{chat['filename']} (ID: {chat['id']})": chat['id'] for chat in pdf_chats}
        selected_chat = st.selectbox("Select a chat to analyze", options=list(chat_options.keys()))
        
        if selected_chat:
            chat_id = chat_options[selected_chat]
            chat = next(chat for chat in pdf_chats if chat['id'] == chat_id)
            st.subheader("Basic Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Words", len(chat['extracted_text'].split()))
            with col2:
                st.metric("Unique Words", len(set(chat['extracted_text'].lower().split())))
            with col3:
                st.metric("Average Word Length", round(sum(len(word) for word in chat['extracted_text'].split()) / len(chat['extracted_text'].split()), 2))

            st.subheader("Word Frequency Analysis")
            words = chat['extracted_text'].lower().split()
            word_freq = Counter(words)
            word_freq_df = pd.DataFrame(word_freq.most_common(10), columns=['Word', 'Frequency'])
            st.bar_chart(word_freq_df.set_index('Word'))
            if chat['summary']:
                st.subheader("Summary")
                st.write(chat['summary'])
                
                if 'analysis' in chat:
                    analysis = chat['analysis']
                    st.subheader("Conversation Analysis")

                    st.write("Overall Sentiment:", analysis['sentiment'])

                    st.write("Participants:", ", ".join(analysis['participants']))
                    st.write("Message Count:", analysis['message_count'])

                    st.subheader("Conversation Flow")
                    messages = chat['extracted_text'].split('\n')
                    participants = {}
                    for msg in messages:
                        match = re.match(r'^([A-Za-z\s]+):(.*)', msg)
                        if match:
                            speaker = match.group(1).strip()
                            if speaker not in participants:
                                participants[speaker] = []
                            participants[speaker].append(match.group(2).strip())

                    participant_counts = {k: len(v) for k, v in participants.items()}
                    participant_df = pd.DataFrame(list(participant_counts.items()), columns=['Participant', 'Message Count'])
                    st.bar_chart(participant_df.set_index('Participant'))

                    st.subheader("Conversation Timeline")
                    for speaker, messages in participants.items():
                        with st.expander(f"{speaker} ({len(messages)} messages)"):
                            for msg in messages:
                                st.write(f"- {msg}")