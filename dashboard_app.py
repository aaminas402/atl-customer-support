import streamlit as st
import psycopg2
from datetime import datetime
from retriever import retrieve_and_summarize

import re

# ---------------------------
# Ticket classification logic
# ---------------------------
def classify_ticket(body, subject=""):
    text = (subject + " " + body).lower()

    if re.search(r"\bhow to\b|\bsteps\b|\bguide\b|\bconfigure\b|\bsetup\b|\bwalkthrough\b", text):
        topic = "How-to"
    elif any(word in text for word in ["snowflake", "redshift", "bigquery", "fivetran", "tableau", "airflow", "connector", "integration"]):
        topic = "Connector"
    elif "lineage" in text or any(word in text for word in ["upstream", "downstream", "impact analysis", "data flow"]):
        topic = "Lineage"
    elif "api" in text or "sdk" in text or "endpoint" in text or "webhook" in text:
        topic = "API/SDK"
    elif "sso" in text or "single sign on" in text or "saml" in text or "okta" in text or "azure ad" in text or "login" in text or "auth" in text:
        topic = "SSO"
    elif "glossary" in text or "term" in text or "definition" in text:
        topic = "Glossary"
    elif "best practice" in text or "recommendation" in text or "guideline" in text or "workflow" in text or "scale" in text or "catalog hygiene" in text:
        topic = "Best practices"
    elif any(word in text for word in ["pii", "hipaa", "gdpr", "sensitive", "masking", "dlp", "secrets manager"]):
        topic = "Sensitive data"
    elif any(word in text for word in ["error", "fail", "issue", "bug", "not working", "problem", "crash", "role", "permission"]):
        topic = "Product"
    else:
        topic = "Product"

    if any(word in text for word in ["urgent", "asap", "blocked", "angry", "infuriating", "critical", "frustrated"]):
        sentiment = "Frustrated"
    elif any(word in text for word in ["please", "could you", "wondering", "interested"]):
        sentiment = "Curious"
    else:
        sentiment = "Neutral"

    if any(word in text for word in ["urgent", "asap", "blocked", "critical", "infuriating"]):
        priority = "P0"
    elif any(word in text for word in ["error", "fail", "not working", "problem", "issue"]):
        priority = "P1"
    else:
        priority = "P2"

    return topic, sentiment, priority

# ---------------------------
# Database Connection
# ---------------------------
def get_connection():
    return psycopg2.connect(
        host=st.secrets["aiven"]["host"],
        dbname=st.secrets["aiven"]["dbname"],
        user=st.secrets["aiven"]["user"],
        password=st.secrets["aiven"]["password"],
        port=st.secrets["aiven"]["port"],
        sslmode='require'
    )

# ---------------------------
# Streamlit App
# ---------------------------
st.set_page_config(page_title="Support Dashboard", page_icon="📊", layout="wide")
st.title("📊 Support Dashboard")

# Sidebar navigation
page = st.sidebar.radio("Navigation", ["Submit Ticket", "Dashboard"])

# ---------------------------
# Submit Ticket Page
# ---------------------------
if page == "Submit Ticket":
    from datetime import datetime
    with st.form("ticket_form"):
        subject = st.text_input("Subject *", placeholder="Brief description of your issue")
        body = st.text_area("Body *", placeholder="Describe your issue in detail...", height=200)
        submitted = st.form_submit_button("Submit Ticket")
        if submitted:
            if not subject or not body:
                st.error("Please fill in both subject and body.")
            else:
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO tickets (subject, body, created_at)
                        VALUES (%s, %s, %s) RETURNING id;
                    """, (subject, body, datetime.now()))
                    ticket_id = cur.fetchone()[0]
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Ticket submitted successfully! Ticket ID: #{ticket_id}")
                except Exception as e:
                    st.error(f"Error submitting ticket: {e}")

# ---------------------------
# Dashboard Page
# ---------------------------
elif page == "Dashboard":
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, subject, body FROM tickets ORDER BY created_at DESC;")
        tickets = cur.fetchall()
        conn.close()
    except Exception as e:
        st.error(f"Error fetching tickets: {e}")
        tickets = []

    if not tickets:
        st.info("No tickets found.")
    else:
        for ticket in tickets:
            ticket_id, subject, body = ticket
            with st.expander(f"#{ticket_id}: {subject}"):
                # Internal analysis
                topic, sentiment, priority = classify_ticket(body, subject)
                st.markdown("**Internal Analysis**")
                st.write(f"**Topic:** {topic}")
                st.write(f"**Sentiment:** {sentiment}")
                st.write(f"**Priority:** {priority}")

                # Fetch or generate final response
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("SELECT answer, citations FROM responses WHERE ticket_id=%s;", (ticket_id,))
                    row = cur.fetchone()
                    if row:
                        answer, citations = row
                    else:
                        if topic in {"How-to", "Product", "Best practices", "API/SDK", "SSO"}:
                            with st.spinner("Generating AI response..."):
                                answer, citations = retrieve_and_summarize(body)
                            cur.execute("""
                                INSERT INTO responses (ticket_id, topic, sentiment, priority, answer, citations, created_at)
                                VALUES (%s, %s, %s, %s, %s, %s, NOW());
                            """, (ticket_id, topic, sentiment, priority, answer, citations))
                            conn.commit()
                        else:
                            answer = f"This ticket has been classified as a '{topic}' issue and routed to the appropriate team."
                            citations = []
                            cur.execute("""
                                INSERT INTO responses (ticket_id, topic, sentiment, priority, answer, citations, created_at)
                                VALUES (%s, %s, %s, %s, %s, %s, NOW());
                            """, (ticket_id, topic, sentiment, priority, answer, citations))
                            conn.commit()
                    conn.close()
                except Exception as e:
                    st.error(f"Error generating or fetching response: {e}")
                    answer = "Error generating response."
                    citations = []

                # Display final response
                st.markdown("**Final Response**")
                st.write(answer)
                if citations:
                    st.markdown("**Citations:**")
                    for url in citations:
                        st.write(f"- {url}")
