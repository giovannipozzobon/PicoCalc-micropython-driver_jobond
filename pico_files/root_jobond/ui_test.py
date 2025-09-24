# ui_test.py
"""
Test interattivo per tutti i componenti UI definiti in ui.py

Controlli:
- Frecce [up]/[down]: cambia focus tra i controlli input
- [o]: attiva il pulsante OK (retcode="ok")
- [c]: attiva il pulsante Annulla (retcode="cancel")
- [esc]: esce dal test

Nota:
- Il disegno e la gestione della tastiera sono delegati a Page/Widget come da ui.py
- I layout VBox/HBox sono usati per dimostrare composizione verticale/orizzontale
"""

try:
    import ui  # Il tuo modulo (ui.py) con Page, Layouts e Widgets
except ImportError as e:
    raise SystemExit("Impossibile importare 'ui.py' nello stesso percorso: {}".format(e))


def build_page():
    """Crea una pagina di test con tutti i componenti e layout."""
    page = ui.Page()

    # Intestazione
    header = ui.Header(title="PicoCalc UI — Demo componenti")

    # Sezione campi (VBox con righe in HBox)
    fields = ui.VBoxLayout()
    fields.add_widget(ui.Label(title="Dati utente"))

    row1 = ui.HBoxLayout()
    row1.add_widget(ui.Text_Input(label_text="Nome:",    input_width=120))
    row1.add_widget(ui.Text_Input(label_text="Cognome:", input_width=140))
    fields.add_widget(row1)

    row2 = ui.HBoxLayout()
    row2.add_widget(ui.Text_Input(label_text="Email:", input_width=200))
    fields.add_widget(row2)

    # Sezione opzioni (VBox)
    options = ui.VBoxLayout()
    options.add_widget(ui.Label(title="Opzioni"))
    options.add_widget(ui.Check_Box(label_text="Accetto i termini"))
    options.add_widget(ui.Check_Box(label_text="Iscrivimi alla newsletter"))

    # Pulsanti azione (HBox)
    buttons = ui.HBoxLayout()
    ok_btn     = ui.Button(title="OK   [o]",      hotkey="o", retcode="ok")
    cancel_btn = ui.Button(title="Annulla  [c]",  hotkey="c", retcode="cancel")
    buttons.add_widget(ok_btn)
    buttons.add_widget(cancel_btn)

    # Barra di stato (Label)
    status = ui.Label(
        title="Pronto — Usa [up]/[down] per il focus, [o]/[c] per azioni, [esc] per uscire."
    )

    # Composizione sulla Page (render verticale in quest’ordine)
    page.add_widget(header)
    page.add_widget(fields)
    page.add_widget(options)
    page.add_widget(buttons)
    page.add_widget(status)

    return page, status


def main():
    # Costruisci la pagina e ottieni la barra di stato per aggiornamenti
    page, status = build_page()

    # Primo disegno completo
    page.draw(force_draw=True)

    # Loop di gestione eventi
    while True:
        action = page.check_keyboard()

        if action is None:
            # Nessun tasto interessante: ridisegna solo se necessario
            page.draw()
            continue

        if action == "exit":
            # Uscita con [esc]
            break

        # Qualsiasi altra azione (es. hotkey dei bottoni): aggiorna lo status
        status.title = "Azione: {}".format(action)
        status.refresh_needed = True

        # Ridisegna il frame
        page.draw()


if __name__ == "__main__":
    main()