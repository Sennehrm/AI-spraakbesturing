# AI spraakbesturing van computer of ledstrip

## Installatie instructies en gebruik uitleg volgen nog!

# Versie updates:
## V1
  - Aanmaak repo.
  - Basis commando's voor aansturing van pc.
  - Beginsel test gui.
  - Uitgevoerde commando's worden naar een json geschreven.



## V2
  - Selectie keuze tussen pc besturing en led besturing.
  - Pc commando's zijn verplaatst naar een json voor een makkelijkere toevoeging van toekomste commando's.
  - Backup python file.
  - Gui toevoeging voor modus selectie, microfoon selectie, muten van mic en start/stop spraak besturing.
  - verzending & ontvanging van data met test mqtt broker.
  - Optimalizatie van recognizer voor betere noise handling.
  - Aanduiding of de geselecteerde microfoon werkt / een input heeft.
  - Weergave led status.
  - Visuele weergave van inkomende audio.
  - Tkinter voor gui.
  - Paho.mqtt.client voor de test broker.
  - Pyaudio voor microfoon selectie.
    
## V3
  - Aansturen van ledstrip met behulp van mqtt.
  - Huidige status ontvangen van letstrip met behulp van mqtt.
  - Aanmaak json bestand met alle ledstrip commando's.
  - Aanmaak json bestand voor mqtt client configuratie.
  - Gui deoptimaliseerd.
  - Meer pc commando's toegevoegd.
  - Onnodige debug berichten verwijderen.
  - Code en gui dummy proof maken.
  - Optimaliseren code.

## V4
  - Meer ledstrip commando's toegevoegd.
  - Commentaar toegevoegd in de code, Belangrijkste items, settings en varabelen worden uitgelegd.
  - requirements.txt file toegevoegd.
    
## Toekomst
  - README updaten & installatie / gebruik instructies invoegen.
  - Met de toekomst kunnen er misschien nog dingen bij komen of aangepast worden.
    
# Belangrijkste gebruikte resources:
  - speech_recognition : https://pypi.org/project/SpeechRecognition/ & https://github.com/Uberi/speech_recognition/blob/master/examples/microphone_recognition.py
  - Json: https://docs.python.org/3/library/json.html#module-json
  - Tkinter : https://docs.python.org/3/library/tkinter.html
  - Paho.mqtt.client: https://eclipse.dev/paho/files/paho.mqtt.python/html/client.html
  - Pyaudio: https://people.csail.mit.edu/hubert/pyaudio/docs/
