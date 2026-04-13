import streamlit as st
from PyPDF2 import PdfReader
import pandas as pd
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Set page configuration INTEGRATION: Function to extract text from PDF
st.set_page_config(
    page_title="AI Resume Screening System", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
    }
    .stAlert {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Function to extract text from PDF with better error handling  INTEGRATION: Function to extract text from PDF
def extract_text_from_pdf(file):
    """
    Extract text from PDF file with improved error handling
    """
    try:
        pdf = PdfReader(file)
        text = ""
        total_pages = len(pdf.pages)
        
        for i, page in enumerate(pdf.pages):
            try:
                extracted_text = page.extract_text()
                if extracted_text:
                    text += extracted_text + " "
            except Exception as page_error:
                st.warning(f"Error reading page {i+1} of {file.name}: {str(page_error)}")
                continue
        
        return text.strip(), total_pages
    except Exception as e:
        st.error(f"Error reading PDF {file.name}: {str(e)}")
        return "", 0

# Enhanced text preprocessing
def preprocess_text(text):
    """
    Enhanced text preprocessing with multiple cleaning steps
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep important ones like @, +, -
    text = re.sub(r'[^\w\s@+\-.]', ' ', text)
    
    # Remove numbers that are standalone (keep alphanumeric)
    text = re.sub(r'\b\d+\b', '', text)
    
    # Remove extra spaces
    text = ' '.join(text.split())
    
    return text.strip()

# Enhanced ranking function with additional metrics
def rank_resumes(job_description, resumes, resume_names):
    """
    Rank resumes with additional metrics and insights
    """
    if not job_description or not resumes:
        return pd.DataFrame()
    
    documents = [job_description] + resumes
    
    # Use TF-IDF with optimized parameters
    vectorizer = TfidfVectorizer(
        stop_words='english',
        max_features=1000,
        ngram_range=(1, 2),  # Include bigrams
        min_df=1,
        max_df=0.95
    )
    
    try:
        vectors = vectorizer.fit_transform(documents).toarray()
        job_description_vector = vectors[0]
        resume_vectors = vectors[1:]
        
        # Calculate cosine similarities CALLING THE FUNCTION
        cosine_similarities = cosine_similarity([job_description_vector], resume_vectors).flatten()
        
        # Calculate additional metrics
        word_counts = [len(resume.split()) for resume in resumes]
        
        # Create results DataFrame
        results = pd.DataFrame({
            "Resume": resume_names,
            "Similarity_Score": cosine_similarities,
            "Word_Count": word_counts,
            "Rank": range(1, len(resume_names) + 1)
        })
        
        # Sort by similarity score
        results = results.sort_values(by="Similarity_Score", ascending=False)
        results["Rank"] = range(1, len(results) + 1)
        
        return results, vectorizer.get_feature_names_out()
        
    except Exception as e:
        st.error(f"Error in ranking process: {str(e)}")
        return pd.DataFrame(), []

# Function to extract key skills from text
def extract_skills(text, skill_keywords):
    """
    Extract skills mentioned in the resume
    """
    found_skills = []
    text_lower = text.lower()
    
    for skill in skill_keywords:
        if skill.lower() in text_lower:
            found_skills.append(skill)
    
    return found_skills

# Generate enhanced downloadable report
def generate_download_link(df, filename="resume_ranking.csv"):
    """
    Generate download link for results
    """
    output = BytesIO()
    
    # Add timestamp and additional info
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df_with_info = df.copy()
    df_with_info.insert(0, "Generated_On", timestamp)
    
    df_with_info.to_csv(output, index=False)
    output.seek(0)
    b64 = base64.b64encode(output.read()).decode()
    
    return f'<a href="data:file/csv;base64,{b64}" download="{filename}">📥 Download Complete Report</a>'

# Main application
def main():
    # Header
    st.markdown("<h1 class='main-header'>🎯 AI Resume Screening & Candidate Ranking System</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Similarity threshold
        similarity_threshold = st.slider(
            "Minimum Similarity Threshold", 
            min_value=0.0, 
            max_value=1.0, 
            value=0.1, 
            step=0.05,
            help="Filter out resumes below this similarity score"
        )
        
        # Common skills for analysis
        st.subheader("🔧 Skills to Analyze")
        default_skills = "Python, Java, JavaScript, SQL, Machine Learning, Data Analysis, Project Management, Communication, Leadership, Teamwork"
        skills_input = st.text_area(
            "Enter skills separated by commas:", 
            value=default_skills,
            height=100
        )
        skill_keywords = [skill.strip() for skill in skills_input.split(",") if skill.strip()]
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Job description input
        st.subheader("📄 Job Description")
        job_description = st.text_area(
            "Enter or paste the job description here:", 
            height=200,
            placeholder="Paste the complete job description including required skills, experience, and qualifications..."
        )
        
        # Character count
        if job_description:
            st.caption(f"Character count: {len(job_description)}")
    
    with col2:
        # Instructions
        st.subheader("📝 Instructions")
        st.info("""
        1. Enter the complete job description
        2. Upload PDF resumes (multiple files supported)
        3. Adjust similarity threshold in sidebar
        4. View ranking results and download report
        """)
    
    # File uploader
    st.subheader("📂 Upload Resume Files")
    uploaded_files = st.file_uploader(
        "Select PDF resume files", 
        type=["pdf"], 
        accept_multiple_files=True,
        help="You can upload multiple PDF files at once"
    )
    
    # Display file information
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully!")
        
        # Show file details
        with st.expander("📋 File Details"):
            for i, file in enumerate(uploaded_files, 1):
                st.write(f"{i}. **{file.name}** ({file.size:,} bytes)")
    
    # Process files when both job description and files are available
    if uploaded_files and job_description.strip():
        st.markdown("---")
        st.subheader("⚡ Processing Resumes...")
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Process job description
        status_text.text("Processing job description...")
        processed_job_desc = preprocess_text(job_description)
        progress_bar.progress(10)
        
        # Process resumes
        resumes = []
        resume_names = []
        resume_stats = []
        
        for i, file in enumerate(uploaded_files):
            status_text.text(f"Processing {file.name}...")
            
            text, page_count = extract_text_from_pdf(file)
            processed_text = preprocess_text(text)
            
            if processed_text:
                resumes.append(processed_text)
                resume_names.append(file.name)
                
                # Collect stats
                stats = {
                    "filename": file.name,
                    "pages": page_count,
                    "word_count": len(processed_text.split()),
                    "char_count": len(processed_text)
                }
                resume_stats.append(stats)
            else:
                st.warning(f"⚠️ No text extracted from {file.name}")
            
            progress_bar.progress(10 + (i + 1) * 70 // len(uploaded_files))
        
        if resumes:
            # Perform ranking
            status_text.text("Ranking resumes...")
            results, feature_names = rank_resumes(processed_job_desc, resumes, resume_names)
            progress_bar.progress(90)
            
            # Filter by threshold
            filtered_results = results[results["Similarity_Score"] >= similarity_threshold]
            
            status_text.text("Analysis complete!")
            progress_bar.progress(100)
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            # Display results
            st.markdown("---")
            st.subheader("📊 Ranking Results")
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Resumes", len(results))
            
            with col2:
                st.metric("Above Threshold", len(filtered_results))
            
            with col3:
                if len(results) > 0:
                    st.metric("Avg Similarity", f"{results['Similarity_Score'].mean():.3f}")
                else:
                    st.metric("Avg Similarity", "N/A")
            
            with col4:
                if len(results) > 0:
                    st.metric("Best Score", f"{results['Similarity_Score'].max():.3f}")
                else:
                    st.metric("Best Score", "N/A")
            
            # Results table
            if len(filtered_results) > 0:
                st.subheader("🏆 Top Candidates")
                
                # Format and display table
                display_df = filtered_results.copy()
                display_df["Similarity_Score"] = display_df["Similarity_Score"].round(4)
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Visualizations
                st.subheader("📈 Visualizations")
                
                # Create tabs for different visualizations
                tab1, tab2, tab3 = st.tabs(["📊 Bar Chart", "📈 Distribution", "🔍 Skills Analysis"])
                
                with tab1:
                    # Interactive bar chart
                    fig = px.bar(
                        filtered_results.head(10), 
                        x="Similarity_Score", 
                        y="Resume",
                        orientation='h',
                        title="Top 10 Resume Rankings",
                        color="Similarity_Score",
                        color_continuous_scale="viridis"
                    )
                    fig.update_layout(height=500)
                    st.plotly_chart(fig, use_container_width=True)
                
                with tab2:
                    # Score distribution
                    fig = px.histogram(
                        results, 
                        x="Similarity_Score", 
                        nbins=20,
                        title="Distribution of Similarity Scores"
                    )
                    fig.add_vline(x=similarity_threshold, line_dash="dash", line_color="red", 
                                annotation_text="Threshold")
                    st.plotly_chart(fig, use_container_width=True)
                
                with tab3:
                    # Skills analysis
                    if skill_keywords:
                        st.write("**Skills Found in Resumes:**")
                        
                        skills_data = []
                        for i, resume in enumerate(resumes):
                            found_skills = extract_skills(resume, skill_keywords)
                            skills_data.append({
                                "Resume": resume_names[i],
                                "Skills_Found": len(found_skills),
                                "Skills_List": ", ".join(found_skills)
                            })
                        
                        skills_df = pd.DataFrame(skills_data)
                        skills_df = skills_df.merge(results[["Resume", "Similarity_Score"]], on="Resume")
                        skills_df = skills_df.sort_values("Similarity_Score", ascending=False)
                        
                        st.dataframe(skills_df, use_container_width=True, hide_index=True)
                        
                        # Skills correlation
                        if len(skills_df) > 1:
                            correlation = skills_df["Skills_Found"].corr(skills_df["Similarity_Score"])
                            st.metric("Skills-Score Correlation", f"{correlation:.3f}")
                
                # Download section
                st.subheader("💾 Download Results")
                
                # Prepare comprehensive report
                comprehensive_report = filtered_results.merge(
                    pd.DataFrame(resume_stats), 
                    left_on="Resume", 
                    right_on="filename", 
                    how="left"
                ).drop("filename", axis=1)
                
                # Add skills analysis to report if available
                if 'skills_df' in locals():
                    comprehensive_report = comprehensive_report.merge(
                        skills_df[["Resume", "Skills_Found", "Skills_List"]], 
                        on="Resume", 
                        how="left"
                    )
                
                st.markdown(
                    generate_download_link(comprehensive_report, "comprehensive_resume_analysis.csv"), 
                    unsafe_allow_html=True
                )
                
            else:
                st.warning(f"⚠️ No resumes found above the similarity threshold of {similarity_threshold:.2f}")
                st.info("Try lowering the threshold in the sidebar or check if your job description matches the resume content.")
                
                # Show all results anyway
                if len(results) > 0:
                    st.subheader("📋 All Results (Below Threshold)")
                    display_df = results.copy()
                    display_df["Similarity_Score"] = display_df["Similarity_Score"].round(4)
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.error("❌ No valid text could be extracted from any of the uploaded PDF files.")
            st.info("Please ensure your PDF files contain selectable text (not scanned images).")
    
    elif uploaded_files and not job_description.strip():
        st.warning("⚠️ Please enter a job description to start the analysis.")
    
    elif job_description.strip() and not uploaded_files:
        st.warning("⚠️ Please upload resume files to start the analysis.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>🔧 Built with Streamlit | 🤖 Powered by TF-IDF & Cosine Similarity</p>
        <p><small>To run: <code>streamlit run app.py</code></small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()