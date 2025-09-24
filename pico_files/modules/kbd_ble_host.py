# kbd_ble_host.py  — MicroPython (Pico W / Pico 2 W)
import bluetooth
from micropython import const
import struct, time
from ble_advertising import decode_services, decode_name  # dal repo esempi MicroPython

# ---- Costanti/UUID BLE ----
_IRQ_SCAN_RESULT                = const(5)
_IRQ_SCAN_DONE                  = const(6)
_IRQ_PERIPHERAL_CONNECT         = const(7)
_IRQ_PERIPHERAL_DISCONNECT      = const(8)
_IRQ_GATTC_SERVICE_RESULT       = const(9)
_IRQ_GATTC_SERVICE_DONE         = const(10)
_IRQ_GATTC_CHARACTERISTIC_RESULT= const(11)
_IRQ_GATTC_CHARACTERISTIC_DONE  = const(12)
_IRQ_GATTC_DESCRIPTOR_RESULT    = const(13)
_IRQ_GATTC_DESCRIPTOR_DONE      = const(14)
_IRQ_GATTC_NOTIFY               = const(18)

_ADV_IND        = const(0x00)
_ADV_DIRECT_IND = const(0x01)

UUID_HID_SERVICE    = bluetooth.UUID(0x1812)
UUID_HID_REPORT     = bluetooth.UUID(0x2A4D)
UUID_HID_REPORT_MAP = bluetooth.UUID(0x2A4B)
UUID_REPORT_REF_DESC= bluetooth.UUID(0x2908)   # Report Reference Descriptor
UUID_CCCD           = bluetooth.UUID(0x2902)

# ---- Mappa HID usage -> ASCII (layout US, base) ----
# HID Usage IDs for 'a'..'z' start at 0x04, '1'..'0' at 0x1E..0x27, ecc.
HID_TO_ASCII = {
    # letters
    **{i: chr(ord('a') + i - 0x04) for i in range(0x04, 0x1e)},
    # numbers row
    0x1e:'1',0x1f:'2',0x20:'3',0x21:'4',0x22:'5',0x23:'6',0x24:'7',0x25:'8',0x26:'9',0x27:'0',
    0x2c:' ', 0x28:'\n', 0x2a:'\b',  # space, Enter, Backspace
    0x2d:'-', 0x2e:'=', 0x2f:'[', 0x30:']', 0x31:'\\',
    0x33:';', 0x34:"'", 0x35:'`', 0x36:',', 0x37:'.', 0x38:'/',
}

SHIFTED = {
    # shifted variants
    '1':'!', '2':'@', '3':'#', '4':'$', '5':'%', '6':'^', '7':'&', '8':'*', '9':'(', '0':')',
    '-':'_', '=':'+','[':'{',']':'}','\\':'|',';':':',"'":'"','`':'~',',':'<','.':'>','/':'?',
}

MODIFIER_SHIFT_MASK = 0x22  # bit1=LeftShift (0x02), bit5=RightShift (0x20)

class BLEKeyboardHost:
    def __init__(self):
        self.ble = bluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self._irq)

        self.reset_state()

    def reset_state(self):
        self.addr_type = None
        self.addr = None
        self.name = None

        self.conn_handle = None
        self.svc_start = None
        self.svc_end = None

        # Elenco di (value_handle, cccd_handle, report_id, report_type)
        self.input_reports = []

        self._scan_cb = None

    # --- IRQ handler ---
    def _irq(self, event, data):
        if event == _IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            if adv_type in (_ADV_IND, _ADV_DIRECT_IND):
                svcs = decode_services(adv_data)
                if UUID_HID_SERVICE in svcs:
                    # Trovata potenziale tastiera
                    self.addr_type = addr_type
                    self.addr = bytes(addr)
                    self.name = decode_name(adv_data) or "?"
                    self.ble.gap_scan(None)  # stop early

        elif event == _IRQ_SCAN_DONE:
            if self._scan_cb:
                self._scan_cb(self.addr_type, self.addr, self.name)
                self._scan_cb = None

        elif event == _IRQ_PERIPHERAL_CONNECT:
            conn_handle, at, a = data
            if at == self.addr_type and a == self.addr:
                self.conn_handle = conn_handle
                # Scopri i servizi
                self.ble.gattc_discover_services(self.conn_handle)

        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            conn_handle, _, _ = data
            if conn_handle == self.conn_handle:
                print("Disconnesso")
                self.reset_state()

        elif event == _IRQ_GATTC_SERVICE_RESULT:
            conn_handle, start, end, uuid = data
            if conn_handle == self.conn_handle and uuid == UUID_HID_SERVICE:
                self.svc_start, self.svc_end = start, end

        elif event == _IRQ_GATTC_SERVICE_DONE:
            if self.svc_start and self.svc_end:
                # Scopri caratteristiche del servizio HID
                self.ble.gattc_discover_characteristics(self.conn_handle, self.svc_start, self.svc_end)
            else:
                print("Servizio HID non trovato")

        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
            conn_handle, def_handle, value_handle, props, uuid = data
            if conn_handle == self.conn_handle and uuid == UUID_HID_REPORT:
                # Potrebbe essere input/output/feature: lo capiremo dal Report Reference Descriptor
                # Per ora registriamo il value_handle e cercheremo descrittori
                self.input_reports.append([value_handle, None, None, None])  # cccd, id, type da riempire

        elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:
            # A questo punto cerchiamo i descrittori per ogni caratteristica trovata
            for i, (vh, cccd, rid, rtype) in enumerate(self.input_reports):
                self.ble.gattc_discover_descriptors(self.conn_handle, vh, vh+5)

        elif event == _IRQ_GATTC_DESCRIPTOR_RESULT:
            conn_handle, d_handle, d_uuid = data
            # Scopri CCCD e Report Reference per ciascun report
            for rep in self.input_reports:
                vh = rep[0]
                if d_uuid == UUID_CCCD and rep[1] is None and d_handle >= vh:
                    rep[1] = d_handle  # cccd_handle
                elif d_uuid == UUID_REPORT_REF_DESC and rep[2] is None and d_handle >= vh:
                    # Report Reference contiene [report_id, report_type]
                    def _on_read_report_ref(conn, value_handle, value):
                        # Non usiamo value_handle qui; value = 2 bytes
                        if value and len(value) >= 2:
                            rep[2] = value[0]      # report_id
                            rep[3] = value[1]      # 1=input, 2=output, 3=feature
                    # Leggi sincrono (in pratica è async, ma ignoriamo l'esito qui)
                    try:
                        self.ble.gattc_read(self.conn_handle, d_handle)
                    except:
                        pass

        elif event == _IRQ_GATTC_DESCRIPTOR_DONE:
            # Abilita notifiche solo sui report di tipo Input
            for vh, cccd_h, rid, rtype in self.input_reports:
                if cccd_h:
                    # 0x0001 = notifications
                    try:
                        self.ble.gattc_write(self.conn_handle, cccd_h, struct.pack('<h', 0x0001), 1)
                    except OSError as e:
                        print("CCCD write err:", e)
            print("Notifiche abilitate (se supportate)")

        elif event == _IRQ_GATTC_NOTIFY:
            conn_handle, value_handle, notify_data = data
            if conn_handle == self.conn_handle:
                self._handle_hid_input_report(notify_data)

    # --- API utente ---
    def scan_and_connect(self, timeout_ms=5000):
        def _done(at, addr, name):
            if at is None:
                print("Nessuna tastiera BLE HOGP trovata")
                return
            print("Trovata:", name, addr)
            self.ble.gap_connect(at, addr)

        self._scan_cb = _done
        # intervallo/finestra bilanciati per demo
        self.ble.gap_scan(timeout_ms, 30000, 30000)

    # --- Decodifica HID "boot keyboard" ---
    def _handle_hid_input_report(self, data: bytes):
        # Formato standard: [modifiers][reserved][k1][k2][k3][k4][k5][k6]
        if len(data) < 8:
            return
        mods = data[0]
        keys = data[2:8]

        pressed = [kc for kc in keys if kc != 0]
        if not pressed:
            return

        for kc in pressed:
            ch = HID_TO_ASCII.get(kc)
            if ch:
                if mods & MODIFIER_SHIFT_MASK:
                    if 'a' <= ch <= 'z':
                        ch = ch.upper()
                    else:
                        ch = SHIFTED.get(ch, ch)
                print(ch, end="", flush=True)
            else:
                # Tasti non stampabili o speciali (F-keys, arrows, ecc.)
                print(f"[KC 0x{kc:02X}]", end="", flush=True)

# ---- Main ----
if __name__ == "__main__":
    host = BLEKeyboardHost()
    print("Scansione per tastiere BLE HID...")
    host.scan_and_connect()
    # Mantieni vivo il main loop
    while True:
        time.sleep_ms(200)
