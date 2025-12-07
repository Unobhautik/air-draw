import cv2
import numpy as np
import mediapipe as mp

# ------------ Config ------------
wCam, hCam = 1280, 720

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, wCam)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, hCam)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils

canvas = np.zeros((hCam, wCam, 3), np.uint8)

# BGR colors
colors = [
    (255,   0, 255),   # purple
    (255,   0,   0),   # blue
    (0,   255,   0),   # green
    (0,   255, 255),   # yellow
]
color_names = ["PURPLE", "BLUE", "GREEN", "YELLOW"]

# index 0–3 = colors, 4 = eraser
buttons_count = 5
button_height = 80
button_width = wCam // buttons_count

current_color_idx = 1
current_color = colors[current_color_idx]
eraser_color = (0, 0, 0)
brush_thickness = 12
eraser_thickness = 60

prev_x, prev_y = None, None
mode_text = "IDLE"
is_eraser = False


# ------------ UI Drawing helpers ------------
def draw_top_bar(img, active_idx, is_eraser_mode):
    # Background bar
    overlay = img.copy()
    cv2.rectangle(overlay, (0, 0), (wCam, button_height + 20), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)

    # Title
    cv2.putText(
        img, "AIR DRAW",
        (20, 55),
        cv2.FONT_HERSHEY_SIMPLEX, 1.3,
        (255, 255, 255), 3, cv2.LINE_AA
    )

    # Color / eraser buttons
    for i in range(buttons_count):
        x1 = i * button_width
        x2 = x1 + button_width
        y1 = 20
        y2 = y1 + button_height - 20

        if i < 4:
            col = colors[i]
            label = color_names[i]
        else:
            col = (60, 60, 60)
            label = "ERASER"

        cv2.rectangle(img, (x1 + 5, y1), (x2 - 5, y2), col, -1)

        # active state border
        if i == active_idx or (i == 4 and is_eraser_mode):
            border_col = (255, 255, 255)
            thickness = 4
        else:
            border_col = (180, 180, 180)
            thickness = 2

        cv2.rectangle(img, (x1 + 5, y1), (x2 - 5, y2), border_col, thickness)

        text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        text_x = x1 + (button_width - text_size[0]) // 2
        text_y = y2 - 10
        cv2.putText(
            img, label, (text_x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6,
            (255, 255, 255), 2, cv2.LINE_AA
        )


def draw_bottom_hud(img, mode_text, brush_size, eraser_mode):
    overlay = img.copy()
    cv2.rectangle(
        overlay,
        (0, hCam - 70),
        (wCam, hCam),
        (0, 0, 0),
        -1
    )
    cv2.addWeighted(overlay, 0.6, img, 0.4, 0, img)

    left_text = f"MODE: {mode_text}"
    cv2.putText(
        img, left_text,
        (20, hCam - 25),
        cv2.FONT_HERSHEY_SIMPLEX, 0.8,
        (255, 255, 255), 2, cv2.LINE_AA
    )

    mid_text = "INDEX+MIDDLE: Select | INDEX: Draw"
    cv2.putText(
        img, mid_text,
        (wCam // 2 - 260, hCam - 25),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6,
        (200, 200, 200), 2, cv2.LINE_AA
    )

    right_text = "C: Clear  |  Q: Quit"
    cv2.putText(
        img, right_text,
        (wCam - 310, hCam - 25),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6,
        (180, 180, 180), 2, cv2.LINE_AA
    )

    # brush size indicator
    center_x = wCam - 70
    center_y = hCam - 40
    size = eraser_thickness if eraser_mode else brush_size
    cv2.circle(img, (center_x, center_y), size // 4, (255, 255, 255), 2)
    cv2.putText(
        img, "SIZE",
        (center_x - 25, center_y - 25),
        cv2.FONT_HERSHEY_PLAIN, 1.2,
        (220, 220, 220), 1, cv2.LINE_AA
    )


# ------------ Main loop ------------
while True:
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)

    draw_top_bar(frame, current_color_idx, is_eraser)

    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

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
                prev_x, prev_y = None, None
                mode_text = "SELECT"

                if iy < button_height + 20:
                    idx = ix // button_width
                    idx = int(np.clip(idx, 0, buttons_count - 1))

                    if idx == 4:
                        is_eraser = True
                        current_color_idx = -1
                    else:
                        is_eraser = False
                        current_color_idx = idx
                        current_color = colors[current_color_idx]

                cv2.circle(frame, (ix, iy), 14, (255, 255, 255), cv2.FILLED)

            # Draw mode
            elif index_up and not middle_up:
                mode_text = "DRAW (ERASER)" if is_eraser else "DRAW"

                draw_color = eraser_color if is_eraser else current_color
                thickness = eraser_thickness if is_eraser else brush_thickness

                cv2.circle(frame, (ix, iy), 14, draw_color, cv2.FILLED)

                if prev_x is None and prev_y is None:
                    prev_x, prev_y = ix, iy

                cv2.line(canvas, (prev_x, prev_y), (ix, iy), draw_color, thickness)
                prev_x, prev_y = ix, iy

            else:
                prev_x, prev_y = None, None
                mode_text = "IDLE"

            mp_draw.draw_landmarks(
                frame, handLms, mp_hands.HAND_CONNECTIONS
            )
    else:
        mode_text = "NO HAND"

    # merge canvas and frame
    gray_canvas = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
    _, inv = cv2.threshold(gray_canvas, 20, 255, cv2.THRESH_BINARY_INV)
    inv = cv2.cvtColor(inv, cv2.COLOR_GRAY2BGR)

    frame_no_paint = cv2.bitwise_and(frame, inv)
    frame_with_paint = cv2.bitwise_or(frame_no_paint, canvas)

    draw_bottom_hud(frame_with_paint, mode_text, brush_thickness, is_eraser)

    cv2.imshow("AIR DRAW", frame_with_paint)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break
    elif key == ord('c'):
        canvas = np.zeros((hCam, wCam, 3), np.uint8)

cap.release()
cv2.destroyAllWindows()
