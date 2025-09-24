
import btclassic_kbd as kbd

# Se il Wi‑Fi è già attivo lato MicroPython, salta init CYW43
try:
    import network
    wlan = network.WLAN()
    skip = True
except:
    skip = False

kbd.init(skip_cyw43=skip)
kbd.set_layout("IT")

print("Scanning for HID devices...")
devs = kbd.scan(timeout_ms=8000, hid_only=True, names=True)
for d in devs:
    print(d)

if devs:
    addr = devs[0][0]
    print("Connecting to", addr)
    print("OK?", kbd.connect(addr))
    while True:
        ev = kbd.get_event(200)
        if ev:
            print(ev)
else:
    print("No HID devices found.")
