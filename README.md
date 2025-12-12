# AI spraakbesturing van computer of ledstrip

# Installatie

1. Clone deze repo: https://github.com/Sennehrm/AI-spraakbesturing.git
2. Open een terminal en voer <b><ins>pip install -r requirements.txt</ins></b> uit.
3. Pas de mqtt info aan in mqtt_config.json.
  - Indien je een lokale test broker gebruikt laat dit staan.
4. Pas de led_commandos.json aan zodat na de <b><ins>:</ins></b> en binnen de <b><ins>""</ins></b> de juiste data wordt verstuurd naar de broker.
5. Voeg indien nodig meer pc of led commando's toe.

# Gebruik

1. Zorg er voor dat mqtt broker online is.
   - Indien je een lokale broker gebruikt start deze in je terminal met <b><ins>& "C:\Program Files\mosquitto\mosquitto.exe" -v</ins></b>.
3. Run de spraak.py file. Nu zal er een extra window geopend worden met de gui er op.
4. Op de gui vindt men allerlei dingen
  - Selectie knop voor pc besturing of led besturing.
  - Status weergave van de mqtt connectie.
  - Dropdown menu waar de juiste microfoon kan geslecteerd worden.
  - Naast de dropdown staat een kleine visualisatie om aan te tonen dat de mic werkt.
  - Ronde mute knop die de microfoon kan muten.
  - Audio visualisatie die beweegt op mate van het spraak volume.
  - Knop om te starten met luisteren naar microfoon input.
  - Knop om te stoppen met luisteren.
  - Feedback zin die van alles toont, dingen zoals: uitgevoerde command, kalibratie, geen bestaand command, verzonden item naar mqtt, starten met luisteren, gestopt, ...
4. Voor debugging gebruik een mqtt viewer zoals <b><ins>MQTTX</ins></b>, <b><ins>MQTT Explorer</ins></b>, <b><ins>MQTTBox</ins></b>, ...
5. Zorg er voor dat de juiste microfoon is geslecteerd en de mute knop op rood staat.
6. Druk op <b><ins>begin met luisteren</ins><b>. Om te stoppen druk op <b><ins>stop</ins></b>.

<h1>Begin met praten!</h1>


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
  - Met de toekomst kunnen er misschien nog dingen bij komen of aangepast worden.
    
# Belangrijkste gebruikte resources:
  - speech_recognition : https://pypi.org/project/SpeechRecognition/ & https://github.com/Uberi/speech_recognition/blob/master/examples/microphone_recognition.py
  - Json: https://docs.python.org/3/library/json.html#module-json
  - Tkinter : https://docs.python.org/3/library/tkinter.html
  - Paho.mqtt.client: https://eclipse.dev/paho/files/paho.mqtt.python/html/client.html
  - Pyaudio: https://people.csail.mit.edu/hubert/pyaudio/docs/
