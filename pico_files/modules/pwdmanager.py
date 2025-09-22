import hashlib, ubinascii, os
import ucryptolib

PASSWORD_FILE = "password.db"
KEY_FILE = "aes.key"
IV_FILE  = "aes.iv"

# --- Inizializza chiavi AES ---
def init_keys():
    if KEY_FILE not in os.listdir():
        with open(KEY_FILE, "wb") as f:
            f.write(os.urandom(16))  # 16 byte = AES-128
    if IV_FILE not in os.listdir():
        with open(IV_FILE, "wb") as f:
            f.write(os.urandom(16))  # 16 byte IV

    with open(KEY_FILE, "rb") as f:
        AES_KEY = f.read()
    with open(IV_FILE, "rb") as f:
        AES_IV = f.read()

    if len(AES_KEY) not in (16, 24, 32):
        raise ValueError("AES_KEY deve avere lunghezza 16, 24 o 32 byte")
    if len(AES_IV) != 16:
        raise ValueError("AES_IV deve avere lunghezza 16 byte")

    return AES_KEY, AES_IV

AES_KEY, AES_IV = init_keys()

# --- AES helpers ---
def pad(data: bytes) -> bytes:
    pad_len = 16 - (len(data) % 16)
    return data + bytes([pad_len]) * pad_len

def unpad(data: bytes) -> bytes:
    pad_len = data[-1]
    return data[:-pad_len]

def aes_encrypt(data: bytes) -> bytes:
    cipher = ucryptolib.aes(AES_KEY, 2, AES_IV)  # 2 = CBC
    return cipher.encrypt(pad(data))

def aes_decrypt(data: bytes) -> bytes:
    cipher = ucryptolib.aes(AES_KEY, 2, AES_IV)
    return unpad(cipher.decrypt(data))

# --- Hash password con salt ---
def hash_password(password: str, salt: bytes = None) -> tuple[str, bytes]:
    if salt is None:
        salt = os.urandom(16)
    h = hashlib.sha256()
    h.update(salt + password.encode("utf-8"))
    digest = h.digest()
    return ubinascii.hexlify(digest).decode(), salt

# --- Salva o aggiorna password per un utente ---
def set_password(username: str, password: str, filename: str = PASSWORD_FILE):
    users = {}
    try:
        with open(filename, "rb") as f:
            encrypted = f.read()
            raw = aes_decrypt(encrypted).decode()
            for line in raw.strip().split("\n"):
                u, h, s, p = line.split(":")
                users[u] = (h, s, p)
    except OSError:
        pass  # File non esiste ancora

    hash_hex, salt = hash_password(password)
    users[username] = (hash_hex, salt.hex(), password)

    lines = [f"{u}:{h}:{s}:{p}" for u, (h, s, p) in users.items()]
    raw = "\n".join(lines).encode()
    encrypted = aes_encrypt(raw)
    with open(filename, "wb") as f:
        f.write(encrypted)
    print(f"✅ Password per '{username}' salvata.")

# --- Verifica login per un utente ---
def check_password(username: str, password: str, filename: str = PASSWORD_FILE) -> bool:
    try:
        with open(filename, "rb") as f:
            encrypted = f.read()
            raw = aes_decrypt(encrypted).decode()
            for line in raw.strip().split("\n"):
                u, h, s, p = line.split(":")
                if u == username:
                    salt = bytes.fromhex(s)
                    check_hash, _ = hash_password(password, salt)
                    return check_hash == h
    except Exception as e:
        print("❌ Errore:", e)
    return False

# --- Lista tutti gli utenti registrati ---
def get_users(filename: str = PASSWORD_FILE):
    try:
        with open(filename, "rb") as f:
            encrypted = f.read()
            raw = aes_decrypt(encrypted).decode()
            return [line.split(":")[0] for line in raw.strip().split("\n")]
    except Exception as e:
        print("❌ Errore:", e)
        return []

# --- Cancella un utente dal database ---
def delete_user(username: str, filename: str = PASSWORD_FILE):
    users = {}
    try:
        with open(filename, "rb") as f:
            encrypted = f.read()
            raw = aes_decrypt(encrypted).decode()
            for line in raw.strip().split("\n"):
                u, h, s, p = line.split(":")
                users[u] = (h, s, p)
    except OSError:
        print("⚠️ Nessun database trovato.")
        return

    if username in users:
        del users[username]
        if users:
            lines = [f"{u}:{h}:{s}:{p}" for u, (h, s, p) in users.items()]
            raw = "\n".join(lines).encode()
            encrypted = aes_encrypt(raw)
            with open(filename, "wb") as f:
                f.write(encrypted)
        else:
            os.remove(filename)
        print(f"🗑️ Utente '{username}' cancellato.")
    else:
        print(f"❌ Utente '{username}' non trovato.")

# --- Cambia la password di un utente ---
def change_password(username: str, old_password: str, new_password: str, filename: str = PASSWORD_FILE):
    users = {}
    try:
        with open(filename, "rb") as f:
            encrypted = f.read()
            raw = aes_decrypt(encrypted).decode()
            for line in raw.strip().split("\n"):
                u, h, s, p = line.split(":")
                users[u] = (h, s, p)
    except OSError:
        print("⚠️ Nessun database trovato.")
        return

    if username not in users:
        print(f"❌ Utente '{username}' non trovato.")
        return

    # Verifica la vecchia password
    h, s, _ = users[username]
    salt = bytes.fromhex(s)
    check_hash, _ = hash_password(old_password, salt)
    if check_hash != h:
        print("⛔ Vecchia password errata.")
        return

    # Aggiorna con la nuova password
    hash_hex, new_salt = hash_password(new_password)
    users[username] = (hash_hex, new_salt.hex(), new_password)

    lines = [f"{u}:{h}:{s}:{p}" for u, (h, s, p) in users.items()]
    raw = "\n".join(lines).encode()
    encrypted = aes_encrypt(raw)
    with open(filename, "wb") as f:
        f.write(encrypted)
    print(f"🔄 Password per '{username}' aggiornata.")

# --- Leggi la password in chiaro di un utente (solo username) ---
def get_password_by_username(username: str, filename: str = PASSWORD_FILE):
    try:
        with open(filename, "rb") as f:
            encrypted = f.read()
            raw = aes_decrypt(encrypted).decode()
            for line in raw.strip().split("\n"):
                u, h, s, p = line.split(":")
                if u == username:
                    return p
        print(f"❌ Utente '{username}' non trovato.")
    except Exception as e:
        print("❌ Errore:", e)
    return None

# --- Demo ---
if __name__ == "__main__":
    print("Utenti registrati:", get_users())
    action = input("Vuoi [A]ggiungere/aggiornare, [V]erificare login, [C]ancellare utente, [P]er cambiare password o [R]ecuperare password per utente? (A/V/C/P/R): ").strip().upper()
    if action == "A":
        username = input("Nuovo username: ").strip()
        password = input("Nuova password: ").strip()
        set_password(username, password)
    elif action == "V":
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        if check_password(username, password):
            print("🔓 Accesso consentito!")
        else:
            print("⛔ Username o password errati.")
    elif action == "C":
        username = input("Username da cancellare: ").strip()
        delete_user(username)
    elif action == "P":
        username = input("Username: ").strip()
        old_password = input("Vecchia password: ").strip()
        new_password = input("Nuova password: ").strip()
        change_password(username, old_password, new_password)
    elif action == "R":
        username = input("Username di cui vuoi leggere la password: ").strip()
        pwd = get_password_by_username(username)
        if pwd is not None:
            print(f"🔑 Password salvata per '{username}': {pwd}")
    else:
        print("Azione non riconosciuta.")
