from flask import Flask, render_template, request, send_file
from translate import Translator
from gtts import gTTS
import os
import platform
import textwrap
from yt_dlp import YoutubeDL
import assemblyai as aai

app = Flask(__name__)

# AssemblyAI API key
aai.settings.api_key = "8ded3e61ee47493b8d2bcc093ca1bf67"

# Available languages
available_languages = {
    'Tamil': 'ta',
    'Hindi': 'hi',
    'French': 'fr',
    'Spanish': 'es',
    'German': 'de',
    'Chinese': 'zh-CN',
    'Japanese': 'ja'
}

def download_audio(url, output_filename):
    try:
        # Ensure the filename has the .mp3 extension
        if not output_filename.endswith('.mp3'):
            output_filename += '.mp3'  # Append .mp3 if not already present

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': output_filename.replace('.mp3', '')  # Remove .mp3 from outtmpl to avoid duplication
        }

        print(f"Downloading audio from URL: {url}")
        print(f"Saving audio to: {output_filename}")

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Verify the file was downloaded
        if not os.path.exists(output_filename):
            print("Error: Audio file was not downloaded.")
            return None

        print("Audio downloaded successfully.")
        return output_filename
    except Exception as e:
        print("Error during audio download:", e)
        return None
            
def transcribe_audio(file_path):
    try:
        print(f"Attempting to transcribe audio file: {file_path}")
        if not os.path.exists(file_path):
            print("Error: Audio file does not exist.")
            return None

        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(file_path)
        if transcript.error:
            print(f"Transcription error: {transcript.error}")
            return None

        print("Transcription successful.")
        return transcript.text
    except Exception as e:
        print(f"Error during transcription: {e}")
        return None

def translate_text_to_audio(text, target_lang):
    # Step 1: Split text into smaller chunks
    chunk_size = 500  # Limit of characters per request
    chunks = textwrap.wrap(text, chunk_size)
    translated_text = ""

    # Step 2: Translate each chunk and combine results
    translator = Translator(to_lang=target_lang)
    for chunk in chunks:
        translated_chunk = translator.translate(chunk)
        translated_text += translated_chunk + " "

    # Step 3: Convert the translated text to speech
    tts = gTTS(text=translated_text, lang=target_lang)
    audio_file = "static/translated_audio.mp3"  # Fixed filename
    tts.save(audio_file)

    return translated_text, audio_file

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Get the URL from the form
        video_url = request.form.get("url")
        if not video_url:
            return render_template("index.html", error="Please enter a valid URL.", available_languages=available_languages)

        # Download the audio
        output_filename = "trans"
        audio_path = download_audio(video_url, output_filename)
        if not audio_path:
            return render_template("index.html", error="Failed to download the audio.", available_languages=available_languages)

        # Transcribe the audio
        transcription = transcribe_audio(audio_path)
        if not transcription:
            return render_template("index.html", error="Failed to transcribe the audio.", available_languages=available_languages)

        # Get the selected language
        selected_lang_name = request.form.get("language")
        target_lang = available_languages.get(selected_lang_name)
        if not target_lang:
            return render_template("index.html", error="Invalid language selection.", available_languages=available_languages)

        # Translate and generate audio
        translated_text, audio_file = translate_text_to_audio(transcription, target_lang)

        # Render the result page with the audio player
        return render_template("index.html", 
                               translated_text=translated_text, 
                               audio_file=audio_file, 
                               success="Translation and audio generation successful!",
                               available_languages=available_languages)

    return render_template("index.html", available_languages=available_languages)

@app.route("/download/<filename>")
def download(filename):
    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)