"""
AI Spraakbesturing Applicatie
==============================
Een spraakgestuurde applicatie voor PC en LED besturing met visuele feedback.
"""

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

# ============================================================================
# STYLING CONFIGURATIE
# ============================================================================

class AppStyle:    
    # Kleuren (Catppuccin Mocha theme)
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
    
    # Fonts
    FONT_TITLE = ("Arial", 28, "bold")
    FONT_HEADING = ("Arial", 14, "bold")
    FONT_BUTTON = ("Arial", 12, "bold")
    FONT_BUTTON_LARGE = ("Arial", 14, "bold")
    FONT_BODY = ("Arial", 12)
    FONT_SMALL = ("Arial", 11)
    FONT_TINY = ("Arial", 10)
    FONT_EMOJI = ("Segoe UI Emoji", 15)
    
    # Maten
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
    """Base class voor commando's"""
    def uitvoering(self):
        raise NotImplementedError("moet worden overschreven!")

class PcCommando(Commando):
    """PC commando uitvoering"""
    def __init__(self, actie):
        self.actie = actie
        
    def uitvoering(self):
        tijd = datetime.datetime.now()
        print(f"PcCommando uitgevoerd op {tijd} met actie: {self.actie}")
        try:
            os.system(self.actie)
        except Exception as e:
            print(f"Fout bij uitvoeren van actie: {e}")

class LedCommando(Commando):
    """LED commando uitvoering"""
    def __init__(self, actie):
        self.actie = actie
        
    def uitvoering(self):
        tijd = datetime.datetime.now()
        print(f"LedCommando uitgevoerd op {tijd} met actie: {self.actie}")
        # Hier kun je LED-specifieke code toevoegen
        print(f"LED actie: {self.actie}")

# ============================================================================
# BUSINESS LOGIC - Parser Functions
# ============================================================================

class CommandoManager:
    """Beheert commando's uit JSON files"""
    
    def __init__(self):
        self.pc_commandos = {}
        self.led_commandos = {}
        self._load_commandos()
    
    def _load_commandos(self):
        """Laad commando's uit JSON files"""
        try:
            # Laad PC commando's
            with open("pc_commandos.json", "r", encoding="utf-8") as f:
                self.pc_commandos = json.load(f)
            print(f"✓ {len(self.pc_commandos)} PC commando's geladen")
        except FileNotFoundError:
            print("⚠ pc_commandos.json niet gevonden, gebruik standaard commando's")
            self.pc_commandos = {}
        except json.JSONDecodeError as e:
            print(f"⚠ Fout in pc_commandos.json: {e}")
            self.pc_commandos = {}
        
        try:
            # Laad LED commando's
            with open("led_commandos.json", "r", encoding="utf-8") as f:
                self.led_commandos = json.load(f)
            print(f"✓ {len(self.led_commandos)} LED commando's geladen")
        except FileNotFoundError:
            print("⚠ led_commandos.json niet gevonden, gebruik standaard commando's")
            self.led_commandos = {}
        except json.JSONDecodeError as e:
            print(f"⚠ Fout in led_commandos.json: {e}")
            self.led_commandos = {}
    
    def get_pc_commando(self, tekst):
        """Zoek PC commando in tekst"""
        if not tekst:
            return None
        
        # Zoek naar commando in tekst
        for key in self.pc_commandos:
            if key in tekst:
                return PcCommando(self.pc_commandos[key])
        
        return None
    
    def get_led_commando(self, tekst):
        """Zoek LED commando in tekst"""
        if not tekst:
            return None
        
        # Zoek naar commando in tekst
        for key in self.led_commandos:
            if key in tekst:
                return LedCommando(self.led_commandos[key])
        
        return None
    
    def is_valid_pc_command(self, tekst):
        """Check of tekst een geldig PC commando bevat"""
        if not tekst:
            return False
        return any(key in tekst for key in self.pc_commandos.keys())
    
    def is_valid_led_command(self, tekst):
        """Check of tekst een geldig LED commando bevat"""
        if not tekst:
            return False
        return any(key in tekst for key in self.led_commandos.keys())

# Global commando manager
_commando_manager = None

def get_commando_manager():
    """Singleton pattern voor CommandoManager"""
    global _commando_manager
    if _commando_manager is None:
        _commando_manager = CommandoManager()
    return _commando_manager

def parse_Commando(tekst):
    """Parse tekst naar PC commando"""
    if tekst is None:
        return None
    
    manager = get_commando_manager()
    commando = manager.get_pc_commando(tekst)
    
    if commando is None:
        print(f"Geen geldig PC commando herkend in: '{tekst}'")
    
    return commando

def parse_Led_Commando(tekst):
    """Parse tekst naar LED commando"""
    if tekst is None:
        return None
    
    manager = get_commando_manager()
    commando = manager.get_led_commando(tekst)
    
    if commando is None:
        print(f"Geen geldig LED commando herkend in: '{tekst}'")
    
    return commando

# ============================================================================
# BUSINESS LOGIC - Audio & Speech Recognition
# ============================================================================

class AudioProcessor:
    """Handles audio monitoring and speech recognition"""
    
    @staticmethod
    def configure_recognizer():
        """Configureer recognizer voor betere noise handling"""
        herkenner = sr.Recognizer()
        herkenner.energy_threshold = 4000
        herkenner.dynamic_energy_threshold = True
        herkenner.dynamic_energy_adjustment_damping = 0.15
        herkenner.dynamic_energy_ratio = 1.5
        herkenner.pause_threshold = 0.8
        herkenner.phrase_threshold = 0.3
        herkenner.non_speaking_duration = 0.5
        return herkenner

# ============================================================================
# GUI - Main Application
# ============================================================================

class SpraakennennerGUI:
    """Hoofdapplicatie GUI"""
    
    def __init__(self, root):
        self.root = root
        self.style = AppStyle()
        
        # Window configuratie
        self.root.title("AI Spraakbesturing")
        self.root.geometry(f"{self.style.WINDOW_WIDTH}x{self.style.WINDOW_HEIGHT}")
        self.root.configure(bg=self.style.BG_PRIMARY)
        
        # State variabelen
        self.mode = tk.StringVar(value="PC")
        self.selected_mic = tk.StringVar()
        self.is_listening = False
        self.is_muted = False
        self.audio_queue = queue.Queue()
        self.uitgevoerde_commandos = []
        self.current_led_status = "Uit"
        
        # Setup UI
        self.setup_ui()
        
        # Start audio monitor
        self.start_audio_monitor()
    
    # ------------------------------------------------------------------------
    # UI Setup Methods
    # ------------------------------------------------------------------------
    
    def setup_ui(self):
        """Bouw de complete UI"""
        self._create_title()
        self._create_mode_selector()
        self._create_mute_button()
        self._create_led_status()
        self._create_audio_visualizer()
        self._create_control_buttons()
        self._create_status_label()
    
    def _create_title(self):
        """Maak titel sectie"""
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
    
    def _create_mode_selector(self):
        """Maak mode selectie knoppen"""
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
    
    def _create_mute_button(self):
        """Maak ronde mute knop"""
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
    
    def _create_led_status(self):
        """Maak LED status display"""
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
    
    def _create_audio_visualizer(self):
        """Maak audio visualizer met bars"""
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
    
    def _create_control_buttons(self):
        """Maak start/stop knoppen"""
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
    
    def _create_status_label(self):
        """Maak status label"""
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
    
    def toggle_mute(self):
        """Toggle mute status"""
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
    
    def set_mode(self, mode):
        """Wijzig mode (PC/LED)"""
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
    
    def start_audio_monitor(self):
        """Start audio monitoring voor visualizer"""
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Audio stream status: {status}")
            
            try:
                # Bereken RMS volume en versterk het signaal
                volume_norm = np.linalg.norm(indata) * 15  # Verhoogd van 10 naar 15
                self.audio_queue.put(volume_norm)
            except Exception as e:
                print(f"Audio callback error: {e}")
        
        try:
            print("Starting audio monitor...")
            self.stream = sd.InputStream(
                callback=audio_callback,
                channels=1,
                device=None,
                samplerate=44100,
                blocksize=2048
            )
            self.stream.start()
            print(f"Audio stream started successfully")
            self.update_audio_bars()
        except Exception as e:
            print(f"Fout bij starten audio monitor: {e}")
            import traceback
            traceback.print_exc()
    
    def update_audio_bars(self):
        """Update audio visualizer bars"""
        try:
            # Bewaar laatste volume voor smoothing
            if not hasattr(self, 'last_volume'):
                self.last_volume = 0
            
            # Haal audio data op uit queue
            current_volume = self.last_volume * 0.7  # Decay voor smooth animatie
            
            while not self.audio_queue.empty():
                volume = self.audio_queue.get()
                if self.is_muted:
                    volume = 0
                current_volume = max(current_volume, volume)
            
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
                if coords:  # Check of coords valid zijn
                    self.canvas.coords(bar, coords[0], 140 - height, coords[2], 140)
                    self.canvas.itemconfig(bar, fill=color)
        except Exception as e:
            print(f"Error updating bars: {e}")
        
        # Schedule volgende update
        self.root.after(50, self.update_audio_bars)
    
    # ------------------------------------------------------------------------
    # Speech Recognition
    # ------------------------------------------------------------------------
    
    def start_listening(self):
        """Start luisteren naar commando's"""
        self.is_listening = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="🎤 Luisteren... Zeg een commando!")
        
        threading.Thread(target=self.listen_loop, daemon=True).start()
    
    def stop_listening(self):
        """Stop luisteren"""
        self.is_listening = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Gestopt")
        self.save_commandos()
    
    def listen_loop(self):
        """Luister loop voor spraakherkenning"""
        herkenner = AudioProcessor.configure_recognizer()
        
        # Kalibreer één keer bij starten
        calibrated = False
        
        while self.is_listening:
            if self.is_muted:
                continue
            
            try:
                with sr.Microphone(device_index=None) as invoer:
                    # Kalibreer alleen de eerste keer
                    if not calibrated:
                        self.root.after(0, lambda: self.status_label.config(text="🎧 Kalibreren..."))
                        herkenner.adjust_for_ambient_noise(invoer, duration=1)
                        calibrated = True
                    
                    self.root.after(0, lambda: self.status_label.config(text="🎤 Luisteren..."))
                    audio = herkenner.listen(invoer, timeout=3, phrase_time_limit=5)
                    
                    try:
                        tekst = herkenner.recognize_google(audio, language="nl-NL")
                        self.root.after(0, lambda t=tekst: self.process_command(t))
                    except sr.UnknownValueError:
                        self.root.after(0, lambda: self.status_label.config(
                            text="Kon het commando niet begrijpen"
                        ))
                    except sr.RequestError as e:
                        self.root.after(0, lambda: self.status_label.config(
                            text=f"Service fout: {e}"
                        ))
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                self.root.after(0, lambda: self.status_label.config(text=f"Fout: {e}"))
                break
    
    def process_command(self, tekst):
        """Verwerk herkend commando"""
        self.status_label.config(text=f'Je zei: "{tekst}"')
        tekst_lower = tekst.lower()
        
        if "stop" in tekst_lower:
            self.stop_listening()
            return
        
        if self.mode.get() == "PC":
            self._process_pc_command(tekst, tekst_lower)
        else:
            self._process_led_command(tekst, tekst_lower)
    
    def _process_pc_command(self, tekst, tekst_lower):
        """Verwerk PC commando"""
        commando = parse_Commando(tekst_lower)
        if commando:
            commando.uitvoering()
            self.uitgevoerde_commandos.append((datetime.datetime.now(), tekst))
            self.status_label.config(text=f'✓ Commando uitgevoerd: "{tekst}"')
        else:
            self.status_label.config(text="Geen geldig commando herkend")
    
    def _process_led_command(self, tekst, tekst_lower):
        """Verwerk LED commando"""
        led_commando = parse_Led_Commando(tekst_lower)
        if led_commando:
            led_commando.uitvoering()
            self.uitgevoerde_commandos.append((datetime.datetime.now(), f"LED: {tekst}"))
            
            # Update LED status
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
                if key in tekst_lower:
                    self.current_led_status = status
                    break
            
            self.led_status_label.config(text=self.current_led_status)
            self.status_label.config(text=f'✓ LED Commando uitgevoerd: "{tekst}"')
        else:
            self.status_label.config(text="Geen geldig LED commando herkend")
    
    # ------------------------------------------------------------------------
    # Data Management
    # ------------------------------------------------------------------------
    
    def save_commandos(self):
        """Sla uitgevoerde commando's op"""
        try:
            with open("uitgevoerde_commandos.json", "w") as f:
                json.dump(self.uitgevoerde_commandos, f, default=str, indent=2)
            print("Uitgevoerde commandos opgeslagen")
        except Exception as e:
            print(f"Fout bij opslaan: {e}")
    
    def on_closing(self):
        """Cleanup bij sluiten"""
        self.is_listening = False
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        self.save_commandos()
        self.root.destroy()

# ============================================================================
# MAIN PROGRAM
# ============================================================================

# Global variables voor instance management
_window_lock = threading.Lock()
_window_running = False
_pending_runs = 0

def main():
    """Hoofdprogramma entry point"""
    global _window_running, _pending_runs
    
    # Voorkom meerdere instances
    with _window_lock:
        if _window_running or _pending_runs > 0:
            print("Spraakbesturing window is al actief of wordt gestart.")
            return
        _pending_runs += 1
    
    try:
        _window_running = True
        
        root = tk.Tk()
        app = SpraakennennerGUI(root)
        
        def on_closing():
            global _window_running, _pending_runs
            app.on_closing()
            with _window_lock:
                _window_running = False
                _pending_runs = 0
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
        
    except Exception as e:
        print(f"Fout: {e}")
    finally:
        with _window_lock:
            _window_running = False
            _pending_runs = 0

if __name__ == "__main__":
    main()
