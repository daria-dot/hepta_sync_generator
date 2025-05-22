import tkinter as tk
from tkinter import messagebox, filedialog
import numpy as np
from scipy.io.wavfile import write as write_wav
import threading # For running audio generation in a separate thread

class HeptaSynchronicityApp:
    def __init__(self, master):
        self.master = master
        master.title("Hepta Synchronicity Audio Generator")
        master.geometry("800x750") # Keeping the increased window height
        master.resizable(False, False) # Prevent resizing

        self.sampling_rate = 44100 # Standard audio CD quality sampling rate

        # --- Presets for Brainwave States ---
        # These are lists of 7 frequency offsets (binaural beat frequencies)
        self.presets = {
            "Custom": [], # Empty, will be populated by user input
            "Delta (0.5-4 Hz)": [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0],
            "Theta (4-8 Hz)": [4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0],
            "Alpha (8-12 Hz)": [8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0],
            "Beta (13-30 Hz)": [13.0, 15.0, 17.0, 20.0, 23.0, 26.0, 30.0],
            "Gamma (30-100 Hz)": [30.0, 35.0, 40.0, 50.0, 60.0, 70.0, 80.0]
        }

        # --- GUI Elements ---
        self.create_widgets()

    def create_widgets(self):
        # Frame for General Settings (top)
        general_frame = tk.LabelFrame(self.master, text="General Settings", padx=10, pady=10)
        general_frame.pack(pady=8, padx=20, fill="x")

        tk.Label(general_frame, text="Duration (minutes):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.duration_entry = tk.Entry(general_frame, width=10)
        self.duration_entry.insert(0, "5") # Default duration
        self.duration_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        tk.Label(general_frame, text="Output Filename (e.g., my_audio.wav):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.filename_entry = tk.Entry(general_frame, width=40)
        self.filename_entry.insert(0, "hepta_synchronicity_output.wav")
        self.filename_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Frame to hold Base and Offset Frequency frames side-by-side
        freq_container_frame = tk.Frame(self.master)
        freq_container_frame.pack(pady=8, padx=20, fill="both", expand=True) # Fill and expand to take available space

        # Frame for Base Frequencies (Left Ear) - packed to the left
        base_freq_frame = tk.LabelFrame(freq_container_frame, text="Base Frequencies (Left Ear - Hz)", padx=10, pady=10)
        base_freq_frame.pack(side=tk.LEFT, padx=10, pady=5, fill="both", expand=True) # Fill and expand horizontally

        self.base_freq_entries = []
        default_base_freqs = [200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 320.0]
        for i in range(7):
            tk.Label(base_freq_frame, text=f"Pair {i+1} Base Freq:").grid(row=i, column=0, padx=5, pady=2, sticky="w")
            entry = tk.Entry(base_freq_frame, width=15)
            entry.insert(0, str(default_base_freqs[i]))
            entry.grid(row=i, column=1, padx=5, pady=2, sticky="w")
            self.base_freq_entries.append(entry)

        # Frame for Frequency Offsets (Binaural Beats) - packed to the right
        offset_freq_frame = tk.LabelFrame(freq_container_frame, text="Frequency Offsets (Binaural Beat - Hz)", padx=10, pady=10)
        offset_freq_frame.pack(side=tk.RIGHT, padx=10, pady=5, fill="both", expand=True) # Fill and expand horizontally

        tk.Label(offset_freq_frame, text="Select Preset:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.preset_var = tk.StringVar(self.master)
        self.preset_var.set("Custom") # Default preset
        self.preset_var.trace_add("write", self.apply_preset) # Call apply_preset when dropdown changes

        preset_options = list(self.presets.keys())
        self.preset_menu = tk.OptionMenu(offset_freq_frame, self.preset_var, *preset_options)
        self.preset_menu.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        self.offset_freq_entries = []
        default_offsets = [5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0]
        for i in range(7):
            tk.Label(offset_freq_frame, text=f"Pair {i+1} Offset:").grid(row=i+1, column=0, padx=5, pady=2, sticky="w")
            entry = tk.Entry(offset_freq_frame, width=15)
            entry.insert(0, str(default_offsets[i]))
            entry.grid(row=i+1, column=1, padx=5, pady=2, sticky="w")
            self.offset_freq_entries.append(entry)

        # Pro Tip Text Box
        pro_tip_text = (
            "Pro Tip: Key Synergetic Effects:\n"
            "Delta + Theta → Deep restorative sleep when paired at night.\n"
            "Alpha + Low Beta → \"Flow state\" for creative work.\n"
            "Gamma + Schumann → Mental clarity + concentration"
            "Check out the manual on the Github README :)"
        )
        self.pro_tip_label = tk.Label(self.master, text=pro_tip_text, justify=tk.LEFT,
                                      bg="lightyellow", fg="darkgreen", relief=tk.GROOVE,
                                      borderwidth=2, padx=10, pady=10)
        self.pro_tip_label.pack(pady=10, padx=20, fill="x")


        # Frame for Button and Status Label (bottom)
        button_frame = tk.Frame(self.master, padx=10, pady=10)
        button_frame.pack(pady=10, padx=20, fill="x")

        self.generate_button = tk.Button(button_frame, text="Generate Audio", command=self.start_audio_generation)
        self.generate_button.pack(pady=5, fill="x", expand=True)

        self.status_label = tk.Label(button_frame, text="", fg="blue")
        self.status_label.pack(pady=5)


    def apply_preset(self, *args):
        """Applies the selected preset frequencies to the offset entry fields."""
        selected_preset = self.preset_var.get()
        if selected_preset == "Custom":
            # Do not change values if "Custom" is selected, let user input
            return

        offsets = self.presets.get(selected_preset, [])
        if len(offsets) == 7:
            for i, offset_val in enumerate(offsets):
                self.offset_freq_entries[i].delete(0, tk.END)
                self.offset_freq_entries[i].insert(0, str(offset_val))
        else:
            messagebox.showwarning("Preset Error", "Selected preset does not have 7 values. Please check.")

    def start_audio_generation(self):
        """Starts the audio generation in a separate thread to keep GUI responsive."""
        self.status_label.config(text="Generating audio... Please wait.", fg="blue")
        self.generate_button.config(state=tk.DISABLED) # Disable button during generation

        # Use threading to prevent GUI from freezing
        self.audio_thread = threading.Thread(target=self._generate_audio_task)
        self.audio_thread.start()

    def _generate_audio_task(self):
        """Task to generate audio, run in a separate thread."""
        try:
            # --- Validate and Get Inputs ---
            duration_minutes_str = self.duration_entry.get()
            output_filename = self.filename_entry.get()

            try:
                duration_minutes = float(duration_minutes_str)
                if duration_minutes <= 0:
                    raise ValueError("Duration must be positive.")
                duration_seconds = int(duration_minutes * 60)
            except ValueError:
                messagebox.showerror("Input Error", "Invalid duration. Please enter a number.")
                self.reset_gui_state()
                return

            if not output_filename.strip():
                messagebox.showerror("Input Error", "Output filename cannot be empty.")
                self.reset_gui_state()
                return
            if not output_filename.endswith(".wav"):
                output_filename += ".wav" # Ensure .wav extension

            base_frequencies_left = []
            for entry in self.base_freq_entries:
                try:
                    freq = float(entry.get())
                    if freq <= 0:
                        raise ValueError("Frequencies must be positive.")
                    base_frequencies_left.append(freq)
                except ValueError:
                    messagebox.showerror("Input Error", "Invalid base frequency. Please enter numbers.")
                    self.reset_gui_state()
                    return
            if len(base_frequencies_left) != 7:
                messagebox.showerror("Input Error", "Please enter 7 base frequencies.")
                self.reset_gui_state()
                return

            frequency_offsets = []
            for entry in self.offset_freq_entries:
                try:
                    offset = float(entry.get())
                    # Offsets can be negative for right ear freq < left ear freq, but 0 is silent beat
                    frequency_offsets.append(offset)
                except ValueError:
                    messagebox.showerror("Input Error", "Invalid frequency offset. Please enter numbers.")
                    self.reset_gui_state()
                    return
            if len(frequency_offsets) != 7:
                messagebox.showerror("Input Error", "Please enter 7 frequency offsets.")
                self.reset_gui_state()
                return

            # --- Audio Generation Logic (adapted from previous script) ---
            t = np.linspace(0, duration_seconds, int(self.sampling_rate * duration_seconds), endpoint=False)

            left_channel_audio = np.zeros_like(t, dtype=np.float32)
            right_channel_audio = np.zeros_like(t, dtype=np.float32)

            for i in range(7):
                f_left = base_frequencies_left[i]
                f_offset = frequency_offsets[i]
                f_right = f_left + f_offset

                # Check if right frequency becomes non-positive, which can cause issues or be inaudible
                if f_right <= 0:
                    messagebox.showwarning("Frequency Warning",
                                           f"Pair {i+1}: Right ear frequency ({f_right:.2f} Hz) is non-positive. "
                                           "This may result in inaudible or distorted sound for this pair. "
                                           "Consider adjusting base frequency or offset.")
                    # Continue, but the sound for this specific pair might be bad
                
                sine_wave_left = np.sin(2 * np.pi * f_left * t)
                sine_wave_right = np.sin(2 * np.pi * f_right * t)

                left_channel_audio += sine_wave_left
                right_channel_audio += sine_wave_right

            max_amplitude = max(np.max(np.abs(left_channel_audio)), np.max(np.abs(right_channel_audio)))
            if max_amplitude > 0:
                left_channel_audio = left_channel_audio / max_amplitude
                right_channel_audio = right_channel_audio / max_amplitude
            else:
                messagebox.showwarning("Audio Warning", "Generated audio is silent. Check your frequency inputs.")
                self.reset_gui_state()
                return

            stereo_audio = np.stack((left_channel_audio, right_channel_audio), axis=-1)

            # --- Save Audio File ---
            # Use filedialog to ensure valid path and user control
            save_path = filedialog.asksaveasfilename(
                defaultextension=".wav",
                initialfile=output_filename,
                filetypes=[("WAV files", "*.wav")]
            )

            if save_path: # If user didn't cancel the save dialog
                write_wav(save_path, self.sampling_rate, stereo_audio)
                self.status_label.config(text=f"Audio saved successfully to {save_path}", fg="green")
                messagebox.showinfo("Success", f"Audio file saved to:\n{save_path}")
            else:
                self.status_label.config(text="Audio generation cancelled by user.", fg="orange")

        except Exception as e:
            messagebox.showerror("Generation Error", f"An unexpected error occurred:\n{e}")
            self.status_label.config(text="Error during generation.", fg="red")
        finally:
            self.reset_gui_state()

    def reset_gui_state(self):
        """Resets the GUI state after generation or error."""
        self.generate_button.config(state=tk.NORMAL) # Re-enable button
        # Status label will be updated by the task itself before calling this.

# --- Main Application Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = HeptaSynchronicityApp(root)
    root.mainloop()
