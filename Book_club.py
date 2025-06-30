import streamlit as st
import requests
import os   #system ke sath kam krne k liy jase files ye environment variables ko access krna.
from dotenv import load_dotenv  #.env file se secret keys ko load krna
import speech_recognition as sr  #Awwaz ko text main bdlne k liy use krte han.
import tempfile   #Temporary files upload krne k liy jaise koi audio upload hoti ha.
import datetime
from googletrans import Translator  #Googletrans wo service ha jise hum browser main use krte han.

# Load API key from .env
load_dotenv()
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
GROQ_MODEL = "llama3-8b-8192"

# Translator for Urdu
translator = Translator()

# Streamlit page config
st.set_page_config(page_title="Book Club AI Companion", layout="wide")

# Sidebar
with st.sidebar:
    st.title("Book Club AI")=
    task = st.selectbox("Choose a task", [
        "Summarize Chapter",
        "Translate & Explain Quote",
        "Generate Discussion Questions",
        "Recap Characters & Themes",
        "Voice-to-Text Input"
    ])
    translate_to_urdu = st.checkbox("Translate response to Urdu")  #checkbox agr user urdu translate krna chahta ha.

    if st.button("Download Last Response") and "last_response" in st.session_state:  #yahan hum ne aik btn bnaya ha jo pichle response ko save kr leta ha
        with open("last_response.txt", "w", encoding="utf-8") as f:  # Hum ek new file bana rahe hain jiska naam hai last_response.txt. encoding="utf-8" Urdu/Arabic jese characters ke liye zaroori hai
            f.write(st.session_state.last_response)
        with open("last_response.txt", "rb") as f:  #file readmode main dubara khol rhe han.
            st.download_button(
                label="Download Response as .txt",
                data=f,  #file ko download data bnata ha.
                file_name="response.txt",  #download hone wali file ka name.
                mime="text/plain"  #btata ha k file aik plain text file ha.
            )

    if st.button("Save Chat History") and "messages" in st.session_state:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  #datetime.datetime.now() — abhi ka waqt .strftime(...) — us waqt ko ek file-friendly string mein badal rahe hain . Jaise: 2025-06-03_14-25-59. Taa ke har file ka unique naam ho
        with open(f"chat_history_{timestamp}.txt", "w", encoding="utf-8") as f:  #Ek nayi file banayi ja rahi hai:Naam hoga chat_history_2025-06-03_14-25-59.txt
            for msg in st.session_state.messages:
                f.write(f"{msg['role'].capitalize()}: {msg['content']}\n\n") #msg['role'] = "user" ya "assistant".capitalize() = pehla letter bada.msg['content'] = message ka actual text
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
    recognizer = sr.Recognizer()  #Speech recognition ka ek object recognizer banaya ja raha hai, jo audio ko samajh kar usse text mein convert karega.
    with sr.AudioFile(file) as source:  #file jo audio file ka path hai, usko source ke naam se use karte hue speech recognition ke liye khol rahe hain.
        audio = recognizer.record(source)   #: source se poora audio record kar rahe hain, 
    try:
        return recognizer.recognize_google(audio)  #Google Speech Recognition API ka use kar ke audio ko text mein convert karein.
    except sr.UnknownValueError:  #agr google api ko smjh nhi paya to ye message display ho ga
        return "Sorry, I couldn't understand the audio."
    except sr.RequestError as e:  #Agar Google Speech API mein koi technical problem aaye (jaise internet ya server problem), to yeh error message return karega.
        return f"Speech recognition API error: {e}"  #e mein error ka detail hoga.
    except Exception as e:
        return f"Unexpected error: {e}"  #Agar koi aur bhi problem ho jo upar mention nahi hai, to uska message return kar dega.

# Main input
if task == "Voice-to-Text Input":
    st.markdown("🎤 Upload your voice message (WAV format)")
    audio_file = st.file_uploader("Upload audio", type=["wav"])
    if audio_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp: #tempfile.NamedTemporaryFile = temporary file banana .delete=False = file turant delete na ho jab band ho.suffix=".wav" = file ka naam .wav extension ke sath hoga
            tmp.write(audio_file.read())  #suffix=".wav" = file ka naam .wav extension ke sath hoga.audio_file.read() = uploaded file ka content padhna
            tmp.flush()   #file ka content save krna
            transcript = transcribe_audio(tmp.name)  #transcribe_audio(...) = pehle banaya gaya function jo audio ko text mein badalta hai #tmp.name = temporary file ka path
            st.write("Transcribed Text:", transcript)  #"Transcribed Text:" = screen par ye text dikhana,transcript = jo text audio se mila wo bhi dikhana
            user_input = transcript
    else:
        user_input = ""  #(agar file upload nahi hui) user_input = "" = input khali (empty string) rakhna
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




