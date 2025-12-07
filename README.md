# 🎨 Virtual Painter - Air Draw

A web-based virtual painter application that lets you draw in the air using hand gestures! Control colors and draw with simple finger movements. Fully optimized for desktop, Android, and iOS devices. Built with Streamlit, OpenCV, and MediaPipe.

## Features

- ✨ Real-time hand tracking using MediaPipe
- 🎨 Multiple color options (Purple, Blue, Green, Yellow)
- 🧹 Eraser mode
- 📱 Web-based - works on any device with a camera
- 🆓 Free to deploy and use

## How to Use

### Desktop:
1. **Select Color**: Raise both your index and middle fingers and point at the color buttons at the top, OR use the controls in the sidebar
2. **Draw**: Point only your index finger and move it to draw
3. **Erase**: Select the eraser option and draw to erase
4. **Clear**: Click the "Clear Canvas" button to start over

### Mobile (Android & iOS):
1. **Allow Camera Access**: When prompted, allow the app to access your camera
2. **Select Color**: 
   - Use the color buttons below the camera (🟣 Purple, 🔵 Blue, 🟢 Green, 🟡 Yellow, 🧹 Eraser)
   - OR raise both index and middle fingers and point at the color buttons at the top
3. **Draw**: Point only your index finger and move it to draw
4. **Adjust Settings**: Use the sliders to adjust brush and eraser sizes
5. **Clear**: Tap the "🗑️ Clear Canvas" button to start over

**Mobile Tips:**
- Works best in landscape mode for better hand tracking
- Ensure good lighting for accurate hand detection
- Hold your phone steady or use a stand for best results

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the app:
```bash
streamlit run app.py
```

## Free Deployment Options

### Option 1: Streamlit Cloud (Recommended - Easiest) ⭐

**Completely FREE** with no credit card required!

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with your GitHub account
4. Click "New app"
5. Select your repository and branch
6. Set the main file path to `app.py`
7. Click "Deploy"

Your app will be live at: `https://your-app-name.streamlit.app`

### Option 2: Render (Free Tier)

1. Create a free account at [render.com](https://render.com)
2. Create a new "Web Service"
3. Connect your GitHub repository
4. Use these settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
5. Deploy!

### Option 3: PythonAnywhere (Free Tier)

1. Sign up at [pythonanywhere.com](https://www.pythonanywhere.com)
2. Upload your files
3. Create a new Web App
4. Configure it to run your Streamlit app

### Option 4: Hugging Face Spaces (Free)

1. Create account at [huggingface.co](https://huggingface.co)
2. Create a new Space
3. Select "Streamlit" as the SDK
4. Upload your files
5. Your app will be live automatically!

## Files

- `app.py` - Main Streamlit application
- `virtual_painter.py` - Original desktop OpenCV version
- `requirements.txt` - Python dependencies

## Requirements

- Python 3.8+ (for local development)
- Webcam/Camera access
- Modern web browser (Chrome, Safari, Firefox, Edge)
- **Mobile**: iOS 11+ or Android 5+ with modern browser (Chrome, Safari, Firefox)

## Mobile Compatibility

✅ **Fully optimized for mobile devices!**
- Responsive design that adapts to screen size
- Touch-friendly controls
- Works on both Android and iOS
- Automatic canvas sizing based on camera resolution
- Optimized UI elements for smaller screens

## Notes

- The app requires camera access to work
- Works best in well-lit environments
- Hand tracking works best when your hand is clearly visible

## License

Free to use and modify!

