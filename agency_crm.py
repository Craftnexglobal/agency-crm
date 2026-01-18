import streamlit as st
from supabase import create_client, Client
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import hashlib
import os

# --- CLOUD DATABASE CONNECTION ---
url: str = "https://hkifcumhbgfqszcgvrrw.supabase.co"
key: str = "sb_publishable_-n7XYPCit-RvNs4lhE6IAQ_cQElRuHI"
supabase: Client = create_client(url, key)

# --- DATABASE HELPER FUNCTIONS ---
def fetch_leads():
    """Fetches all leads from the Supabase 'leads' table"""
    try:
        response = supabase.table("leads").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error fetching leads: {e}")
        return pd.DataFrame()

def save_lead(data_dict):
    """Saves a new lead dictionary to Supabase"""
    try:
        supabase.table("leads").insert(data_dict).execute()
        return True
    except Exception as e:
        st.error(f"Error saving lead: {e}")
        return False

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Agency CRM Pro", 
    page_icon="🚀", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- MODERN ANIMATED CSS ---
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main Container */
    .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
    }
    
    /* Smooth Page Transitions */
    .main {
        animation: fadeIn 0.5s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Title Styling */
    h1, h2, h3 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        animation: slideIn 0.6s ease-out;
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    /* Card Styling with Hover Effect */
    .stMetric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.2);
        transition: all 0.3s ease;
        animation: scaleIn 0.5s ease-out;
    }
    
    .stMetric:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 48px rgba(102, 126, 234, 0.3);
    }
    
    @keyframes scaleIn {
        from { opacity: 0; transform: scale(0.9); }
        to { opacity: 1; transform: scale(1); }
    }
    
    .stMetric label {
        color: rgba(255, 255, 255, 0.9) !important;
        font-weight: 600;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stMetric [data-testid="stMetricValue"] {
        color: white !important;
        font-size: 2rem;
        font-weight: 700;
    }
    
    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.6rem 2rem;
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    
    /* Form Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select,
    .stNumberInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        padding: 0.8rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 10px;
        padding: 0.8rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        border: none;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        transform: scale(1.05);
    }
    
    /* Data Editor Styling */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    }
    
    /* Alert Boxes */
    .stAlert {
        border-radius: 12px;
        border-left: 4px solid #667eea;
        animation: slideIn 0.4s ease-out;
    }
    
    /* Warning Box Enhancement */
    [data-testid="stNotification"] {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        border-radius: 12px;
        padding: 1rem;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.02); }
    }
    
    /* Success Box */
    .element-container:has(.stSuccess) {
        animation: bounceIn 0.6s ease-out;
    }
    
    @keyframes bounceIn {
        0% { transform: scale(0.3); opacity: 0; }
        50% { transform: scale(1.05); }
        70% { transform: scale(0.9); }
        100% { transform: scale(1); opacity: 1; }
    }
    
    /* Progress Bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    /* Divider */
    hr {
        margin: 2rem 0;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
    }
    
    /* Logo/Header Area */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        animation: slideDown 0.6s ease-out;
    }
    
    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Info Cards for Pipeline */
    .pipeline-card {
        background: white;
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        border-left: 4px solid #667eea;
        animation: fadeInUp 0.5s ease-out;
    }
    
    .pipeline-card:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }
    
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
""", unsafe_allow_html=True)

# --- DATABASE SETUP ---
def get_connection():
    return sqlite3.connect('agency_crm_v3.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT,
        contact_person TEXT,
        mobile TEXT,
        alt_mobile TEXT,
        email TEXT,
        gst_no TEXT,
        address TEXT,
        service_interest TEXT,
        projected_value REAL,
        status TEXT,
        next_followup TEXT,
        date_added TEXT,
        assigned_to TEXT,
        remarks TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT)''')
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
        c.execute("INSERT INTO users (username, password, role) VALUES (?,?,?)", 
                  (username, hashed_pw, role))
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
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div style='text-align: center; padding: 2rem 0;'>", unsafe_allow_html=True)
        st.markdown("# 🚀 Agency CRM Pro")
        st.markdown("### Welcome Back!")
        st.markdown("</div>", unsafe_allow_html=True)
        
        with st.container():
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            
            if st.button("🚀 Login", use_container_width=True):
                role = login_user(username, password)
                if role:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.session_state['role'] = role
                    st.success("Login Successful! 🎉")
                    st.rerun()
                else:
                    st.error("❌ Invalid Credentials")

# --- MAIN DASHBOARD ---
else:
    # HEADER SECTION
    st.markdown("""
    <div class='header-container'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <div>
                <h1 style='color: white; margin: 0; -webkit-text-fill-color: white;'>🚀 Agency Sales Manager</h1>
                <p style='color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;'>Manage your leads and close more deals</p>
            </div>
            <div style='text-align: right;'>
                <p style='color: white; margin: 0; font-weight: 600;'>👤 {}</p>
                <p style='color: rgba(255,255,255,0.8); margin: 0; font-size: 0.9rem;'>{}</p>
            </div>
        </div>
    </div>
    """.format(st.session_state['username'], st.session_state['role']), unsafe_allow_html=True)
    
    if st.button("🚪 Logout", key="logout_btn"):
        st.session_state['logged_in'] = False
        st.rerun()
    
    
    # CREATE TABS
    tabs = st.tabs([
        "📊 Dashboard",
        "🔥 Pipeline",
        "➕ New Lead",
        "📁 Lead Directory",
        "📥 Bulk Upload",
        "⚙️ Settings"
    ])
    
    tab1, tab2, tab3, tab4, tab5, tab6 = tabs
    
    # --- Tab 1: DASHBOARD ---
    with tab1:
        df = pd.read_sql_query("SELECT * FROM leads", get_connection())
        
        # Tasks Section
        st.markdown("### ⚠️ Today's Follow-ups")
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        if not df.empty:
            reminders = df[
                (df['next_followup'] <= today_str) & 
                (~df['status'].isin(['Won', 'Lost']))
            ]
            
            if not reminders.empty:
                st.warning(f"🔔 You have **{len(reminders)} pending follow-ups** today!")
                
                for idx, row in reminders.iterrows():
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                        with col1:
                            st.markdown(f"**🏢 {row['company_name']}**")
                        with col2:
                            st.markdown(f"👤 {row['contact_person']}")
                        with col3:
                            st.markdown(f"📞 {row['mobile']}")
                        with col4:
                            st.markdown(f"📅 {row['next_followup']}")
                    st.markdown("---")
            else:
                st.success("🎉 **All caught up!** No pending follow-ups for today.")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Metrics
            total = df['projected_value'].sum()
            won = df[df['status'] == 'Won']['projected_value'].sum()
            target = 1000000
            progress = min(won / target, 1.0) if target > 0 else 0
            win_rate = (len(df[df['status']=='Won'])/len(df)*100) if len(df) > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="💰 Pipeline Value",
                    value=f"₹{total/1000:.1f}K",
                    delta=f"{len(df)} Leads"
                )
            
            with col2:
                st.metric(
                    label="✅ Revenue Won",
                    value=f"₹{won/1000:.1f}K",
                    delta=f"{len(df[df['status']=='Won'])} Deals"
                )
            
            with col3:
                st.metric(
                    label="🎯 Win Rate",
                    value=f"{win_rate:.1f}%",
                    delta="Target: 30%"
                )
            
            with col4:
                st.metric(
                    label="📈 Target Progress",
                    value=f"{(progress*100):.0f}%",
                    delta=f"Goal: ₹{target/1000}K"
                )
            
            # Progress Bar
            st.markdown("### 🎯 Monthly Target Progress")
            st.progress(progress)
            st.caption(f"₹{won:,.0f} of ₹{target:,.0f} target achieved")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📊 Services Distribution")
                fig = px.pie(
                    df, 
                    names='service_interest', 
                    hole=0.4,
                    color_discrete_sequence=px.colors.sequential.Purples_r
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(showlegend=False, height=350)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("### 📈 Lead Status")
                status_counts = df['status'].value_counts()
                fig = go.Figure(data=[
                    go.Bar(
                        x=status_counts.index,
                        y=status_counts.values,
                        marker_color=['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b', '#fa709a']
                    )
                ])
                fig.update_layout(
                    showlegend=False,
                    height=350,
                    xaxis_title="Status",
                    yaxis_title="Count"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📝 No leads yet. Add your first lead to get started!")
    
    # --- Tab 2: PIPELINE ---
    with tab2:
        st.markdown("### 🔥 Deal Pipeline")
        df = pd.read_sql_query("SELECT * FROM leads", get_connection())
        
        if not df.empty:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### 🆕 New / Contacted")
                new_leads = df[df['status'].isin(['New', 'Contacted'])]
                for _, r in new_leads.iterrows():
                    st.markdown(f"""
                    <div class='pipeline-card' style='border-left-color: #4facfe;'>
                        <h4 style='margin: 0; color: #333;'>{r['company_name']}</h4>
                        <p style='margin: 0.5rem 0; color: #666;'>💰 ₹{r['projected_value']:,.0f}</p>
                        <p style='margin: 0; color: #999; font-size: 0.9rem;'>👤 {r['contact_person']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                if len(new_leads) == 0:
                    st.info("No new leads")
            
            with col2:
                st.markdown("#### 🔥 In Negotiation")
                hot_leads = df[df['status'].isin(['Proposal', 'Negotiation'])]
                for _, r in hot_leads.iterrows():
                    st.markdown(f"""
                    <div class='pipeline-card' style='border-left-color: #f093fb;'>
                        <h4 style='margin: 0; color: #333;'>{r['company_name']}</h4>
                        <p style='margin: 0.5rem 0; color: #666;'>💰 ₹{r['projected_value']:,.0f}</p>
                        <p style='margin: 0; color: #999; font-size: 0.9rem;'>📦 {r['service_interest']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                if len(hot_leads) == 0:
                    st.info("No active negotiations")
            
            with col3:
                st.markdown("#### ✅ Won Deals")
                won_leads = df[df['status'] == 'Won']
                for _, r in won_leads.iterrows():
                    st.markdown(f"""
                    <div class='pipeline-card' style='border-left-color: #43e97b;'>
                        <h4 style='margin: 0; color: #333;'>{r['company_name']}</h4>
                        <p style='margin: 0.5rem 0; color: #666;'>💰 ₹{r['projected_value']:,.0f}</p>
                        <p style='margin: 0; color: #999; font-size: 0.9rem;'>🎉 Closed</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                if len(won_leads) == 0:
                    st.info("No won deals yet")
        else:
            st.info("📝 No leads in pipeline")
    
    # --- Tab 3: NEW LEAD ---
    with tab3:
        st.markdown("### 📝 Add New Lead")
        
        with st.form("add_lead", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                comp = st.text_input("🏢 Company Name*", placeholder="Acme Corp")
                cont = st.text_input("👤 Contact Person", placeholder="John Doe")
                gst = st.text_input("📄 GST Number", placeholder="22AAAAA0000A1Z5")
            
            with col2:
                mob = st.text_input("📞 Mobile*", placeholder="9876543210")
                alt = st.text_input("📱 Alt Mobile", placeholder="9876543211")
                email = st.text_input("📧 Email", placeholder="contact@company.com")
            
            with col3:
                serv = st.selectbox("🎯 Service", 
                                   ["SEO", "PPC", "Social Media", "Web Dev", "App Dev", "Branding"])
                val = st.number_input("💰 Deal Value (₹)", step=5000, min_value=0)
                stat = st.selectbox("📊 Status", 
                                   ["New", "Contacted", "Proposal", "Negotiation", "Won", "Lost"])
            
            col4, col5 = st.columns(2)
            with col4:
                f_date = st.date_input("📅 Next Follow-Up", min_value=date.today())
            with col5:
                addr = st.text_area("📍 Address", placeholder="123 Business Street")
            
            rem = st.text_area("📝 Remarks", placeholder="Additional notes...")
            
            submit = st.form_submit_button("✨ Save Lead", use_container_width=True)
            
            if submit:
                if comp and mob:
                    new_lead_data = {
                        "company_name": comp,
                        "contact_person": cont,
                        "mobile": mob,
                        "alt_mobile": alt,
                        "email": email,
                        "gst_no": gst,
                        "address": addr,
                        "service_interest": serv,
                        "projected_value": float(val),
                        "status": stat,
                        "next_followup": str(f_date),
                        "date_added": datetime.now().strftime("%Y-%m-%d"),
                        "assigned_to": st.session_state.get('username', 'Admin'),
                        "remarks": rem
                    }
                    
                    try:
                        response = supabase.table("leads").insert(new_lead_data).execute()
                        if response.data:
                            st.success(f"✅ Lead **{comp}** added successfully!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Failed to save. Check your connection.")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                else:
                    st.error("⚠️ Company Name and Mobile are required!")
    
    # --- Tab 4: LEAD DIRECTORY ---
    with tab4:
        st.markdown("### 📁 Lead Directory")
        
        df = fetch_leads()
        
        if not df.empty:
            df['next_followup'] = pd.to_datetime(df['next_followup'], errors='coerce').dt.date
            
            # Filters
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_status = st.multiselect(
                    "Filter by Status", 
                    ["New", "Contacted", "Proposal", "Negotiation", "Won", "Lost"],
                    default=[]
                )
            with col2:
                search_q = st.text_input("🔍 Search", placeholder="Company or contact name")
            with col3:
                st.metric("Total Leads", len(df))
            
            # Apply Filters
            filtered_df = df.copy()
            if filter_status:
                filtered_df = filtered_df[filtered_df['status'].isin(filter_status)]
            if search_q:
                filtered_df = filtered_df[
                    filtered_df['company_name'].str.contains(search_q, case=False, na=False) | 
                    filtered_df['contact_person'].str.contains(search_q, case=False, na=False)
                ]
            
            # WhatsApp Link
            filtered_df['whatsapp_link'] = "https://wa.me/91" + filtered_df['mobile'].astype(str).str.replace(" ", "").str[-10:]
            
            # Data Editor
            edited_df = st.data_editor(
                filtered_df,
                column_config={
                    "whatsapp_link": st.column_config.LinkColumn(
                        "💬 WhatsApp",
                        display_text="Chat"
                    ),
                    "status": st.column_config.SelectboxColumn(
                        "Status",
                        options=["New", "Contacted", "Proposal", "Negotiation", "Won", "Lost"]
                    ),
                    "next_followup": st.column_config.DateColumn("Next Follow-up"),
                    "projected_value": st.column_config.NumberColumn(
                        "Value (₹)",
                        format="₹%.0f"
                    )
                },
                hide_index=True,
                column_order=(
                    "company_name", "contact_person", "mobile", "whatsapp_link",
                    "service_interest", "projected_value", "status", "next_followup", "remarks"
                ),
                use_container_width=True,
                key="lead_editor"
            )
            
            # Sync Button
            if st.button("💾 Sync Changes to Cloud", use_container_width=True):
                with st.spinner("Syncing..."):
                    try:
                        for index, row in edited_df.iterrows():
                            update_data = row.to_dict()
                            if 'whatsapp_link' in update_data:
                                del update_data['whatsapp_link']
                            update_data['next_followup'] = str(update_data['next_followup'])
                            supabase.table("leads").update(update_data).eq("id", row['id']).execute()
                        st.success("✅ Successfully synced to cloud!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Sync failed: {e}")
        else:
            st.info("📝 No leads found. Add your first lead!")
    
  # --- Tab 5: BULK UPLOAD ---
    with tab5:
        st.markdown("### 📥 Bulk Import Leads")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info("💡 **Tip:** Download the template, fill it with your leads, and upload it back!")
        
        with col2:
            csv_template = pd.DataFrame(columns=[
                "company_name", "contact_person", "mobile", "email",
                "service_interest", "projected_value", "status", "remarks"
            ]).to_csv(index=False).encode('utf-8')
            st.download_button(
                "⬇️ Download Template",
                csv_template,
                "leads_template.csv",
                "text/csv",
                use_container_width=True
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("📤 Upload CSV File", type="csv")
        
        if uploaded_file is not None:
            try:
                preview_df = pd.read_csv(uploaded_file)
                st.markdown("#### 📋 Preview")
                st.dataframe(preview_df, use_container_width=True)
                
                if st.button("✨ Import All Leads", use_container_width=True):
                    try:
                        preview_df['date_added'] = datetime.now().strftime("%Y-%m-%d")
                        preview_df['assigned_to'] = st.session_state['username']
                        preview_df['next_followup'] = datetime.now().strftime("%Y-%m-%d")
                        
                        success_count = 0
                        for _, row in preview_df.iterrows():
                            if save_lead(row.to_dict()):
                                success_count += 1
                        
                        st.success(f"✅ Imported {success_count} leads successfully!")
                        st.balloons()
                        st.rerun()
                    except Exception as import_error:
                        st.error(f"❌ Import error: {import_error}")
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")

    # --- Tab 6: ADMIN ---
    with tab6:
        if st.session_state['role'] == "Admin":
            st.markdown("### ⚙️ User Management")
            
            with st.form("new_user"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    u = st.text_input("👤 Username", placeholder="john_doe")
                with col2:
                    p = st.text_input("🔒 Password", type="password", placeholder="********")
                with col3:
                    r = st.selectbox("🎭 Role", ["Staff", "Admin"])
                
                if st.form_submit_button("➕ Create User", use_container_width=True):
                    if u and p:
                        if add_user(u, p, r):
                            st.success(f"✅ User **{u}** created successfully!")
                        else:
                            st.error("❌ Username already exists")
                    else:
                        st.error("⚠️ All fields required!")
            
            st.markdown("### 👥 Existing Users")
            users_df = pd.read_sql_query("SELECT username, role FROM users", get_connection())
            st.dataframe(users_df, use_container_width=True, hide_index=True)
        else:
            st.warning("🔒 Admin Access Only")