import base64
from PIL import Image
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta, date
import random




st.set_page_config(
    page_title="Exam Dashboard",
    #page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
<style>
   
    .main-title {
        text-align: center;
        color: #1f77b4;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 20px;
    }
    
  
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    
   
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%);
    }
    
   
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 10px 24px;
        font-weight: 600;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
    }
    
    
    .status-pending {
        background-color: #ffc107;
        color: #000;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
    }
    
    .status-approved {
        background-color: #28a745;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
    }
    
    .status-rejected {
        background-color: #dc3545;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


if "role" not in st.session_state:
    st.session_state.role = "student"   
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "page" not in st.session_state:
    st.session_state.page = None



@st.cache_resource
def get_engine():
   # return create_engine("postgresql://marwa:strongpassword@localhost/exam_scheduler")
    return create_engine(
        "postgresql://neondb_owner:npg_y5D7ZaibChGp@ep-rapid-sunset-agqksqfx-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    )

engine = get_engine()


def get_count(table):
    try:
        with engine.connect() as conn:
            return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
    except Exception as e:
        st.error(f"Error fetching count: {str(e)}")
        return 0

def generate_exam_slots(start_date, end_date):
    slots = []
    current_date = start_date
    exam_times = ["08:30", "10:30", "13:30", "15:30"]

    while current_date <= end_date:
        if current_date.weekday() != 4:  
            for t in exam_times:
                slot_time = datetime.combine(
                    current_date,
                    datetime.strptime(t, "%H:%M").time()
                )
                slots.append(slot_time)
        current_date += timedelta(days=1)
    
    return slots

# menu ---------------------------------------

with st.sidebar:
    st.markdown("### Navigation Menu")
    
    if st.session_state.role == "student":
        st.info("**Student Dashboard**")
        st.markdown("---")
        if st.button("Login", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()
    
    elif st.session_state.role is None:
        st.write("Please login to continue")
    
    if st.session_state.role in ["admin", "doyen", "professor"]:
        st.success(f"Logged in as **{st.session_state.role.upper()}**")
        if st.button(" Logout ", use_container_width=True):
            st.session_state.role = "student"
            st.session_state.user_id = None
            st.rerun()
    
    st.markdown("---")
    
   
    with st.expander("💬 Send Feedback"):
        feedback = st.text_area("Your feedback", label_visibility="collapsed")
        if st.button("Submit", use_container_width=True):
            st.success("Thank you,Your feedback was recorded.")


if st.session_state.page == "login":

    st.markdown("### Login as Staff", unsafe_allow_html=True)

    with st.form("staff_login_form"):
        user_input = st.text_input("Enter your ID / Password")
        submit = st.form_submit_button(" Login ")

        if submit:
            if user_input == "admin123":
                st.session_state.role = "admin"
                st.session_state.user_id = "admin"
                st.session_state.page = None
                st.rerun()

            elif user_input == "doyen123" :
                st.session_state.role = "doyen"
                st.session_state.user_id = "doyen"
                st.session_state.page = None
                st.rerun()

            else:
                prof = pd.read_sql(
                    text("SELECT id FROM professors WHERE id = :id"),
                    engine,
                    params={"id": user_input}
                )
                if not prof.empty:
                    st.session_state.role = "professor"
                    st.session_state.user_id = int(user_input)
                    st.session_state.page = None
                    st.rerun()
                else:
                    st.error("Invalid ID or password")


# admin --------------------------------------
#---------------------------------------------------------------

elif st.session_state.role == "admin":
    
    st.markdown("""
    <style>
        .stApp {
            background-color: #f5f5f7;
        }
        
        .day-header {
            background-color: #f5f5f7;
            color: #333;
            padding: 10px;
            text-align: center;
            font-weight: 600;
            border-bottom: 2px solid #e0e0e0;
            margin-bottom: 10px;
        }
        
        .day-name {
            font-size: 0.85em;
            color: #888;
            margin-bottom: 3px;
        }
        
        .day-date {
            font-size: 1.8em;
            font-weight: bold;
            color: #333;
        }
        
        .time-slot {
            background: white;
            border-radius: 12px;
            padding: 14px;
            margin: 10px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            transition: all 0.2s ease;
        }
        
        .time-slot:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        .exam-time {
            font-size: 0.85em;
            color: #666;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .exam-module {
            font-size: 0.95em;
            color: #1a1a1a;
            font-weight: 600;
            margin: 8px 0;
            line-height: 1.3;
        }
        
        .exam-group {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 0.85em;
            color: #666;
            margin: 5px 0;
        }
        
        .exam-prof {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 0.85em;
            color: #666;
            margin: 5px 0;
        }
        
        .exam-room {
            color: #666;
            font-size: 0.85em;
            margin-top: 8px;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .no-exam {
            background: transparent;
            color: #ccc;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
        }
        
        .exam-card-blue { border-left: 4px solid #5b9cf5; }
        .exam-card-orange { border-left: 4px solid #ff9f43; }
        .exam-card-green { border-left: 4px solid #26de81; }
        .exam-card-pink { border-left: 4px solid #fc5c65; }
        .exam-card-purple { border-left: 4px solid #a55eea; }
        .exam-card-teal { border-left: 4px solid #20bf6b; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 style="color: #4f3b63;">Administrator Dashboard</h1>', unsafe_allow_html=True)
    
    st.markdown('<p style="color: #764ba2; font-size: 22px; font-weight:bold;">Global Statistics</p>', unsafe_allow_html=True)
    
    rooms_count = get_count("exam_locations")
    exams_count = get_count("exams")
    profs_count = get_count("professors")
    students_count = get_count("students")
    
    col1, col2 = st.columns(2)
    
    with col1:
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%); border-radius: 20px; padding: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); position: relative; overflow: hidden; margin-bottom: 20px;">
            <div style="position: absolute; top: -10px; right: -10px; width: 80px; height: 80px; background: #00bcd4; border-radius: 50%; opacity: 0.3;"></div>
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="background: #00bcd4; width: 60px; height: 60px; border-radius: 15px; display: flex; align-items: center; justify-content: center; font-size: 30px; box-shadow: 0 4px 8px rgba(0, 188, 212, 0.3);"><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M0-240v-63q0-43 44-70t116-27q13 0 25 .5t23 2.5q-14 21-21 44t-7 48v65H0Zm240 0v-65q0-32 17.5-58.5T307-410q32-20 76.5-30t96.5-10q53 0 97.5 10t76.5 30q32 20 49 46.5t17 58.5v65H240Zm540 0v-65q0-26-6.5-49T754-397q11-2 22.5-2.5t23.5-.5q72 0 116 26.5t44 70.5v63H780Zm-455-80h311q-10-20-55.5-35T480-370q-55 0-100.5 15T325-320ZM160-440q-33 0-56.5-23.5T80-520q0-34 23.5-57t56.5-23q34 0 57 23t23 57q0 33-23 56.5T160-440Zm640 0q-33 0-56.5-23.5T720-520q0-34 23.5-57t56.5-23q34 0 57 23t23 57q0 33-23 56.5T800-440Zm-320-40q-50 0-85-35t-35-85q0-51 35-85.5t85-34.5q51 0 85.5 34.5T600-600q0 50-34.5 85T480-480Zm0-80q17 0 28.5-11.5T520-600q0-17-11.5-28.5T480-640q-17 0-28.5 11.5T440-600q0 17 11.5 28.5T480-560Zm1 240Zm-1-280Z"/></svg></div>
                <div>
                    <div style="color: #0097a7; font-size: 0.9em; font-weight: 500;">Students</div>
                    <div style="color: #006064; font-size: 2.2em; font-weight: 700; margin-top: 5px;">{students_count}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); border-radius: 20px; padding: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); position: relative; overflow: hidden;">
            <div style="position: absolute; top: -10px; right: -10px; width: 80px; height: 80px; background: #2196f3; border-radius: 50%; opacity: 0.3;"></div>
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="background: #2196f3; width: 60px; height: 60px; border-radius: 15px; display: flex; align-items: center; justify-content: center; font-size: 30px; box-shadow: 0 4px 8px rgba(33, 150, 243, 0.3);"><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M120-120v-560h240v-80l120-120 120 120v240h240v400H120Zm80-80h80v-80h-80v80Zm0-160h80v-80h-80v80Zm0-160h80v-80h-80v80Zm240 320h80v-80h-80v80Zm0-160h80v-80h-80v80Zm0-160h80v-80h-80v80Zm0-160h80v-80h-80v80Zm240 480h80v-80h-80v80Zm0-160h80v-80h-80v80Z"/></svg></div>
                <div>
                    <div style="color: #1976d2; font-size: 0.9em; font-weight: 500;">Rooms</div>
                    <div style="color: #0d47a1; font-size: 2.2em; font-weight: 700; margin-top: 5px;">{rooms_count}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f1f8e9 0%, #dcedc8 100%); border-radius: 20px; padding: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); position: relative; overflow: hidden; margin-bottom: 20px;">
            <div style="position: absolute; top: -10px; right: -10px; width: 80px; height: 80px; background: #8bc34a; border-radius: 50%; opacity: 0.3;"></div>
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="background: #8bc34a; width: 60px; height: 60px; border-radius: 15px; display: flex; align-items: center; justify-content: center; font-size: 30px; box-shadow: 0 4px 8px rgba(139, 195, 74, 0.3);"><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M40-160v-112q0-34 17.5-62.5T104-378q62-31 126-46.5T360-440q66 0 130 15.5T616-378q29 15 46.5 43.5T680-272v112H40Zm720 0v-120q0-44-24.5-84.5T666-434q51 6 96 20.5t84 35.5q36 20 55 44.5t19 53.5v120H760ZM360-480q-66 0-113-47t-47-113q0-66 47-113t113-47q66 0 113 47t47 113q0 66-47 113t-113 47Zm400-160q0 66-47 113t-113 47q-11 0-28-2.5t-28-5.5q27-32 41.5-71t14.5-81q0-42-14.5-81T544-792q14-5 28-6.5t28-1.5q66 0 113 47t47 113ZM120-240h480v-32q0-11-5.5-20T580-306q-54-27-109-40.5T360-360q-56 0-111 13.5T140-306q-9 5-14.5 14t-5.5 20v32Zm240-320q33 0 56.5-23.5T440-640q0-33-23.5-56.5T360-720q-33 0-56.5 23.5T280-640q0 33 23.5 56.5T360-560Zm0 320Zm0-400Z"/></svg></div>
                <div>
                    <div style="color: #689f38; font-size: 0.9em; font-weight: 500;">Professors</div>
                    <div style="color: #33691e; font-size: 2.2em; font-weight: 700; margin-top: 5px;">{profs_count}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #fce4ec 0%, #f8bbd0 100%); border-radius: 20px; padding: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); position: relative; overflow: hidden;">
            <div style="position: absolute; top: -10px; right: -10px; width: 80px; height: 80px; background: #e91e63; border-radius: 50%; opacity: 0.3;"></div>
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="background: #e91e63; width: 60px; height: 60px; border-radius: 15px; display: flex; align-items: center; justify-content: center; font-size: 30px; box-shadow: 0 4px 8px rgba(233, 30, 99, 0.3);"><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M680-80q-83 0-141.5-58.5T480-280q0-83 58.5-141.5T680-480q83 0 141.5 58.5T880-280q0 83-58.5 141.5T680-80Zm67-105 28-28-75-75v-112h-40v128l87 87Zm-547 65q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h167q11-35 43-57.5t70-22.5q40 0 71.5 22.5T594-840h166q33 0 56.5 23.5T840-760v250q-18-13-38-22t-42-16v-212h-80v120H280v-120h-80v560h212q7 22 16 42t22 38H200Zm280-640q17 0 28.5-11.5T520-800q0-17-11.5-28.5T480-840q-17 0-28.5 11.5T440-800q0 17 11.5 28.5T480-760Z"/></svg></div>
                <div>
                    <div style="color: #c2185b; font-size: 0.9em; font-weight: 500;">Exams</div>
                    <div style="color: #880e4f; font-size: 2.2em; font-weight: 700; margin-top: 5px;">{exams_count}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    
    try:
        departments = pd.read_sql("SELECT id, name FROM departments ORDER BY name", engine)
        formations = pd.read_sql("SELECT id, name, dept_id, validation_status FROM formations", engine)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<p style="color: #2196f3; font-weight: 600; margin-bottom: 5px;"> Select Department</p>', unsafe_allow_html=True)
            dept_choice = st.selectbox("", departments["name"])
            dept_id = int(departments.loc[departments.name == dept_choice, "id"].values[0])
        
        with col2:
            formation_options = formations[formations.dept_id == dept_id]
            if formation_options.empty:
                st.warning("No formations in this department")
                st.stop()

            st.markdown('<p style="color: #2196f3; font-weight: 600; margin-bottom: 5px;"> Select Formation</p>', unsafe_allow_html=True)
            formation_choice = st.selectbox("", formation_options["name"])
            formation_id = int(formation_options.loc[formation_options.name == formation_choice, "id"].values[0])
        
        st.markdown("---")
        
        st.markdown('<p style="color: #764ba2; font-size: 22px; font-weight:bold;">Schedule Configuration</p>', unsafe_allow_html=True)
        st.caption("Maximum 22 days, no exams on Fridays")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<p style="color: #2196f3; font-weight: 600; margin-bottom: 5px;"> Start Date</p>', unsafe_allow_html=True)
            start = st.date_input("", value=date.today())
        with col2:
            st.markdown('<p style="color: #2196f3; font-weight: 600; margin-bottom: 5px;"> End Date</p>', unsafe_allow_html=True)
            end = st.date_input("", value=date.today() + timedelta(days=14))
        
        slots = []
        if start and end:
            if end < start:
                st.error("End date cannot be before start date")
            elif (end - start).days + 1 > 22:
                st.error("Exam period cannot exceed 22 days")
            else:
                slots = generate_exam_slots(start, end)
                st.success(f"{len(slots)} exam slots generated")
        
        modules = pd.read_sql(
            text("SELECT id, name FROM modules WHERE formation_id = :fid ORDER BY id"),
            engine,
            params={"fid": formation_id}
        )
        
        professors = pd.read_sql(
            "SELECT id, first_name, last_name, dept_id FROM professors",
            engine
        )
        
        students = pd.read_sql(
            text("SELECT id, first_name, last_name FROM students WHERE formation_id = :fid ORDER BY id"),
            engine,
            params={"fid": formation_id}
        )
        
        rooms = pd.read_sql(
            "SELECT id, name, capacity FROM exam_locations ORDER BY capacity DESC",
            engine
        )
        
        existing_full = pd.read_sql(
            text("""
                SELECT e.id, m.name AS module, el.name AS room,
                       e.date_time::date AS date,
                       e.date_time::time AS time,
                       CONCAT(p.first_name, ' ', p.last_name) AS professor
                FROM exams e
                JOIN modules m ON e.module_id = m.id
                JOIN exam_locations el ON e.room_id = el.id
                JOIN professors p ON e.prof_id = p.id
                WHERE m.formation_id = :fid
                ORDER BY e.date_time
            """),
            engine,
            params={"fid": formation_id}
        )
        
        status_row = formation_options.loc[formation_options.name == formation_choice]
        current_status = status_row["validation_status"].values[0]
        
        st.markdown("---")
        st.markdown('<p style="color: #764ba2; font-size: 22px; font-weight:bold;">Current Schedule Status</p>', unsafe_allow_html=True)
        
        status_html = f'<span class="status-{current_status}">{current_status.upper()}</span>'
        st.markdown(status_html, unsafe_allow_html=True)
        
        if not existing_full.empty:
            
            exam_schedule = existing_full.copy()
            exam_schedule['slot_key'] = (
                exam_schedule['date'].astype(str) + '_' + 
                exam_schedule['time'].astype(str) + '_' + 
                exam_schedule['module']
            )
            exam_schedule['group_num'] = exam_schedule.groupby('slot_key').cumcount() + 1
            
            unique_dates = sorted(exam_schedule['date'].unique())
            colors = ['blue', 'orange', 'green', 'pink', 'purple', 'teal']
            
            st.markdown("""
            <style>
            div[data-baseweb="tab-list"] button {
                color: #393b40;
                font-weight: 800;
                font-size: 14px;
            }

            div[data-baseweb="tab-list"] button[aria-selected="true"] {
                color:#d61609;
            }
            </style>
            """, unsafe_allow_html=True)
            
            if len(unique_dates) > 7:
                weeks = []
                for i in range(0, len(unique_dates), 7):
                    weeks.append(unique_dates[i:i+7])
                
                tabs = st.tabs([f"Week {i+1}" for i in range(len(weeks))])
                
                for tab, week_dates in zip(tabs, weeks):
                    with tab:
                        cols = st.columns(len(week_dates))
                        
                        for col_idx, exam_date in enumerate(week_dates):
                            with cols[col_idx]:
                                day_name = pd.to_datetime(exam_date).strftime('%a')
                                day_num = pd.to_datetime(exam_date).strftime('%d')
                                
                                st.markdown(f"""
                                <div class="day-header">
                                    <div class="day-name">{day_name}</div>
                                    <div class="day-date">{day_num}</div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                day_exams = exam_schedule[exam_schedule['date'] == exam_date]
                                
                                if day_exams.empty:
                                    st.markdown('<div class="no-exam">No exams</div>', unsafe_allow_html=True)
                                else:
                                    for idx, exam in day_exams.iterrows():
                                        color_idx = hash(exam['module']) % len(colors)
                                        card_class = f"exam-card-{colors[color_idx]}"
                                        time_str = str(exam['time'])[:5]
                                        
                                        st.markdown(f"""
                                        <div class="time-slot {card_class}">
                                            <div class="exam-time">
                                                <span>🕐</span>
                                                <span>{time_str}</span>
                                            </div>
                                            <div class="exam-module">{exam['module']}</div>
                                            <div class="exam-group">
                                                <span><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M0-240v-63q0-43 44-70t116-27q13 0 25 .5t23 2.5q-14 21-21 44t-7 48v65H0Zm240 0v-65q0-32 17.5-58.5T307-410q32-20 76.5-30t96.5-10q53 0 97.5 10t76.5 30q32 20 49 46.5t17 58.5v65H240Zm540 0v-65q0-26-6.5-49T754-397q11-2 22.5-2.5t23.5-.5q72 0 116 26.5t44 70.5v63H780Zm-455-80h311q-10-20-55.5-35T480-370q-55 0-100.5 15T325-320ZM160-440q-33 0-56.5-23.5T80-520q0-34 23.5-57t56.5-23q34 0 57 23t23 57q0 33-23 56.5T160-440Zm640 0q-33 0-56.5-23.5T720-520q0-34 23.5-57t56.5-23q34 0 57 23t23 57q0 33-23 56.5T800-440Zm-320-40q-50 0-85-35t-35-85q0-51 35-85.5t85-34.5q51 0 85.5 34.5T600-600q0 50-34.5 85T480-480Zm0-80q17 0 28.5-11.5T520-600q0-17-11.5-28.5T480-640q-17 0-28.5 11.5T440-600q0 17 11.5 28.5T480-560Zm1 240Zm-1-280Z"/></svg></span>
                                                <span>Group G{exam['group_num']}</span>
                                            </div>
                                            <div class="exam-prof">
                                                <span><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M40-160v-112q0-34 17.5-62.5T104-378q62-31 126-46.5T360-440q66 0 130 15.5T616-378q29 15 46.5 43.5T680-272v112H40Zm720 0v-120q0-44-24.5-84.5T666-434q51 6 96 20.5t84 35.5q36 20 55 44.5t19 53.5v120H760ZM360-480q-66 0-113-47t-47-113q0-66 47-113t113-47q66 0 113 47t47 113q0 66-47 113t-113 47Zm400-160q0 66-47 113t-113 47q-11 0-28-2.5t-28-5.5q27-32 41.5-71t14.5-81q0-42-14.5-81T544-792q14-5 28-6.5t28-1.5q66 0 113 47t47 113ZM120-240h480v-32q0-11-5.5-20T580-306q-54-27-109-40.5T360-360q-56 0-111 13.5T140-306q-9 5-14.5 14t-5.5 20v32Zm240-320q33 0 56.5-23.5T440-640q0-33-23.5-56.5T360-720q-33 0-56.5 23.5T280-640q0 33 23.5 56.5T360-560Zm0 320Zm0-400Z"/></svg></span>
                                                <span>{exam['professor']}</span>
                                            </div>
                                            <div class="exam-room">
                                                <span>📍</span>
                                                <span>{exam['room']}</span>
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
            else:
                cols = st.columns(len(unique_dates))
                
                for col_idx, exam_date in enumerate(unique_dates):
                    with cols[col_idx]:
                        day_name = pd.to_datetime(exam_date).strftime('%a')
                        day_num = pd.to_datetime(exam_date).strftime('%d')
                        
                        st.markdown(f"""
                        <div class="day-header">
                            <div class="day-name">{day_name}</div>
                            <div class="day-date">{day_num}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        day_exams = exam_schedule[exam_schedule['date'] == exam_date]
                        
                        if day_exams.empty:
                            st.markdown('<div class="no-exam">No exams</div>', unsafe_allow_html=True)
                        else:
                            for idx, exam in day_exams.iterrows():
                                color_idx = hash(exam['module']) % len(colors)
                                card_class = f"exam-card-{colors[color_idx]}"
                                time_str = str(exam['time'])[:5]
                                
                                st.markdown(f"""
                                <div class="time-slot {card_class}">
                                    <div class="exam-time">
                                        <span>🕐</span>
                                        <span>{time_str}</span>
                                    </div>
                                    <div class="exam-module">{exam['module']}</div>
                                    <div class="exam-group">
                                        <span><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M0-240v-63q0-43 44-70t116-27q13 0 25 .5t23 2.5q-14 21-21 44t-7 48v65H0Zm240 0v-65q0-32 17.5-58.5T307-410q32-20 76.5-30t96.5-10q53 0 97.5 10t76.5 30q32 20 49 46.5t17 58.5v65H240Zm540 0v-65q0-26-6.5-49T754-397q11-2 22.5-2.5t23.5-.5q72 0 116 26.5t44 70.5v63H780Zm-455-80h311q-10-20-55.5-35T480-370q-55 0-100.5 15T325-320ZM160-440q-33 0-56.5-23.5T80-520q0-34 23.5-57t56.5-23q34 0 57 23t23 57q0 33-23 56.5T160-440Zm640 0q-33 0-56.5-23.5T720-520q0-34 23.5-57t56.5-23q34 0 57 23t23 57q0 33-23 56.5T800-440Zm-320-40q-50 0-85-35t-35-85q0-51 35-85.5t85-34.5q51 0 85.5 34.5T600-600q0 50-34.5 85T480-480Zm0-80q17 0 28.5-11.5T520-600q0-17-11.5-28.5T480-640q-17 0-28.5 11.5T440-600q0 17 11.5 28.5T480-560Zm1 240Zm-1-280Z"/></svg></span>
                                        <span>Group G{exam['group_num']}</span>
                                    </div>
                                    <div class="exam-prof">
                                        <span><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M40-160v-112q0-34 17.5-62.5T104-378q62-31 126-46.5T360-440q66 0 130 15.5T616-378q29 15 46.5 43.5T680-272v112H40Zm720 0v-120q0-44-24.5-84.5T666-434q51 6 96 20.5t84 35.5q36 20 55 44.5t19 53.5v120H760ZM360-480q-66 0-113-47t-47-113q0-66 47-113t113-47q66 0 113 47t47 113q0 66-47 113t-113 47Zm400-160q0 66-47 113t-113 47q-11 0-28-2.5t-28-5.5q27-32 41.5-71t14.5-81q0-42-14.5-81T544-792q14-5 28-6.5t28-1.5q66 0 113 47t47 113ZM120-240h480v-32q0-11-5.5-20T580-306q-54-27-109-40.5T360-360q-56 0-111 13.5T140-306q-9 5-14.5 14t-5.5 20v32Zm240-320q33 0 56.5-23.5T440-640q0-33-23.5-56.5T360-720q-33 0-56.5 23.5T280-640q0 33 23.5 56.5T360-560Zm0 320Zm0-400Z"/></svg></span>
                                        <span>{exam['professor']}</span>
                                    </div>
                                    <div class="exam-room">
                                        <span>📍</span>
                                        <span>{exam['room']}</span>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            if current_status == "approved":
                st.success("Schedule approved — visible to students & professors")
                st.stop()
            
            if current_status == "pending":
                st.warning("Pending approval from Doyen")
            
            if current_status == "rejected":
                st.error("Schedule rejected — delete and regenerate")
            
            if current_status in ["pending", "rejected"]:
                if st.button("Delete Current Schedule", type="secondary"):
                    try:
                        with engine.begin() as conn:
                            conn.execute(
                                text("DELETE FROM exams WHERE module_id IN (SELECT id FROM modules WHERE formation_id = :fid)"),
                                {"fid": formation_id}
                            )
                            conn.execute(
                                text("UPDATE formations SET validation_status='pending' WHERE id=:fid"),
                                {"fid": formation_id}
                            )
                        st.success("Schedule deleted successfully")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting schedule: {str(e)}")
            st.stop()
        
        else:
            st.info("No schedule exists — ready to generate")
        
        groups = []
        if not students.empty:
            records = students.to_dict("records")
            groups = [records[i:i + 20] for i in range(0, len(records), 20)]
            
           # with st.expander(f"Student Groups ({len(groups)} groups)", expanded=False):
               # dfs = []
                #for i, g in enumerate(groups, 1):
                   # df = pd.DataFrame(g)
                   # df.insert(0, "Group", f"G{i}")
                 #  dfs.append(df)
               # st.dataframe(pd.concat(dfs, ignore_index=True), use_container_width=True)
        
        st.markdown("---")
        
        if st.button("Generate Exam Schedule", type="primary", use_container_width=True):
         if not slots:
           st.error("Please configure the exam period first")
         elif modules.empty:
           st.error("No modules found for this formation")
         elif groups == []:
           st.error("No students found for this formation")
        else:
           with st.spinner("Generating schedule..."):
            student_exams = {}       
            professor_exams = {}     
            room_bookings = {}       
            prof_total = {p.id: 0 for _, p in professors.iterrows()}
            schedule = []
            
            for module in modules.to_dict("records"):
                scheduled = False
                
                for slot in slots:
                    exam_date = slot.date()
                    used_rooms = set()
                    used_profs = set()
                    temp = []

                    for gi, group in enumerate(groups, 1):

                        
                        if any(exam_date in student_exams.get(s["id"], set()) for s in group):
                            break

                       
                        room = None
                        for _, r in rooms.iterrows():
                            effective_capacity = min(r.capacity, 20) if "amphi" in r.name.lower() else r.capacity

                            if effective_capacity >= len(group) and r.id not in used_rooms:
                                
                                if slot in room_bookings.get(r.id, set()):
                                    continue
                                room = r
                                break

                        if room is None:
                            break

                       
                        dept_profs = [p for p in professors.to_dict("records") if p["dept_id"] == dept_id]
                        other_profs = [p for p in professors.to_dict("records") if p["dept_id"] != dept_id]

                        dept_profs.sort(key=lambda p: prof_total[p["id"]])
                        other_profs.sort(key=lambda p: prof_total[p["id"]])

                        sorted_profs = dept_profs + other_profs

                        prof = None
                        for p in sorted_profs:
                            exams_for_prof = professor_exams.get(p["id"], {})

                           
                            if sum(1 for dt in exams_for_prof if dt.date() == exam_date) >= 3:
                                continue

                           
                            if slot in exams_for_prof:
                                continue

                           
                            if prof_total[p["id"]] - min(prof_total.values()) > 1:
                                continue

                            if p["id"] in used_profs:
                                continue

                            prof = p
                            break

                        if prof is None:
                            break

                        temp.append((gi, group, room, prof))
                        used_rooms.add(room.id)
                        used_profs.add(prof["id"])

                 
                    if len(temp) == len(groups):
                        for gi, group, room, prof in temp:
                           
                            for s in group:
                                student_exams.setdefault(s["id"], set()).add(exam_date)

                            
                            professor_exams.setdefault(prof["id"], {})
                            professor_exams[prof["id"]][slot] = professor_exams[prof["id"]].get(slot, 0) + 1
                            prof_total[prof["id"]] += 1

                          
                            room_bookings.setdefault(room.id, set()).add(slot)

                            schedule.append({
                                "Module": module["name"],
                                "Formation": formation_choice,
                                "Group": f"G{gi}",
                                "Room": room.name,
                                "Professor": f"{prof['first_name']} {prof['last_name']}",
                                "Date": exam_date,
                                "Time": slot.time(),
                                "module_id": module["id"],
                                "prof_id": prof["id"],
                                "room_id": room.id,
                                "date_time": slot
                            })

                        scheduled = True
                        break

                if not scheduled:
                    st.warning(f"Could not schedule module: {module['name']}")

            
            if schedule:
                st.success(f"Successfully scheduled {len(set(s['Module'] for s in schedule))} modules")
                df = pd.DataFrame(schedule)
                st.dataframe(df.drop(columns=["module_id", "prof_id", "room_id", "date_time"]), use_container_width=True)

                try:
                    with engine.begin() as conn:
                        for row in schedule:
                            conn.execute(
                                text("""
                                    INSERT INTO exams (module_id, prof_id, room_id, date_time)
                                    VALUES (:mid, :pid, :rid, :dt)
                                """),
                                {"mid": row["module_id"], "pid": row["prof_id"], "rid": row["room_id"], "dt": row["date_time"]}
                            )
                        conn.execute(
                            text("UPDATE formations SET validation_status='pending' WHERE id=:fid"),
                            {"fid": formation_id}
                        )
                    st.success("Schedule saved! Waiting for Doyen validation.")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error saving schedule: {str(e)}")
            else:
                st.error("Could not generate schedule. Please adjust constraints.")

    except Exception as e:
        st.error(f"Error in admin dashboard: {str(e)}")


# doyen -----------------------------------
#---------------------------------------------

elif st.session_state.role == "doyen":
    
    st.markdown("""
    <style>
        .stApp {
            background-color: #f5f5f7;
        }
        
        .day-header {
            background-color: #f5f5f7;
            color: #333;
            padding: 10px;
            text-align: center;
            font-weight: 600;
            border-bottom: 2px solid #e0e0e0;
            margin-bottom: 10px;
        }
        
        .day-name {
            font-size: 0.85em;
            color: #888;
            margin-bottom: 3px;
        }
        
        .day-date {
            font-size: 1.8em;
            font-weight: bold;
            color: #333;
        }
        
        .time-slot {
            background: white;
            border-radius: 12px;
            padding: 14px;
            margin: 10px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            transition: all 0.2s ease;
        }
        
        .time-slot:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        .exam-time {
            font-size: 0.85em;
            color: #666;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .exam-module {
            font-size: 0.95em;
            color: #1a1a1a;
            font-weight: 600;
            margin: 8px 0;
            line-height: 1.3;
        }
        
        .exam-prof {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 0.85em;
            color: #666;
            margin: 5px 0;
        }
        
        .exam-room {
            color: #666;
            font-size: 0.85em;
            margin-top: 8px;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .no-exam {
            background: transparent;
            color: #ccc;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
        }
        
        .exam-card-blue { border-left: 4px solid #5b9cf5; }
        .exam-card-orange { border-left: 4px solid #ff9f43; }
        .exam-card-green { border-left: 4px solid #26de81; }
        .exam-card-pink { border-left: 4px solid #fc5c65; }
        .exam-card-purple { border-left: 4px solid #a55eea; }
        .exam-card-teal { border-left: 4px solid #20bf6b; }
        
        .room-card {
            background: white;
            border-radius: 12px;
            padding: 16px;
            margin: 10px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .room-name {
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 8px;
        }
        
        .room-stats {
            display: flex;
            justify-content: space-between;
            font-size: 0.85em;
            color: #666;
            margin-bottom: 8px;
        }
        
        .progress-bar-container {
            background: #f0f0f0;
            border-radius: 10px;
            height: 8px;
            overflow: hidden;
        }
        
        .progress-bar {
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        
        .progress-blue { background: linear-gradient(90deg, #5b9cf5, #4a8ee8); }
        .progress-orange { background: linear-gradient(90deg, #ff9f43, #ff8c2e); }
        .progress-green { background: linear-gradient(90deg, #26de81, #20bf6b); }
        .progress-pink { background: linear-gradient(90deg, #fc5c65, #eb3b5a); }
        .progress-purple { background: linear-gradient(90deg, #a55eea, #8854d0); }
        .progress-teal { background: linear-gradient(90deg, #20bf6b, #01a3a4); }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 style="color: #4f3b63;">Doyen Dashboard</h1>', unsafe_allow_html=True)

    st.markdown("""
    <style>
        div[data-baseweb="tab-list"] button {
            color: #000000 !important;
            font-weight: 800;
            font-size: 14px;
    }

        div[data-baseweb="tab-list"] button[aria-selected="true"] {
            color: #d61609 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Global Overview", "Validation"])

    
    with tab1:
        st.markdown('<p style="color: #764ba2; font-size: 22px; font-weight:bold;">Global Statistics</p>', unsafe_allow_html=True)
        
        rooms_count = get_count("exam_locations")
        exams_count = get_count("exams")
        profs_count = get_count("professors")
        students_count = get_count("students")
        
        col1, col2 = st.columns(2)
        
        with col1:
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); border-radius: 20px; padding: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); position: relative; overflow: hidden; margin-bottom: 20px;">
                <div style="position: absolute; top: -10px; right: -10px; width: 80px; height: 80px; background: #2196f3; border-radius: 50%; opacity: 0.3;"></div>
                <div style="display: flex; align-items: center; gap: 15px;">
                    <div style="background: #2196f3; width: 60px; height: 60px; border-radius: 15px; display: flex; align-items: center; justify-content: center; font-size: 30px; box-shadow: 0 4px 8px rgba(33, 150, 243, 0.3);"><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M120-120v-560h240v-80l120-120 120 120v240h240v400H120Zm80-80h80v-80h-80v80Zm0-160h80v-80h-80v80Zm0-160h80v-80h-80v80Zm240 320h80v-80h-80v80Zm0-160h80v-80h-80v80Zm0-160h80v-80h-80v80Zm0-160h80v-80h-80v80Zm240 480h80v-80h-80v80Zm0-160h80v-80h-80v80Z"/></svg></div>
                    <div>
                        <div style="color: #1976d2; font-size: 0.9em; font-weight: 500;">Total Rooms</div>
                        <div style="color: #0d47a1; font-size: 2.2em; font-weight: 700; margin-top: 5px;">{rooms_count}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f1f8e9 0%, #dcedc8 100%); border-radius: 20px; padding: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); position: relative; overflow: hidden;">
                <div style="position: absolute; top: -10px; right: -10px; width: 80px; height: 80px; background: #8bc34a; border-radius: 50%; opacity: 0.3;"></div>
                <div style="display: flex; align-items: center; gap: 15px;">
                    <div style="background: #8bc34a; width: 60px; height: 60px; border-radius: 15px; display: flex; align-items: center; justify-content: center; font-size: 30px; box-shadow: 0 4px 8px rgba(139, 195, 74, 0.3);"><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M40-160v-112q0-34 17.5-62.5T104-378q62-31 126-46.5T360-440q66 0 130 15.5T616-378q29 15 46.5 43.5T680-272v112H40Zm720 0v-120q0-44-24.5-84.5T666-434q51 6 96 20.5t84 35.5q36 20 55 44.5t19 53.5v120H760ZM360-480q-66 0-113-47t-47-113q0-66 47-113t113-47q66 0 113 47t47 113q0 66-47 113t-113 47Zm400-160q0 66-47 113t-113 47q-11 0-28-2.5t-28-5.5q27-32 41.5-71t14.5-81q0-42-14.5-81T544-792q14-5 28-6.5t28-1.5q66 0 113 47t47 113ZM120-240h480v-32q0-11-5.5-20T580-306q-54-27-109-40.5T360-360q-56 0-111 13.5T140-306q-9 5-14.5 14t-5.5 20v32Zm240-320q33 0 56.5-23.5T440-640q0-33-23.5-56.5T360-720q-33 0-56.5 23.5T280-640q0 33 23.5 56.5T360-560Zm0 320Zm0-400Z"/></svg></div>
                    <div>
                        <div style="color: #689f38; font-size: 0.9em; font-weight: 500;">Professors</div>
                        <div style="color: #33691e; font-size: 2.2em; font-weight: 700; margin-top: 5px;">{profs_count}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fce4ec 0%, #f8bbd0 100%); border-radius: 20px; padding: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); position: relative; overflow: hidden; margin-bottom: 20px;">
                <div style="position: absolute; top: -10px; right: -10px; width: 80px; height: 80px; background: #e91e63; border-radius: 50%; opacity: 0.3;"></div>
                <div style="display: flex; align-items: center; gap: 15px;">
                    <div style="background: #e91e63; width: 60px; height: 60px; border-radius: 15px; display: flex; align-items: center; justify-content: center; font-size: 30px; box-shadow: 0 4px 8px rgba(233, 30, 99, 0.3);"><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M680-80q-83 0-141.5-58.5T480-280q0-83 58.5-141.5T680-480q83 0 141.5 58.5T880-280q0 83-58.5 141.5T680-80Zm67-105 28-28-75-75v-112h-40v128l87 87Zm-547 65q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h167q11-35 43-57.5t70-22.5q40 0 71.5 22.5T594-840h166q33 0 56.5 23.5T840-760v250q-18-13-38-22t-42-16v-212h-80v120H280v-120h-80v560h212q7 22 16 42t22 38H200Zm280-640q17 0 28.5-11.5T520-800q0-17-11.5-28.5T480-840q-17 0-28.5 11.5T440-800q0 17 11.5 28.5T480-760Z"/></svg></div>
                    <div>
                        <div style="color: #c2185b; font-size: 0.9em; font-weight: 500;">Total Exams</div>
                        <div style="color: #880e4f; font-size: 2.2em; font-weight: 700; margin-top: 5px;">{exams_count}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%); border-radius: 20px; padding: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); position: relative; overflow: hidden;">
                <div style="position: absolute; top: -10px; right: -10px; width: 80px; height: 80px; background: #00bcd4; border-radius: 50%; opacity: 0.3;"></div>
                <div style="display: flex; align-items: center; gap: 15px;">
                    <div style="background: #00bcd4; width: 60px; height: 60px; border-radius: 15px; display: flex; align-items: center; justify-content: center; font-size: 30px; box-shadow: 0 4px 8px rgba(0, 188, 212, 0.3);"><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M0-240v-63q0-43 44-70t116-27q13 0 25 .5t23 2.5q-14 21-21 44t-7 48v65H0Zm240 0v-65q0-32 17.5-58.5T307-410q32-20 76.5-30t96.5-10q53 0 97.5 10t76.5 30q32 20 49 46.5t17 58.5v65H240Zm540 0v-65q0-26-6.5-49T754-397q11-2 22.5-2.5t23.5-.5q72 0 116 26.5t44 70.5v63H780Zm-455-80h311q-10-20-55.5-35T480-370q-55 0-100.5 15T325-320ZM160-440q-33 0-56.5-23.5T80-520q0-34 23.5-57t56.5-23q34 0 57 23t23 57q0 33-23 56.5T160-440Zm640 0q-33 0-56.5-23.5T720-520q0-34 23.5-57t56.5-23q34 0 57 23t23 57q0 33-23 56.5T800-440Zm-320-40q-50 0-85-35t-35-85q0-51 35-85.5t85-34.5q51 0 85.5 34.5T600-600q0 50-34.5 85T480-480Zm0-80q17 0 28.5-11.5T520-600q0-17-11.5-28.5T480-640q-17 0-28.5 11.5T440-600q0 17 11.5 28.5T480-560Zm1 240Zm-1-280Z"/></svg></div>
                    <div>
                        <div style="color: #0097a7; font-size: 0.9em; font-weight: 500;">Students</div>
                        <div style="color: #006064; font-size: 2.2em; font-weight: 700; margin-top: 5px;">{students_count}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        
        st.markdown('<p style="color: #764ba2; font-size: 22px; font-weight:bold;">Room Occupancy</p>', unsafe_allow_html=True)
        try:
            room_usage = pd.read_sql(
                """
                SELECT 
                    el.name AS room,
                    el.capacity,
                    COUNT(e.id) AS exams_scheduled
                FROM exam_locations el
                LEFT JOIN exams e ON e.room_id = el.id
                GROUP BY el.name, el.capacity
                ORDER BY exams_scheduled DESC
                """,
                engine
            )
            
            if room_usage.empty:
                st.info("No exams scheduled yet")
            else:
                colors = ['blue', 'orange', 'green', 'pink', 'purple', 'teal']
                
                for idx, row in room_usage.iterrows():
                    color = colors[idx % len(colors)]
                    max_exams = room_usage['exams_scheduled'].max() if room_usage['exams_scheduled'].max() > 0 else 1
                    percentage = (row['exams_scheduled'] / max_exams) * 100
                    
                    st.markdown(f"""
                    <div class="room-card">
                        <div class="room-name">📍 {row['room']}</div>
                        <div class="room-stats">
                            <span>Capacity: {row['capacity']}</span>
                            <span>Exams: {row['exams_scheduled']}</span>
                        </div>
                        <div class="progress-bar-container">
                            <div class="progress-bar progress-{color}" style="width: {percentage}%"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
        except Exception as e:
            st.error(f"Error fetching room usage: {str(e)}")
        
        st.markdown("---")
        
        st.markdown('<p style="color: #764ba2; font-size: 22px; font-weight:bold;">Conflicts by Department</p>', unsafe_allow_html=True)
        try:
            conflicts = pd.read_sql(
                """
                SELECT 
                    d.name AS department,
                    COUNT(*) AS conflicts
                FROM exams e1
                JOIN exams e2
                     ON e1.room_id = e2.room_id
                    AND e1.date_time = e2.date_time
                    AND e1.id < e2.id
                JOIN modules m ON e1.module_id = m.id
                JOIN formations f ON m.formation_id = f.id
                JOIN departments d ON f.dept_id = d.id
                GROUP BY d.name
                ORDER BY conflicts DESC
                """,
                engine
            )
            
            if conflicts.empty:
                st.success("No conflicts found!")
            else:
                st.dataframe(conflicts, use_container_width=True)
        except Exception as e:
            st.error(f"Error checking conflicts: {str(e)}")
        
        st.markdown("---")
        
        st.markdown('<p style="color: #764ba2; font-size: 22px; font-weight:bold;">Professor Workload</p>', unsafe_allow_html=True)
        try:
            prof_hours = pd.read_sql(
                """
                SELECT 
                    CONCAT(p.first_name, ' ', p.last_name) AS professor,
                    d.name AS department,
                    d.id AS dept_id,
                    COUNT(e.id) AS exams_supervised
                FROM professors p
                JOIN departments d ON p.dept_id = d.id
                LEFT JOIN exams e ON e.prof_id = p.id
                GROUP BY professor, d.name, d.id
                ORDER BY d.name, exams_supervised DESC
                """,
                engine
            )
            
            if prof_hours.empty:
                st.info("No professor workload data available")
            else:
                departments_list = prof_hours['department'].unique()
                
                for dept in departments_list:
                    dept_data = prof_hours[prof_hours['department'] == dept].copy()
                    
                   # st.markdown(f'<p style="color: #666; font-size: 0.80em; text-align: center;">{dept} Department Workload</p>', unsafe_allow_html=True)

                    chart_cols = st.columns(len(dept_data))
                    
                    max_exams = dept_data['exams_supervised'].max() if dept_data['exams_supervised'].max() > 0 else 1
                    colors = ['#5b9cf5', '#66c9db', "#2f5f7f", '#8ab4d6', "#f19832", '#4a90b8']
                    
                    for idx, (col, (_, prof_row)) in enumerate(zip(chart_cols, dept_data.iterrows())):
                        with col:
                            color = colors[idx % len(colors)]
                            height_percentage = (prof_row['exams_supervised'] / max_exams) * 100
                            
                            bar_height = int((height_percentage / 100) * 200)
                            
                            name_parts = prof_row['professor'].split()
                            short_name = f"{name_parts[0][:1]}. {name_parts[-1]}" if len(name_parts) > 1 else prof_row['professor']
                            
                            st.markdown(f"""
                            <div style="display: flex; flex-direction: column; align-items: center; margin: 10px 0;">
                                <div style="display: flex; flex-direction: column; justify-content: flex-end; height: 220px; align-items: center;">
                                    <div style="font-weight: 600; color: #333; margin-bottom: 5px; font-size: 1.1em;">
                                        {prof_row['exams_supervised']}
                                    </div>
                                    <div style="
                                        width: 50px;
                                        height: {bar_height}px;
                                        background: linear-gradient(180deg, {color}, {color}dd);
                                        border-radius: 8px 8px 0 0;
                                        transition: all 0.3s ease;
                                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                                    "></div>
                                </div>
                                <div style="
                                    width: 70px;
                                    height: 2px;
                                    background: #e0e0e0;
                                    margin: 0;
                                "></div>
                                <div style="
                                    margin-top: 8px;
                                    font-size: 0.75em;
                                    color: #666;
                                    text-align: center;
                                    word-wrap: break-word;
                                    width: 70px;
                                ">
                                    {short_name}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    st.markdown(f'<p style="color: #666; font-size: 0.80em; text-align: center;">{dept} Department Workload</p>', unsafe_allow_html=True)

                    
        except Exception as e:
            st.error(f"Error fetching professor workload: {str(e)}")
    
    with tab2:
        st.markdown('<p style="color: #764ba2; font-size: 22px; font-weight:bold;">Formation Exams Validation</p>', unsafe_allow_html=True)
        
        try:
            departments = pd.read_sql("SELECT id, name FROM departments ORDER BY name", engine)
            dept_name = st.selectbox("Select Department", departments["name"])
            dept_id = int(departments[departments.name == dept_name].iloc[0].id)
            
            formations = pd.read_sql(
                text("SELECT id, name, validation_status FROM formations WHERE dept_id = :did ORDER BY name"),
                engine,
                params={"did": dept_id}
            )
            
            if formations.empty:
                st.warning("No formations in this department")
                st.stop()
            
            form_name = st.selectbox("", formations["name"])
            form_row = formations[formations.name == form_name].iloc[0]
            form_id = int(form_row.id)
            validation_state = form_row.validation_status
            
            st.markdown("---")
            status_html = f'<span class="status-{validation_state}">Status: {validation_state.upper()}</span>'
            st.markdown(status_html, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown('<p style="color: #764ba2; font-size: 22px; font-weight:bold;">Exams Schedule</p>', unsafe_allow_html=True)
            
            exam_schedule_raw = pd.read_sql(
                text("""
                    SELECT 
                        e.date_time::date AS date,
                        e.date_time::time AS time,
                        m.name AS module,
                        el.name AS room,
                        CONCAT(p.first_name, ' ', p.last_name) AS professor,
                        e.id AS exam_id
                    FROM exams e
                    JOIN modules m ON e.module_id = m.id
                    JOIN exam_locations el ON e.room_id = el.id
                    JOIN professors p ON e.prof_id = p.id
                    WHERE m.formation_id = :fid
                    ORDER BY e.date_time
                """),
                engine,
                params={"fid": form_id}
            )
            
            if exam_schedule_raw.empty:
                st.info("No schedule available yet")
            else:
                exam_schedule = exam_schedule_raw.copy()
                exam_schedule['slot_key'] = (
                    exam_schedule['date'].astype(str) + '_' + 
                    exam_schedule['time'].astype(str) + '_' + 
                    exam_schedule['module']
                )
                exam_schedule['group_num'] = exam_schedule.groupby('slot_key').cumcount() + 1
                
                unique_dates = sorted(exam_schedule['date'].unique())
                colors = ['blue', 'orange', 'green', 'pink', 'purple', 'teal']
                
                cols = st.columns(min(len(unique_dates), 7))
                
                for col_idx, exam_date in enumerate(unique_dates[:7]):
                    with cols[col_idx]:
                        day_name = pd.to_datetime(exam_date).strftime('%a')
                        day_num = pd.to_datetime(exam_date).strftime('%d')
                        
                        st.markdown(f"""
                        <div class="day-header">
                            <div class="day-name">{day_name}</div>
                            <div class="day-date">{day_num}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        day_exams = exam_schedule[exam_schedule['date'] == exam_date]
                        
                        if day_exams.empty:
                            st.markdown('<div class="no-exam">No exams</div>', unsafe_allow_html=True)
                        else:
                            for idx, exam in day_exams.iterrows():
                                color_idx = hash(exam['module']) % len(colors)
                                card_class = f"exam-card-{colors[color_idx]}"
                                time_str = str(exam['time'])[:5]
                                
                                st.markdown(f"""
                                <div class="time-slot {card_class}">
                                    <div class="exam-time">
                                        <span>🕐</span>
                                        <span>{time_str}</span>
                                    </div>
                                    <div class="exam-module">{exam['module']}</div>
                                    <div class="exam-prof">
                                        <span><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M480-480q-66 0-113-47t-47-113q0-66 47-113t113-47q66 0 113 47t47 113q0 66-47 113t-113 47ZM160-160v-112q0-34 17.5-62.5T224-378q62-31 126-46.5T480-440q66 0 130 15.5T736-378q29 15 46.5 43.5T800-272v112H160Zm80-80h480v-32q0-11-5.5-20T700-306q-54-27-109-40.5T480-360q-56 0-111 13.5T260-306q-9 5-14.5 14t-5.5 20v32Zm240-320q33 0 56.5-23.5T560-640q0-33-23.5-56.5T480-720q-33 0-56.5 23.5T400-640q0 33 23.5 56.5T480-560Zm0-80Zm0 400Z"/></svg></span>
                                        <span>{exam['professor']}</span>
                                    </div>
                                    <div class="exam-room">
                                        <span>📍</span>
                                        <span>{exam['room']}</span>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                
                st.markdown("---")
            
            st.markdown('<p style="color: #764ba2; font-size: 22px; font-weight:bold;">Actions</p>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Approve Schedule", type="primary", use_container_width=True):
                    try:
                        with engine.begin() as conn:
                            conn.execute(
                                text("UPDATE formations SET validation_status = 'approved' WHERE id = :fid"),
                                {"fid": form_id}
                            )
                        st.success("Schedule approved successfully!")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error approving schedule: {str(e)}")
            
            with col2:
                if st.button("Reject Schedule", type="secondary", use_container_width=True):
                    try:
                        with engine.begin() as conn:
                            conn.execute(
                                text("UPDATE formations SET validation_status = 'rejected' WHERE id = :fid"),
                                {"fid": form_id}
                            )
                        st.error("Schedule rejected!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error rejecting schedule: {str(e)}")
        
        except Exception as e:
            st.error(f"Error in validation tab: {str(e)}")


elif st.session_state.role == "student":

    #image = Image.open("logo.png")

    def display_calendar_week(exam_schedule, dates):
    
        cols = st.columns(len(dates))
    
        colors = ['blue', 'orange', 'green', 'pink', 'purple', 'teal']
    
        for col_idx, exam_date in enumerate(dates):
            with cols[col_idx]:
                day_name = pd.to_datetime(exam_date).strftime('%a')
                day_num = pd.to_datetime(exam_date).strftime('%d')
            
                st.markdown(f"""
                <div class="day-header">
                    <div class="day-name">{day_name}</div>
                    <div class="day-date">{day_num}</div>
                </div>
                """, unsafe_allow_html=True)
            
                day_exams = exam_schedule[exam_schedule['date'] == exam_date]
            
                if day_exams.empty:
                    st.markdown('<div class="no-exam">No exams</div>', unsafe_allow_html=True)
                else:
                    for idx, exam in day_exams.iterrows():
                        color_idx = hash(exam['module']) % len(colors)
                        card_class = f"exam-card-{colors[color_idx]}"
                    
                        time_str = str(exam['time'])[:5]
                    
                        st.markdown(f"""
                        <div class="time-slot {card_class}">
                            <div class="exam-time">
                                <span>🕐</span>
                                <span>{time_str}</span>
                            </div>
                            <div class="exam-module">{exam['module']}</div>
                            <div class="exam-group">
                                <span><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M0-240v-63q0-43 44-70t116-27q13 0 25 .5t23 2.5q-14 21-21 44t-7 48v65H0Zm240 0v-65q0-32 17.5-58.5T307-410q32-20 76.5-30t96.5-10q53 0 97.5 10t76.5 30q32 20 49 46.5t17 58.5v65H240Zm540 0v-65q0-26-6.5-49T754-397q11-2 22.5-2.5t23.5-.5q72 0 116 26.5t44 70.5v63H780Zm-455-80h311q-10-20-55.5-35T480-370q-55 0-100.5 15T325-320ZM160-440q-33 0-56.5-23.5T80-520q0-34 23.5-57t56.5-23q34 0 57 23t23 57q0 33-23 56.5T160-440Zm640 0q-33 0-56.5-23.5T720-520q0-34 23.5-57t56.5-23q34 0 57 23t23 57q0 33-23 56.5T800-440Zm-320-40q-50 0-85-35t-35-85q0-51 35-85.5t85-34.5q51 0 85.5 34.5T600-600q0 50-34.5 85T480-480Zm0-80q17 0 28.5-11.5T520-600q0-17-11.5-28.5T480-640q-17 0-28.5 11.5T440-600q0 17 11.5 28.5T480-560Zm1 240Zm-1-280Z"/></svg></span>
                                <span>Group G{exam['group_num']}</span>
                            </div>
                            <div class="exam-room">
                                <span>📍</span>
                                <span>{exam['room']}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)



    st.markdown("""
    <style>
        .stApp {
            background-color: #f5f5f7;
        }
        
        .day-header {
            background-color: #f5f5f7;
            color: #333;
            padding: 10px;
            text-align: center;
            font-weight: 600;
            border-bottom: 2px solid #e0e0e0;
            margin-bottom: 10px;
        }
        
        .day-name {
            font-size: 0.85em;
            color: #888;
            margin-bottom: 3px;
        }
        
        .day-date {
            font-size: 1.8em;
            font-weight: bold;
            color: #333;
        }
        
        .time-slot {
            background: white;
            border-radius: 12px;
            padding: 14px;
            margin: 10px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            transition: all 0.2s ease;
        }
        
        .time-slot:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        .exam-time {
            font-size: 0.85em;
            color: #666;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .exam-module {
            font-size: 0.95em;
            color: #1a1a1a;
            font-weight: 600;
            margin: 8px 0;
            line-height: 1.3;
        }
        
        .exam-group {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 0.85em;
            color: #666;
            margin: 5px 0;
        }
        
        .exam-room {
            color: #666;
            font-size: 0.85em;
            margin-top: 8px;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .no-exam {
            background: transparent;
            color: #ccc;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
        }
        
        .exam-card-blue { border-left: 4px solid #5b9cf5; }
        .exam-card-orange { border-left: 4px solid #ff9f43; }
        .exam-card-green { border-left: 4px solid #26de81; }
        .exam-card-pink { border-left: 4px solid #fc5c65; }
        .exam-card-purple { border-left: 4px solid #a55eea; }
        .exam-card-teal { border-left: 4px solid #20bf6b; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
       .fixed-box-top-center {
       position: relative;
       top: 0px;                    
       left: 50%;                    
       transform: translateX(-50%);  
       width: 100%;                   
       height: 80px;                
       padding: 20px;
       background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

       border-radius: 15px;
       box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
       z-index: 999;
                
       display: flex;           
       justify-content: center; 
       align-items: center;     
    }
                
    .fixed-box-top-center h1 {    
    
       text-shadow: 2px 2px 4px rgba(0,0,0,0.1); 
               
    }
}
    </style> 
                 

    """, unsafe_allow_html=True)
    


    st.markdown('<h1 style="color: #4f3b63 ;"> Student Dashboard</h1>', unsafe_allow_html=True)
    
    try:
        
        st.markdown('<p style="color: #764ba2; font-size: 22px; font-weight:bold;">Select Your Department and Formation</p>', unsafe_allow_html=True)
        departments = pd.read_sql("SELECT id, name FROM departments ORDER BY name", engine)
        dept_name = st.selectbox("", departments["name"])
        dept_id = int(departments[departments.name == dept_name].iloc[0].id)
        
       
        formations = pd.read_sql(
            text("SELECT id, name FROM formations WHERE dept_id = :did ORDER BY name"),
            engine,
            params={"did": dept_id}
        )
        
        if formations.empty:
            st.error("No formations in this department.")
            st.stop()
        
        form_name = st.selectbox("", formations["name"])
        form_id = int(formations[formations.name == form_name].iloc[0].id)
        
        st.success(f" You study: **{form_name}** — **{dept_name}**")
        
        st.markdown("---")
        
        
        all_students = pd.read_sql(
            text("""
                SELECT id, first_name, last_name
                FROM students
                WHERE formation_id = :fid
                ORDER BY id
            """),
            engine,
            params={"fid": form_id}
        )
        
        if all_students.empty:
            st.warning("No students registered.")
            st.stop()
        
        
        num_students = len(all_students)
        num_groups = (num_students // 20) + (1 if num_students % 20 else 0)
        
        
    
        st.markdown('<h1 style="color: #4f3b63 ;"> Exams Schedule</h1>', unsafe_allow_html=True)

        exam_schedule_raw = pd.read_sql(
            text("""
                SELECT 
                    e.date_time::date AS date,
                    e.date_time::time AS time,
                    m.name AS module,
                    el.name AS room,
                    e.id AS exam_id
                FROM exams e
                JOIN modules m ON e.module_id = m.id
                JOIN formations f ON m.formation_id = f.id
                JOIN exam_locations el ON e.room_id = el.id
                WHERE m.formation_id = :fid
                   AND f.validation_status = 'approved'
                ORDER BY e.date_time
            """),
            engine,
            params={"fid": form_id}
        )
        
        if exam_schedule_raw.empty:
            st.info("Your department has not published the exam schedule yet. Please check again later.")
        else:
            exam_schedule = exam_schedule_raw.copy()
            
            exam_schedule['slot_key'] = (
                exam_schedule['date'].astype(str) + '_' + 
                exam_schedule['time'].astype(str) + '_' + 
                exam_schedule['module']
            )
            
            exam_schedule['group_num'] = exam_schedule.groupby('slot_key').cumcount() + 1
            
            
            st.markdown("""
            <style>
            div[data-baseweb="tab-list"] button {
                color: #393b40;          
                font-weight: 800;
                font-size: 14px;
            }

            div[data-baseweb="tab-list"] button[aria-selected="true"] {
                color:#d61609 ;        
            }
            </style>
            """, unsafe_allow_html=True)


            unique_dates = sorted(exam_schedule['date'].unique())
            
            if len(unique_dates) > 7:
                weeks = []
                for i in range(0, len(unique_dates), 7):
                    weeks.append(unique_dates[i:i+7])
                
                tabs = st.tabs([f"Week {i+1}" for i in range(len(weeks))])
                
                for tab, week_dates in zip(tabs, weeks):
                    with tab:
                        display_calendar_week(exam_schedule, week_dates)
            else:
                display_calendar_week(exam_schedule, unique_dates)
            
            st.markdown("---")
            
            
            csv = exam_schedule[['date', 'time', 'module', 'group_num', 'room']].to_csv(index=False)
            st.download_button(
                label="Download Schedule as CSV",
                data=csv,
                file_name=f"exam_schedule_{form_name}.csv",
                mime="text/csv",
                use_container_width=True
            )

            
        st.markdown("""
        <style>
            .group-button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px 24px;
                border-radius: 10px;
                border: none;
                font-weight: 600;
                font-size: 1em;
                cursor: pointer;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
            }
    
           .group-button:hover {
               transform: translateY(-2px);
               box-shadow: 0 6px 12px rgba(0,0,0,0.15);
           }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("""
        <style>
                    
            .groups-container {
                display: flex;
                flex-direction: column;
                align-items: center;  
                gap: 12px;            
            }      
            .group-card {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 15px;
                width: 70%;          
                margin-bottom: 12px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.05);
                    
            }

           .group-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                font-weight: bold;
                padding: 8px 12px;
                border-radius: 8px;
                margin-bottom: 10px;
                width: 70%;         

            }

            .student-row {
                padding: 6px 10px;
                width: 70%;          
                border-bottom: 1px solid #e0e0e0;
                transition: background 0.2s, transform 0.15s;
            }

            .student-row:nth-child(even) {
                background-color: white;
            }

            .student-row:nth-child(odd) {
                background-color: #f8f9fa;
            }

            .student-row:hover {
                background-color: #f0f0f5;
                transform: scale(1.01);
            }

            .student-name {
                display: inline-block;
                color: #333;
                margin-left: 6px;
            }
        </style>
        """, unsafe_allow_html=True)

        #st.markdown('<h1 style="color: #4f3b63 ;"> Find Your Group</h1>', unsafe_allow_html=True)
        st.markdown('<p style="color: #764ba2; font-size: 22px; font-weight:bold;">Find Your Exam Group</p>', unsafe_allow_html=True)


        st.markdown('<div class="groups-container">', unsafe_allow_html=True)
        for g in range(1, num_groups + 1):
                group_start = (g - 1) * 20

                group_students = pd.read_sql(
                    text("""
                        SELECT id, first_name, last_name
                        FROM students
                        WHERE formation_id = :fid
                        ORDER BY id
                        LIMIT 20 OFFSET :offset
                    """),
                    engine,
                    params={"fid": form_id, "offset": group_start}
                )

                st.markdown(f'<div class="group-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="group-header">Group G{g}</div>', unsafe_allow_html=True)

                for idx, student in group_students.iterrows():
                 st.markdown(
                    f'<div class="student-row"><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#999999"><path d="M480-480q-66 0-113-47t-47-113q0-66 47-113t113-47q66 0 113 47t47 113q0 66-47 113t-113 47ZM160-160v-112q0-34 17.5-62.5T224-378q62-31 126-46.5T480-440q66 0 130 15.5T736-378q29 15 46.5 43.5T800-272v112H160Zm80-80h480v-32q0-11-5.5-20T700-306q-54-27-109-40.5T480-360q-56 0-111 13.5T260-306q-9 5-14.5 14t-5.5 20v32Zm240-320q33 0 56.5-23.5T560-640q0-33-23.5-56.5T480-720q-33 0-56.5 23.5T400-640q0 33 23.5 56.5T480-560Zm0-80Zm0 400Z"/></svg> <span class="student-name">{student["first_name"]} {student["last_name"]}</span></div>',
                    unsafe_allow_html=True
                 )
                st.markdown('</div>', unsafe_allow_html=True)  

        st.markdown('</div>', unsafe_allow_html=True)  

        
    
    except Exception as e:
        st.error(f"Error in student dashboard: {str(e)}")


    

elif st.session_state.role == "professor":
    
    st.markdown("""
    <style>
        
        .stApp {
            background-color: #f5f5f7;
        }
        
        .day-header {
            background-color: #f5f5f7;
            color: #333;
            padding: 10px;
            text-align: center;
            font-weight: 600;
            border-bottom: 2px solid #e0e0e0;
            margin-bottom: 10px;
        }
        
        .day-name {
            font-size: 0.85em;
            color: #888;
            margin-bottom: 3px;
        }
        
        .day-date {
            font-size: 1.8em;
            font-weight: bold;
            color: #333;
        }
        
        .time-slot {
            background: white;
            border-radius: 12px;
            padding: 14px;
            margin: 10px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            transition: all 0.2s ease;
        }
        
        .time-slot:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        .exam-time {
            font-size: 0.85em;
            color: #666;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .exam-module {
            font-size: 0.95em;
            color: #1a1a1a;
            font-weight: 600;
            margin: 8px 0;
            line-height: 1.3;
        }
        
        .exam-formation {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 0.85em;
            color: #666;
            margin: 5px 0;
        }
        
        .exam-room {
            color: #666;
            font-size: 0.85em;
            margin-top: 8px;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .no-exam {
            background: transparent;
            color: #ccc;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
        }
        
        .exam-card-blue { border-left: 4px solid #5b9cf5; }
        .exam-card-orange { border-left: 4px solid #ff9f43; }
        .exam-card-green { border-left: 4px solid #26de81; }
        .exam-card-pink { border-left: 4px solid #fc5c65; }
        .exam-card-purple { border-left: 4px solid #a55eea; }
        .exam-card-teal { border-left: 4px solid #20bf6b; }
        
        div[data-baseweb="tab-list"] button {
            color: #393b40;
            font-weight: 800;
            font-size: 14px;
        }

        div[data-baseweb="tab-list"] button[aria-selected="true"] {
            color:#d61609;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 style="color: #4f3b63;">Professor Dashboard</h1>', unsafe_allow_html=True)
    
    prof_id = st.session_state.user_id
    
    try:
        prof_info = pd.read_sql(
            text("""
                SELECT p.first_name, p.last_name, d.name AS department
                FROM professors p
                JOIN departments d ON p.dept_id = d.id
                WHERE p.id = :pid
            """),
            engine,
            params={"pid": prof_id}
        )
        
        if not prof_info.empty:
            prof = prof_info.iloc[0]
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f1f8e9 0%, #dcedc8 100%); border-radius: 20px; padding: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px;">
                <div style="display: flex; align-items: center; gap: 15px;">
                    <div style="background: #8bc34a; width: 60px; height: 60px; border-radius: 15px; display: flex; align-items: center; justify-content: center; font-size: 30px; box-shadow: 0 4px 8px rgba(139, 195, 74, 0.3);"><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M480-480q-66 0-113-47t-47-113q0-66 47-113t113-47q66 0 113 47t47 113q0 66-47 113t-113 47ZM160-160v-112q0-34 17.5-62.5T224-378q62-31 126-46.5T480-440q66 0 130 15.5T736-378q29 15 46.5 43.5T800-272v112H160Zm80-80h480v-32q0-11-5.5-20T700-306q-54-27-109-40.5T480-360q-56 0-111 13.5T260-306q-9 5-14.5 14t-5.5 20v32Zm240-320q33 0 56.5-23.5T560-640q0-33-23.5-56.5T480-720q-33 0-56.5 23.5T400-640q0 33 23.5 56.5T480-560Zm0-80Zm0 400Z"/></svg></div>
                    <div>
                        <div style="color: #689f38; font-size: 0.9em; font-weight: 500;">Professor</div>
                        <div style="color: #33691e; font-size: 1.5em; font-weight: 700; margin-top: 5px;">{prof['first_name']} {prof['last_name']}</div>
                        <div style="color: #689f38; font-size: 0.9em; margin-top: 5px;">Department: {prof['department']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            prof_schedule = pd.read_sql(
                text("""
                    SELECT 
                        e.date_time::date AS date,
                        e.date_time::time AS time,
                        m.name AS module,
                        f.name AS formation,
                        d.name AS department,
                        el.name AS room,
                        el.capacity
                    FROM exams e
                    JOIN modules m ON e.module_id = m.id
                    JOIN formations f ON m.formation_id = f.id
                    JOIN departments d ON f.dept_id = d.id
                    JOIN exam_locations el ON e.room_id = el.id
                    WHERE e.prof_id = :pid
                       AND f.validation_status = 'approved'
                    ORDER BY e.date_time
                """),
                engine,
                params={"pid": prof_id}
            )
            
            if prof_schedule.empty:
                st.info("You don't have any assigned exams yet.")
            else:
                st.markdown('<p style="color: #764ba2; font-size: 22px; font-weight:bold;">Statistics</p>', unsafe_allow_html=True)
                
                unique_dates = prof_schedule['date'].nunique()
                unique_modules = prof_schedule['module'].nunique()
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #fce4ec 0%, #f8bbd0 100%); border-radius: 15px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center;">
                        <div style="color: #c2185b; font-size: 0.85em; font-weight: 500;">Total Exams</div>
                        <div style="color: #880e4f; font-size: 2em; font-weight: 700; margin-top: 8px;"> {len(prof_schedule)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); border-radius: 15px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center;">
                        <div style="color: #1976d2; font-size: 0.85em; font-weight: 500;">Exam Days</div>
                        <div style="color: #0d47a1; font-size: 2em; font-weight: 700; margin-top: 8px;"> {unique_dates}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #f1f8e9 0%, #dcedc8 100%); border-radius: 15px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center;">
                        <div style="color: #689f38; font-size: 0.85em; font-weight: 500;">Different Modules</div>
                        <div style="color: #33691e; font-size: 2em; font-weight: 700; margin-top: 8px;"> {unique_modules}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                st.markdown('<p style="color: #764ba2; font-size: 22px; font-weight:bold;">Your Exam Supervision Schedule</p>', unsafe_allow_html=True)
                
                unique_dates_list = sorted(prof_schedule['date'].unique())
                colors = ['blue', 'orange', 'green', 'pink', 'purple', 'teal']
                
                if len(unique_dates_list) > 7:
                    weeks = []
                    for i in range(0, len(unique_dates_list), 7):
                        weeks.append(unique_dates_list[i:i+7])
                    
                    tabs = st.tabs([f"Week {i+1}" for i in range(len(weeks))])
                    
                    for tab, week_dates in zip(tabs, weeks):
                        with tab:
                            cols = st.columns(len(week_dates))
                            
                            for col_idx, exam_date in enumerate(week_dates):
                                with cols[col_idx]:
                                    day_name = pd.to_datetime(exam_date).strftime('%a')
                                    day_num = pd.to_datetime(exam_date).strftime('%d')
                                    
                                    st.markdown(f"""
                                    <div class="day-header">
                                        <div class="day-name">{day_name}</div>
                                        <div class="day-date">{day_num}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    day_exams = prof_schedule[prof_schedule['date'] == exam_date]
                                    
                                    if day_exams.empty:
                                        st.markdown('<div class="no-exam">No exams</div>', unsafe_allow_html=True)
                                    else:
                                        for idx, exam in day_exams.iterrows():
                                            color_idx = hash(exam['module']) % len(colors)
                                            card_class = f"exam-card-{colors[color_idx]}"
                                            time_str = str(exam['time'])[:5]
                                            
                                            st.markdown(f"""
                                            <div class="time-slot {card_class}">
                                                <div class="exam-time">
                                                    <span>🕐</span>
                                                    <span>{time_str}</span>
                                                </div>
                                                <div class="exam-module">{exam['module']}</div>
                                                <div class="exam-formation">
                                                    <span><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M0-240v-63q0-43 44-70t116-27q13 0 25 .5t23 2.5q-14 21-21 44t-7 48v65H0Zm240 0v-65q0-32 17.5-58.5T307-410q32-20 76.5-30t96.5-10q53 0 97.5 10t76.5 30q32 20 49 46.5t17 58.5v65H240Zm540 0v-65q0-26-6.5-49T754-397q11-2 22.5-2.5t23.5-.5q72 0 116 26.5t44 70.5v63H780Zm-455-80h311q-10-20-55.5-35T480-370q-55 0-100.5 15T325-320ZM160-440q-33 0-56.5-23.5T80-520q0-34 23.5-57t56.5-23q34 0 57 23t23 57q0 33-23 56.5T160-440Zm640 0q-33 0-56.5-23.5T720-520q0-34 23.5-57t56.5-23q34 0 57 23t23 57q0 33-23 56.5T800-440Zm-320-40q-50 0-85-35t-35-85q0-51 35-85.5t85-34.5q51 0 85.5 34.5T600-600q0 50-34.5 85T480-480Zm0-80q17 0 28.5-11.5T520-600q0-17-11.5-28.5T480-640q-17 0-28.5 11.5T440-600q0 17 11.5 28.5T480-560Zm1 240Zm-1-280Z"/></svg></span>
                                                    <span>{exam['formation']}</span>
                                                </div>
                                                <div class="exam-room">
                                                    <span>📍</span>
                                                    <span>{exam['room']}</span>
                                                </div>
                                            </div>
                                            """, unsafe_allow_html=True)
                else:
                    cols = st.columns(len(unique_dates_list))
                    
                    for col_idx, exam_date in enumerate(unique_dates_list):
                        with cols[col_idx]:
                            day_name = pd.to_datetime(exam_date).strftime('%a')
                            day_num = pd.to_datetime(exam_date).strftime('%d')
                            
                            st.markdown(f"""
                            <div class="day-header">
                                <div class="day-name">{day_name}</div>
                                <div class="day-date">{day_num}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            day_exams = prof_schedule[prof_schedule['date'] == exam_date]
                            
                            if day_exams.empty:
                                st.markdown('<div class="no-exam">No exams</div>', unsafe_allow_html=True)
                            else:
                                for idx, exam in day_exams.iterrows():
                                    color_idx = hash(exam['module']) % len(colors)
                                    card_class = f"exam-card-{colors[color_idx]}"
                                    time_str = str(exam['time'])[:5]
                                    
                                    st.markdown(f"""
                                    <div class="time-slot {card_class}">
                                        <div class="exam-time">
                                            <span>🕐</span>
                                            <span>{time_str}</span>
                                        </div>
                                        <div class="exam-module">{exam['module']}</div>
                                        <div class="exam-formation">
                                            <span><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M0-240v-63q0-43 44-70t116-27q13 0 25 .5t23 2.5q-14 21-21 44t-7 48v65H0Zm240 0v-65q0-32 17.5-58.5T307-410q32-20 76.5-30t96.5-10q53 0 97.5 10t76.5 30q32 20 49 46.5t17 58.5v65H240Zm540 0v-65q0-26-6.5-49T754-397q11-2 22.5-2.5t23.5-.5q72 0 116 26.5t44 70.5v63H780Zm-455-80h311q-10-20-55.5-35T480-370q-55 0-100.5 15T325-320ZM160-440q-33 0-56.5-23.5T80-520q0-34 23.5-57t56.5-23q34 0 57 23t23 57q0 33-23 56.5T160-440Zm640 0q-33 0-56.5-23.5T720-520q0-34 23.5-57t56.5-23q34 0 57 23t23 57q0 33-23 56.5T800-440Zm-320-40q-50 0-85-35t-35-85q0-51 35-85.5t85-34.5q51 0 85.5 34.5T600-600q0 50-34.5 85T480-480Zm0-80q17 0 28.5-11.5T520-600q0-17-11.5-28.5T480-640q-17 0-28.5 11.5T440-600q0 17 11.5 28.5T480-560Zm1 240Zm-1-280Z"/></svg></span>
                                            <span>{exam['formation']}</span>
                                        </div>
                                        <div class="exam-room">
                                            <span>📍</span>
                                            <span>{exam['room']}</span>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                csv = prof_schedule.to_csv(index=False)
                st.download_button(
                    label="Download My Schedule as CSV",
                    data=csv,
                    file_name=f"professor_schedule_{prof_id}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    
    except Exception as e:
        st.error(f"Error in professor dashboard: {str(e)}")