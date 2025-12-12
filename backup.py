

import speech_recognition as sr
import datetime
import math
import os, sys, subprocess, webbrowser
import json
import cv2 
import numpy as np
import sounddevice as sd
import tkinter as tk
from tkinter import ttk
import threading
import queue
import paho.mqtt.client as mqtt
import pyaudio

# ============================================================================
# STYLING CONFIGURATIE
# ============================================================================

class AppStyle:    
    BG_PRIMARY = "#1e1e2e"
    BG_SECONDARY = "#313244"
    BG_DARK = "#181825"
    
    TEXT_PRIMARY = "#cdd6f4"
    TEXT_SECONDARY = "#a6adc8"
    TEXT_YELLOW = "#f9e2af"
    
    BLUE = "#89b4fa"
    BLUE_LIGHT = "#74c7ec"
    GREEN = "#a6e3a1"
    GREEN_DARK = "#94e2d5"
    RED = "#f38ba8"
    RED_LIGHT = "#eba0ac"
    GRAY = "#45475a"
    
    FONT_TITLE = ("Arial", 28, "bold")
    FONT_HEADING = ("Arial", 14, "bold")
    FONT_BUTTON = ("Arial", 12, "bold")
    FONT_BUTTON_LARGE = ("Arial", 14, "bold")
    FONT_BODY = ("Arial", 12)
    FONT_SMALL = ("Arial", 11)
    FONT_TINY = ("Arial", 10)
    FONT_EMOJI = ("Segoe UI Emoji", 15)
    
    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 600
    
    BUTTON_PADX = 30
    BUTTON_PADY = 15
    MODE_BUTTON_PADX = 20
    MODE_BUTTON_PADY = 10
    
    MUTE_BUTTON_SIZE = 50
    MUTE_CIRCLE_SIZE = (5, 5, 45, 45)
    MUTE_ICON_POS = (25, 24)
    
    CANVAS_WIDTH = 600
    CANVAS_HEIGHT = 150
    BAR_COUNT = 20
    BAR_WIDTH = 25
    BAR_SPACING = 5

# ============================================================================
# BUSINESS LOGIC - Commando Classes
# ============================================================================

class Commando:
    def uitvoering(self):
        raise NotImplementedError("moet worden overschreven!")

# PC commando's uitvoeren (notepad, calculator, etc.)
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

# LED commando's via MQTT versturen
class LedCommando(Commando):
    def __init__(self, actie, mqtt_client=None):
        self.actie = actie
        self.mqtt_client = mqtt_client
        
    def uitvoering(self):
        tijd = datetime.datetime.now()
        print(f"LedCommando uitgevoerd op {tijd} met actie: {self.actie}")
        
        if self.mqtt_client:
            self.mqtt_client.publish_command(self.actie)

# ============================================================================
# BUSINESS LOGIC - MQTT Client
# ============================================================================

# Laad MQTT broker instellingen uit mqtt_config.json
def load_mqtt_config():
    default_config = { # Standaard instellingen indien bestand ontbreekt of onjuist is
        "broker": "localhost",
        "port": 1883,
        "topic": "led/commands"
    }
    
    try:
        with open("mqtt_config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            
            # Valideer configuratie
            if not isinstance(config.get("broker"), str) or not config.get("broker"):
                config["broker"] = default_config["broker"]
            
            if not isinstance(config.get("port"), int) or not (1 <= config.get("port", 0) <= 65535):
                config["port"] = default_config["port"]
            
            if not isinstance(config.get("topic"), str) or not config.get("topic"):
                config["topic"] = default_config["topic"]
            
            return config
            
    except FileNotFoundError:
        # Maak bestand aan met standaard configuratie
        try:
            with open("mqtt_config.json", "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2)
        except Exception as e:
            pass
        return default_config
        
    except json.JSONDecodeError as e:
        return default_config
    except Exception as e:
        return default_config

# MQTT client met automatische reconnect en status feedback
class MqttClient:
    def __init__(self, broker=None, port=None, topic=None, status_callback=None):
        config = load_mqtt_config()
        self.broker = broker or config.get("broker")
        self.port = port or config.get("port")
        self.topic = topic or config.get("topic")
        self.client = mqtt.Client()
        self.connected = False
        self.message_callback = None
        self.status_callback = status_callback
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
        # Valideer configuratie
        if not self.broker or not self.port or not self.topic:
            raise ValueError("MQTT configuratie onvolledig")
        
        # Callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish
        self.client.on_message = self._on_message
        
        # Probeer verbinding te maken
        self.connect()
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            self.reconnect_attempts = 0
            self.client.subscribe(self.topic)
            
            if self.status_callback:
                self.status_callback(True, "Verbonden") #aanduiding van succesvolle verbinding
        else:
            self.connected = False
            if self.status_callback:
                self.status_callback(False, f"Fout: {rc}") #aanduiding van verbindingsfout
    
    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        
        if self.status_callback:
            self.status_callback(False, "Verbinding verbroken")
        
        # Automatisch opnieuw verbinden (max 5 pogingen)
        if rc != 0 and self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            try:
                self.client.reconnect()
            except Exception as e:
                pass
    
    def _on_publish(self, client, userdata, mid):
        pass
    
    def _on_message(self, client, userdata, msg):
        try:
            command = msg.payload.decode('utf-8') #decoderen van ontvangen bericht
            print(f"MQTT ontvangen: '{command}'") #tonen van ontvangen bericht
            
            if self.message_callback:
                self.message_callback(command)
        except Exception as e:
            pass
    
    def set_message_callback(self, callback):
        self.message_callback = callback
    
    def connect(self):
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            return True
        except Exception as e:
            self.connected = False
            return False
    
    # Verstuur LED commando naar MQTT broker
    def publish_command(self, command):
        if not command or not isinstance(command, str):
            return False
            
        if not self.connected:
            if self.status_callback:
                self.status_callback(False, "Niet verbonden")
            return False
            
        try:
            result = self.client.publish(self.topic, command, qos=1) #verzenden van mqtt bericht
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"MQTT: '{command}' → {self.topic}") #tonen van verzonden bericht
                return True
            else:
                return False
        except Exception as e:
            return False
    
    def disconnect(self):
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception as e:
            pass

# ============================================================================
# BUSINESS LOGIC - Parser Functions
# ============================================================================

# Beheert alle PC en LED commando's uit JSON files
class CommandoManager:
    def __init__(self, mqtt_client=None):
        self.pc_commandos = {}
        self.led_commandos = {}
        self.mqtt_client = mqtt_client
        self._load_commandos()
    
    def _load_commandos(self):
        try:
            with open("pc_commandos.json", "r", encoding="utf-8") as f:
                self.pc_commandos = json.load(f) #laden van pc commando's
        except FileNotFoundError:
            self.pc_commandos = {}
        except json.JSONDecodeError as e:
            self.pc_commandos = {}
        
        try:
            with open("led_commandos.json", "r", encoding="utf-8") as f:
                self.led_commandos = json.load(f) #laden van led commando's
        except FileNotFoundError:
            self.led_commandos = {}
        except json.JSONDecodeError as e:
            self.led_commandos = {}
    
    def get_pc_commando(self, tekst):
        if not tekst:
            return None
        
        # Zoek naar commando in pc tekst
        for key in self.pc_commandos:
            if key in tekst:
                return PcCommando(self.pc_commandos[key])
        
        return None
    
    def get_led_commando(self, tekst):
        if not tekst:
            return None
        
        # Zoek naar commando in led tekst
        for key in self.led_commandos:
            if key in tekst:
                return LedCommando(self.led_commandos[key], mqtt_client=self.mqtt_client)
        
        return None
    
    def is_valid_pc_command(self, tekst):
        if not tekst:
            return False
        return any(key in tekst for key in self.pc_commandos.keys())
    
    def is_valid_led_command(self, tekst):
        if not tekst:
            return False
        return any(key in tekst for key in self.led_commandos.keys())

# Singleton instances (1x aanmaken, overal gebruiken)
_commando_manager = None
_mqtt_client = None

def get_mqtt_client(): # Singleton MQTT client
    global _mqtt_client
    if _mqtt_client is None:
        _mqtt_client = MqttClient()
    return _mqtt_client

def get_commando_manager(): # Singleton CommandoManager
    global _commando_manager
    if _commando_manager is None:
        mqtt_client = get_mqtt_client()
        _commando_manager = CommandoManager(mqtt_client=mqtt_client)
    return _commando_manager

def parse_Commando(tekst): # Parse PC commando uit tekst
    if tekst is None:
        return None
    
    manager = get_commando_manager() # Haal CommandoManager op
    commando = manager.get_pc_commando(tekst)
    return commando

def parse_Led_Commando(tekst): # Parse LED commando uit tekst
    if tekst is None:
        return None
    
    manager = get_commando_manager() # Haal CommandoManager op
    commando = manager.get_led_commando(tekst)
    return commando

# ============================================================================
# BUSINESS LOGIC - Audio & Speech Recognition
# ============================================================================

# Audio verwerking en spraakherkenning instellingen
class AudioProcessor:
    @staticmethod
    def configure_recognizer():
        herkenner = sr.Recognizer()
        herkenner.energy_threshold = 4000 #basis energie drempel
        herkenner.dynamic_energy_threshold = True #automatische aanpassing energie drempel
        herkenner.dynamic_energy_adjustment_damping = 0.15 #snelheid van aanpassing
        herkenner.dynamic_energy_ratio = 1.5 #versterking van energie drempel
        herkenner.pause_threshold = 0.8 #tijd in seconden voor pauze
        herkenner.phrase_threshold = 0.2 #minimale tijd voor spraak
        herkenner.non_speaking_duration = 0.5 #tijd voor en na spraak
        return herkenner

# ============================================================================
# GUI - Main Application
# ============================================================================

# Hoofdapplicatie met GUI
class SpraakennennerGUI:
    def __init__(self, root):
        self.root = root
        self.style = AppStyle()
        
        self.root.title("AI Spraakbesturing")
        self.root.geometry(f"{self.style.WINDOW_WIDTH}x{self.style.WINDOW_HEIGHT}")
        self.root.configure(bg=self.style.BG_PRIMARY)
        
        self.mode = tk.StringVar(value="PC") # Standaard modus is PC
        self.selected_mic = tk.StringVar()
        self.is_listening = False
        self.is_muted = False
        self.audio_queue = queue.Queue(maxsize=100) # Queue voor audio niveaus
        self.uitgevoerde_commandos = []
        self.current_led_status = "Uit" # Huidige LED status
        self.mqtt_status = "Connecting..." # Huidige MQTT status
        
        self.setup_ui()
        
        # MQTT ontvangen berichten callback
        mqtt_client = get_mqtt_client()
        mqtt_client.status_callback = self.update_mqtt_status
        mqtt_client.set_message_callback(self.update_led_status_from_mqtt)
        
        # Audio visualizer starten
        self.start_audio_monitor()
    
    # ------------------------------------------------------------------------
    # UI Setup Methods
    # ------------------------------------------------------------------------
    
    def setup_ui(self):
        self._create_title()
        self._create_mode_selector() 
        self._create_mic_selector()
        self._create_mqtt_status()
        self._create_mute_button()
        self._create_led_status()
        self._create_audio_visualizer()
        self._create_control_buttons()
        self._create_status_label()

    def _create_title(self): # Titel label
        title_frame = tk.Frame(self.root, bg=self.style.BG_PRIMARY)
        title_frame.pack(pady=20)
        
        title_label = tk.Label(
            title_frame, 
            text="🎤 AI Spraakbesturing",
            font=self.style.FONT_TITLE,
            bg=self.style.BG_PRIMARY,
            fg=self.style.TEXT_PRIMARY
        )
        title_label.pack()
    
    def _create_mode_selector(self): # Modus selectie knoppen
        mode_frame = tk.Frame(self.root, bg=self.style.BG_PRIMARY)
        mode_frame.pack(pady=20)
        
        mode_label = tk.Label(
            mode_frame,
            text="Selecteer Modus:",
            font=self.style.FONT_HEADING,
            bg=self.style.BG_PRIMARY,
            fg=self.style.TEXT_PRIMARY
        )
        mode_label.pack(side=tk.LEFT, padx=10)
        
        # PC Button
        self.pc_button = tk.Button(
            mode_frame,
            text="🖥️ PC Besturing",
            font=self.style.FONT_BUTTON,
            bg=self.style.BLUE,
            fg=self.style.BG_PRIMARY,
            activebackground=self.style.BLUE_LIGHT,
            relief=tk.RAISED,
            borderwidth=3,
            padx=self.style.MODE_BUTTON_PADX,
            pady=self.style.MODE_BUTTON_PADY,
            command=lambda: self.set_mode("PC")
        )
        self.pc_button.pack(side=tk.LEFT, padx=10)
        
        # LED Button
        self.led_button = tk.Button(
            mode_frame,
            text="💡 LED Besturing",
            font=self.style.FONT_BUTTON,
            bg=self.style.GRAY,
            fg=self.style.TEXT_PRIMARY,
            activebackground=self.style.BLUE_LIGHT,
            relief=tk.FLAT,
            borderwidth=3,
            padx=self.style.MODE_BUTTON_PADX,
            pady=self.style.MODE_BUTTON_PADY,
            command=lambda: self.set_mode("LED")
        )
        self.led_button.pack(side=tk.LEFT, padx=10)
    
    def _create_mic_selector(self): # Microfoon selectie dropdown
        mic_frame = tk.Frame(self.root, bg=self.style.BG_PRIMARY)
        mic_frame.pack(pady=10)
        
        mic_label = tk.Label(
            mic_frame,
            text="Microfoon:",
            font=self.style.FONT_BODY,
            bg=self.style.BG_PRIMARY,
            fg=self.style.TEXT_PRIMARY
        )
        mic_label.pack(side=tk.LEFT, padx=10)
        
        # Haal beschikbare microfoons op
        self.mic_devices = self._get_audio_devices()
        mic_names = [f"{idx}: {name}" for idx, name in self.mic_devices]
        
        if not mic_names:
            mic_names = ["Geen microfoons gevonden"]
        
        # Dropdown voor microfoon selectie
        self.mic_dropdown = ttk.Combobox(
            mic_frame,
            textvariable=self.selected_mic,
            values=mic_names,
            state="readonly",
            width=50,
            font=self.style.FONT_SMALL
        )
        
        if mic_names and mic_names[0] != "Geen microfoons gevonden":
            self.mic_dropdown.current(0)
            self.current_mic_index = self.mic_devices[0][0] if self.mic_devices else None
        else:
            self.current_mic_index = None
        
        self.mic_dropdown.bind('<<ComboboxSelected>>', self._on_mic_change)
        self.mic_dropdown.pack(side=tk.LEFT, padx=10)
        
        # Info label voor audio status
        self.audio_info_label = tk.Label(
            mic_frame,
            text="🎤",
            font=self.style.FONT_BODY,
            bg=self.style.BG_PRIMARY,
            fg=self.style.GREEN
        )
        self.audio_info_label.pack(side=tk.LEFT, padx=10)
    
    def _create_mqtt_status(self): # MQTT status indicator
        mqtt_frame = tk.Frame(self.root, bg=self.style.BG_PRIMARY)
        mqtt_frame.pack(pady=5)
        
        mqtt_label = tk.Label(
            mqtt_frame,
            text="MQTT:",
            font=self.style.FONT_SMALL,
            bg=self.style.BG_PRIMARY,
            fg=self.style.TEXT_SECONDARY
        )
        mqtt_label.pack(side=tk.LEFT, padx=5)
        
        self.mqtt_status_label = tk.Label(
            mqtt_frame,
            text="⚫ Verbinden...",
            font=self.style.FONT_SMALL,
            bg=self.style.BG_PRIMARY,
            fg=self.style.TEXT_SECONDARY
        )
        self.mqtt_status_label.pack(side=tk.LEFT, padx=5)
    
    def _get_audio_devices(self): # Haal lijst van audio input devices op
        devices = []
        try:
            p = pyaudio.PyAudio()
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:  # Alleen input devices
                    devices.append((i, info['name']))
            p.terminate()
        except Exception as e:
            pass
        return devices
    
    def _on_mic_change(self, event=None): # Microfoon wijziging handler
        selection = self.mic_dropdown.get()
        if selection and ':' in selection:
            try:
                idx = int(selection.split(':')[0])
                self.current_mic_index = idx
                
                # Herstart audio stream met nieuwe microfoon
                if hasattr(self, 'stream'):
                    self.stream.stop()
                    self.stream.close()
                self.start_audio_monitor()
                
                self.status_label.config(text=f"Microfoon gewijzigd: {selection}")
            except Exception as e:
                pass
    
    def _create_mute_button(self): # Mute knop
        mic_frame = tk.Frame(self.root, bg=self.style.BG_PRIMARY)
        mic_frame.pack(pady=10)
        
        mute_frame = tk.Frame(mic_frame, bg=self.style.BG_PRIMARY)
        mute_frame.pack()
        
        self.mute_canvas = tk.Canvas(
            mute_frame,
            width=self.style.MUTE_BUTTON_SIZE,
            height=self.style.MUTE_BUTTON_SIZE,
            bg=self.style.BG_PRIMARY,
            highlightthickness=0,
            cursor="hand2"
        )
        self.mute_canvas.pack()
        
        # Cirkel achtergrond
        self.mute_circle = self.mute_canvas.create_oval(
            *self.style.MUTE_CIRCLE_SIZE,
            fill=self.style.GREEN,
            outline=self.style.TEXT_PRIMARY,
            width=2
        )
        
        # Microfoon emoji
        self.mute_icon = self.mute_canvas.create_text(
            *self.style.MUTE_ICON_POS,
            text="🎙️",
            font=self.style.FONT_EMOJI,
            fill=self.style.BG_PRIMARY,
            anchor="center"
        )
        
        # Mute streep (verborgen)
        self.mute_line = self.mute_canvas.create_line(
            12, 12, 38, 38,
            fill=self.style.BG_PRIMARY,
            width=3,
            state="hidden"
        )
        
        self.mute_canvas.bind("<Button-1>", lambda e: self.toggle_mute())
    
    def _create_led_status(self): # LED status display
        self.led_status_frame = tk.Frame(
            self.root, 
            bg=self.style.BG_SECONDARY, 
            relief=tk.RIDGE, 
            borderwidth=2
        )
        
        led_status_title = tk.Label( 
            self.led_status_frame,
            text="💡 LED Strip Status",
            font=self.style.FONT_BUTTON,
            bg=self.style.BG_SECONDARY,
            fg=self.style.TEXT_PRIMARY
        )
        led_status_title.pack(pady=5)
        
        self.led_status_label = tk.Label(
            self.led_status_frame,
            text="Uit",
            font=self.style.FONT_HEADING,
            bg=self.style.BG_SECONDARY,
            fg=self.style.TEXT_YELLOW
        )
        self.led_status_label.pack(pady=10, padx=20)
    
    def _create_audio_visualizer(self): # Audio visualizer bars
        viz_frame = tk.Frame(self.root, bg=self.style.BG_PRIMARY)
        viz_frame.pack(pady=30)
        
        viz_label = tk.Label(
            viz_frame,
            text="Audio Niveau:",
            font=self.style.FONT_BODY,
            bg=self.style.BG_PRIMARY,
            fg=self.style.TEXT_PRIMARY
        )
        viz_label.pack()
        
        # Canvas voor audio bars
        self.canvas = tk.Canvas(
            viz_frame,
            width=self.style.CANVAS_WIDTH,
            height=self.style.CANVAS_HEIGHT,
            bg=self.style.BG_DARK,
            highlightthickness=0
        )
        self.canvas.pack(pady=10)
        
        # Maak audio bars
        self.bars = []
        self.bar_count = self.style.BAR_COUNT
        
        for i in range(self.bar_count):
            x = i * (self.style.BAR_WIDTH + self.style.BAR_SPACING) + 10
            bar = self.canvas.create_rectangle(
                x, 140, 
                x + self.style.BAR_WIDTH, 140,
                fill=self.style.GRAY,
                outline=""
            )
            self.bars.append(bar)
    
    def _create_control_buttons(self): # Start/Stop knoppen
        control_frame = tk.Frame(self.root, bg=self.style.BG_PRIMARY)
        control_frame.pack(pady=20)
        
        self.start_button = tk.Button(
            control_frame,
            text="▶ Start Luisteren",
            font=self.style.FONT_BUTTON_LARGE,
            bg=self.style.GREEN,
            fg=self.style.BG_PRIMARY,
            activebackground=self.style.GREEN_DARK,
            padx=self.style.BUTTON_PADX,
            pady=self.style.BUTTON_PADY,
            command=self.start_listening
        )
        self.start_button.pack(side=tk.LEFT, padx=10)
        
        self.stop_button = tk.Button(
            control_frame,
            text="⏹ Stop",
            font=self.style.FONT_BUTTON_LARGE,
            bg=self.style.RED,
            fg=self.style.BG_PRIMARY,
            activebackground=self.style.RED_LIGHT,
            padx=self.style.BUTTON_PADX,
            pady=self.style.BUTTON_PADY,
            state=tk.DISABLED,
            command=self.stop_listening
        )
        self.stop_button.pack(side=tk.LEFT, padx=10)
    
    def _create_status_label(self): # Status label onderaan
        self.status_label = tk.Label(
            self.root,
            text="Klaar om te starten",
            font=self.style.FONT_SMALL,
            bg=self.style.BG_PRIMARY,
            fg=self.style.TEXT_SECONDARY
        )
        self.status_label.pack(pady=10)
    
    # ------------------------------------------------------------------------
    # Event Handlers
    # ------------------------------------------------------------------------
    
    def toggle_mute(self): # Mute/unmute microfoon
        self.is_muted = not self.is_muted
        
        if self.is_muted:
            self.mute_canvas.itemconfig(self.mute_line, state="normal")
            self.mute_canvas.itemconfig(
                self.mute_circle, 
                fill=self.style.RED, 
                outline=self.style.RED
            )
            self.status_label.config(text="🔇 Microfoon gedempt")
            
            if hasattr(self, 'stream') and self.stream.active:
                self.stream.stop()
        else:
            self.mute_canvas.itemconfig(self.mute_line, state="hidden")
            self.mute_canvas.itemconfig(
                self.mute_circle, 
                fill=self.style.GREEN, 
                outline=self.style.TEXT_PRIMARY
            )
            self.status_label.config(text="🔊 Microfoon actief")
            
            if hasattr(self, 'stream') and not self.stream.active:
                self.stream.start()
    
    def set_mode(self, mode): # Wijzig modus tussen PC en LED
        self.mode.set(mode)
        
        if mode == "PC":
            self.pc_button.configure(bg=self.style.BLUE, relief=tk.RAISED)
            self.led_button.configure(bg=self.style.GRAY, relief=tk.FLAT)
            self.led_status_frame.pack_forget()
        else:
            self.pc_button.configure(bg=self.style.GRAY, relief=tk.FLAT)
            self.led_button.configure(bg=self.style.BLUE, relief=tk.RAISED)
            self.led_status_frame.pack(pady=10, before=self.canvas.master)
            
        self.status_label.config(text=f"Modus gewijzigd naar: {mode}")
    
    # ------------------------------------------------------------------------
    # Audio Processing
    # ------------------------------------------------------------------------
    
    # Update MQTT status indicator (thread-safe)
    def update_mqtt_status(self, connected, status_text):
        def update():
            if connected:
                self.mqtt_status_label.config(
                    text=f"🟢 {status_text}",
                    fg=self.style.GREEN
                )
            else:
                self.mqtt_status_label.config(
                    text=f"🔴 {status_text}",
                    fg=self.style.RED
                )
        
        try:
            self.root.after(0, update)
        except Exception as e:
            pass
    
    # ------------------------------------------------------------------------
    # Audio Processing
    # ------------------------------------------------------------------------
    
    # Audio stream voor visualizer bars
    def start_audio_monitor(self):
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Audio stream status: {status}")
            
            try:
                # Bereken RMS volume en versterk het signaal
                volume_norm = np.linalg.norm(indata) * 15
                
                # Voeg toe aan queue, skip als vol
                try:
                    self.audio_queue.put_nowait(volume_norm)
                except queue.Full:
                    # Queue is vol, skip dit sample
                    pass
                
                # Update audio info indicator (green bij geluid)
                if volume_norm > 5:
                    self.root.after(0, lambda: self.audio_info_label.config(
                        text="🔊", fg=self.style.GREEN
                    ))
                else:
                    if hasattr(self, 'root') and hasattr(self, 'audio_info_label'):
                        try:
                            self.root.after(0, lambda: self.audio_info_label.config(
                                text="🎤", fg=self.style.GRAY
                            ))
                        except:
                            pass
            except Exception as e:
                print(f"Audio callback error: {e}")
        
        try:
            device_index = self.current_mic_index if hasattr(self, 'current_mic_index') else None
            print(f"Starting audio monitor met device index: {device_index}...")
            
            # Probeer stream te starten
            self.stream = sd.InputStream(
                callback=audio_callback,
                channels=1,
                device=device_index,
                samplerate=44100,
                blocksize=2048
            )
            self.stream.start()
            
            # Haal device info op
            device_info = sd.query_devices(device_index, 'input')
            print(f"Audio stream actief op: {device_info['name']}")
            print(f"  Sample rate: {device_info['default_samplerate']} Hz")
            print(f"  Channels: {device_info['max_input_channels']}")
            
            # Start audio bars update loop (alleen als nog niet actief)
            if not hasattr(self, 'audio_bars_running') or not self.audio_bars_running:
                self.audio_bars_running = True
                print("Starting audio bars animation...")
                self.update_audio_bars()
        except Exception as e:
            print(f"Fout bij starten audio monitor: {e}")
            self.status_label.config(text=f"Audio fout: {e}")
            import traceback
            traceback.print_exc()
    
    def update_audio_bars(self): # Update audio visualizer bars
        if not self.audio_bars_running:
            return
            
        try:
            # Bewaar laatste volume voor smoothing
            if not hasattr(self, 'last_volume'):
                self.last_volume = 0
            
            # Haal audio data op uit queue
            current_volume = self.last_volume * 0.7  # Decay voor smooth animatie
            audio_detected = False
            
            queue_items = 0
            while not self.audio_queue.empty():
                volume = self.audio_queue.get()
                queue_items += 1
                if self.is_muted:
                    volume = 0
                current_volume = max(current_volume, volume)
                if volume > 5:
                    audio_detected = True
            
            self.last_volume = current_volume
            
            # Update alle bars
            for i, bar in enumerate(self.bars):
                # Creëer golf effect vanuit midden
                offset = abs(i - self.bar_count / 2)
                height_factor = 1 - (offset / self.bar_count)
                height = max(10, min(130, current_volume * height_factor))
                
                # Kleur gradient gebaseerd op hoogte
                if height < 40:
                    color = self.style.GRAY
                elif height < 80:
                    color = self.style.BLUE
                else:
                    color = self.style.GREEN
                
                # Update bar positie en kleur
                coords = self.canvas.coords(bar)
                if coords:
                    self.canvas.coords(bar, coords[0], 140 - height, coords[2], 140)
                    self.canvas.itemconfig(bar, fill=color)
        except Exception as e:
            pass
        
        # Schedule volgende update
        if self.audio_bars_running:
            self.root.after(50, self.update_audio_bars)
    
    # ------------------------------------------------------------------------
    # Speech Recognition
    # ------------------------------------------------------------------------
    
    def start_listening(self): # Start spraakherkenning
        self.is_listening = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="🎤 Luisteren... Zeg een commando!")
        
        threading.Thread(target=self.listen_loop, daemon=True).start()
    
    def stop_listening(self): # Stop spraakherkenning
        self.is_listening = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Gestopt")
        self.save_commandos()
    
    # Spraakherkenning loop (draait in aparte thread)
    def listen_loop(self):
        herkenner = AudioProcessor.configure_recognizer()
        
        # Kalibreer één keer bij starten
        calibrated = False
        error_count = 0
        max_errors = 5
        
        while self.is_listening:
            if self.is_muted:
                continue
            
            try:
                with sr.Microphone(device_index=self.current_mic_index) as invoer:
                    # Kalibreer alleen de eerste keer
                    if not calibrated:
                        try:
                            self.root.after(0, lambda: self.status_label.config(text="🎧 Kalibreren..."))
                            herkenner.adjust_for_ambient_noise(invoer, duration=1)
                            calibrated = True
                        except Exception as e:
                            calibrated = True
                    
                    try:
                        self.root.after(0, lambda: self.status_label.config(text="🎤 Luisteren..."))
                    except:
                        pass
                        
                    audio = herkenner.listen(invoer, timeout=3, phrase_time_limit=5)
                    
                    try:
                        tekst = herkenner.recognize_google(audio, language="nl-NL")
                        error_count = 0  # Reset error counter
                        try:
                            self.root.after(0, lambda t=tekst: self.process_command(t))
                        except:
                            pass
                    except sr.UnknownValueError: # Onbekende spraak
                        try:
                            self.root.after(0, lambda: self.status_label.config(
                                text="Kon het commando niet begrijpen"
                            ))
                        except:
                            pass
                    except sr.RequestError as e: # Service fout
                        error_count += 1
                        try:
                            self.root.after(0, lambda err=str(e): self.status_label.config(
                                text=f"Service fout: {err}"
                            ))
                        except:
                            pass
                        if error_count >= max_errors:
                            break
                            
            except sr.WaitTimeoutError: # Timeout bij luisteren
                continue
            except Exception as e: # Algemene fout
                error_count += 1
                try:
                    self.root.after(0, lambda err=str(e): self.status_label.config(text=f"Fout: {err}"))
                except:
                    pass
                if error_count >= max_errors:
                    break
        
        # Cleanup
        if error_count >= max_errors:
            try:
                self.root.after(0, lambda: self.stop_listening())
            except:
                pass
    
    def process_command(self, tekst): # Verwerk herkend commando
        if not tekst or not isinstance(tekst, str):
            return
            
        try:
            self.status_label.config(text=f'Je zei: "{tekst}"') # Toon herkend tekst
        except:
            pass
            
        tekst_lower = tekst.lower() # Voor eenvoudige matching
        
        if "stop" in tekst_lower:
            self.stop_listening() # Stop commando
            return
        
        if self.mode.get() == "PC": # PC modus
            self._process_pc_command(tekst, tekst_lower)
        else:
            self._process_led_command(tekst, tekst_lower)
    
    def _process_pc_command(self, tekst, tekst_lower): # Verwerk PC commando
        commando = parse_Commando(tekst_lower)
        if commando:
            commando.uitvoering()
            self.uitgevoerde_commandos.append((datetime.datetime.now(), tekst))
            self.status_label.config(text=f'✓ Commando uitgevoerd: "{tekst}"')
        else:
            self.status_label.config(text="Geen geldig commando herkend")
    
    def _process_led_command(self, tekst, tekst_lower): # Verwerk LED commando
        led_commando = parse_Led_Commando(tekst_lower)
        if led_commando:
            led_commando.uitvoering()
            self.uitgevoerde_commandos.append((datetime.datetime.now(), f"LED: {tekst}"))
            
            # Update LED status
            self._update_led_status_display(tekst_lower)
            self.status_label.config(text=f'✓ LED Commando uitgevoerd: "{tekst}"')
        else:
            self.status_label.config(text="Geen geldig LED commando herkend")
    
    def _update_led_status_display(self, command_text): # Update LED status label
        status_map = {
            "aan": "Aan",
            "uit": "Uit",
            "rood": "🔴 Rood",
            "blauw": "🔵 Blauw",
            "groen": "🟢 Groen",
            "geel": "🟡 Geel",
            "paars": "🟣 Paars",
            "oranje": "🟠 Oranje",
            "wit": "⚪ Wit",
            "regenboog": "🌈 Regenboog",
            "knipperen": "⚡ Knipperend"
        }
        
        for key, status in status_map.items():
            if key in command_text.lower():
                self.current_led_status = status
                break
        
        # Update alleen als LED status frame zichtbaar is
        if self.led_status_frame.winfo_ismapped():
            self.led_status_label.config(text=self.current_led_status)
    
    def update_led_status_from_mqtt(self, command): # Update LED status van MQTT bericht
        if not command or not isinstance(command, str):
            return
        
        def safe_update():
            try:
                # Update status display
                self._update_led_status_display(command)
                
                # Update status label
                self.status_label.config(
                    text=f'MQTT ontvangen: "{command}"'
                )
            except Exception as e:
                pass
        
        try:
            self.root.after(0, safe_update)
        except Exception as e:
            pass
    
    # ------------------------------------------------------------------------
    # Data Management
    # ------------------------------------------------------------------------
    
    def save_commandos(self): # Sla uitgevoerde commando's op in JSON file
        try:
            with open("uitgevoerde_commandos.json", "w") as f:
                json.dump(self.uitgevoerde_commandos, f, default=str, indent=2)
        except Exception as e:
            pass
    
    # Cleanup bij afsluiten applicatie
    def on_closing(self):
        self.is_listening = False
        self.audio_bars_running = False
        
        if hasattr(self, 'stream'):
            try:
                self.stream.stop()
                self.stream.close()
            except Exception as e:
                pass
        
        try:
            mqtt_client = get_mqtt_client()
            mqtt_client.disconnect()
        except Exception as e:
            pass
        
        try:
            self.save_commandos()
        except Exception as e:
            pass
        
        try:
            self.root.destroy()
        except Exception as e:
            pass

# ============================================================================
# MAIN PROGRAM
# ============================================================================

# Global variables voor instance management
_window_lock = threading.Lock()
_window_running = False
_pending_runs = 0

# Hoofdprogramma
def main(): 
    global _window_running, _pending_runs
    
    # Voorkom meerdere instances
    with _window_lock:
        if _window_running or _pending_runs > 0:
            return
        _pending_runs += 1
    
    try:
        _window_running = True
        
        root = tk.Tk()
        app = SpraakennennerGUI(root) 
        
        def on_closing(): # Afsluit event handler
            global _window_running, _pending_runs
            app.on_closing() # Cleanup in app
            with _window_lock:
                _window_running = False
                _pending_runs = 0
        
        root.protocol("WM_DELETE_WINDOW", on_closing) # Sluit event handler
        root.mainloop()
        
    except Exception as e:
        pass
    finally:
        with _window_lock:
            _window_running = False
            _pending_runs = 0

if __name__ == "__main__":
    main() 