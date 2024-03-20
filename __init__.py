import os
from ovos_workshop.skills import OVOSSkill
from ovos_workshop.decorators import intent_handler
from ovos_bus_client.message import Message
import time
import json
from ovos_utils.log import LOG

class AdventureGameSkill(OVOSSkill):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def initialize(self):
        self.game_running = False
        with open(os.path.join(self.root_dir, "adventure_data.json")) as file:
            data = json.load(file)
            self.options_mapping = data["options_mapping"]
            self.adventure_data = data["adventure_data"]
        
    def play(self, audio_file):
        file_path = os.path.join(self.root_dir, "audio", f"{audio_file}.mp3")
        LOG.info("Playing audio file: %s", file_path)  # Log the file path
        self.play_audio(file_path, wait=True)

    def stop_audio(self):
        self.bus.emit(Message("mycroft.audio.speech.stop"))

    def play_adventure(self):
        self.game_running = True
        current_path = "intro"  # Begin at the intro

        while self.game_running:
            current_scene = self.adventure_data[current_path]
            audio_file_key = self.options_mapping[current_path]  # Use the numerical key for the audio file
            self.play(audio_file_key)
            options = current_scene.get("options", {})

            if options:
                self.speak("", wait=True)  # hack to let it wait
                for key, value in options.items():
                    self.speak(f"{value}", wait=True, expect_response=True)  # I know this adds an extra get_response, but it's the only way so far to get it right
                
                choice = self.get_response()
                
                if choice.lower() == "stop":
                    self.speak_dialog("stopping_game")
                    self.game_running = False
                    self.stop_audio()  # Stop the currently playing audio
                elif choice.lower() in map(str.lower, options.values()):  # Check if the lowercase choice is in the lowercase values of the options
                    current_path = next(key for key, val in options.items() if val.lower() == choice.lower())
                else:
                    self.speak_dialog("invalid_choice", wait=True)  # Adjusted

            else:
                self.speak_dialog("congratulations", wait=True)  # Adjusted
                audio_file_key = self.options_mapping[current_path]  # Use the numerical key for the audio file
                self.play(audio_file_key)
                time.sleep(0)  # Adjust the sleep duration as needed
                self.game_running = False  # Stop the game
                self.stop_audio()  # Stop the currently playing audio
                break  # Exit the loop when the adventure is completed

    @intent_handler("play.intent")
    def handle_start_adventure(self, message):
        self.play_adventure()

    @intent_handler("stop.intent")
    def handle_stop_adventure(self, message):
        if self.game_running:
            self.speak_dialog("stopping_game", wait=True)  # Adjusted
            self.game_running = False
            self.stop_audio()  # Stop the currently playing audio
        else:
            self.speak_dialog("no_game_running", wait=True)  # Adjusted
