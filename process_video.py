import torch
import subprocess
import speech_recognition as sr
from translate import Translator
import noisereduce as nr
import moviepy.editor as mp
from TTS.api import TTS
from pydub import AudioSegment
from base64 import b64encode
from IPython.display import HTML
import os
ffmpeg_path = "D:/@2nd(3rd sem)Quantum/ffmpeg-2024-03-20-git-e04c638f5f-full_build/ffmpeg-2024-03-20-git-e04c638f5f-full_build/bin/ffmpeg.exe"

def remove_background_noise(audio_file):
    audio = AudioSegment.from_wav(audio_file)
    reduced_noise = nr.reduce_noise(audio.get_array_of_samples(), audio.frame_rate)
    cleaned_audio = AudioSegment(
        data=reduced_noise.tobytes(),
        sample_width=audio.sample_width,
        frame_rate=audio.frame_rate,
        channels=audio.channels
    )
    cleaned_audio.export("vocals.wav", format="wav")
    return "vocals.wav"

def transcribe_and_translate_audio(audio_path, input_language='en', target_language='en'):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio_data, language=input_language)
        translator = Translator(to_lang=target_language)
        translated_text = translator.translate(text)
        # Prompt the user to modify the translated text
        modified_text = input("Translated text: " + translated_text + "\nEnter modified text (leave blank to keep original): ").strip()
        translated_text = modified_text if modified_text else translated_text
        return translated_text
    except sr.UnknownValueError:
        print("Speech Recognition could not understand audio")
        return ""
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return ""

device = "cuda" if torch.cuda.is_available() else "cpu"
# Modify the path to your TTS model
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

def process_video(input_video_path, input_language='en', target_language='en'):
    if not os.path.exists(input_video_path):
        print("File not found.")
        return

    subprocess.run([ffmpeg_path, "-i", input_video_path, "-c:v", "copy", "only_video.mp4"])
    subprocess.run([ffmpeg_path, "-i", input_video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "only_audio.wav"])
    cleaned_audio_file = remove_background_noise("only_audio.wav")
    print(f"Background noise removed. Cleaned audio saved as '{cleaned_audio_file}'")

    audio_chunks = []
    for i in range(0, len(AudioSegment.from_wav(cleaned_audio_file)), 50000):
        chunk = AudioSegment.from_wav(cleaned_audio_file)[i:i + 50000]
        chunk.export(f"chunk{i}.wav", format="wav")
        audio_chunks.append(f"chunk{i}.wav")

    combined_audio = AudioSegment.empty()
    for chunk_path in audio_chunks:
        text = transcribe_and_translate_audio(chunk_path, input_language=input_language, target_language=target_language)
        if text:
            output_path = f"output_{os.path.basename(chunk_path)}"
            with open(f"vocal_text_{os.path.basename(chunk_path)}.txt", "w", encoding="utf-8") as file:
                file.write(text)
            tts.tts_to_file(text=text, speaker_wav=chunk_path, language="hi", file_path=output_path)
            combined_audio += AudioSegment.from_wav(output_path)

    combined_audio.export("combined_output.wav", format="wav")

    combined_duration = len(combined_audio)

    subprocess.run([ffmpeg_path, "-i", "only_video.mp4", "-ss", "0", "-t", str(combined_duration / 1000), "-c:v", "copy", "trimmed_video.mp4"])

    subprocess.run([ffmpeg_path, "-i", "trimmed_video.mp4", "-i", "combined_output.wav", "-c:v", "copy", "-c:a", "aac", "-strict", "experimental", "-map", "0:v:0", "-map", "1:a:0", "Final_output.mp4"])

    if os.path.exists('Final_output.mp4'):
        mp4 = open('Final_output.mp4', 'rb').read()
        data_url = "data:video/mp4;base64," + b64encode(mp4).decode()
        return f"""
        <video width=400 controls>
            <source src="{data_url}" type="video/mp4">
        </video>
        """
    else:
        return "<p>Error: Final_output.mp4 not found.</p>"