import json
import os
from pathlib import Path
from PySide6.QtWidgets import QPushButton, QLineEdit
from STT_engine import SpeechRecognitionEngine

class SpeechRecognitionController:
    def __init__(self, speech_buttons: dict, keyword_input: QLineEdit, text_browser=None, ui=None):
        self.buttons = speech_buttons
        self.keyword_input = keyword_input
        self.text_browser = text_browser
        self.ui = ui
        self.config_path = str(Path.home() / "Saved Games" / "EDVoicePlugin" / "resources" / "Speech_Reconition.json")
        model_path = str(Path(__file__).parent / "resources" / "vosk" / "vosk_small")
        self.speech_engine = SpeechRecognitionEngine(
            model_path,
            text_browser=self.text_browser,
            progress_bar=self.ui.progressBar_STT if hasattr(self.ui, 'progressBar_STT') else None
        )
        try:
            self.speech_engine.set_speech_browser(self.ui.lineEdit_SpeechOutput)
            self.speech_engine.signal_emitter.speech_text.connect(self.ui.update_speech_output)
            self.speech_engine.signal_emitter.clear_text.connect(self.ui.lineEdit_SpeechOutput.clear)
        except AttributeError:
            pass
        self._connect_sent_text_signal()
        for button_name, button in self.buttons.items():
            if button:  # Проверяем, что кнопка существует
                button.toggled.connect(lambda state, name=button_name: self.toggle_setting(name, state))
        self.load_settings()
        self.toggle_keyword_filter(self.buttons["tool_button_CheckUseKeyword"].isChecked())
        if self.buttons["tool_button_CheckSpeechReconition"].isChecked():
            self.toggle_speech_recognition(True)
        if hasattr(self.ui, 'comboBox_CheckModelSpeechReconition'):
            self.ui.comboBox_CheckModelSpeechReconition.currentTextChanged.connect(self.change_model)
        if hasattr(self.ui, 'horizontalSlider_NoiseReduction'):
            self.ui.horizontalSlider_NoiseReduction.valueChanged.connect(self.update_noise_level)
            self.ui.horizontalSlider_NoiseReduction.setEnabled(self.buttons["tool_button_NoiseReduction"].isChecked())

    def _connect_sent_text_signal(self):
        try:
            self.speech_engine.signal_emitter.sent_text.connect(self.ui.update_sent_phrase)
        except AttributeError:
            pass

    def load_settings(self):
        config = self._load_config_file()
        for name, button in self.buttons.items():
            if button:
                state = config.get(name, False)
                button.setChecked(state)
                self.toggle_setting(name, state)
        keyword = config.get("VoiceCommandKeyword", "")
        self.keyword_input.setText(keyword)
        self.speech_engine.set_keyword(keyword)
        model = config.get("SpeechRecognitionModel", "")
        if model and hasattr(self.ui, 'comboBox_CheckModelSpeechReconition'):
            self.ui.comboBox_CheckModelSpeechReconition.setCurrentText(model)
            self.speech_engine.set_model(model)
        if self.buttons.get("tool_button_NoiseReduction"):
            self.speech_engine.enable_noise_reduction(self.buttons["tool_button_NoiseReduction"].isChecked())
        if hasattr(self.ui, 'horizontalSlider_NoiseReduction'):
            level = config.get("NoiseReductionLevel", 0)
            self.ui.horizontalSlider_NoiseReduction.setValue(level)
            self.speech_engine.set_noise_level(level)
        # Синхронизация эхо-подавления (удалена обработка EchoCancellation)
        echo_state = config.get("tool_button_EchoCancellation", False)
        if self.buttons.get("tool_button_EchoCancellation"):
            self.buttons["tool_button_EchoCancellation"].setChecked(echo_state)
            self.buttons["tool_button_EchoCancellation"].setEnabled(True)
        self.speech_engine.enable_echo_cancellation(echo_state)

    def save_config(self):
        config = self._load_config_file()
        for name, button in self.buttons.items():
            if button:
                config[name] = button.isChecked()
        config["VoiceCommandKeyword"] = self.keyword_input.text()
        if hasattr(self.ui, 'comboBox_CheckModelSpeechReconition'):
            config["SpeechRecognitionModel"] = self.ui.comboBox_CheckModelSpeechReconition.currentText()
        if hasattr(self.ui, 'horizontalSlider_NoiseReduction') and self.buttons.get("tool_button_NoiseReduction", False).isChecked():
            level = self.ui.horizontalSlider_NoiseReduction.value()
            config["NoiseReductionLevel"] = level
        else:
            config.setdefault("NoiseReductionLevel", 0)
        # Синхронизация эхо-подавления (удалена запись EchoCancellation)
        echo_state = self.buttons.get("tool_button_EchoCancellation", False).isChecked() if self.buttons.get("tool_button_EchoCancellation") else False
        config["tool_button_EchoCancellation"] = echo_state
        self._save_config_file(config)

    def _load_config_file(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_config_file(self, config):
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    def set_tts_mediator(self, tts_mediator):
        self.tts_mediator = tts_mediator
        self.speech_engine.tts_mediator = tts_mediator

    def toggle_setting(self, name, state):
        if self.buttons[name]:
            self.buttons[name].setChecked(state)
            self.buttons[name].update()
            self.buttons[name].repaint()
        if name == "tool_button_CheckSpeechReconition":
            self.toggle_speech_recognition(state)
        elif name == "tool_button_CheckVoiceControl":
            self.toggle_voice_control(state)
        elif name == "tool_button_NoiseReduction":
            self.toggle_noise_reduction(state)
            if hasattr(self.ui, 'horizontalSlider_NoiseReduction'):
                self.ui.horizontalSlider_NoiseReduction.setEnabled(state)
        elif name == "tool_button_CheckUseKeyword":
            self.toggle_keyword_filter(state)
        elif name == "tool_button_EchoCancellation":
            self.toggle_echo_cancellation(state)

    def toggle_speech_recognition(self, state):
        if state:
            self.speech_engine.start_recognition()
        else:
            self.speech_engine.stop_recognition()
        if hasattr(self, 'tts_mediator') and self.tts_mediator:
            self.tts_mediator.queue.append(f"Распознавание речи {'включено.' if state else 'отключено.'}")
            self.tts_mediator.start_play_thread()
        self.save_config()

    def toggle_voice_control(self, state):
        self.speech_engine.enable_voice_control(state)
        self._connect_sent_text_signal()
        if hasattr(self, 'tts_mediator') and self.tts_mediator:
            self.tts_mediator.queue.append(f"Голосовое управление {'включено.' if state else 'выключено.'}")
            self.tts_mediator.start_play_thread()
        self.save_config()

    def toggle_noise_reduction(self, state):
        self.speech_engine.enable_noise_reduction(state)
        if hasattr(self, 'tts_mediator') and self.tts_mediator:
            self.tts_mediator.queue.append(f"Шумоподавление {'включено!' if state else 'отключено!'}")
            self.tts_mediator.start_play_thread()
        self.save_config()

    def toggle_echo_cancellation(self, state):
        self.speech_engine.enable_echo_cancellation(state)
        if self.buttons.get("tool_button_EchoCancellation"):
            self.buttons["tool_button_EchoCancellation"].setChecked(state)
            self.buttons["tool_button_EchoCancellation"].setEnabled(True)
        if hasattr(self, 'tts_mediator') and self.tts_mediator:
            self.tts_mediator.queue.append(f"Подавление эхо {'включено!' if state else 'отключено!'}")
            self.tts_mediator.start_play_thread()
        self.save_config()

    def toggle_keyword_filter(self, state):
        if state and not self.keyword_input.text():
            self.buttons["tool_button_CheckUseKeyword"].setChecked(False)
            state = False
        self.speech_engine.enable_keyword_filter(state)
        if hasattr(self, 'tts_mediator') and self.tts_mediator:
            self.tts_mediator.queue.append(f"Фильтр ключевого слова {'включён.' if state else 'отключён.'}")
            self.tts_mediator.start_play_thread()
        self.save_config()

    def update_keyword(self):
        keyword = self.keyword_input.text()
        self.speech_engine.set_keyword(keyword)
        if not keyword and self.buttons.get("tool_button_CheckUseKeyword", None):
            self.buttons["tool_button_CheckUseKeyword"].setChecked(False)
            self.speech_engine.enable_keyword_filter(False)
        self.save_config()

    def change_model(self, model):
        self.speech_engine.set_model(model)
        self.save_config()

    def update_noise_level(self, value):
        self.speech_engine.set_noise_level(value)
        self.save_config()