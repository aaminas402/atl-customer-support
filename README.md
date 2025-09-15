## Introduction
An intelligent AI-powered helpdesk system that automates ticket classification and generates contextual responses using RAG (Retrieval-Augmented Generation) technology.
This project implements a comprehensive customer support automation pipeline that can:

* Classify support tickets by topic, sentiment, and priority
* Generate intelligent responses using knowledge from Atlan's documentation
* Route complex issues to appropriate teams
* Provide real-time analysis of customer queries

## Architecture
![Untitled](https://github.com/user-attachments/assets/e4bf654c-1ac7-4c5f-a993-b69c47f656e4)

## System Architecture overview

* **Data Ingestion**: Source documents are scraped from the target website using *BeautifulSoup*, with a controlled crawl depth limit of 2. This ensures broad yet focused coverage of relevant content without introducing excessive noise.

* **Document Processing**: The collected text is segmented into chunks of 1,000 tokens with a 200-token overlap. This strategy preserves contextual continuity across boundaries, resulting in fuller and more coherent responses.

* **Embedding Layer**: We utilize the *all-MiniLM-L6-v2* embedding model from Hugging Face, chosen for its balance of semantic accuracy and lightweight performance, making it ideal for real-time retrieval.

* **Classification Module**: A hybrid approach is applied—rule-based logic, derived from historical support tickets, handles the majority of classification, while ambiguous cases are escalated to the LLM for nuanced interpretation.

* **Generative Model**: A locally hosted GPT-2 model (via Hugging Face) powers response generation. While GPT-2 provides a lightweight baseline, the system is architected to scale seamlessly to more powerful models (e.g., Gemini, GPT-5) as future requirements evolve. Locally hosted GPT-2 was selected to eliminate external dependencies and ensure offline operation.

* **Vector Store**: *FAISS* serves as the vector datastore, enabling efficient and low-latency similarity search.

* **Data Persistence**: Tickets and responses are stored in a managed PostgreSQL database on *Aiven*, ensuring durability and reliability.

* **Deployment**: The application is deployed on *Streamlit Community Cloud*, enabling rapid iteration, lightweight hosting, and an interactive user interface.

## Modules

* **Dashboard (UI Layer)**

Built with Streamlit, this serves as the primary user interface.Provides ticket submission, response visualization, and interactive monitoring of the pipeline.

* **Retriever (Core RAG Engine)**

Handles query embedding, similarity-based retrieval, and final response generation.Integrates the embedding model (all-MiniLM-L6-v2), FAISS vector search, and the generative LLM.

* **Services (Utility & Indexing Layer)**

Implements document preprocessing, including chunking (1,000 tokens with 200 overlap) and vector indexing.Provides auxiliary functions to manage updates to the knowledge base and streamline ingestion workflows.

## Database Schema

**`tickets` table**

| Column           | Type                        | Description                                               |
|------------------|----------------------------|-----------------------------------------------------------|
| `id`             | integer (PK)               | Unique ticket identifier                                  |
| `created_at`     | timestamp without time zone | Time the ticket was created                               |
| `subject`        | text                        | Ticket subject or title                                   |
| `body`           | text                        | Full content of the ticket                                |
| `customer_email` | text                        | Email of the customer who submitted the ticket           |

**`responses` table**

| Column       | Type                        | Description                           |
|--------------|----------------------------|---------------------------------------|
| `id`         | integer (PK)               | Unique response identifier            |
| `created_at` | timestamp without time zone | Time the response was generated       |
| `ticket_id`  | integer (FK)               | References `tickets.id`               |
| `body`       | text                        | Generated response content            |

**Relationship:**  
- One `ticket` → Many `responses` (supports multiple system-generated answers per ticket)

## Project Structure
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

#### Deployment: https://atlan-customer-support.streamlit.app/

## Setup Instructions

*  Clone Repository
```
git clone <repo-url>
cd <project-directory>
```

* Create Virtual Environment
```
python -m venv venv
source venv/bin/activate   # On Linux/Mac  
venv\Scripts\activate      # On Windows  
```

* Install Dependencies
```
pip install -r requirements.txt
```

* Configure Environment

Add database credentials and other secrets in the environment configuration (.env or secrets.toml if deploying on Streamlit Cloud).

* Initialize Knowledge Base

Run preprocessing scripts to scrape, chunk, and index documents. Ensure the FAISS vector datastore is populated.

* Launch Application
```
streamlit run dashboard_app.py
```
## Screenshots
<img width="1917" height="865" alt="Screenshot 2025-09-14 204954" src="https://github.com/user-attachments/assets/1cca8621-0800-4543-ae0d-1dcb6a025104" />
<img width="1918" height="839" alt="image" src="https://github.com/user-attachments/assets/4c3b95f7-8452-439e-b054-0064275bfb75" />


