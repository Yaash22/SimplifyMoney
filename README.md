# SimplifyMoney - PDF Chat Analysis Application

A powerful application that allows users to upload PDF documents containing chat conversations, analyze them, and generate meaningful summaries with sentiment analysis.

## Features

- 📤 PDF Upload: Upload chat conversations in PDF format
- 📝 Automatic Summarization: Generate concise summaries of chat conversations
- 🎯 Sentiment Analysis: Analyze the overall sentiment of conversations
- 👥 Participant Analysis: Identify and track conversation participants
- 📊 Conversation Insights: View detailed statistics and analysis of chat patterns
- 🔍 Search Functionality: Search through uploaded chats by filename, content, or summary
- 🗑️ Chat Management: Delete unwanted chat documents

## Tech Stack

- **Frontend**: Streamlit
- **Backend**: FastAPI
- **Database**: SQLite with SQLAlchemy ORM
- **AI/ML**: 
  - Transformers (Hugging Face)
  - PyTorch
  - BART (for summarization)
  - DistilBERT (for sentiment analysis)

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/SimplifyMoney.git
cd SimplifyMoney
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install specific versions of PyTorch and Transformers:
```bash
pip install torch==2.0.1
pip install transformers==4.30.2
pip install sentencepiece
pip install protobuf
```

## Project Structure

```
SimplifyMoney/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── models.py         # Database models
│   ├── schemas.py        # Pydantic schemas
│   ├── database.py       # Database configuration
│   ├── summarizer.py     # Text summarization logic
│   └── streamlit_app.py  # Streamlit frontend
├── requirements.txt
└── README.md
```

## Running the Application

1. Start the FastAPI backend server:
```bash
uvicorn app.main:app --reload
```

2. In a new terminal, start the Streamlit frontend:
```bash
streamlit run app/streamlit_app.py
```

3. Open your web browser and navigate to:
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000

## Usage Guide

1. **User Management**:
   - Create a new user using the sidebar form
   - Enter your username and email
   - Note down your User ID

2. **Uploading PDFs**:
   - Navigate to the "Upload PDF" page
   - Select a PDF file containing chat conversations
   - Click "Upload PDF"
   - Wait for the upload confirmation

3. **Generating Summaries**:
   - Go to the "Summarize Chats" page
   - Select your uploaded PDF from the dropdown
   - Click "Generate New Summary"
   - View the generated summary and analysis

4. **Searching Chats**:
   - Visit the "Search Chats" page
   - Enter your search term
   - Choose search type (Filename, Content, or Summary)
   - Click "Search"

5. **Managing Chats**:
   - Go to the "Delete Chats" page
   - Select chats to delete
   - Click "Delete Selected Chats"

6. **Viewing Insights**:
   - Navigate to "Conversation Insights"
   - Select a chat to analyze
   - View detailed statistics and visualizations

## API Endpoints

- `POST /users/`: Create a new user
- `GET /users/{user_id}/pdf-chats`: Get user's PDF chats
- `POST /pdf-chats/upload/`: Upload a new PDF chat
- `POST /pdf-chats/{chat_id}/summarize/`: Generate summary for a chat
- `GET /pdf-chats/{chat_id}`: Get specific chat details
- `DELETE /pdf-chats/{chat_id}`: Delete a chat

## Database Schema

### Users Table
- id (Primary Key)
- username
- email

### PDF Chats Table
- id (Primary Key)
- user_id (Foreign Key)
- filename
- pdf_content
- created_at
- summary
- extracted_text
- analysis

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Hugging Face Transformers library
- FastAPI framework
- Streamlit
- SQLAlchemy 