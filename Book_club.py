import streamlit as st
import requests
import os
from dotenv import load_dotenv
import speech_recognition as sr
import tempfile
import datetime
from googletrans import Translator

# Load API key from .env
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama3-8b-8192"

# Translator for Urdu
translator = Translator()

# Streamlit page config
st.set_page_config(page_title="Book Club AI Companion", layout="wide")

# Sidebar
with st.sidebar:
    st.title("Book Club AI")
    task = st.selectbox("Choose a task", [
        "Summarize Chapter",
        "Translate & Explain Quote",
        "Generate Discussion Questions",
        "Recap Characters & Themes",
        "Voice-to-Text Input"
    ])
    translate_to_urdu = st.checkbox("Translate response to Urdu")

    if st.button("Download Last Response") and "last_response" in st.session_state:
        with open("last_response.txt", "w", encoding="utf-8") as f:
            f.write(st.session_state.last_response)
        with open("last_response.txt", "rb") as f:
            st.download_button(
                label="Download Response as .txt",
                data=f,
                file_name="response.txt",
                mime="text/plain"
            )

    if st.button("Save Chat History") and "messages" in st.session_state:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with open(f"chat_history_{timestamp}.txt", "w", encoding="utf-8") as f:
            for msg in st.session_state.messages:
                f.write(f"{msg['role'].capitalize()}: {msg['content']}\n\n")
        st.success("Chat history saved!")

    st.markdown("Talk to your smart assistant about books!")

# Initialize message history
if "messages" not in st.session_state:
    system_msg = "You are a helpful AI for book clubs. Provide clear, concise, and friendly support on books, and no longer than 3-4 lines"
    if task == "Summarize Chapter":
        system_msg += " Summarize the given book chapter briefly and clearly."
    elif task == "Translate & Explain Quote":
        system_msg += " Translate the quote to English and explain its meaning simply."
    elif task == "Generate Discussion Questions":
        system_msg += " Create thoughtful, discussion-worthy questions from the given text."
    elif task == "Recap Characters & Themes":
        system_msg += " Recap important characters and central themes from the given chapter or book."
    elif task == "Voice-to-Text Input":
        system_msg += " Transcribe the audio and answer based on the spoken input."
    st.session_state.messages = [{"role": "system", "content": system_msg}]

# Voice-to-text support 
def transcribe_audio(file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return "Sorry, I couldn't understand the audio."
    except sr.RequestError as e:
        return f"Speech recognition API error: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

# Main input
if task == "Voice-to-Text Input":
    st.markdown("🎤 Upload your voice message (WAV format)")
    audio_file = st.file_uploader("Upload audio", type=["wav"])
    if audio_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_file.read())
            tmp.flush()
            transcript = transcribe_audio(tmp.name)
            st.write("Transcribed Text:", transcript)
            user_input = transcript
    else:
        user_input = ""
else:
    user_input = st.chat_input("Type your message here...")

st.markdown("<h1 style='text-align:center;'>Book Club Ai Companion</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Talk to your assistant about book summaries, quotes, and discussions.</p><hr>", unsafe_allow_html=True)

# Send message to Groq
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": GROQ_MODEL,
            "messages": st.session_state.messages,
            "temperature": 0.6
        }
    )
    if response.status_code == 200:
        reply = response.json()["choices"][0]["message"]["content"]

        #  Urdu translation
        if translate_to_urdu:
            try:
                translated = translator.translate(reply, dest='ur')
                reply += f"\n\n (Translated to Urdu):\n{translated.text}"
            except Exception as e:
                reply += f"\n\nUrdu translation failed: {str(e)}"

        st.session_state.last_response = reply
    else:
        reply = "Error communicating with Groq API."

    st.session_state.messages.append({"role": "assistant", "content": reply})

# Display chat
for msg in st.session_state.messages[1:]:  # skip system message
    if msg["role"] == "user":
        with st.chat_message("user", avatar="🧑‍🎓"):
            st.markdown(
                f"""
                <div style='
                    background-color: #f0f0f5;
                    color: #333333;
                    padding: 15px 18px;
                    border-radius: 15px;
                    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
                    font-size: 16px;
                    font-weight: 500;
                    box-shadow: 2px 2px 6px rgba(0,0,0,0.1);
                    max-width: 75%;
                    margin-left: auto;
                    letter-spacing: 0.4px;
                '>{msg['content']}</div>
                """,
                unsafe_allow_html=True
            )
    else:
        with st.chat_message("assistant", avatar="📘"):
            st.markdown(
                f"""
                <div style='
                    background-color: #d9e2ec;
                    color: #1f2937;
                    padding: 15px 18px;
                    border-radius: 15px;
                    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
                    font-size: 16px;
                    font-weight: 500;
                    box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
                    max-width: 75%;
                    margin-right: auto;
                    letter-spacing: 0.4px;
                '>{msg['content']}</div>
                """,
                unsafe_allow_html=True
            )




