import turtle

def test_turtle_module():
    # Inizializza lo schermo Turtle
    screen = turtle.init()
    print("Schermo inizializzato.")

    # Resetta lo schermo
    turtle.reset()
    print("Schermo resettato.")

    # Riempie lo schermo di nero (colore 0)
    screen.fill(0)
    print("Schermo riempito di nero.")

    # Disegna un rettangolo rosso (colore 1) in posizione (50, 50), larghezza 100, altezza 60
    turtle.fill_rect(50, 50, 100, 60, 1)
    print("Rettangolo rosso disegnato.")

    # Scrive del testo bianco (colore 7) in posizione (60, 120)
    screen.draw_text("Test Turtle!", 60, 120, 7)
    print("Testo scritto sullo schermo.")

    # Mostra lo schermo
    screen.show()
    print("Schermo aggiornato.")

    # Legge la tastiera (mostra i tasti premuti)
    keys = turtle.check_keyboard(verbose=True)
    print("Tasti premuti:", keys)

# Esegui il test
test_turtle_module()
