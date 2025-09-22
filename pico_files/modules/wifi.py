
#  Micropython Libraries
import json
import logging
import network
import socket
import time

#  Logger Setup
logging.basicConfig( level = logging.INFO )

#  Global Variable to store WLAN Instance
wifi = None

class Wifi_Manager:

    def __init__( self ):
        
        #  Setup Internal Logger
        self.logger = logging.getLogger('Wifi_Manager')
        self.logger.setLevel( logging.INFO )
        
        #  Create a new WLAN instance
        self.wlan   = network.WLAN( network.STA_IF )


    def save_file( self, ssid, password, pathname = 'wifi.json' ):
        '''Save WiFi credentials to a file'''
        
        config = {
            "ssid": ssid,
            "password": password
        }
        with open(pathname, 'w') as f:
            json.dump(config, f)

        print( f"Saved credentials for {ssid} to {pathname}" )

    def load_file(self, pathname = 'wifi.json' ):
        '''
        Load WiFi Credentials from File
        '''
        try:
            with open( pathname, 'r') as f:
                config = json.load(f)
                return config.get( 'ssid', '' ), config.get( 'password', '' )
        except:
            return '',''

    def connect( self, ssid = None, password = None, pathname = 'wifi.json' ):
        '''Connect to WiFi with given or saved credentials'''

        # If no credentials provided, try to load saved ones
        if not ssid or not password:
            ssid, password = self.load_file( pathname )
            if not ssid or not password:
                self.logger.error( f'No WiFi credentials found!\nUsage: wifi.connect("your_ssid", "your_password")')
                return None
            
        else:
            # Save the credentials for future use
            self.save_file( ssid, password, pathname )

        # Check if already connected
        if self.wlan.isconnected():
            
            message = f'Already connected to {ssid}\nIP: {self.wlan.ifconfig()[0]}'
            self.logger.warning( message )
            
            return self.wlan

        self.logger.info(f"Connecting to {ssid}...")
        self.wlan.connect(ssid, password)

        # Wait for connection with timeout
        timeout = 10
        while timeout > 0 and not self.wlan.isconnected():
            print(".", end="")
            time.sleep(1)
            timeout -= 1
        print()

        if self.wlan.isconnected():
            print( f'Connected to {ssid}!' )
            print( f'IP: {self.wlan.ifconfig()[0]}' )
            return self.wlan
        else:
            print( 'Connection failed!' )
            print( 'Check your credentials or signal strength' )
            return None

    def status(self):
        '''
        Check WiFi Connection Status
        '''

        if self.wlan.isconnected():
            ip, subnet, gateway, dns = self.wlan.ifconfig()
            ssid = self.wlan.config('essid')

            output  = f'Connected to: {ssid}\n'
            output += f'IP address  : {ip}\n'
            output += f'Gateway     : {gateway}\n'
            output += f'DNS         : {dns}\n'
            logging.info(output)

            return True
        else:
            print("Not connected to WiFi")
            return False


    def scan(self):
        '''Scan for Wifi Networks'''

        #  Perform the network scan
        networks = self.wlan.scan()

        #  Setup Output Log Message
        output  =  'Available Networks:\n'
        output += '+' + '-' * 64 + '+\n'
        output += '|   SSID                     | Channel | Signal      | Security  |\n'
        output += '+' + '-' * 64 + '+\n'

        for ssid, bssid, channel, rssi, security, hidden in networks:
            ssid = ssid.decode('utf-8') if isinstance(ssid, bytes) else ssid

            # Convert RSSI to a readable signal strength
            signal_strength = "Weak"
            if rssi > -67:
                signal_strength = "Excellent"
            elif rssi > -70:
                signal_strength = "Good"
            elif rssi > -80:
                signal_strength = "Fair"

            # Convert security to readable format
            security_types = ["Open", "WEP", "WPA-PSK", "WPA2-PSK", "WPA/WPA2-PSK", "WPA3"]
            security_str = security_types[security] if security < len(security_types) else "Unknown"

            output += f'|  {ssid:<25} | {channel:^7} | {signal_strength:<11} | {security_str}      |\n'

        print(output)

        return networks

    def ping( host = '8.8.8.8' ):
        '''Test internet connectivity by pinging a host'''
        if not self.status():
            return False

        try:
            print( f'Pinging {host}...' )
            ip = socket.getaddrinfo(host, 80)[0][-1][0]
            print( f'Success! Host {host} is reachable at {ip}' )
            return True
        except Exception as e:
            print( f'Ping failed: {e}' )
            return False

def init():
    '''
    Initialize Wifi
    '''
    global wifi
    if not wifi:
        wifi = Wifi_Manager()
        wifi.wlan.active(True)
        wifi.logger.info("Scanning for networks...")
        wifi.scan()

    return wifi

def webrepl( ssid = None, password = None ):
    '''
    Launch the Web-Based Read-Eval-Print-Loop server.
    The SSID and Password are provided as inputs if the user has never connected
    and saved their credentials before.
    '''
    global wifi
    
    wifi = init()
    if wifi.status():
        pass
    else:
        wifi.connect( ssid, password )
        if wifi.status() == False:
            raise Exception('Could not connect to wifi')
    
    #  Setup WebREPL
    import webrepl
    wifi.logger.info( 'Launching Web-REPL' )
    webrepl.start()