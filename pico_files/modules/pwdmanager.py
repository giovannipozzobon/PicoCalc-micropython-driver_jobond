import hashlib, ubinascii, os
import ucryptolib

PASSWORD_FILE = "password.db"
KEY_FILE = "aes.key"
IV_FILE  = "aes.iv"

# --- Initialize AES keys ---
def init_keys():
    if KEY_FILE not in os.listdir():
        with open(KEY_FILE, "wb") as f:
            f.write(os.urandom(16))
    if IV_FILE not in os.listdir():
        with open(IV_FILE, "wb") as f:
            f.write(os.urandom(16))

    with open(KEY_FILE, "rb") as f:
        AES_KEY = f.read()
    with open(IV_FILE, "rb") as f:
        AES_IV = f.read()

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
    cipher = ucryptolib.aes(AES_KEY, 2, AES_IV)
    return cipher.encrypt(pad(data))

def aes_decrypt(data: bytes) -> bytes:
    cipher = ucryptolib.aes(AES_KEY, 2, AES_IV)
    return unpad(cipher.decrypt(data))

# --- Hash password with salt ---
def hash_password(password: str, salt: bytes = None) -> tuple[str, bytes]:
    if salt is None:
        salt = os.urandom(16)
    h = hashlib.sha256()
    h.update(salt + password.encode("utf-8"))
    digest = h.digest()
    return ubinascii.hexlify(digest).decode(), salt

# --- Save or update password ---
def set_password(username: str, password: str, type_: str, filename: str = PASSWORD_FILE):
    users = {}
    try:
        with open(filename, "rb") as f:
            raw = aes_decrypt(f.read()).decode()
            for line in raw.strip().split("\n"):
                parts = line.split(":")
                if len(parts) == 5:
                    u, h, s, p, t = parts
                    users[u] = (h, s, p, t)
    except OSError:
        pass

    hash_hex, salt = hash_password(password)
    users[username] = (hash_hex, salt.hex(), password, type_)

    lines = [f"{u}:{h}:{s}:{p}:{t}" for u, (h, s, p, t) in users.items()]
    encrypted = aes_encrypt("\n".join(lines).encode())
    with open(filename, "wb") as f:
        f.write(encrypted)
    print(f"✅ Password for '{username}' saved with type '{type_}'.")

# --- Verify login ---
def check_password(username: str, password: str, filename: str = PASSWORD_FILE) -> bool:
    try:
        with open(filename, "rb") as f:
            raw = aes_decrypt(f.read()).decode()
            for line in raw.strip().split("\n"):
                parts = line.split(":")
                if len(parts) == 5:
                    u, h, s, p, t = parts
                    if u == username:
                        salt = bytes.fromhex(s)
                        check_hash, _ = hash_password(password, salt)
                        return check_hash == h
    except Exception as e:
        print("❌ Error:", e)
    return False

# --- List users ---
def get_users(filename: str = PASSWORD_FILE):
    try:
        with open(filename, "rb") as f:
            raw = aes_decrypt(f.read()).decode()
            return [line.split(":")[0] for line in raw.strip().split("\n") if len(line.split(":")) == 5]
    except Exception as e:
        print("❌ Error:", e)
        return []

# --- Delete user ---
def delete_user(username: str, filename: str = PASSWORD_FILE):
    users = {}
    try:
        with open(filename, "rb") as f:
            raw = aes_decrypt(f.read()).decode()
            for line in raw.strip().split("\n"):
                parts = line.split(":")
                if len(parts) == 5:
                    u, h, s, p, t = parts
                    users[u] = (h, s, p, t)
    except OSError:
        print("⚠️ No database found.")
        return

    if username in users:
        del users[username]
        if users:
            lines = [f"{u}:{h}:{s}:{p}:{t}" for u, (h, s, p, t) in users.items()]
            encrypted = aes_encrypt("\n".join(lines).encode())
            with open(filename, "wb") as f:
                f.write(encrypted)
        else:
            os.remove(filename)
        print(f"🗑️ User '{username}' deleted.")
    else:
        print(f"❌ User '{username}' not found.")

# --- Change password ---
def change_password(username: str, old_password: str, new_password: str, type_: str, filename: str = PASSWORD_FILE):
    users = {}
    try:
        with open(filename, "rb") as f:
            raw = aes_decrypt(f.read()).decode()
            for line in raw.strip().split("\n"):
                parts = line.split(":")
                if len(parts) == 5:
                    u, h, s, p, t = parts
                    users[u] = (h, s, p, t)
    except OSError:
        print("⚠️ No database found.")
        return

    if username not in users:
        print(f"❌ User '{username}' not found.")
        return

    h, s, _, _ = users[username]
    salt = bytes.fromhex(s)
    check_hash, _ = hash_password(old_password, salt)
    if check_hash != h:
        print("⛔ Incorrect old password.")
        return

    hash_hex, new_salt = hash_password(new_password)
    users[username] = (hash_hex, new_salt.hex(), new_password, type_)

    lines = [f"{u}:{h}:{s}:{p}:{t}" for u, (h, s, p, t) in users.items()]
    encrypted = aes_encrypt("\n".join(lines).encode())
    with open(filename, "wb") as f:
        f.write(encrypted)
    print(f"🔄 Password for '{username}' updated with type '{type_}'.")

# --- Read password for user ---
def get_password_by_username(username: str, filename: str = PASSWORD_FILE):
    try:
        with open(filename, "rb") as f:
            raw = aes_decrypt(f.read()).decode()
            for line in raw.strip().split("\n"):
                parts = line.split(":")
                if len(parts) == 5:
                    u, h, s, p, t = parts
                    if u == username:
                        return p, t
        print(f"❌ User '{username}' not found.")
    except Exception as e:
        print("❌ Error:", e)
    return None, None

# --- Search by type ---
def search_by_type(type_: str, filename: str = PASSWORD_FILE):
    results = []
    try:
        with open(filename, "rb") as f:
            raw = aes_decrypt(f.read()).decode()
            for line in raw.strip().split("\n"):
                parts = line.split(":")
                if len(parts) == 5:
                    u, h, s, p, t = parts
                    if t.lower() == type_.lower():
                        results.append((u, p))
    except Exception as e:
        print("❌ Error:", e)
    return results

# --- Demo ---
if __name__ == "__main__":
    print("Registered users:", get_users())
    action = input("Do you want to [A]dd, [V]erify login, [C]ancel, [P]change password, [R]retrieve password or search by [T]ype? (A/V/C/P/R/T): ").strip().upper()
    if action == "A":
        username = input("New username: ").strip()
        password = input("New password: ").strip()
        type_ = input("Type (e.g. WiFi, Admin, IoT...): ").strip()
        set_password(username, password, type_)
    elif action == "V":
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        if check_password(username, password):
            print("🔓 Access granted!")
        else:
            print("⛔ Incorrect username or password.")
    elif action == "C":
        username = input("Username to delete: ").strip()
        delete_user(username)
    elif action == "P":
        username = input("Username: ").strip()
        old_password = input("Old password: ").strip()
        new_password = input("New password: ").strip()
        type_ = input("New type: ").strip()
        change_password(username, old_password, new_password, type_)
    elif action == "R":
        username = input("Username: ").strip()
        pwd, type_ = get_password_by_username(username)
        if pwd is not None:
            print(f"🔑 Password for '{username}': {pwd} (Type: {type_})")
    elif action == "T":
        type_ = input("Type to search: ").strip()
        results = search_by_type(type_)
        if results:
            print(f"🔍 Passwords found for type '{type_}':")
            for u, p in results:
                print(f" - {u}: {p}")
        else:
            print(f"⚠️ No passwords found for type '{type_}'.")
    else:
        print("Unrecognized action.")
