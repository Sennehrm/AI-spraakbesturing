import speech_recognition as sr
import datetime
import math
import os
import json
import cv2 

class Commando:
    def uitvoering(self):
        raise NotImplementedError("moet worden overschreven!")
    
class PcCommando(Commando):
    def __init__(self, actie):
        self.actie = actie
    def uitvoering(self):
        tijd = datetime.datetime.now()
        print(f"PcCommando uitgevoerd op {tijd} met actie: {self.actie}")
        try:
            os.system(self.actie)
        except Exception as e:
            print(f"Fout bij uitvoeren van actie: {e}")

# Spraakherkenning functie

def Spraakherkenning():
    herkenner = sr.Recognizer()
    with sr.Microphone() as invoer:
        print("Zeg iets...")
        audio = herkenner.listen(invoer)
        try:
            tekst = herkenner.recognize_google(audio)
            print(f"Je zei: {tekst}")
            return tekst.lower()
        except sr.UnknownValueError:
            print("Kon het commando niet begrijpen.")
            return None
        except sr.RequestError as e:
            print(f"Fout bij spraakherkenningsservice: {e}")
            return None
        
# Commando parser functie

def parse_Commando(tekst):
    if tekst is None:
        return None
    Commando_map = {
        "open notepad": "notepad",
        "open calculator": "calc",
        "open browser": "start chrome",
        "open paint": "mspaint",
        "open camera": "start microsoft.windows.camera:",
        "open settings": "start ms-settings:",
        "open website": "start https://www.xswim.be",
        "open school website": "start https://www.vives.be",
        "open visual studio code": "code",
        "open powershell": "start powershell",
        "open spotify": "start spotify",
        "open youtube": "start https://www.youtube.com",
        "open chat gpt": "start https://chat.openai.com",
        "open verkenner": "explorer"
    }
    for key in Commando_map:
        if key in tekst:
            actie = Commando_map[key]
            return PcCommando(actie)
    print("Geen geldig commando herkend.")
    return None

# Hoofdprogramma

def main():
    cv2.namedWindow("Spraak Besturingssysteem", cv2.WINDOW_NORMAL,)
    uitgevoerde_commandos = []
    while True:
        try:
            tekst = Spraakherkenning()
            if tekst is None:
                continue
            if "stop" in tekst:
                print("Spraak besturingssysteem gestopt.")
                break
            commando = parse_Commando(tekst)
            if commando:
                commando.uitvoering()
                uitgevoerde_commandos.append((datetime.datetime.now(), tekst))
        except KeyboardInterrupt:
            print("Spraak besturingssysteem gestopt door gebruiker.")
            break
        except Exception as e:
            print(f"Fout opgetreden: {e}")
    try:
        with open("uitgevoerde_commandos.json", "w") as f:
            json.dump(uitgevoerde_commandos, f, default=str)
        print("Uitgevoerde commandos opgeslagen in uitgevoerde_commandos.json")
    except Exception as e:
        print(f"Fout bij opslaan van commandos: {e}")
if __name__ == "__main__":
    main()