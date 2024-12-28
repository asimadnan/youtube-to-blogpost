import streamlit as st
from fetch_transcripts import process_url, fetch_transcript
from transcript_to_blog import BlogPostGenerator
import os 

# Sidebar for OpenAI API key and links
with st.sidebar:
    st.header("Configuration")
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    if openai_api_key:
        st.session_state.openai_api_key = openai_api_key
        os.environ["OPENAI_API_KEY"] = openai_api_key
        st.success("OpenAI API Key set successfully!")
    st.markdown("[Get an OpenAI API key](https://platform.openai.com/account/api-keys)")

# Streamlit app layout
st.title("YouTube Transcript to Blog Converter")

# Step 1: Input YouTube URL
st.header("Step 1: Enter YouTube URL")
url = st.text_input("Enter YouTube URL:")

# Initialize session state
if "transcript_text" not in st.session_state:
    st.session_state.transcript_text = None
if "blog_post" not in st.session_state:
    st.session_state.blog_post = None

def fetch_transcript_ui(url):
    """Fetch transcript and store it in session state."""
    st.info(f"Fetching transcript for: {url}")
    try:
        # video_title = process_url(url, "en")  # Assuming 'en' for English language

        result = fetch_transcript(url, 'en')
        if result:
            transcript, video_title = result
            st.session_state.transcript_text = f"{transcript}"  # Mocked text for testing
            st.success("Transcript fetched successfully!")
        else:
            st.error("Failed to fetch transcript.")
    except Exception as e:
        st.error(f"Error fetching transcript: {e}")

def generate_blog_ui(transcript_text):
    """Generate blog post and store it in session state."""
    st.info("Generating blog from the transcript...")
    try:
        config_path = "config.json"
        generator = BlogPostGenerator(config_path)
        blog_post = generator.generate_blog_post(transcript_text)
        st.session_state.blog_post = blog_post
        st.success("Blog post generated successfully!")
    except Exception as e:
        st.error(f"Error generating blog post: {e}")

# Step 2: Fetch Transcript
if url and st.button("Fetch Transcript"):
    fetch_transcript_ui(url)

# Step 3: Show Transcript
if st.session_state.transcript_text:
    st.markdown("### Transcript:")
    st.text_area("Transcript", st.session_state.transcript_text, height=300)

    # Step 4: Generate Blog
    st.header("Step 4: Generate Blog")
    if st.button("Convert to Blog"):
        generate_blog_ui(st.session_state.transcript_text)

# Step 5: Preview Blog Post
if st.session_state.blog_post:
    st.markdown("### Blog Post Preview:")
    st.markdown(st.session_state.blog_post)  # Render as Markdown

    if st.button("Copy Blog"):
        st.code(st.session_state.blog_post, language="markdown")
        st.success("Blog content copied to clipboard! Use Ctrl+C to paste.")