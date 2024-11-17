import streamlit as st
import requests
from datetime import datetime
from fpdf import FPDF
import time

# Page config with custom CSS
st.set_page_config(
    page_title="ZecoED Assessment System",
    page_icon="🎓",
    layout="wide"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stButton button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-weight: 600;
    }
    .css-1d391kg {
        padding: 2rem;
        border-radius: 15px;
    }
    .stAlert {
        padding: 1rem;
        border-radius: 10px;
    }
    div[data-testid="stSelectbox"] {
        border-radius: 10px;
    }
    div[data-testid="stNumberInput"] {
        border-radius: 10px;
    }
    .exam-preview {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #dee2e6;
    }
    .sidebar-content {
        padding: 20px;
        background-color: #f8f9fa;
        border-radius: 10px;
        margin: 10px 0;
    }
    .subject-card {
        padding: 20px;
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# Enhanced mock database with more user details
users_db = {
    'teacher1': {
        'password': 'pass123',
        'type': 'teacher',
        'name': 'John Smith',
        'subjects': ['Mathematics', 'Physics'],
        'avatar': '👨‍🏫'
    },
    'student1': {
        'password': 'pass123',
        'type': 'student',
        'name': 'Jane Doe',
        'class': 'Form 3',
        'avatar': '👩‍🎓'
    }
}

# Enhanced subject categories
SUBJECT_CATEGORIES = {
    'Sciences': ['Mathematics', 'Biology', 'Chemistry', 'Physics'],
    'Languages': ['English', 'Kiswahili', 'French', 'German'],
    'Humanities': ['Geography', 'History', 'CRE', 'IRE'],
    'Technical': ['Computer Studies', 'Business Studies', 'Agriculture'],
    'Arts': ['Art and Design', 'Music', 'Home Science']
}

CLASSES = ['Form 1', 'Form 2', 'Form 3', 'Form 4']

# Flatten subjects for selection
SUBJECTS = [subject for category in SUBJECT_CATEGORIES.values() for subject in category]

def handle_login(username, password):
    """Enhanced login handler with loading animation"""
    if username in users_db and users_db[username]['password'] == password:
        with st.spinner('Logging in...'):
            time.sleep(1)  # Simulate loading
            st.session_state.logged_in = True
            st.session_state.user_type = users_db[username]['type']
            st.session_state.user_data = {
                'username': username,
                'name': users_db[username]['name'],
                'avatar': users_db[username]['avatar']
            }
        return True
    return False



def generate_questions_rapidapi(subject, class_level, paper=None, num_questions=10):
    """Generate exam questions with enhanced error handling and progress tracking"""
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Update progress
        status_text.text("Initializing question generation...")
        progress_bar.progress(20)
        time.sleep(0.5)

        url = "https://chatgpt-api8.p.rapidapi.com/"
        paper_info = f" (Paper {paper})" if paper else ""

        status_text.text("Preparing prompt...")
        progress_bar.progress(40)
        time.sleep(0.5)

        prompt = f"""Generate {num_questions} multiple choice questions for {subject}{paper_info} for {class_level}.
        Each question should follow this format:
        1. Question text
        2. Four options labeled A, B, C, D
        3. Correct answer letter
        4. Brief explanation

        Make the questions challenging but appropriate for the level.
        Ensure a mix of conceptual understanding and problem-solving.
        """

        payload = [
            {
                "content": "You are an experienced education professional creating high-quality exam questions.",
                "role": "system"
            },
            {
                "content": prompt,
                "role": "user"
            }
        ]

        headers = {
            "x-rapidapi-key": "d26bbb724amshab9f9f59d682630p1a4c64jsn59c5579eaef8",
            "x-rapidapi-host": "chatgpt-api8.p.rapidapi.com",
            "Content-Type": "application/json"
        }

        status_text.text("Generating questions...")
        progress_bar.progress(60)
        
        response = requests.post(url, json=payload, headers=headers)
        progress_bar.progress(80)
        
        if response.status_code == 200:
            response_data = response.json()
            if isinstance(response_data, dict) and "text" in response_data:
                status_text.text("Processing results...")
                progress_bar.progress(100)
                time.sleep(0.5)
                status_text.empty()
                progress_bar.empty()
                return response_data["text"]
        
        st.error("Failed to generate questions. Please try again.")
        return None

    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None
    
def split_questions_and_answers(raw_text):
    """
    Split raw text into questions and answers sections with enhanced formatting.
    
    Args:
        raw_text (str): Raw text containing both questions and answers
        
    Returns:
        tuple: (questions_text, answers_text)
    """
    try:
        questions = []
        answers = []
        current_question = []
        current_answer = []
        
        # Split into lines and process
        lines = raw_text.split('\n')
        in_answer_section = False
        
        for line in lines:
            line = line.strip()
            if not line:  # Skip empty lines
                continue
                
            # Check for answer/explanation markers
            if any(marker in line.lower() for marker in ['correct answer:', 'explanation:', 'answer key:']):
                if current_question:
                    questions.append('\n'.join(current_question))
                    current_question = []
                in_answer_section = True
                current_answer.append(line)
            elif line.lower().startswith(('question', 'q.', 'q)', '#')) or line[0].isdigit():
                # New question starts
                if current_answer:
                    answers.append('\n'.join(current_answer))
                    current_answer = []
                in_answer_section = False
                current_question.append(line)
            else:
                # Add line to current section
                if in_answer_section:
                    current_answer.append(line)
                else:
                    current_question.append(line)
        
        # Add the last question/answer if any
        if current_question:
            questions.append('\n'.join(current_question))
        if current_answer:
            answers.append('\n'.join(current_answer))
        
        # Format final texts
        questions_text = '\n\n'.join(questions)
        answers_text = '\n\n'.join(answers)
        
        # Add headers
        questions_text = "EXAM QUESTIONS\n" + "="*15 + "\n\n" + questions_text
        answers_text = "ANSWER KEY\n" + "="*10 + "\n\n" + answers_text
        
        return questions_text, answers_text
        
    except Exception as e:
        st.error(f"Error processing questions and answers: {str(e)}")
        return "Error processing questions", "Error processing answers"

def create_pdf(content, title):
    """Enhanced PDF creation with better formatting"""
    pdf = FPDF()
    pdf.add_page()
    
    # Title with decorative elements
    pdf.set_font("Arial", "B", 18)
    pdf.set_fill_color(240, 240, 240)  # Light gray background
    pdf.cell(0, 20, title, ln=True, align="C", fill=True)
    
    # Metadata
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
    
    # Add a decorative line
    pdf.set_draw_color(200, 200, 200)  # Gray line
    pdf.line(10, pdf.get_y() + 5, 200, pdf.get_y() + 5)
    pdf.ln(10)
    
    # Content with better formatting
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(50, 50, 50)  # Dark gray text
    
    # Process content line by line for better formatting
    for line in content.split("\n"):
        # Check if line is a question number or header
        if line.strip().startswith(("Question", "EXAM", "ANSWER", "=")):
            pdf.set_font("Arial", "B", 12)
            pdf.multi_cell(0, 10, line)
            pdf.set_font("Arial", "", 12)
        else:
            pdf.multi_cell(0, 10, line)
        pdf.ln(2)
    
    # Footer
    pdf.set_y(-30)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(128, 128, 128)  # Light gray text
    pdf.cell(0, 10, "Generated by ZecoED Assessment System", align="C")
    pdf.cell(0, 10, f"Page {pdf.page_no()}", align="R")
    
    return pdf.output(dest="S").encode("latin1")

def display_dashboard_metrics():
    """Display dashboard metrics for teachers"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Exams Created", "24", "+3")
    with col2:
        st.metric("Students Assessed", "150", "+12")
    with col3:
        st.metric("Average Score", "76%", "+2.1%")
    with col4:
        st.metric("Questions Generated", "480", "+60")

def main_app():
    # Header with user info
    col1, col2 = st.columns([2, 1])
    with col1:
        st.title(f"🎓 ZecoED Assessment System")
    with col2:
        st.write(f"{st.session_state.user_data['avatar']} Welcome, {st.session_state.user_data['name']}")
    
    # Sidebar enhancement
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-content">
            <h3>Quick Actions</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.user_type == 'teacher':
            display_dashboard_metrics()
        
        st.markdown("---")
        if st.button("🚪 Logout", type="primary"):
            st.session_state.logged_in = False
            st.session_state.user_type = None
            st.session_state.user_data = None
            st.rerun()
    
    # Main content in tabs
    tab1, tab2 = st.tabs(["Create Exam", "History"])
    
    with tab1:
        st.markdown("""
        <div class="subject-card">
            <h3>Exam Configuration</h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            class_level = st.selectbox("📚 Select Class", CLASSES)
        
        with col2:
            # Group subjects by category
            category = st.selectbox("📑 Select Category", list(SUBJECT_CATEGORIES.keys()))
            subject = st.selectbox("📖 Select Subject", SUBJECT_CATEGORIES[category])
        
        with col3:
            paper = None
            if class_level in ["Form 3", "Form 4"] and subject in ["Mathematics", "English", "Kiswahili", "Biology", "Chemistry", "Physics"]:
                paper = st.selectbox("📝 Select Paper", ["Paper 1", "Paper 2"])
        
        # Exam options
        col4, col5 = st.columns(2)
        with col4:
            num_questions = st.number_input("Number of Questions", min_value=5, max_value=50, value=10)
        with col5:
            time_limit = st.number_input("Time Limit (minutes)", min_value=30, max_value=180, value=60)
        
        # Generate button
        if st.button("🔄 Generate Exam", type="primary"):
            with st.spinner("Generating your exam..."):
                raw_questions = generate_questions_rapidapi(subject, class_level, paper, num_questions)
                
                if raw_questions:
                    questions_text, answers_text = split_questions_and_answers(raw_questions)
                    
                    # Display in tabs
                    preview_tab1, preview_tab2 = st.tabs(["Questions", "Answers"])
                    
                    with preview_tab1:
                        st.markdown('<div class="exam-preview">', unsafe_allow_html=True)
                        st.markdown("### 📝 Questions")
                        st.text_area("", value=questions_text, height=300, label_visibility="collapsed")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        questions_pdf = create_pdf(questions_text, f"{class_level} {subject} Exam Questions")
                        st.download_button(
                            label="📥 Download Questions PDF",
                            data=questions_pdf,
                            file_name=f"{class_level}_{subject}_questions_{datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf"
                        )
                    
                    with preview_tab2:
                        st.markdown('<div class="exam-preview">', unsafe_allow_html=True)
                        st.markdown("### ✅ Answers")
                        st.text_area("", value=answers_text, height=300, label_visibility="collapsed")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        answers_pdf = create_pdf(answers_text, f"{class_level} {subject} Exam Answers")
                        st.download_button(
                            label="📥 Download Answers PDF",
                            data=answers_pdf,
                            file_name=f"{class_level}_{subject}_answers_{datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf"
                        )
    
    with tab2:
        st.info("📊 Exam history and analytics will be displayed here")

def login_page():
    st.markdown("""
    <style>
        .login-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            background-color: white;
            border-radius: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .big-emoji {
            font-size: 100px;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="login-container">
        <h1 style="text-align: center;">🎓 ZecoED Assessment System</h1>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="big-emoji">🎓📚</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center;">
            <h3>Welcome to ZecoED</h3>
            <p>Your comprehensive educational assessment solution</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="login-form">', unsafe_allow_html=True)
        username = st.text_input("👤 Username")
        password = st.text_input("🔒 Password", type="password")
        
        if st.button("🔐 Login", type="primary"):
            if handle_login(username, password):
                st.success("Login successful! Redirecting...")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Invalid username or password")
        
        st.markdown("---")
        st.markdown("""
        # <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 10px;">
        #     <h4>Demo Credentials</h4>
        #     <code>
        #     Teacher: teacher1 / pass123<br>
        #     Student: student1 / pass123
        #     </code>
        # </div>
        """, unsafe_allow_html=True)

def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()
