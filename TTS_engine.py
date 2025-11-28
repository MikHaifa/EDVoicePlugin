# filename: TTS_engine.py
import torch
import os
import wave
from pydub import AudioSegment
import numpy as np
import tempfile
from TTS.api import TTS
from pathlib import Path
import pygame  # Для воспроизведения с pause/stop
import time  # Добавлен импорт time

class TTS_Engine:
    def __init__(self, fp16=False):
        # Динамические пути
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.silero_model_path = os.path.join(script_dir, 'resources', 'silero', 'v4_ru.pt')
        self.sample_rate = 48000
        self.xtts_sample_rate = 22050  # XTTS требует 22050 Hz
        self.xtts_tts = None
        self.silero_model = None
        self.speaker_wav_path = os.path.expanduser('~/Saved Games/EDVoicePlugin/resources/silero')
        os.makedirs(self.speaker_wav_path, exist_ok=True)

        self.fp16 = fp16  # FP16 для ускорения на GPU

        # Инициализация Silero
        try:
            if not os.path.exists(self.silero_model_path):
                raise FileNotFoundError(f"Модель Silero не найдена: {self.silero_model_path}")
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.silero_model = torch.package.PackageImporter(self.silero_model_path).load_pickle("tts_models", "model")
            self.silero_model.to(self.device)
            print(f"Silero инициализирован на устройстве: {self.device}")
            # Прогрев Silero
            self.synthesize("Тест", model="Silero", speaker="baya", speed=1.0, volume=1.0, language="ru")
            # Автоматическое создание WAV-файлов для всех голосов Silero
            self.create_voice_samples()
        except Exception as e:
            print(f"Ошибка инициализации Silero: {e}")

        # Инициализация XTTS-v2
        try:
            self.xtts_tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
            if self.fp16:
                self.xtts_tts = self.xtts_tts.half()  # FP16 для ускорения на GPU
                print("XTTS-v2 инициализирован с FP16")
            else:
                print("XTTS-v2 инициализирован (FP32)")
        except Exception as e:
            print(f"Ошибка инициализации XTTS: {e}")

    def create_voice_samples(self):
        voices = ["aidar", "baya", "eugene", "kseniya", "xenia"]  # Все голоса Silero
        test_phrase = "Тестовый голос для клонирования."
        for voice in voices:
            wav_path = os.path.join(self.speaker_wav_path, f"{voice}_sample.wav")
            if not os.path.exists(wav_path):
                try:
                    temp_path = self.synthesize(test_phrase, model="Silero", speaker=voice, speed=1.0, volume=1.0, language="ru")
                    # Resample до 22050 Hz для XTTS
                    segment = AudioSegment.from_wav(temp_path)
                    segment = segment.set_frame_rate(self.xtts_sample_rate)
                    segment.export(wav_path, format='wav')
                    os.remove(temp_path)
                    print(f"{voice}_sample.wav создан автоматически!")
                except Exception as e:
                    print(f"Ошибка автоматического создания {voice}_sample.wav: {e}")

    def synthesize(self, text, model="Silero", speaker="baya", speed=1.0, volume=1.0, language="ru", fp16=None):
        output_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
        print(f"Синтез: model={model}, speaker={speaker}, text={text}, language={language}")
        if model == "Silero":
            if not self.silero_model:
                raise ValueError("Silero модель не инициализирована")
            try:
                audio = self.silero_model.apply_tts(text=text, speaker=speaker, sample_rate=self.sample_rate, put_accent=True)
                audio_np = audio.cpu().numpy()
                with wave.open(output_file, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(self.sample_rate)
                    wf.writeframes((audio_np * 32767).astype(np.int16).tobytes())
                segment = AudioSegment.from_wav(output_file)
                if speed != 1.0:
                    segment = segment.speedup(playback_speed=speed) if speed > 1 else segment._spawn(
                        segment.raw_data, overrides={"frame_rate": int(segment.frame_rate * speed)})
                if volume != 1.0:
                    gain_db = 20 * np.log10(volume)
                    segment = segment + gain_db
                segment.export(output_file, format='wav')
                print(f"Silero синтезировал: {output_file}")
                return output_file
            except Exception as e:
                raise ValueError(f"Ошибка синтеза Silero: {e}")
        elif model == "XTTS-v2" and self.xtts_tts:
            try:
                speaker_wav = None
                if speaker.endswith("_clone"):
                    base_voice = speaker.replace("_clone", "")
                    speaker_wav = os.path.join(self.speaker_wav_path, f"{base_voice}_sample.wav")
                    print(f"XTTS speaker_wav: {speaker_wav} for {speaker}")
                # FP16: Переключить модель, если указано (но init уже half, если fp16=True)
                current_fp16 = fp16 if fp16 is not None else self.fp16
                if current_fp16 and not self.xtts_tts.is_half:
                    self.xtts_tts = self.xtts_tts.half()
                self.xtts_tts.tts_to_file(text=text, speaker_wav=speaker_wav, file_path=output_file, language=language, speed=speed)
                segment = AudioSegment.from_wav(output_file)
                if volume != 1.0:
                    gain_db = 20 * np.log10(volume)
                    segment = segment + gain_db
                segment.export(output_file, format='wav')
                print(f"XTTS синтезировал: {output_file}")
                return output_file
            except Exception as e:
                raise ValueError(f"Ошибка синтеза XTTS: {e}")
        else:
            raise ValueError("Неподдерживаемый движок или XTTS не инициализирован")

    def play(self, audio_path):
        print(f"Воспроизведение: {audio_path}")
        try:
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
        except Exception as e:
            print(f"Ошибка воспроизведения: {e}")
        finally:
            if os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except Exception as e:
                    print(f"Ошибка удаления файла: {e}")