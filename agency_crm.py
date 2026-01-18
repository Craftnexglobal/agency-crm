import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime, date
import hashlib
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Agency CRM Pro", page_icon="🇮🇳", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
        .block-container {padding-top: 1rem;}
        h1 {color: #2E4053;}
        .stMetric {background-color: #F4F6F7; padding: 10px; border-radius: 5px;}
    </style>
""", unsafe_allow_html=True)

# --- DATABASE SETUP ---
def get_connection():
    return sqlite3.connect('agency_crm_v3.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Leads Table with Follow-up Date
    c.execute('''CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        company_name TEXT, contact_person TEXT, mobile TEXT, alt_mobile TEXT,
        email TEXT, gst_no TEXT, address TEXT, service_interest TEXT, 
        projected_value REAL, status TEXT, 
        next_followup TEXT,
        date_added TEXT, assigned_to TEXT, remarks TEXT
    )''')
    # Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    
    # Default Admin
    hashed_pw = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?,?,?)", 
              ('admin', hashed_pw, 'Admin'))
    conn.commit()
    conn.close()

# --- AUTH FUNCTIONS ---
def login_user(username, password):
    conn = get_connection()
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username, hashed_pw))
    data = c.fetchone()
    conn.close()
    return data[0] if data else None

def add_user(username, password, role):
    conn = get_connection()
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?,?,?)", (username, hashed_pw, role))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

# --- MAIN APP ---
init_db()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- LOGIN PAGE ---
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if os.path.exists("logo.png"):
            st.image("logo.png", width=150)
        st.title("🇮🇳 Agency CRM Login")
        
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            role = login_user(username, password)
            if role:
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['role'] = role
                st.rerun()
            else:
                st.error("Invalid Credentials")

# --- MAIN DASHBOARD ---
# --- MAIN DASHBOARD ---
else:
    # 1. FIXED TOP BAR LAYOUT
    # [1.5, 5, 2] gives specific space for Logo, Title, and User Info
    col_logo, col_title, col_user = st.columns([1.5, 5, 2])
    
    with col_logo:
        if os.path.exists("logo.png"):
            st.image("logo.png", width=100)
        else:
            st.write("🏢 **CRM**")

    with col_title:
        # Using a single line for the Title to prevent wrapping
        st.markdown(f"<h2 style='margin-bottom:0;'>Agency Sales Manager</h2>", unsafe_allow_html=True)
        st.caption("Sales & Lead Management System")

    with col_user:
        # We wrap the User Info and Logout button in a clean container
        # 'use_container_width' ensures the button fits perfectly
        st.markdown(f"**👤 {st.session_state['username']}** ({st.session_state['role']})")
        if st.button("🚪 Logout", use_container_width=True, key="logout_fixed"):
            st.session_state['logged_in'] = False
            st.rerun()

    st.divider() # Adds a clean separation line

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Dashboard", "🌪️ Pipeline", "➕ New Lead", "🗂️ Lead Directory", "📥 Bulk Upload", "⚙️ Admin"
    ])

    # 1. DASHBOARD (Enhanced)
    with tab1:
        df = pd.read_sql_query("SELECT * FROM leads", get_connection())
        
        # Section A: Today's Reminders (The "Useful" Part)
        st.subheader("⚠️ Tasks for Today")
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        if not df.empty:
            # Filter for leads where follow-up is today or past due, AND status is not Closed
            reminders = df[
                (df['next_followup'] <= today_str) & 
                (~df['status'].isin(['Won', 'Lost']))
            ]
            
            if not reminders.empty:
                st.warning(f"You have {len(reminders)} pending follow-ups!")
                st.dataframe(reminders[['company_name', 'contact_person', 'mobile', 'next_followup', 'status']], hide_index=True)
            else:
                st.success("🎉 No pending calls for today. Great job!")

            st.divider()

            # Section B: Financials & Target
            total = df['projected_value'].sum()
            won = df[df['status'] == 'Won']['projected_value'].sum()
            target = 1000000 # Example Monthly Target: 10 Lakhs
            progress = min(won / target, 1.0)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Pipeline Value", f"₹{total:,.0f}")
            c2.metric("Revenue Won", f"₹{won:,.0f}")
            c3.metric("Win Rate", f"{(len(df[df['status']=='Won'])/len(df)*100):.1f}%")
            
            st.caption(f"🎯 Monthly Target Progress (Goal: ₹{target:,.0f})")
            st.progress(progress)
            
            # Charts
            g1, g2 = st.columns(2)
            with g1: st.plotly_chart(px.pie(df, names='service_interest', title="Services", hole=0.4), use_container_width=True)
            with g2: st.plotly_chart(px.bar(df, x='status', color='status', title="Lead Stages"), use_container_width=True)
        else:
            st.info("Add leads to see analytics.")

    # 2. PIPELINE (Kanban)
    with tab2:
        st.header("Deal Pipeline")
        df = pd.read_sql_query("SELECT * FROM leads", get_connection())
        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("❄️ New / Contacted")
            for _, r in df[df['status'].isin(['New', 'Contacted'])].iterrows():
                st.info(f"**{r['company_name']}**\n\n₹{r['projected_value']:,.0f} | {r['contact_person']}")
        with c2:
            st.subheader("🔥 In Negotiation")
            for _, r in df[df['status'].isin(['Proposal', 'Negotiation'])].iterrows():
                st.warning(f"**{r['company_name']}**\n\n₹{r['projected_value']:,.0f} | {r['service_interest']}")
        with c3:
            st.subheader("✅ Won Deals")
            for _, r in df[df['status'] == 'Won'].iterrows():
                st.success(f"**{r['company_name']}**\n\n₹{r['projected_value']:,.0f}")

    # 3. NEW LEAD (With Follow-up Date)
    with tab3:
        st.header("📝 Register New Lead")
        with st.form("add_lead"):
            c1, c2, c3 = st.columns(3)
            with c1:
                comp = st.text_input("Company Name*")
                cont = st.text_input("Contact Person")
                gst = st.text_input("GST No.")
            with c2:
                mob = st.text_input("Mobile* (10 digits)")
                alt = st.text_input("Alt Mobile")
                email = st.text_input("Email")
            with c3:
                serv = st.selectbox("Service", ["SEO", "PPC", "Social Media", "Web Dev", "App Dev"])
                val = st.number_input("Value (₹)", step=5000)
                stat = st.selectbox("Status", ["New", "Contacted", "Proposal", "Negotiation", "Won", "Lost"])
            
            c4, c5 = st.columns(2)
            with c4: 
                f_date = st.date_input("Next Follow-Up Date", min_value=date.today())
            with c5:
                addr = st.text_area("Address")
            
            rem = st.text_area("Remarks")
            
            if st.form_submit_button("Save Lead"):
                if comp and mob:
                    conn = get_connection()
                    conn.execute("""INSERT INTO leads 
                        (company_name, contact_person, mobile, alt_mobile, email, gst_no, address, service_interest, projected_value, status, next_followup, date_added, assigned_to, remarks) 
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (comp, cont, mob, alt, email, gst, addr, serv, val, stat, f_date, datetime.now().strftime("%Y-%m-%d"), st.session_state['username'], rem))
                    conn.commit()
                    st.success("Lead Added!")
                else:
                    st.error("Company Name and Mobile are required!")

    # 4. VIEW LEADS (User Friendly WhatsApp Link)
    with tab4:
        st.header("🗂️ Lead Directory")
        
        # Filters
        col_f1, col_f2 = st.columns(2)
        with col_f1: filter_status = st.multiselect("Filter by Status", ["New", "Contacted", "Proposal", "Negotiation", "Won", "Lost"])
        with col_f2: search_q = st.text_input("🔍 Search Company or Name")
        
        df = pd.read_sql_query("SELECT * FROM leads", get_connection())
        
        # Apply Filters
        if filter_status: df = df[df['status'].isin(filter_status)]
        if search_q: df = df[df['company_name'].str.contains(search_q, case=False) | df['contact_person'].str.contains(search_q, case=False)]
        
        # Create WhatsApp Link Column
        # Assumes indian numbers. Adds 91 if missing, removes spaces.
        df['whatsapp_link'] = "https://wa.me/91" + df['mobile'].astype(str).str.replace(" ", "").str[-10:]
        
        # Display with Clickable Links and Editing
        edited_df = st.data_editor(
            df,
            column_config={
                "whatsapp_link": st.column_config.LinkColumn(
                    "WhatsApp", display_text="Chat 💬"
                ),
                "status": st.column_config.SelectboxColumn(
                    "Status", options=["New", "Contacted", "Proposal", "Negotiation", "Won", "Lost"]
                ),
                "next_followup": st.column_config.DateColumn("Next Call Date")
            },
            hide_index=True,
            column_order=("company_name", "contact_person", "mobile", "whatsapp_link", "service_interest", "status", "next_followup", "remarks"),
            use_container_width=True
        )
        
        if st.button("💾 Save Database Changes"):
            conn = get_connection()
            # Drop the link column before saving back to DB
            save_df = edited_df.drop(columns=['whatsapp_link'])
            save_df.to_sql('leads', conn, if_exists='replace', index=False)
            st.success("Updated Successfully!")

    # 5. BULK UPLOAD
    with tab5:
        st.header("📥 Bulk Import")
        csv = pd.DataFrame(columns=["company_name", "contact_person", "mobile", "service_interest", "projected_value", "status"]).to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download Template", csv, "template.csv", "text/csv")
        upl = st.file_uploader("Upload CSV", type="csv")
        if upl and st.button("Import Data"):
            try:
                d = pd.read_csv(upl)
                d['date_added'] = datetime.now().strftime("%Y-%m-%d")
                d['assigned_to'] = st.session_state['username']
                d['next_followup'] = datetime.now().strftime("%Y-%m-%d") # Default to today
                conn = get_connection()
                d.to_sql('leads', conn, if_exists='append', index=False)
                st.success("Import Successful!")
            except Exception as e:
                st.error(f"Error: {e}")

    # 6. ADMIN
    with tab6:
        if st.session_state['role'] == "Admin":
            st.header("⚙️ User Management")
            with st.form("new_user"):
                u = st.text_input("New Username")
                p = st.text_input("New Password", type="password")
                r = st.selectbox("Role", ["Staff", "Admin"])
                if st.form_submit_button("Create User"):
                    if add_user(u, p, r): st.success("User Created")
                    else: st.error("User exists")
            st.dataframe(pd.read_sql_query("SELECT username, role FROM users", get_connection()), use_container_width=True)
        else:
            st.warning("Admin Only")