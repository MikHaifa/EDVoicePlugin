# -*- coding: utf-8 -*-
# Команда: Запретный_Запад_On
# Процесс: HorizonForbiddenWest
# Группа: Запретный запад Вкл.

import time
import keyboard
import pyautogui
import psutil

# Псевдокод команды:
# Если активна программа 'H:\SteamLibrary\steamapps\common\Horizon Forbidden West Complete Edition\HorizonForbiddenWest.exe'
# TODO: Реализовать проверку активного окна
if is_program_active('H:\SteamLibrary\steamapps\common\Horizon Forbidden West Complete Edition\HorizonForbiddenWest.exe'):
    # Сказать фразу: 'Игра Запретный запад уже открыта'
    # TODO: Реализовать синтез речи
    import pyttsx3
    engine = pyttsx3.init()
    engine.say('Игра Запретный запад уже открыта')
    engine.runAndWait()
else:
    # Сказать фразу: 'Запускаю игру Запретный запад'
    # TODO: Реализовать синтез речи
    import pyttsx3
    engine = pyttsx3.init()
    engine.say('Запускаю игру Запретный запад')
    engine.runAndWait()
    # Открыть файл или программу: notepad.exe
    import subprocess
    subprocess.Popen('notepad.exe')

