import streamlit as st
import PyPDF2
import re
import pandas as pd
from io import BytesIO

# Page Setup
st.set_page_config(page_title="ATS alike | ATS Pro + Analytics", layout="wide")

def extract_text_from_pdf(file):
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except:
        return ""

def screen_resume(text, keywords):
    text_lower = text.lower()
    found = [k.strip() for k in keywords if re.search(r'\b' + re.escape(k.strip().lower()) + r'\b', text_lower)]
    score = len(found)
    status = "SHORTLIST" if score > 0 else "REJECT"
    return status, found, score

# --- Sidebar UI ---
st.sidebar.header("ATS Settings")
keywords_input = st.sidebar.text_area("Target Keywords (comma separated)", 
                                     "Excel, Economics, Research, Data Analysis, Python, HR")
keywords_list = [k.strip() for k in keywords_input.split(",") if k.strip()]

# --- Main UI ---
st.title("📄 ATS Alike: Resume Scanner")
st.write("Upload multiple resumes to check against your predefined keywords.")

uploaded_files = st.file_uploader("Drag and drop PDF resumes here", type="pdf", accept_multiple_files=True)

if uploaded_files:
    if st.button("⚡ Start Batch Screening"):
        results_list = []
        
        progress_bar = st.progress(0)
        for i, file in enumerate(uploaded_files):
            resume_text = extract_text_from_pdf(file)
            status, found_keys, count = screen_resume(resume_text, keywords_list)
            
            results_list.append({
                "Candidate File": file.name,
                "Decision": status,
                "Keywords Found": ", ".join(found_keys),
                "Match Count": count
            })
            progress_bar.progress((i + 1) / len(uploaded_files))

        # Convert to DataFrame
        df = pd.DataFrame(results_list)

        # --- NEW: Analytics Section ---
        st.divider()
        st.subheader("📊 Screening Analytics")
        col1, col2, col3 = st.columns(3)
        
        total = len(df)
        shortlisted = len(df[df['Decision'] == 'SHORTLIST'])
        rejected = len(df[df['Decision'] == 'REJECT'])
        
        col1.metric("Total Resumes", total)
        col2.metric("Shortlisted ✅", shortlisted, delta=f"{(shortlisted/total)*100:.1f}%" if total > 0 else 0)
        col3.metric("Rejected ❌", rejected, delta=f"-{(rejected/total)*100:.1f}%" if total > 0 else 0, delta_color="inverse")

        # Simple Bar Chart for Decision Distribution
        chart_data = df['Decision'].value_counts()
        st.bar_chart(chart_data)

        # --- Display Table ---
        st.subheader("Detailed Results")
        st.dataframe(df, use_container_width=True)

        # --- Excel Export ---
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Screening_Report')
        processed_data = output.getvalue()

        st.download_button(
            label="📥 Download Results as Excel",
            data=processed_data,
            file_name="ATS_Screening_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Awaiting file upload...")
