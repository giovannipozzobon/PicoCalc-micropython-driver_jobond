
from machine import I2C, Pin
import time
import socket
import network
import struct

class DS3231:
    def __init__(self, i2c):
        self.i2c = i2c
        self.addr = 0x68

    def bcd2dec(self, bcd):
        return (bcd // 16) * 10 + (bcd % 16)

    def dec2bcd(self, dec):
        return (dec // 10) * 16 + (dec % 10)

    def read_time(self):
        data = self.i2c.readfrom_mem(self.addr, 0x00, 7)
        second = self.bcd2dec(data[0] & 0x7F)
        minute = self.bcd2dec(data[1])
        hour = self.bcd2dec(data[2])
        day = self.bcd2dec(data[4])
        month = self.bcd2dec(data[5] & 0x1F)
        year = self.bcd2dec(data[6]) + 2000
        return (year, month, day, hour, minute, second)

    def set_time(self, year, month, day, hour, minute, second):
        self.i2c.writeto_mem(self.addr, 0x00, bytes([
            self.dec2bcd(second),
            self.dec2bcd(minute),
            self.dec2bcd(hour),
            0,
            self.dec2bcd(day),
            self.dec2bcd(month),
            self.dec2bcd(year - 2000)
        ]))

    # Funzione per ottenere ora da server NTP
    def get_ntp_time(self, host="pool.ntp.org"):
        NTP_DELTA = 2208988800
        addr = socket.getaddrinfo(host, 123)[0][-1]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        msg = b'\x1b' + 47 * b'\0'
        s.sendto(msg, addr)
        msg = s.recv(48)
        s.close()
        val = struct.unpack("!I", msg[40:44])[0]
        return val - NTP_DELTA

    # Sincronizzazione NTP e aggiornamento RTC
    def set_datetime_ntp(self, host="pool.ntp.org"):
        try:
            t = self.get_ntp_time()
            t = time.localtime(t + 2 * 3600)  # Offset +2 ore
            self.set_time(t[0], t[1], t[2], t[3], t[4], t[5])
            print("RTC aggiornato da NTP:")
            print(f"Data: {t[2]:02d}/{t[1]:02d}/{t[0]}")
            print(f"Ora: {t[3]:02d}:{t[4]:02d}:{t[5]:02d}")
        except Exception as e:
            print("Errore nella sincronizzazione NTP:", e)


# Inizializzazione I2C(1) su GP4 (SCL) e GP5 (SDA)
# i2c = I2C(1, scl=Pin(7), sda=Pin(6), freq=10000)
# rtc = DS3231(i2c)

#rtc.set_time(2025,9,18,16,16,00)
# Imposta l'orario (decommenta per usarlo una volta)
# rtc.set_time(2025, 9, 18, 15, 0, 0)

# Loop per leggere e stampare l'orario
# while True:
#     now = rtc.read_time()
#     print("Data e ora:", now)
#     time.sleep(10)
