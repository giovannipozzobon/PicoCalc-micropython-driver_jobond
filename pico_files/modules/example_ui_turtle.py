
from picocalc import PicoDisplay, PicoKeyboard
from ui_picocalc import Page, Text_Input, Button
import ndarray as np
import colors

# Initialize display and keyboard
global display = PicoDisplay(320, 240)
global keyboard = PicoKeyboard()

# Create a UI page
page = Page()

# Add a text input widget
text_input = Text_Input(label_text="Nome:", input_text="", input_width=150)
page.add_widget(text_input)

# Add a button widget
button = Button(title="Invia", hotkey=ord(' '), retcode="submit")
page.add_widget(button)

# Main loop
while True:
    page.draw(force_draw=True)
    display.show()
    buf = bytearray(8)
    n = keyboard.readinto(buf)
    keys = buf[:n] if n else []
    for k in keys:
        if text_input.is_active and 32 <= k <= 126:
            text_input.input_text += chr(k)
            text_input.refresh_needed = True
        elif k == 0x7F and text_input.is_active:  # Backspace
            text_input.input_text = text_input.input_text[:-1]
            text_input.refresh_needed = True
    action = page.check_keyboard(keyboard)
    if action == "submit":
        print("Testo inserito:", text_input.input_text)
        break
    elif action == "exit":
        break
