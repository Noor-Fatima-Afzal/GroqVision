import os
import io
import base64
import time
import streamlit as st
from PIL import Image
from groq import Groq

# ——————————————————————————————————————————————————————————————————————————
# 1. Config & Inject Styles
# ——————————————————————————————————————————————————————————————————————————
st.set_page_config(
    page_title="Groq OCR Demo",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* Page background */
body { background-color: #f7f9fc; }
/* Centered header */
h1 { color: #1f2937; text-align: center; font-size: 2.5rem; margin-bottom: 0.2em; }
/* Subtitle styling */
.subtitle { text-align: center; font-size: 1.1rem; color: #4b5563; margin-bottom: 1.5em; }
/* Sidebar */
[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e5e7eb; }
/* Buttons */
.stButton>button { background-color: #10b981 !important; color: #ffffff !important; border: none !important; padding: 0.6em 1.2em !important; font-size: 1rem !important; border-radius: 0.375rem !important; }
.stButton>button:hover { background-color: #059669 !important; }
/* Image preview box */
.image-container { padding: 0.5em; border: 1px solid #d1d5db; border-radius: 0.375rem; background-color: #ffffff; }
</style>
""", unsafe_allow_html=True)

# ——————————————————————————————————————————————————————————————————————————
# 2. Secrets & Sidebar
# ——————————————————————————————————————————————————————————————————————————
GROQ_API_KEY = st.secrets["API_TOKEN"]
if not GROQ_API_KEY:
    st.error("⚠️ Please set your `API_TOKEN` as an environment variable.")
    st.stop()

with st.sidebar:
    st.header("🔍 OCR Settings")
    uploaded_file = st.file_uploader(
        "Upload image (PNG/JPG)…",
        type=["png", "jpg", "jpeg"],
        help="Receipts, invoices, scanned docs etc."
    )
    st.markdown("---")
    if st.button("♻️ Clear results", use_container_width=True):
        st.session_state.pop("ocr_text", None)
        st.experimental_rerun()
    st.caption("Powered by Groq’s vision LLM")

# ——————————————————————————————————————————————————————————————————————————
# 3. Main Header & Instructions
# ——————————————————————————————————————————————————————————————————————————
st.markdown("<h1>🧾 OCR Text Extraction with Groq</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Upload an image and click <strong>Extract Text</strong> to get formatted output.</p>", unsafe_allow_html=True)

# ——————————————————————————————————————————————————————————————————————————
# 4. Handle Upload & Extraction (image full-width, then action below)
# ——————————————————————————————————————————————————————————————————————————
if uploaded_file:
    raw_bytes = uploaded_file.getvalue()
    img = Image.open(io.BytesIO(raw_bytes))

    # Full-width preview
    st.markdown("<div class='image-container'>", unsafe_allow_html=True)
    st.image(img, caption="🖼️ Preview", use_column_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Action below image
    st.markdown("### Ready to Extract?")
    if st.button("💫 Extract Text", use_container_width=True):
        # Progress bar animation
        progress = st.progress(0)
        for pct in [20, 40, 60, 80, 100]:
            time.sleep(0.1)
            progress.progress(pct)

        # Prepare data URI
        b64 = base64.b64encode(raw_bytes).decode()
        data_uri = f"data:{uploaded_file.type};base64,{b64}"
        prompt = (
            "Extract all readable text from the image and return it as well-formatted "
            "Markdown, using headings, lists, and code blocks where helpful."
        )
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text",      "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_uri}},
                ],
            }
        ]

        client = Groq(api_key=GROQ_API_KEY)
        try:
            with st.spinner("🕑 Processing…"):
                completion = client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    messages=messages,
                    temperature=0.5,
                    max_tokens=1024,
                    top_p=1.0,
                    stream=False,
                )
            st.success("✅ Extraction complete!")
            st.session_state["ocr_text"] = completion.choices[0].message.content

        except Exception as e:
            st.error(f"❌ Failed to extract text: {e}")

# ——————————————————————————————————————————————————————————————————————————
# 5. Display Results (Rendered) & Download Markdown
# ——————————————————————————————————————————————————————————————————————————
if "ocr_text" in st.session_state:
    st.markdown("---")
    st.subheader("📄 Extracted Text")
    # Render the markdown so headings, lists, etc. appear correctly
    st.markdown(st.session_state["ocr_text"], unsafe_allow_html=True)

    # Only the download gives you the raw markdown
    st.download_button(
        "⬇️ Download Markdown",
        data=st.session_state["ocr_text"],
        file_name="ocr_result.md",
        mime="text/markdown",
        use_container_width=True,
    )
