#!/bin/bash
# Audio Visualizer Setup Script

echo "🎵 Audio Visualizer Setup 🎵"
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found."
    exit 1
fi

echo "✓ Python 3 found"

# Install system dependencies for PyAudio (platform-specific)
echo ""
echo "Installing system dependencies..."

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected Linux"
    echo "Run: sudo apt-get install python3-pyaudio portaudio19-dev"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS"
    echo "Run: brew install portaudio"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "Detected Windows"
    echo "PyAudio should install via pip on Windows"
fi

echo ""
echo "Installing Python packages..."
pip install --break-system-packages -r requirements.txt

echo ""
echo "✓ Setup complete!"
echo ""
echo "To run the visualizer:"
echo "  python3 audio_visualizer.py"
echo ""
echo "Controls:"
echo "  1-5: Switch between 5 visualization modes"
echo "  SPACE: Pause/Resume"
echo "  ESC: Quit"
echo ""
echo "🎧 Make sure your microphone is enabled!"
