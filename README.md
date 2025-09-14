## INTRODUCTION
An intelligent AI-powered helpdesk system that automates ticket classification and generates contextual responses using RAG (Retrieval-Augmented Generation) technology.
This project implements a comprehensive customer support automation pipeline that can:

Classify support tickets by topic, sentiment, and priority
Generate intelligent responses using knowledge from Atlan's documentation
Route complex issues to appropriate teams
Provide real-time analysis of customer queries

## ARCHITECTURE
![Untitled](https://github.com/user-attachments/assets/e4bf654c-1ac7-4c5f-a993-b69c47f656e4)

## MODULES
  1. Dashboard - Main Streamlit App
  2. Retriever - Runs the Embedding of queries, Retrieval, and Generation.
  3. Services  - Contains the functions for chunking and indexing the vector database
## PROJECT STRUCTURE
```text
customer-support/
├── README.md
├── requirements.txt
├── .gitignore
├── dashboard_app.py       # Main Streamlit application entry point
├── data/
│   ├── raw
│   ├── processed
│   └── chunks
├── scripts/
│   ├── scrape_docs.py         # Scraper for docs.atlan.com
│   └── preprocess_html_to_json.py
├── backend/
│   ├── services/
│   │   ├── chunk.py
│   │   └── indexing.py
├── index                     # FAISS Index
└── retriever.py
```

##  TECHNICAL DESCRIPTION
1. Chunk Size - 1000 with an overlap of 200 for better context, which will help in fuller and complete answers.
2. Embedding model - all-MiniLM-L6-v2, an open-source Hugging Face model that is lightweight.
3. Classification - Rule-based logic derived from sample tickets and only falling on LLM for ambiguous calls
4. LLM for generation - GPT 2, used locally via Hugging Face. (Future considerations: An LLM with larger parameters like Gemini or GPT-5)
5. Vector Datastore - FAISS, for speed and minimal setup.
6. Database - Tickets and responses are stored in an Aiven PostgreSQL database
7. Deployment - Using Streamlit Community Cloud

### DEPLOYED LINK: https://atlan-customer-support.streamlit.app/

## SETUP
1. 📥 Clone and Navigate to Project
2.  🐍 Create Python Virtual Environment
3.  📦 Install Python Dependencies using requirements.txt
4.  ⚙️ Setup Environment Configuration with database credentials
5.  🕷️ Initialize Knowledge Base (Load Vectordata Store)
6.  🚀 Launch the Application by running the dashboard_app.py file

## SCREENSHOTS - LOCAL DEPLOYMENT
<img width="1917" height="865" alt="Screenshot 2025-09-14 204954" src="https://github.com/user-attachments/assets/1cca8621-0800-4543-ae0d-1dcb6a025104" />

