import streamlit as st
import cv2
import numpy as np
import mediapipe as mp
from PIL import Image

# Page config - mobile optimized
st.set_page_config(
    page_title="Virtual Painter - Air Draw",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed"  # Collapse sidebar on mobile by default
)

# Add mobile-optimized CSS
st.markdown("""
<style>
    /* Mobile optimizations */
    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        h1 {
            font-size: 1.75rem !important;
        }
        .stButton > button {
            width: 100%;
            font-size: 1rem;
            padding: 0.75rem;
        }
        .stSlider {
            width: 100%;
        }
        /* Make camera full width on mobile */
        [data-testid="stCameraInput"] {
            width: 100% !important;
        }
    }
    
    /* Touch-friendly controls */
    .stRadio > div {
        gap: 0.5rem;
    }
    .stRadio > div > label {
        padding: 0.75rem;
        font-size: 1rem;
    }
    
    /* Hide sidebar on very small screens */
    @media (max-width: 480px) {
        section[data-testid="stSidebar"] {
            display: none;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize MediaPipe Hands
@st.cache_resource
def init_hands():
    mp_hands = mp.solutions.hands
    return mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    ), mp_hands, mp.solutions.drawing_utils

hands, mp_hands, mp_draw = init_hands()

# Configuration - Mobile optimized sizes
# Use smaller default for mobile, will scale based on actual frame size
wCam, hCam = 640, 480  # Smaller default for mobile compatibility
button_height = 60  # Smaller buttons for mobile
buttons_count = 5
button_width = wCam // buttons_count

# BGR colors
colors = [
    (255,   0, 255),   # purple
    (255,   0,   0),   # blue
    (0,   255,   0),   # green
    (0,   255, 255),   # yellow
]
color_names = ["PURPLE", "BLUE", "GREEN", "YELLOW"]

# Initialize session state - canvas will be resized to match actual camera size
if 'canvas' not in st.session_state:
    st.session_state.canvas = None  # Will be initialized when first frame arrives
if 'current_color_idx' not in st.session_state:
    st.session_state.current_color_idx = 1
if 'is_eraser' not in st.session_state:
    st.session_state.is_eraser = False
if 'prev_x' not in st.session_state:
    st.session_state.prev_x = None
if 'prev_y' not in st.session_state:
    st.session_state.prev_y = None
if 'brush_thickness' not in st.session_state:
    st.session_state.brush_thickness = 12
if 'eraser_thickness' not in st.session_state:
    st.session_state.eraser_thickness = 60

current_color = colors[st.session_state.current_color_idx]
eraser_color = (0, 0, 0)

# UI Drawing helpers
def draw_top_bar(img, active_idx, is_eraser_mode, img_width, img_height):
    button_h = int(button_height * (img_height / hCam))  # Scale button height
    button_w = img_width // buttons_count  # Scale button width
    
    overlay = img.copy()
    cv2.rectangle(overlay, (0, 0), (img_width, button_h + 20), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)
    
    # Scale font size based on image size
    font_scale = max(0.5, img_width / 640)
    thickness = max(1, int(2 * (img_width / 640)))
    
    cv2.putText(
        img, "AIR DRAW",
        (int(20 * (img_width / wCam)), int(55 * (img_height / hCam))),
        cv2.FONT_HERSHEY_SIMPLEX, font_scale * 1.3,
        (255, 255, 255), thickness, cv2.LINE_AA
    )
    
    for i in range(buttons_count):
        x1 = i * button_w
        x2 = x1 + button_w
        y1 = 20
        y2 = y1 + button_h - 20
        
        if i < 4:
            col = colors[i]
            label = color_names[i]
        else:
            col = (60, 60, 60)
            label = "ERASER"
        
        cv2.rectangle(img, (x1 + 5, y1), (x2 - 5, y2), col, -1)
        
        if i == active_idx or (i == 4 and is_eraser_mode):
            border_col = (255, 255, 255)
            border_thickness = max(2, int(4 * (img_width / wCam)))
        else:
            border_col = (180, 180, 180)
            border_thickness = max(1, int(2 * (img_width / wCam)))
        
        cv2.rectangle(img, (x1 + 5, y1), (x2 - 5, y2), border_col, border_thickness)
        
        text_scale = max(0.3, 0.6 * (img_width / wCam))
        text_thickness = max(1, int(2 * (img_width / wCam)))
        text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, text_scale, text_thickness)[0]
        text_x = x1 + (button_w - text_size[0]) // 2
        text_y = y2 - 10
        cv2.putText(
            img, label, (text_x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX, text_scale,
            (255, 255, 255), text_thickness, cv2.LINE_AA
        )

def draw_bottom_hud(img, mode_text, brush_size, eraser_mode, img_width, img_height):
    hud_height = int(70 * (img_height / hCam))
    overlay = img.copy()
    cv2.rectangle(
        overlay,
        (0, img_height - hud_height),
        (img_width, img_height),
        (0, 0, 0),
        -1
    )
    cv2.addWeighted(overlay, 0.6, img, 0.4, 0, img)
    
    # Scale font sizes
    font_scale_large = max(0.4, 0.8 * (img_width / wCam))
    font_scale_small = max(0.3, 0.6 * (img_width / wCam))
    thickness = max(1, int(2 * (img_width / wCam)))
    
    left_text = f"MODE: {mode_text}"
    cv2.putText(
        img, left_text,
        (int(20 * (img_width / wCam)), img_height - int(25 * (img_height / hCam))),
        cv2.FONT_HERSHEY_SIMPLEX, font_scale_large,
        (255, 255, 255), thickness, cv2.LINE_AA
    )
    
    # Simplified text for mobile
    if img_width < 600:
        mid_text = "2 Fingers: Select | 1 Finger: Draw"
    else:
        mid_text = "INDEX+MIDDLE: Select | INDEX: Draw"
    
    text_size = cv2.getTextSize(mid_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale_small, thickness)[0]
    cv2.putText(
        img, mid_text,
        (img_width // 2 - text_size[0] // 2, img_height - int(25 * (img_height / hCam))),
        cv2.FONT_HERSHEY_SIMPLEX, font_scale_small,
        (200, 200, 200), thickness, cv2.LINE_AA
    )
    
    center_x = img_width - int(70 * (img_width / wCam))
    center_y = img_height - int(40 * (img_height / hCam))
    size = st.session_state.eraser_thickness if eraser_mode else brush_size
    circle_radius = max(5, int((size // 4) * (img_width / wCam)))
    cv2.circle(img, (center_x, center_y), circle_radius, (255, 255, 255), max(1, int(2 * (img_width / wCam))))
    cv2.putText(
        img, "SIZE",
        (center_x - int(25 * (img_width / wCam)), center_y - int(25 * (img_height / hCam))),
        cv2.FONT_HERSHEY_PLAIN, max(0.5, 1.2 * (img_width / wCam)),
        (220, 220, 220), max(1, int(1 * (img_width / wCam))), cv2.LINE_AA
    )

# Main app
st.title("🎨 Virtual Painter - Air Draw")
st.markdown("Use your hand gestures to draw in the air! Point your index finger to draw, raise both index and middle fingers to select colors.")

# Responsive layout - single column on mobile, two columns on desktop
use_sidebar = st.sidebar.checkbox("Show Controls", value=False)

# Main content area
if use_sidebar:
    col1, col2 = st.columns([3, 1])
else:
    col1 = st.container()
    col2 = None

with col1:
    # Camera input
    camera_input = st.camera_input("Camera", label_visibility="collapsed")
    
    if camera_input is not None:
        # Convert PIL Image to numpy array
        frame = np.array(camera_input)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Get actual frame dimensions (mobile cameras vary)
        actual_h, actual_w = frame.shape[:2]
        
        # Initialize or resize canvas to match actual frame size
        if st.session_state.canvas is None:
            st.session_state.canvas = np.zeros((actual_h, actual_w, 3), np.uint8)
        elif st.session_state.canvas.shape[:2] != (actual_h, actual_w):
            # Resize existing canvas to new dimensions
            old_canvas = st.session_state.canvas.copy()
            st.session_state.canvas = np.zeros((actual_h, actual_w, 3), np.uint8)
            # Optionally resize old canvas content (for now, just reset)
        
        frame = cv2.flip(frame, 1)
        
        draw_top_bar(frame, st.session_state.current_color_idx, st.session_state.is_eraser, actual_w, actual_h)
        
        # Process with MediaPipe
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)
        
        mode_text = "NO HAND"
        
        if results.multi_hand_landmarks:
            for handLms in results.multi_hand_landmarks:
                h, w, _ = frame.shape
                lm_list = []
                
                for idx, lm in enumerate(handLms.landmark):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lm_list.append((idx, cx, cy))
                
                index_tip = lm_list[8]
                index_pip = lm_list[6]
                middle_tip = lm_list[12]
                middle_pip = lm_list[10]
                
                ix, iy = index_tip[1], index_tip[2]
                
                index_up = index_tip[2] < index_pip[2]
                middle_up = middle_tip[2] < middle_pip[2]
                
                # Selection mode
                if index_up and middle_up:
                    st.session_state.prev_x = None
                    st.session_state.prev_y = None
                    mode_text = "SELECT"
                    
                    button_h_scaled = int(button_height * (h / hCam))
                    button_w_scaled = w // buttons_count
                    if iy < button_h_scaled + 20:
                        idx = ix // button_w_scaled
                        idx = int(np.clip(idx, 0, buttons_count - 1))
                        
                        if idx == 4:
                            st.session_state.is_eraser = True
                            st.session_state.current_color_idx = -1
                        else:
                            st.session_state.is_eraser = False
                            st.session_state.current_color_idx = idx
                    
                    cv2.circle(frame, (ix, iy), 14, (255, 255, 255), cv2.FILLED)
                
                # Draw mode
                elif index_up and not middle_up:
                    mode_text = "DRAW (ERASER)" if st.session_state.is_eraser else "DRAW"
                    
                    draw_color = eraser_color if st.session_state.is_eraser else colors[st.session_state.current_color_idx]
                    thickness = st.session_state.eraser_thickness if st.session_state.is_eraser else st.session_state.brush_thickness
                    
                    cv2.circle(frame, (ix, iy), 14, draw_color, cv2.FILLED)
                    
                    if st.session_state.prev_x is None and st.session_state.prev_y is None:
                        st.session_state.prev_x, st.session_state.prev_y = ix, iy
                    
                    cv2.line(
                        st.session_state.canvas,
                        (st.session_state.prev_x, st.session_state.prev_y),
                        (ix, iy),
                        draw_color,
                        thickness
                    )
                    st.session_state.prev_x, st.session_state.prev_y = ix, iy
                
                else:
                    st.session_state.prev_x = None
                    st.session_state.prev_y = None
                    mode_text = "IDLE"
                
                mp_draw.draw_landmarks(
                    frame, handLms, mp_hands.HAND_CONNECTIONS
                )
        
        # Merge canvas and frame
        gray_canvas = cv2.cvtColor(st.session_state.canvas, cv2.COLOR_BGR2GRAY)
        _, inv = cv2.threshold(gray_canvas, 20, 255, cv2.THRESH_BINARY_INV)
        inv = cv2.cvtColor(inv, cv2.COLOR_GRAY2BGR)
        
        frame_no_paint = cv2.bitwise_and(frame, inv)
        frame_with_paint = cv2.bitwise_or(frame_no_paint, st.session_state.canvas)
        
        draw_bottom_hud(frame_with_paint, mode_text, st.session_state.brush_thickness, st.session_state.is_eraser, actual_w, actual_h)
        
        # Convert back to RGB for display
        frame_display = cv2.cvtColor(frame_with_paint, cv2.COLOR_BGR2RGB)
        st.image(frame_display, use_container_width=True, channels="RGB")

# Controls section - show in sidebar or below on mobile
if col2 is not None:
    with col2:
        st.header("Controls")
        
        st.subheader("Color Selection")
        selected_color = st.radio(
            "Choose color:",
            ["Purple", "Blue", "Green", "Yellow", "Eraser"],
            index=st.session_state.current_color_idx if not st.session_state.is_eraser else 4,
            horizontal=False
        )
        
        color_map = {"Purple": 0, "Blue": 1, "Green": 2, "Yellow": 3, "Eraser": 4}
        selected_idx = color_map[selected_color]
        
        if selected_idx == 4:
            st.session_state.is_eraser = True
            st.session_state.current_color_idx = -1
        else:
            st.session_state.is_eraser = False
            st.session_state.current_color_idx = selected_idx
        
        st.subheader("Brush Settings")
        st.session_state.brush_thickness = st.slider("Brush Size", 5, 30, st.session_state.brush_thickness)
        st.session_state.eraser_thickness = st.slider("Eraser Size", 30, 100, st.session_state.eraser_thickness)
        
        st.subheader("Canvas")
        if st.button("Clear Canvas", type="primary", use_container_width=True):
            # Get current frame size for canvas
            if camera_input is not None:
                frame_temp = np.array(camera_input)
                h, w = frame_temp.shape[:2]
                st.session_state.canvas = np.zeros((h, w, 3), np.uint8)
            else:
                st.session_state.canvas = np.zeros((hCam, wCam, 3), np.uint8)
            st.session_state.prev_x = None
            st.session_state.prev_y = None
            st.rerun()
        
        st.info("💡 **Tips:**\n- Raise index + middle finger to select colors\n- Point only index finger to draw\n- Use controls for easier selection")
else:
    # Mobile-friendly controls below camera
    st.markdown("---")
    st.header("📱 Controls")
    
    # Color buttons in a row for mobile
    col_p1, col_p2, col_p3, col_p4, col_p5 = st.columns(5)
    
    with col_p1:
        if st.button("🟣", use_container_width=True, key="purple"):
            st.session_state.is_eraser = False
            st.session_state.current_color_idx = 0
            st.rerun()
    with col_p2:
        if st.button("🔵", use_container_width=True, key="blue"):
            st.session_state.is_eraser = False
            st.session_state.current_color_idx = 1
            st.rerun()
    with col_p3:
        if st.button("🟢", use_container_width=True, key="green"):
            st.session_state.is_eraser = False
            st.session_state.current_color_idx = 2
            st.rerun()
    with col_p4:
        if st.button("🟡", use_container_width=True, key="yellow"):
            st.session_state.is_eraser = False
            st.session_state.current_color_idx = 3
            st.rerun()
    with col_p5:
        if st.button("🧹", use_container_width=True, key="eraser"):
            st.session_state.is_eraser = True
            st.session_state.current_color_idx = -1
            st.rerun()
    
    st.caption("Current: " + (["Purple", "Blue", "Green", "Yellow", "Eraser"][st.session_state.current_color_idx if not st.session_state.is_eraser else 4]))
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.session_state.brush_thickness = st.slider("Brush Size", 5, 30, st.session_state.brush_thickness)
    with col_s2:
        st.session_state.eraser_thickness = st.slider("Eraser Size", 30, 100, st.session_state.eraser_thickness)
    
    if st.button("🗑️ Clear Canvas", type="primary", use_container_width=True):
        if camera_input is not None:
            frame_temp = np.array(camera_input)
            h, w = frame_temp.shape[:2]
            st.session_state.canvas = np.zeros((h, w, 3), np.uint8)
        else:
            st.session_state.canvas = np.zeros((hCam, wCam, 3), np.uint8)
        st.session_state.prev_x = None
        st.session_state.prev_y = None
        st.rerun()

st.markdown("---")
st.markdown("Made with ❤️ using Streamlit, OpenCV, and MediaPipe")

