import ui_turtle
import turtle

# Crea una pagina UI
page = ui_turtle.Page()

#Aggiungi Header
header = ui_turtle.Header(title="Titolo")
page.add_widget(header)

# Aggiungi un campo di testo
text_input = ui_turtle.Text_Input(label_text="Nome:", input_text="", input_width=150)
page.add_widget(text_input)

# Aggiungi un bottone
button = ui_turtle.Button(title="Invia", hotkey=turtle.Key.F1, retcode="submit")
page.add_widget(button)

# Aggiungi un bottone
label = ui_turtle.Label(title="Label",foreground_color =5)
page.add_widget(label)

# Aggiungi checkbox
checkbox1 = ui_turtle.Check_Box(label_text="check1")
page.add_widget(checkbox1)


page.draw(True)


# Loop principale
while True:
    #page.draw(force_draw=True)
    action = page.check_keyboard()
    #print("Keyboard:", action)
    if action == "submit":
        print("Testo inserito:", text_input.input_text)
        break
    elif action == "exit":
        break
