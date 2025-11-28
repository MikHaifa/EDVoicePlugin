from PySide6.QtCore import QObject, Signal
from pathlib import Path
import getpass

class STTBus(QObject):
    text_recognized = Signal(str)

    def __init__(self):
        super().__init__()
        self.output_dir = Path(f"C:/Users/{getpass.getuser()}/Saved Games/EDVoicePlugin")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_file = self.output_dir / "voice_commands.txt"

    def send_to_voiceattack(self, text):
        try:
            with open(self.output_file, 'a', encoding='utf-8') as f:
                f.write(text + '\n')
        except Exception as e:
            pass