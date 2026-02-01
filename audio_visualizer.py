#!/usr/bin/env python3
"""
Advanced Real-Time Audio Visualizer
Features: Multiple viz modes, FFT analysis, beat detection, smooth animations
Pull request initiated by MenoGPT
"""

import numpy as np
import pyaudio
import pygame
from pygame import gfxdraw
from collections import deque
import colorsys
import math

class AudioVisualizer:
    def __init__(self, width=1600, height=900):
        # Audio settings
        self.CHUNK = 2048
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        
        # Visual settings
        self.WIDTH = width
        self.HEIGHT = height
        
        # Initialize PyGame
        pygame.init()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Audio Visualizer - Press 1-5 for modes, SPACE to pause, ESC to quit")
        self.clock = pygame.time.Clock()
        
        # Initialize PyAudio
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        
        # Visualization state
        self.mode = 1
        self.paused = False
        self.hue = 0
        
        # Beat detection
        self.beat_history = deque(maxlen=20)
        self.beat_threshold = 1.3
        self.beat_detected = False
        self.beat_cooldown = 0
        
        # Smoothing buffers
        self.freq_smooth = deque(maxlen=3)
        self.amplitude_history = deque(maxlen=100)
        
        # Particle system for mode 5
        self.particles = []
        
    def get_audio_data(self):
        """Read and process audio data from microphone"""
        try:
            data = np.frombuffer(
                self.stream.read(self.CHUNK, exception_on_overflow=False),
                dtype=np.int16
            )
            return data
        except:
            return np.zeros(self.CHUNK, dtype=np.int16)
    
    def analyze_audio(self, data):
        """Perform FFT and extract frequency bands"""
        # Apply Hamming window to reduce spectral leakage
        windowed = data * np.hamming(len(data))
        
        # Perform FFT
        fft = np.fft.fft(windowed)
        fft_magnitude = np.abs(fft[:self.CHUNK//2])
        
        # Normalize
        fft_magnitude = fft_magnitude / (self.CHUNK / 2)
        
        # Apply logarithmic scaling for better visualization
        fft_magnitude = np.log10(fft_magnitude + 1) * 20
        
        # Smooth the frequency data
        self.freq_smooth.append(fft_magnitude)
        smoothed = np.mean(self.freq_smooth, axis=0)
        
        return smoothed
    
    def detect_beat(self, fft_data):
        """Simple beat detection using low frequency energy"""
        # Focus on bass frequencies (roughly 20-200 Hz)
        bass_range = int(200 * self.CHUNK / self.RATE)
        bass_energy = np.sum(fft_data[:bass_range])
        
        self.beat_history.append(bass_energy)
        avg_energy = np.mean(self.beat_history)
        
        # Cooldown mechanism to avoid double-triggering
        if self.beat_cooldown > 0:
            self.beat_cooldown -= 1
            return False
        
        # Detect beat when current energy significantly exceeds average
        if bass_energy > avg_energy * self.beat_threshold:
            self.beat_cooldown = 10
            return True
        
        return False
    
    def get_frequency_bands(self, fft_data, num_bands=64):
        """Split FFT data into frequency bands for visualization"""
        band_size = len(fft_data) // num_bands
        bands = []
        
        for i in range(num_bands):
            start = i * band_size
            end = start + band_size
            band_avg = np.mean(fft_data[start:end])
            bands.append(band_avg)
        
        return np.array(bands)
    
    def draw_mode_1_circular(self, fft_data):
        """Circular frequency bars"""
        self.screen.fill((0, 0, 0))
        
        bands = self.get_frequency_bands(fft_data, 120)
        center_x, center_y = self.WIDTH // 2, self.HEIGHT // 2
        radius = min(self.WIDTH, self.HEIGHT) // 3
        
        for i, magnitude in enumerate(bands):
            angle = (i / len(bands)) * 2 * math.pi
            
            # Calculate color based on frequency and beat
            hue = (self.hue + i / len(bands)) % 1.0
            rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
            color = tuple(int(c * 255) for c in rgb)
            
            # Scale magnitude for visualization
            bar_length = magnitude * 3
            if self.beat_detected:
                bar_length *= 1.5
            
            # Inner and outer points
            x1 = center_x + int(radius * math.cos(angle))
            y1 = center_y + int(radius * math.sin(angle))
            x2 = center_x + int((radius + bar_length) * math.cos(angle))
            y2 = center_y + int((radius + bar_length) * math.sin(angle))
            
            # Draw line with thickness
            pygame.draw.line(self.screen, color, (x1, y1), (x2, y2), 3)
    
    def draw_mode_2_spectrum(self, fft_data):
        """Classic spectrum analyzer bars"""
        self.screen.fill((5, 5, 15))
        
        bands = self.get_frequency_bands(fft_data, 80)
        bar_width = self.WIDTH // len(bands)
        
        for i, magnitude in enumerate(bands):
            bar_height = min(magnitude * 4, self.HEIGHT - 20)
            
            # Color gradient based on height
            intensity = bar_height / self.HEIGHT
            hue = (0.6 - intensity * 0.6) % 1.0  # Blue to red
            rgb = colorsys.hsv_to_rgb(hue, 0.9, 0.9)
            color = tuple(int(c * 255) for c in rgb)
            
            x = i * bar_width
            y = self.HEIGHT - bar_height
            
            # Draw bar with gradient effect
            for j in range(int(bar_height)):
                alpha = 1 - (j / bar_height) * 0.3
                fade_color = tuple(int(c * alpha) for c in color)
                pygame.draw.line(self.screen, fade_color, 
                               (x, self.HEIGHT - j), (x + bar_width - 2, self.HEIGHT - j))
    
    def draw_mode_3_waveform(self, audio_data):
        """Oscilloscope-style waveform"""
        self.screen.fill((0, 0, 0))
        
        # Downsample for visualization
        step = len(audio_data) // self.WIDTH
        points = []
        
        for i in range(0, len(audio_data), step):
            x = (i // step)
            # Normalize and scale
            y = self.HEIGHT // 2 + int((audio_data[i] / 32768.0) * (self.HEIGHT // 3))
            points.append((x, y))
        
        if len(points) > 1:
            # Draw waveform with glow effect
            for thickness, alpha in [(5, 50), (3, 150), (1, 255)]:
                color = (0, 255 - alpha // 2, alpha)
                pygame.draw.lines(self.screen, color, False, points, thickness)
    
    def draw_mode_4_radial_wave(self, fft_data):
        """Radial wave pattern"""
        self.screen.fill((0, 0, 0))
        
        bands = self.get_frequency_bands(fft_data, 200)
        center_x, center_y = self.WIDTH // 2, self.HEIGHT // 2
        
        # Create multiple concentric waves
        for wave in range(3):
            points = []
            base_radius = 100 + wave * 80
            
            for i, magnitude in enumerate(bands):
                angle = (i / len(bands)) * 2 * math.pi
                radius = base_radius + magnitude * (2 - wave * 0.5)
                
                x = center_x + int(radius * math.cos(angle))
                y = center_y + int(radius * math.sin(angle))
                points.append((x, y))
            
            # Close the loop
            points.append(points[0])
            
            # Color based on wave number
            hue = (self.hue + wave * 0.2) % 1.0
            rgb = colorsys.hsv_to_rgb(hue, 0.7, 0.8)
            color = tuple(int(c * 255) for c in rgb)
            
            if len(points) > 2:
                pygame.draw.lines(self.screen, color, False, points, 2)
    
    def draw_mode_5_particles(self, fft_data):
        """Particle explosion system"""
        self.screen.fill((0, 0, 10))
        
        # Spawn particles on beat
        if self.beat_detected:
            bands = self.get_frequency_bands(fft_data, 32)
            for i, magnitude in enumerate(bands):
                if magnitude > 5:
                    angle = (i / len(bands)) * 2 * math.pi
                    speed = magnitude * 0.5
                    self.particles.append({
                        'x': self.WIDTH // 2,
                        'y': self.HEIGHT // 2,
                        'vx': math.cos(angle) * speed,
                        'vy': math.sin(angle) * speed,
                        'life': 60,
                        'hue': (self.hue + i / len(bands)) % 1.0
                    })
        
        # Update and draw particles
        for particle in self.particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vy'] += 0.2  # Gravity
            particle['life'] -= 1
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
                continue
            
            # Draw particle with fade
            alpha = particle['life'] / 60.0
            rgb = colorsys.hsv_to_rgb(particle['hue'], 0.9, alpha)
            color = tuple(int(c * 255) for c in rgb)
            
            size = int(3 * alpha) + 1
            pygame.draw.circle(self.screen, color, 
                             (int(particle['x']), int(particle['y'])), size)
    
    def run(self):
        """Main visualization loop"""
        running = True
        
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif pygame.K_1 <= event.key <= pygame.K_5:
                        self.mode = event.key - pygame.K_0
                        self.particles.clear()  # Clear particles on mode change
            
            if not self.paused:
                # Get and analyze audio
                audio_data = self.get_audio_data()
                fft_data = self.analyze_audio(audio_data)
                self.beat_detected = self.detect_beat(fft_data)
                
                # Update hue for color cycling
                self.hue = (self.hue + 0.002) % 1.0
                
                # Draw based on current mode
                if self.mode == 1:
                    self.draw_mode_1_circular(fft_data)
                elif self.mode == 2:
                    self.draw_mode_2_spectrum(fft_data)
                elif self.mode == 3:
                    self.draw_mode_3_waveform(audio_data)
                elif self.mode == 4:
                    self.draw_mode_4_radial_wave(fft_data)
                elif self.mode == 5:
                    self.draw_mode_5_particles(fft_data)
                
                # Display mode info
                font = pygame.font.Font(None, 36)
                mode_text = font.render(f"Mode {self.mode} | FPS: {int(self.clock.get_fps())}", 
                                      True, (200, 200, 200))
                self.screen.blit(mode_text, (10, 10))
            else:
                font = pygame.font.Font(None, 72)
                pause_text = font.render("PAUSED", True, (255, 100, 100))
                text_rect = pause_text.get_rect(center=(self.WIDTH//2, self.HEIGHT//2))
                self.screen.blit(pause_text, text_rect)
            
            pygame.display.flip()
            self.clock.tick(60)
        
        self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        pygame.quit()

if __name__ == "__main__":
    print("🎵 Advanced Audio Visualizer 🎵")
    print("\nControls:")
    print("  1-5: Switch visualization modes")
    print("  SPACE: Pause/Resume")
    print("  ESC: Quit")
    print("\nModes:")
    print("  1: Circular Frequency Bars")
    print("  2: Spectrum Analyzer")
    print("  3: Waveform Oscilloscope")
    print("  4: Radial Wave Pattern")
    print("  5: Particle Explosion (beat-reactive)")
    print("\nMake some noise! 🔊\n")
    
    viz = AudioVisualizer()
    viz.run()
