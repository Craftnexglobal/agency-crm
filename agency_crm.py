import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib.request

# --- CLOUD DATABASE CONNECTION ---
url: str = "https://dxwvgypklqyxaxquzdnv.supabase.co"
anon_key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR4d3ZneXBrbHF5eGF4cXV6ZG52Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg3Mjg5MDksImV4cCI6MjA4NDMwNDkwOX0.ccPzmQ_jKzNhcQnz2Lek2wvEp_Y0dchtUkK_uR5Xkc0"
service_role_key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR4d3ZneXBrbHF5eGF4cXV6ZG52Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODcyODkwOSwiZXhwIjoyMDg0MzA0OTA5fQ.-Sxcpg0UEO5_8mt5fZ7zEX0XSrtm3whjv1xeyYWQsrE"

@st.cache_resource
def init_supabase():
    """Initialize Supabase clients with caching to improve performance"""
    return create_client(url, anon_key), create_client(url, service_role_key)

supabase, admin_supabase = init_supabase()

def get_admin_client():
    """Gets admin client with service role key for admin operations"""
    return admin_supabase

# --- DATABASE HELPER FUNCTIONS ---
def fetch_leads(username=None):
    """Fetches leads from Supabase, filtered by username if provided"""
    try:
        query = supabase.table("leads").select("*")
        if username:
            query = query.eq("assigned_to", username)
        response = query.execute()
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

def login_user_supabase(username, password):
    """Authenticates user from Supabase users table"""
    try:
        if not username or not password:
            return None
        
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        response = supabase.table("users").select("username, role").eq("username", username).eq("password", hashed_pw).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]['role']
        return None
    except Exception as e:
        # Show detailed error for debugging
        error_msg = str(e)
        if "relation" in error_msg.lower() or "does not exist" in error_msg.lower():
            st.error("⚠️ Users table not found in Supabase. Please create the 'users' table first.")
        else:
            st.error(f"❌ Login error: {error_msg}")
        return None

def add_user_supabase(username, password, role):
    """Adds a new user to Supabase users table (Admin only - uses service role key)
    Returns: (success: bool, error_type: str or None)
    """
    try:
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        # Always use admin client for user creation (bypasses RLS)
        response = admin_supabase.table("users").insert({
            "username": username,
            "password": hashed_pw,
            "role": role
        }).execute()
        return True, None
    except Exception as e:
        error_msg = str(e)
        # Check if it's a dict with message
        if hasattr(e, 'message'):
            error_msg = str(e.message)
        elif isinstance(e, dict) and 'message' in e:
            error_msg = str(e['message'])
        # Also check for nested error messages
        if hasattr(e, 'args') and len(e.args) > 0:
            if isinstance(e.args[0], dict) and 'message' in e.args[0]:
                error_msg = str(e.args[0]['message'])
        
        if "duplicate" in error_msg.lower() or "unique" in error_msg.lower() or "already exists" in error_msg.lower() or "violates unique constraint" in error_msg.lower():
            # Username already exists
            return False, "USER_EXISTS"
        else:
            # Other error - simplified message
            return False, f"Error: {error_msg[:100]}"

def get_all_users():
    """Gets all users from Supabase (Admin only)"""
    try:
        response = supabase.table("users").select("username, role").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error fetching users: {e}")
        return pd.DataFrame()

def check_supabase_setup():
    """Checks if Supabase tables are properly set up"""
    issues = []
    try:
        # Check if users table exists
        response = supabase.table("users").select("username").limit(1).execute()
    except Exception as e:
        error_msg = str(e)
        if "relation" in error_msg.lower() or "does not exist" in error_msg.lower():
            issues.append("❌ 'users' table does not exist in Supabase")
        else:
            issues.append(f"❌ Error accessing users table: {error_msg}")
    
    try:
        # Check if leads table exists
        response = supabase.table("leads").select("id").limit(1).execute()
    except Exception as e:
        error_msg = str(e)
        if "relation" in error_msg.lower() or "does not exist" in error_msg.lower():
            issues.append("❌ 'leads' table does not exist in Supabase")
        else:
            issues.append(f"❌ Error accessing leads table: {error_msg}")
    
    return issues

def test_supabase_connection():
    """Tests the Supabase connection"""
    try:
        # Try a simple query
        response = supabase.table("users").select("username").limit(1).execute()
        return True, "✅ Connection successful!"
    except Exception as e:
        error_msg = str(e)
        if "relation" in error_msg.lower() or "does not exist" in error_msg.lower():
            return False, "⚠️ Connection works, but 'users' table doesn't exist"
        else:
            return False, f"❌ Connection error: {error_msg}"

def get_all_users_list():
    """Gets list of all usernames in the database"""
    try:
        response = supabase.table("users").select("username, role").execute()
        if response.data:
            return response.data
        return []
    except Exception as e:
        return []

def reset_admin_password(new_password="admin123"):
    """Resets the admin user's password (Admin only - uses service role key)"""
    try:
        hashed_pw = hashlib.sha256(new_password.encode()).hexdigest()
        # Always use admin client for password reset (bypasses RLS)
        response = admin_supabase.table("users").update({
            "password": hashed_pw
        }).eq("username", "admin").execute()
        
        if response.data:
            return True, f"✅ Admin password reset successfully!"
        return False, "Failed to reset password"
    except Exception as e:
        error_msg = str(e)
        return False, f"Error: {error_msg[:100]}"

def reset_user_password(username, new_password):
    """Resets any user's password (Admin only - uses service role key)"""
    try:
        if not username or not new_password:
            return False, "Username and password are required"
        
        hashed_pw = hashlib.sha256(new_password.encode()).hexdigest()
        # Always use admin client for password reset (bypasses RLS)
        response = admin_supabase.table("users").update({
            "password": hashed_pw
        }).eq("username", username).execute()
        
        if response.data:
            return True, f"✅ Password reset successfully for user '{username}'!"
        return False, f"User '{username}' not found"
    except Exception as e:
        error_msg = str(e)
        return False, f"Error: {error_msg[:100]}"

def test_login_credentials(username, password):
    """Tests login credentials and shows detailed debug info"""
    debug_info = []
    
    if not username or not password:
        return False, ["⚠️ Username and password are required"], None
    
    # Calculate hash
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    debug_info.append(f"📝 Password hash: {hashed_pw[:20]}...")
    
    try:
        # First, check if user exists
        user_check = supabase.table("users").select("username, password, role").eq("username", username).execute()
        
        if not user_check.data:
            debug_info.append(f"❌ Username '{username}' not found in database")
            all_users = get_all_users_list()
            if all_users:
                debug_info.append(f"📋 Existing users: {[u['username'] for u in all_users]}")
            else:
                debug_info.append("📋 No users found in database")
            return False, debug_info, None
        
        debug_info.append(f"✅ Username '{username}' found in database")
        stored_hash = user_check.data[0]['password']
        debug_info.append(f"📝 Stored hash: {stored_hash[:20]}...")
        
        # Check if password matches
        if stored_hash == hashed_pw:
            debug_info.append("✅ Password hash matches!")
            return True, debug_info, user_check.data[0]['role']
        else:
            debug_info.append("❌ Password hash does NOT match")
            debug_info.append(f"Expected: {hashed_pw}")
            debug_info.append(f"Got: {stored_hash}")
            
            # Detect if password is "admin" instead of "admin123"
            admin_hash = hashlib.sha256("admin".encode()).hexdigest()
            if stored_hash == admin_hash:
                debug_info.append("💡 **Detected:** Admin user has password 'admin' instead of 'admin123'")
                debug_info.append("💡 **Solution:** Try password 'admin' OR click 'Reset Admin Password' button below")
            
            return False, debug_info, None
            
    except Exception as e:
        error_msg = str(e)
        debug_info.append(f"❌ Error: {error_msg}")
        return False, debug_info, None

def send_login_notification(username):
    """Sends email notification when a user logs in"""
    # NOTE: Configure these details to enable email notifications
    sender_email = "your_email@gmail.com"  # Replace with your email
    sender_password = "your_app_password"  # Replace with your app password
    receiver_email = "info.craftnexglobal@gmail.com"
    
    if sender_email == "your_email@gmail.com":
        return # Email not configured
        
    try:
        # Get Public IP
        try:
            public_ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8')
        except:
            public_ip = "Unknown IP"
            
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = f"🔔 Login Alert: {username}"
        
        body = f"User '{username}' logged into Agency CRM at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nIP Address: {public_ip}"
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
    except Exception as e:
        print(f"Email notification failed: {e}")

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Agency CRM Pro", 
    page_icon="🚀", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- TOAST NOTIFICATION HANDLER ---
if 'toast_msg' in st.session_state:
    st.toast(st.session_state['toast_msg'], icon="✅")
    del st.session_state['toast_msg']

# --- THEME SETTINGS ---
if 'theme' not in st.session_state:
    st.session_state['theme'] = 'light'

# Define theme colors
if st.session_state['theme'] == 'dark':
    # Dark Mode Colors
    c_bg = "#0e1117"
    c_card = "#1f2937"
    c_text_main = "#e2e8f0"
    c_text_bold = "#f8fafc"
    c_text_muted = "#94a3b8"
    c_border = "#374151"
    c_input_bg = "#111827"
    c_input_border = "#4b5563"
    c_shadow = "rgba(0, 0, 0, 0.3)"
else:
    # Light Mode Colors
    c_bg = "#f4f6f9"
    c_card = "white"
    c_text_main = "#2d3748"
    c_text_bold = "#1a202c"
    c_text_muted = "#4a5568"
    c_border = "#e2e8f0"
    c_input_bg = "white"
    c_input_border = "#cbd5e0"
    c_shadow = "rgba(0, 0, 0, 0.05)"

# --- BRIGHT & MODERN CSS ---
st.markdown(f"""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');
    
    /* Global Styles */
    * {{
        font-family: 'Poppins', sans-serif;
    }}
    
    /* --- DYNAMIC THEME COLORS --- */
    /* Base text color for the whole app */
    .stApp, .stMarkdown, p, div[data-testid="stMarkdownContainer"] {{
        color: {c_text_main};
    }}
    
    /* Headings */
    h1, h2, h3, h4, h5, h6 {{
        color: {c_text_bold} !important;
    }}
    
    /* Widget Labels (Inputs, Selectboxes, etc.) */
    label, .stWidgetLabel, [data-testid="stWidgetLabel"] {{
        color: {c_text_main} !important;
    }}
    
    /* DataFrames and Tables */
    [data-testid="stDataFrame"] * {{
        color: {c_text_main} !important;
    }}
    
    /* Hide Streamlit Branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* Background */
    .stApp {{
        background-color: {c_bg};
    }}
    
    /* Main Container */
    .block-container {{
        padding: 1rem 2rem;
        max-width: 1400px;
    }}
    
    /* Smooth Page Transitions */
    .main {{
        animation: fadeIn 0.6s ease-in;
    }}
    
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    /* Metric Cards - Bright & Vibrant */
    .stMetric {{
        background: {c_card};
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px {c_shadow};
        border: 1px solid {c_border};
    }}
    
    .stMetric:nth-child(1) {{
        border-left: 5px solid #ff6b6b;
    }}
    
    .stMetric:nth-child(2) {{
        border-left: 5px solid #4ecdc4;
    }}
    
    .stMetric:nth-child(3) {{
        border-left: 5px solid #feca57;
    }}
    
    .stMetric:nth-child(4) {{
        border-left: 5px solid #48dbfb;
    }}
    
    .stMetric:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 15px {c_shadow};
    }}
    
    .stMetric label {{
        color: {c_text_muted} !important;
        font-weight: 600;
        font-size: 1rem;
    }}
    
    .stMetric [data-testid="stMetricValue"] {{
        color: {c_text_bold} !important;
        font-size: 2.5rem;
        font-weight: 800;
    }}
    
    /* Button Styling - Bright & Interactive */
    .stButton > button {{
        background: #4f46e5;
        color: white;
        border: none;
        padding: 0.6rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 1rem;
        box-shadow: 0 4px 6px rgba(79, 70, 229, 0.3);
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(79, 70, 229, 0.4);
        background: #4338ca;
    }}
    
    .stButton > button:active {{
        transform: translateY(-2px) scale(1.02);
    }}
    
    /* Form Inputs - Modern & Bright */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select,
    .stNumberInput > div > div > input {{
        border-radius: 8px;
        border: 1px solid {c_input_border};
        padding: 0.8rem;
        transition: all 0.3s ease;
        background: {c_input_bg};
        font-size: 1rem;
        color: {c_text_main} !important;
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus,
    .stNumberInput > div > div > input:focus {{
        border-color: #4f46e5;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.2);
    }}
    
    /* Tab Styling - Bright Colors */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 1rem;
        background: transparent;
        border-bottom: 2px solid {c_border};
        padding-bottom: 1rem;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: {c_card};
        border-radius: 8px;
        padding: 0.8rem 1.5rem;
        font-weight: 600;
        border: 1px solid {c_border};
        color: {c_text_muted} !important;
        font-size: 1rem;
    }}
    
    .stTabs [data-baseweb="tab"] span {{
        color: {c_text_muted} !important;
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 6px {c_shadow};
    }}
    
    .stTabs [aria-selected="true"] {{
        background: #4f46e5;
        color: white !important;
        border: 1px solid #4f46e5;
    }}
    
    .stTabs [aria-selected="true"] span {{
        color: white !important;
    }}
    
    /* Data Editor Styling */
    .stDataFrame {{
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 6px {c_shadow};
        border: 1px solid {c_border};
    }}
    
    /* Alert Boxes - Bright Colors */
    .stAlert {{
        border-radius: 8px;
        border-left: 5px solid;
        padding: 1rem;
        font-weight: 500;
    }}
    
    .stSuccess {{
        background: #f0fdf4;
        color: #15803d;
        border-left-color: #2ecc71;
    }}
    
    .stError {{
        background: #fef2f2;
        color: #b91c1c;
        border-left-color: #e74c3c;
    }}
    
    .stWarning {{
        background: #fffbeb;
        color: #b45309;
        border-left-color: #f39c12;
    }}
    
    .stInfo {{
        background: #eff6ff;
        color: #1d4ed8;
        border-left-color: #3498db;
    }}
    
    /* Progress Bar */
    .stProgress > div > div > div > div {{
        background: #4f46e5;
        border-radius: 10px;
    }}
    
    /* Divider */
    hr {{
        margin: 2rem 0;
        border: none;
        height: 1px;
        background: {c_border};
    }}
    
    /* Header Container - Bright Gradient */
    .header-container {{
        background: #1e293b;
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px {c_shadow};
    }}
    
    /* Pipeline Cards - Bright & Interactive */
    .pipeline-card {{
        background: {c_card};
        padding: 1.2rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        border-left: 6px solid;
        box-shadow: 0 2px 5px {c_shadow};
        border: 1px solid {c_border};
    }}
    
    .pipeline-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 15px {c_shadow};
    }}
    
    .pipeline-card h4 {{
        color: {c_text_bold} !important;
    }}
    
    .pipeline-card p {{
        color: {c_text_muted} !important;
    }}
    
    /* Login Page Specific */
    .login-container {{
        background: {c_card};
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px {c_shadow};
        width: 100%;
        max-width: 320px;
        margin: 0 auto;
    }}
    
    /* Make input text visible */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select,
    .stNumberInput > div > div > input {{
        color: {c_text_main} !important;
        background-color: {c_input_bg} !important;
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus,
    .stNumberInput > div > div > input:focus {{
        border-color: #4f46e5;
        color: {c_text_main} !important;
        background-color: {c_input_bg} !important;
    }}
    
    /* Input labels */
    .stTextInput > div[data-baseweb="base-input"] > label,
    .stTextArea > div[data-baseweb="base-input"] > label {{
        color: {c_text_main} !important;
        font-weight: 600;
    }}
    
    /* --- MOBILE RESPONSIVENESS --- */
    @media (max-width: 768px) {{
        .block-container {{
            padding: 1rem 0.5rem;
        }}
        h1 {{ font-size: 1.8rem !important; }}
        .stMetric {{ margin-bottom: 0.5rem; }}
    }}
</style>
""", unsafe_allow_html=True)

# --- DATABASE SETUP ---
def init_supabase_tables():
    """Initialize Supabase tables if they don't exist (creates default admin user)"""
    try:
        # Check if admin user exists, if not create it
        response = supabase.table("users").select("username").eq("username", "admin").execute()
        if not response.data:
            hashed_pw = hashlib.sha256("admin123".encode()).hexdigest()
            try:
                supabase.table("users").insert({
                    "username": "admin",
                    "password": hashed_pw,
                    "role": "Admin"
                }).execute()
            except Exception as insert_error:
                # User might already exist or table structure issue
                pass
    except Exception as e:
        # Tables might not exist yet - this is expected if tables haven't been created
        # Error will be shown when user tries to login
        pass

def create_admin_user_if_needed():
    """Creates admin user if it doesn't exist (called on login page)"""
    try:
        response = supabase.table("users").select("username").eq("username", "admin").execute()
        if not response.data:
            hashed_pw = hashlib.sha256("admin123".encode()).hexdigest()
            supabase.table("users").insert({
                "username": "admin",
                "password": hashed_pw,
                "role": "Admin"
            }).execute()
            return True
        return False
    except Exception as e:
        return False

# --- MAIN APP ---
init_supabase_tables()

# Initialize session state with persistent login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'role' not in st.session_state:
    st.session_state['role'] = None

# Check for persistent session via query parameters
query_params = st.query_params
if 'user' in query_params and not st.session_state.get('logged_in'):
    # Try to restore session from query parameter
    username_from_url = query_params['user']
    # Verify user exists and get role to restore session securely
    try:
        user_data = supabase.table("users").select("role").eq("username", username_from_url).execute()
        if user_data.data:
            st.session_state['logged_in'] = True
            st.session_state['username'] = username_from_url
            st.session_state['role'] = user_data.data[0]['role']
    except Exception:
        pass # If verification fails, stay logged out

# --- LOGIN PAGE ---
if not st.session_state['logged_in']:
    # Centered login container at top
    st.markdown("""
    <div style='display: flex; justify-content: center; align-items: flex-start; padding-top: 2rem;'>
        <div class='login-container'>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown("<div style='text-align: center; margin-bottom: 1rem;'>", unsafe_allow_html=True)
        st.markdown("<h2 style='color: #4f46e5; margin: 0; font-size: 1.5rem;'>Agency CRM</h2>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Login Form
        username = st.text_input("Username", placeholder="Username", value=st.session_state.get('username', 'admin'), key="login_username", label_visibility="collapsed")
        st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)
        password = st.text_input("Password", type="password", placeholder="Password", value="", key="login_password", label_visibility="collapsed")
        
        st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)
        
        if st.button("Login", use_container_width=True, type="primary"):
            if not username or not password:
                st.error("⚠️ Enter credentials")
            else:
                with st.spinner("Checking..."):
                    # Try to create admin user if logging in as admin and user doesn't exist
                    if username == "admin":
                        create_admin_user_if_needed()
                    
                    role = login_user_supabase(username, password)
                    if role:
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = username
                        st.session_state['role'] = role
                        st.query_params['user'] = username
                        
                        # Send email notification
                        send_login_notification(username)
                        
                        st.rerun()
                    else:
                        st.error("❌ Invalid Login")
        
        # Forgot Password Link
        st.markdown("""
            <div style='text-align: center; margin-top: 10px;'>
                <a href='#' style='color: #666; text-decoration: none; font-size: 0.8rem;' 
                   onclick='alert("Please contact your administrator to reset your password.")'>
                   Forgot Password?
                </a>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div></div>", unsafe_allow_html=True)

# --- MAIN DASHBOARD ---
else:
    # HEADER SECTION - Bright & Modern
    st.markdown("""
    <div class='header-container'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <div>
                <h1 style='color: white; margin: 0; -webkit-text-fill-color: white; text-shadow: 0 4px 15px rgba(0,0,0,0.3); font-size: 2.5rem;'>🚀 Agency CRM Pro</h1>
                <p style='color: rgba(255,255,255,0.95); margin: 0.5rem 0 0 0; font-size: 1.2rem; font-weight: 500;'>Manage your leads and close more deals 💼</p>
            </div>
            <div style='text-align: right; background: rgba(255,255,255,0.2); padding: 1rem 1.5rem; border-radius: 15px; backdrop-filter: blur(10px);'>
                <p style='color: white; margin: 0; font-weight: 700; font-size: 1.1rem;'>👤 {}</p>
                <p style='color: rgba(255,255,255,0.9); margin: 0.3rem 0 0 0; font-size: 0.95rem; font-weight: 500;'>{}</p>
            </div>
        </div>
    </div>
    """.format(st.session_state['username'], st.session_state['role']), unsafe_allow_html=True)
    
    if st.button("🚪 Logout", key="logout_btn"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = None
        st.session_state['role'] = None
        # Clear query params on logout
        st.query_params.clear()
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
        # Fetch user-specific leads from Supabase
        df = fetch_leads(st.session_state['username'])
        
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
        # Fetch user-specific leads from Supabase
        df = fetch_leads(st.session_state['username'])
        
        if not df.empty:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### 🆕 New / Contacted")
                new_leads = df[df['status'].isin(['New', 'Contacted'])]
                for _, r in new_leads.iterrows():
                    st.markdown(f"""
                    <div class='pipeline-card' style='border-left-color: #4facfe;'>
                        <h4 style='margin: 0;'>{r['company_name']}</h4>
                        <p style='margin: 0.5rem 0;'>💰 ₹{r['projected_value']:,.0f}</p>
                        <p style='margin: 0; font-size: 0.9rem;'>👤 {r['contact_person']}</p>
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
                        <h4 style='margin: 0;'>{r['company_name']}</h4>
                        <p style='margin: 0.5rem 0;'>💰 ₹{r['projected_value']:,.0f}</p>
                        <p style='margin: 0; font-size: 0.9rem;'>📦 {r['service_interest']}</p>
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
                        <h4 style='margin: 0;'>{r['company_name']}</h4>
                        <p style='margin: 0.5rem 0;'>💰 ₹{r['projected_value']:,.0f}</p>
                        <p style='margin: 0; font-size: 0.9rem;'>🎉 Closed</p>
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
                            st.session_state['toast_msg'] = f"Lead '{comp}' added successfully!"
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
        
        # Fetch user-specific leads from Supabase
        df = fetch_leads(st.session_state['username'])
        
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
                        st.session_state['toast_msg'] = "Changes synced to cloud!"
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
                        
                        # Fill missing columns with default values
                        required_cols = ['company_name', 'contact_person', 'mobile', 'alt_mobile', 
                                        'email', 'gst_no', 'address', 'service_interest', 
                                        'projected_value', 'status', 'next_followup', 
                                        'date_added', 'assigned_to', 'remarks']
                        for col in required_cols:
                            if col not in preview_df.columns:
                                preview_df[col] = None
                        
                        success_count = 0
                        for _, row in preview_df.iterrows():
                            # Only save rows with required fields
                            if pd.notna(row.get('company_name')) and pd.notna(row.get('mobile')):
                                lead_dict = {col: row[col] for col in required_cols if col in row}
                                # Convert NaN to None for proper JSON serialization
                                lead_dict = {k: (None if pd.isna(v) else v) for k, v in lead_dict.items()}
                                if save_lead(lead_dict):
                                    success_count += 1
                        
                        st.session_state['toast_msg'] = f"Imported {success_count} leads successfully!"
                        st.rerun()
                    except Exception as import_error:
                        st.error(f"❌ Import error: {import_error}")
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")

    # --- Tab 6: ADMIN ---
    with tab6:
        st.markdown("### ⚙️ Settings")
        
        # Appearance Section
        st.markdown("#### 🎨 Appearance")
        col_theme, col_spacer = st.columns([1, 3])
        with col_theme:
            # Check current theme
            is_dark = st.session_state.get('theme') == 'dark'
            
            # Toggle button
            if st.toggle("🌙 Dark Mode", value=is_dark, key="theme_toggle"):
                if st.session_state.get('theme') != 'dark':
                    st.session_state['theme'] = 'dark'
                    st.rerun()
            else:
                if st.session_state.get('theme') != 'light':
                    st.session_state['theme'] = 'light'
                    st.rerun()
        
        st.markdown("---")
        
        if st.session_state['role'] == "Admin":
            st.markdown("#### 👥 User Management")
            
            # Password Reset Section - Simplified
            st.markdown("---")
            st.markdown("### 🔄 Reset Password")
            
            # Simple one-form approach
            with st.form("reset_password_form"):
                st.markdown("**Reset any user's password:**")
                col_reset1, col_reset2 = st.columns(2)
                with col_reset1:
                    reset_username = st.text_input("👤 Username", placeholder="admin", value="admin", key="reset_username")
                with col_reset2:
                    reset_password = st.text_input("🔒 New Password", type="password", placeholder="Enter new password", key="reset_password")
                
                if st.form_submit_button("🔄 Reset Password", use_container_width=True):
                    if reset_username and reset_password:
                        with st.spinner("Resetting password..."):
                            success, message = reset_user_password(reset_username, reset_password)
                            if success:
                                st.session_state['toast_msg'] = message
                                st.rerun()
                            else:
                                st.error(message)
                    else:
                        st.error("⚠️ Please enter both username and new password")
            
            # Quick reset buttons
            st.markdown("**Quick Reset:**")
            col_quick1, col_quick2 = st.columns(2)
            with col_quick1:
                if st.button("🔄 Reset Admin to 'admin123'", use_container_width=True, key="quick_reset_admin"):
                    with st.spinner("Resetting..."):
                        success, message = reset_user_password("admin", "admin123")
                        if success:
                            st.session_state['toast_msg'] = message
                            st.rerun()
                        else:
                            st.error(message)
            with col_quick2:
                if st.button("🔄 Reset Admin to 'admin'", use_container_width=True, key="quick_reset_admin_old"):
                    with st.spinner("Resetting..."):
                        success, message = reset_user_password("admin", "admin")
                        if success:
                            st.session_state['toast_msg'] = message
                            st.rerun()
                        else:
                            st.error(message)
            
            st.markdown("---")
            st.markdown("### ➕ Create New User")
            
            with st.form("new_user"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    u = st.text_input("👤 Username", placeholder="john_doe", key="new_username")
                with col2:
                    p = st.text_input("🔒 Password", type="password", placeholder="********", key="new_password")
                with col3:
                    r = st.selectbox("🎭 Role", ["Staff", "Admin"], key="new_role")
                
                if st.form_submit_button("➕ Create User", use_container_width=True):
                    if u and p:
                        with st.spinner("Creating user..."):
                            success, error_type = add_user_supabase(u, p, r)
                            if success:
                                st.session_state['toast_msg'] = f"User '{u}' created successfully!"
                                st.rerun()
                            else:
                                if error_type == "USER_EXISTS":
                                    st.error(f"❌ Username **{u}** already exists. Please choose a different username.")
                                else:
                                    st.error(f"❌ {error_type}")
                    else:
                        st.error("⚠️ All fields required!")
            
            st.markdown("---")
            st.markdown("### 👥 Existing Users")
            users_df = get_all_users()
            if not users_df.empty:
                # Add reset password option for each user
                edited_users = st.data_editor(
                    users_df,
                    use_container_width=True,
                    hide_index=True,
                    disabled=["username", "role"],
                    key="users_editor"
                )
                
                # Show password reset for selected user
                if len(users_df) > 0:
                    st.markdown("#### Reset Password for User")
                    col_user, col_pw, col_btn = st.columns([2, 2, 1])
                    with col_user:
                        selected_user = st.selectbox("Select User", users_df['username'].tolist(), key="select_user_reset")
                    with col_pw:
                        new_pw = st.text_input("New Password", type="password", key="new_pw_reset")
                    with col_btn:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("🔄 Reset", use_container_width=True, key="reset_selected_user"):
                            if new_pw:
                                success, message = reset_user_password(selected_user, new_pw)
                                if success:
                                    st.session_state['toast_msg'] = message
                                    st.rerun()
                                else:
                                    st.error(message)
                            else:
                                st.error("⚠️ Please enter a new password")
            else:
                st.info("No users found")
        else:
            st.warning("🔒 Admin Access Only")
            
            # Allow users to reset their own password
            st.markdown("---")
            st.markdown("### 🔄 Change My Password")
            with st.form("change_my_password"):
                current_pw = st.text_input("🔒 Current Password", type="password", key="current_pw")
                new_pw = st.text_input("🔒 New Password", type="password", key="new_pw")
                confirm_pw = st.text_input("🔒 Confirm New Password", type="password", key="confirm_pw")
                if st.form_submit_button("🔄 Change Password", use_container_width=True):
                    if current_pw and new_pw and confirm_pw:
                        if new_pw != confirm_pw:
                            st.error("❌ New passwords do not match")
                        else:
                            # Verify current password first
                            role = login_user_supabase(st.session_state['username'], current_pw)
                            if role:
                                success, message = reset_user_password(st.session_state['username'], new_pw)
                                if success:
                                    st.session_state['toast_msg'] = message
                                    st.rerun()
                                else:
                                    st.error(message)
                            else:
                                st.error("❌ Current password is incorrect")
                    else:
                        st.error("⚠️ All fields required")