import logging
import time
import sys
import subprocess
import os
import hashlib
import warnings
from cryptography.utils import CryptographyDeprecationWarning

# Suppress specific deprecation warnings
warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)

DEBUG_MODE = False

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)
console_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)

file_handler = logging.FileHandler('hetzner_debug.log')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
file_handler.setFormatter(file_formatter)

# Remove existing handlers if any to avoid duplicate logging
if logger.hasHandlers():
    logger.handlers.clear()

logger.addHandler(console_handler)
logger.addHandler(file_handler)

logger.debug("Starting Hetzner Cloud Management Tool")

# Check if running in a frozen state (compiled)
is_frozen = getattr(sys, 'frozen', False)

# Version of the script
version = "0.1.7.6"

# Initialize global variables
api_key = None
winscp_path = None

# Function to calculate the hash of a file
def calculate_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def download_file(url, save_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    else:
        logger.error(f"Failed to download file from {url}")
        raise Exception("Download failed")

def compare_files(file_path1, file_path2):
    with open(file_path1, 'rb') as f1, open(file_path2, 'rb') as f2:
        return f1.read() == f2.read()

def create_updater_script():
    updater_script_content = '''
import os
import sys
import shutil
import time
import logging

# Set up logging
logging.basicConfig(filename='updater.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

def main(script_path, new_script_path):
    logging.debug("Updater script started")

    # Give some time to ensure the main script has exited
    time.sleep(1)

    retries = 6  # Retry every 10 seconds up to 1 minute
    while retries > 0:
        try:
            if os.path.exists(script_path):
                os.remove(script_path)
                logging.debug(f"Removed old script: {script_path}")
            shutil.move(new_script_path, script_path)
            logging.debug(f"Moved new script to: {script_path}")
            print("Update successful. Restarting script...")
            logging.debug("Update successful. Restarting script...")
            # Restart the script
            os.execv(sys.executable, ['python', script_path] + sys.argv[1:])
        except Exception as e:
            logging.error(f"Failed to update the script: {e}")
            print(f"Failed to update the script: {e}")
            retries -= 1
            if retries > 0:
                print("Retrying in 10 seconds...")
                logging.debug("Retrying in 10 seconds...")
                time.sleep(10)
            else:
                print("Max retries reached. Exiting updater.")
                logging.debug("Max retries reached. Exiting updater.")
                sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: updater.py <script_path> <new_script_path>")
        logging.error("Invalid usage. Exiting.")
        sys.exit(1)

    script_path = sys.argv[1]
    new_script_path = sys.argv[2]

    main(script_path, new_script_path)
'''
    with open('updater.py', 'w') as f:
        f.write(updater_script_content)
    logger.debug("Updater script written to disk")
    print("Updater script created")

def setup_virtual_environment():
    logging.debug("Entered setup_virtual_environment function")
    venv_path = os.path.join(os.getcwd(), "hetzner_venv")
    if not os.path.exists(venv_path):
        logging.info("Creating virtual environment...")
        subprocess.check_call([sys.executable, "-m", "venv", venv_path])
        logging.info("Virtual environment created.")
    else:
        logging.info("Virtual environment already exists.")

    activate_script = os.path.join(venv_path, "bin", "activate_this.py")
    exec(open(activate_script).read(), {'__file__': activate_script})
    logging.info("Virtual environment activated.")

def install_required_packages():
    logging.debug("Entered install_required_packages function")
    required_packages = ["requests", "colorama", "paramiko>=3.0.0", "cryptography>=39.0.0"]
    for package in required_packages:
        try:
            __import__(package.split('>=')[0])
            logging.debug(f"Package '{package}' is already installed.")
        except ImportError:
            logging.info(f"Installing package '{package}'...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            logging.info(f"Package '{package}' installed.")
        except Exception:
            logging.info(f"Reinstalling package '{package}'...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package])
            logging.info(f"Package '{package}' reinstalled.")

def install_python():
    logging.debug("Entered install_python function")
    if is_frozen:
        logging.debug("Skipping install_python function in frozen mode")
        return

    try:
        subprocess.check_call([sys.executable, "--version"])
        print("Python is already installed.")
        logging.debug("Python is already installed.")
        print("")
    except subprocess.CalledProcessError:
        if sys.platform == 'win32':
            print("Please visit https://www.python.org/downloads/ to download and install Python manually.")
        elif sys.platform in ['linux', 'darwin']:
            print("Python is not installed on your system.")
            choice = input("Do you want to try to install Python automatically? (y/n): ").strip().lower()
            if choice == 'y':
                if sys.platform == 'linux':
                    command = "sudo apt-get install python3"
                else:  # macOS
                    command = "brew install python3"
                try:
                    subprocess.check_call(command, shell=True)
                    print("Python installed successfully.")
                except Exception as e:
                    print(f"Failed to install Python automatically: {e}")
                    print("Please install Python manually using your package manager.")
            else:
                if sys.platform == 'linux':
                    print("Please run 'sudo apt-get install python3' in your terminal to install Python.")
                elif sys.platform == 'darwin':
                    print("Please run 'brew install python3' in your terminal to install Python.")
        logging.error("Python installation check failed.")

install_python()

def install_and_reload(package):
    logging.debug(f"Entered install_and_reload function for package: {package}")
    if is_frozen:
        logging.debug(f"Skipping install_and_reload for package {package} in frozen mode")
        return

    package_name = package.split('>=')[0]
    try:
        logging.debug(f"Attempting to import {package_name}")
        __import__(package_name)
        logging.debug(f"Successfully imported {package_name}")
    except ImportError:
        logging.debug(f"{package_name} not found, attempting to install")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        logging.debug(f"Successfully installed {package_name}")
    finally:
        logging.debug(f"Reloading or importing {package_name}")
        import importlib
        if package_name in sys.modules:
            globals()[package_name] = importlib.reload(sys.modules[package_name])
        else:
            globals()[package_name] = importlib.import_module(package_name)
        logging.debug(f"Successfully reloaded or imported {package_name}")

# List of required packages
required_packages = ["requests", "colorama", "paramiko>=3.0.0", "cryptography>=39.0.0"]

# Check and install missing packages, then import or reload them
for package in required_packages:
    install_and_reload(package)

import getpass
logging.debug("Imported getpass")
import re
logging.debug("Imported re")
import requests
logging.debug("Imported requests")
import json
logging.debug("Imported json")
import time
logging.debug("Imported time")
import paramiko
logging.debug("Imported paramiko")
from colorama import Fore, Style
logging.debug("Imported colorama")

def make_api_call(url, headers):
    """Utility function to make API calls and handle failures."""
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # This will raise an exception for HTTP errors
        return response
    except requests.exceptions.HTTPError as e:
        print("API call failed, possibly due to a bad API key.")
        # Reset API key if there is a failure in the call
        global api_key
        api_key = None
        return None
    
def pause_and_return():
    input("Press any key to continue...")
    main_menu()

def create_and_upload_ssh_key(ssh_key_name=None):
    global api_key, global_passphrase
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    url = "https://api.hetzner.cloud/v1/ssh_keys"

    # Prompt for SSH key name if not provided
    if ssh_key_name is None:
        ssh_key_name = input("Enter a name for your SSH key \n "
                             f"  [default: {Fore.CYAN}mykey{Style.RESET_ALL}]: ").strip() or 'mykey'

    print("")

    # Fetch existing SSH keys to check if it already exists
    response = requests.get(url, headers=headers)
    existing_keys = response.json().get('ssh_keys', [])
    for key in existing_keys:
        if key['name'] == ssh_key_name:
            print(f"SSH key '{ssh_key_name}' already exists. Using the existing key.")
            key_path = os.path.expanduser(f"~/.ssh/{ssh_key_name}")
            return key['id'], key_path  # Return the existing key ID and path if found

    # Define the path for the new SSH key
    key_path = os.path.expanduser(f"~/.ssh/{ssh_key_name}")
    while True:
        global_passphrase = getpass.getpass("Enter a passphrase for your SSH key (cannot be blank): ")
        if not global_passphrase:
            print("The passphrase cannot be blank.")
            continue
        if re.search(r'[^\w@#$%^&+=]', global_passphrase):
            print("The passphrase contains invalid characters. Only alphanumeric characters and @#$%^&+= are allowed.")
            continue
        confirmation = getpass.getpass("Confirm your passphrase: ")
        if global_passphrase != confirmation:
            print("Passphrases do not match. Please try again.")
            continue
        break

    # Generate the SSH key with the provided passphrase
    cmd = f"ssh-keygen -t rsa -b 4096 -f \"{key_path}\" -N \"{global_passphrase}\" -C \"{ssh_key_name}\""
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL)
    print(f"{Fore.GREEN}SSH Key Pair successfully created.{Style.RESET_ALL}")
    print(f"SSH Private Key: {key_path}")
    print(f"SSH Public Key: {key_path}.pub")

    # Read the public key
    with open(f"{key_path}.pub", "r") as file:
        public_key = file.read().strip()

    # Attempt to upload the new SSH key to Hetzner
    data = {'name': ssh_key_name, 'public_key': public_key}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print("SSH Key is now available in the Hetzner account.")
        return response.json()['ssh_key']['id'], key_path  # Return the new key ID and path
    else:
        print("Failed to upload SSH key.", response.text)
        return None, None
    
def clear_screen():
    logging.debug("Entered clear_screen function")
    if os.name == 'nt':
        _ = os.system('cls')
    else:
        _ = os.system('clear')

def is_valid_hostname(hostname):
    logging.debug("Entered is_valid_hostname function")
    if len(hostname) > 255 or len(hostname) == 0:
        return False
    if hostname[-1] == ".":
        hostname = hostname[:-1]
    allowed = re.compile(r"(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in hostname.split("."))

def execute_ssh_command(host, port, username, private_key_path, passphrase, command, retries=5, delay=3):
    logging.debug(f"Entered execute_ssh_command function for host: {host}")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        private_key = paramiko.RSAKey.from_private_key_file(private_key_path, password=passphrase)
        logging.debug("Private key loaded successfully")
    except paramiko.ssh_exception.PasswordRequiredException as e:
        logging.error("The private key is encrypted and a passphrase is required", exc_info=True)
        print("The private key is encrypted and a passphrase is required")
        return None, str(e)

    attempt = 0
    while attempt < retries:
        try:
            client.connect(host, port=port, username=username, pkey=private_key, timeout=10)
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode()
            errors = stderr.read().decode()
            client.close()
            return output, errors
        except (paramiko.ssh_exception.NoValidConnectionsError, paramiko.ssh_exception.SSHException) as e:
            attempt += 1
            logging.warning(f"Attempt {attempt}/{retries}: Unable to connect, retrying in {delay} seconds...", exc_info=True)
            print(f"Attempt {attempt}/{retries}: Unable to connect, retrying in {delay} seconds...")
            time.sleep(delay)

    logging.error("Failed to establish an SSH connection after several attempts.")
    print("Failed to establish an SSH connection after several attempts.")
    return None, "Failed to connect"

def check_winscp_and_putty_installed():
    if sys.platform != 'win32':
        return True  # Assume non-Windows platforms do not need WinSCP and PuTTY

    try:
        # Check for WinSCP installation
        winscp_check = subprocess.check_output(
            'reg query "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\winscp3_is1" /v InstallLocation',
            shell=True,
            text=True
        )
        # Extract the installation path from the registry output
        winscp_path = re.search(r"InstallLocation\s+REG_SZ\s+(.*)", winscp_check).group(1).strip()

        # Check for PuTTY installation
        putty_check = subprocess.check_output(
            'reg query "HKEY_LOCAL_MACHINE\\SOFTWARE\\SimonTatham\\PuTTY64"',
            shell=True,
            text=True
        )
        if winscp_path and "SimonTatham" in putty_check:
            return winscp_path
        return None
    except subprocess.CalledProcessError:
        return None

def ensure_winscp_and_putty_installed():
    if sys.platform != 'win32':
        return  # No need to check for WinSCP and PuTTY on non-Windows platforms
    
    while True:
        if check_winscp_and_putty_installed():
            print("WinSCP and PuTTY installation detected. Continuing with export...")
            break
        else:
            print("WinSCP and/or PuTTY is not installed. Please install them from their official websites:")
            print("WinSCP: https://winscp.net/eng/download.php")
            print("PuTTY: https://www.putty.org")
            input("Press any key once WinSCP and PuTTY are installed to continue...")

def get_winscp_path():
    if sys.platform != 'win32':
        return None
    
    try:
        output = subprocess.check_output(
            'reg query "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\winscp3_is1" /v InstallLocation',
            shell=True,
            text=True
        )
        path_match = re.search(r"InstallLocation\s+REG_SZ\s+(.+)", output)
        if path_match:
            return path_match.group(1).strip()
    except Exception as e:
        print("Failed to fetch WinSCP path:", e)
        return None

def convert_key_to_ppk(private_key_path, winscp_path, passphrase):
    if sys.platform != 'win32':
        # Non-Windows platforms don't need PPK conversion
        return private_key_path + '.ppk'

    if winscp_path is None:
        print("WinSCP path is not available. Please check the installation.")
        return None

    ppk_path = private_key_path + '.ppk'
    if not os.path.exists(ppk_path):  # Convert key if PPK doesn't already exist
        # Convert all slashes to backslashes
        private_key_path = private_key_path.replace('/', '\\')
        ppk_path = ppk_path.replace('/', '\\')
        winscp_command = f'"{winscp_path}\\WinSCP.com" /keygen "{private_key_path}" /output="{ppk_path}" -passphrase="{passphrase}"'
        try:
            subprocess.run(winscp_command, check=True, shell=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to convert key: {e}")
            return None
    return ppk_path

def export_server_details_to_putty(server_details, winscp_path, passphrase):
    if sys.platform != 'win32':
        # Skip export on non-Windows platforms
        print("Export to PuTTY is not supported on non-Windows platforms.")
        return

    private_key_path = os.path.expanduser(f"~/.ssh/{server_details['ssh_key_name']}")
    private_key_path = private_key_path.replace('/', '\\')  # Ensure the path uses backslashes
    ppk_path = convert_key_to_ppk(private_key_path, winscp_path, passphrase)
    if not ppk_path:
        print("Failed to create the PPK file.")
        return

    session_name = server_details['server_name'].replace(" ", "_")
    registry_commands = [
        f'reg add "HKEY_CURRENT_USER\\Software\\SimonTatham\\PuTTY\\Sessions\\{session_name}" /v HostName /t REG_SZ /d {server_details["host_ip"]} /f',
        f'reg add "HKEY_CURRENT_USER\\Software\\SimonTatham\\PuTTY\\Sessions\\{session_name}" /v PortNumber /t REG_DWORD /d 22 /f',
        f'reg add "HKEY_CURRENT_USER\\Software\\SimonTatham\\PuTTY\\Sessions\\{session_name}" /v PublicKeyFile /t REG_SZ /d "{ppk_path}" /f',
        f'reg add "HKEY_CURRENT_USER\\Software\\SimonTatham\\PuTTY\\Sessions\\{session_name}" /v Protocol /t REG_SZ /d ssh /f'
    ]
    for command in registry_commands:
        subprocess.run(command, shell=True)

    print("Server details exported to PuTTY successfully.")

def print_firewall_details(response_json):
    firewall = response_json.get('firewall', {})
    print('')
    print(f"Firewall '{firewall.get('name')}' updated successfully.")
    print("")
    print("Rules:")
    for rule in firewall.get('rules', []):
        print(f"  - Direction: {rule['direction']} | Protocol: {rule['protocol']} | Port: {rule.get('port', 'N/A')} | Source IPs: {', '.join(rule['source_ips'])}")

def get_public_ip():
    return requests.get('https://api.ipify.org').text

# Function to create or update a firewall
def create_or_update_firewall(firewall_name, inbound_ports):
    global api_key
    headers = {'Authorization': f'Bearer {api_key}'}
    url = 'https://api.hetzner.cloud/v1/firewalls'

    # Fetch the user's public IP
    public_ip = get_public_ip()

    # Determine source IPs
    print("")
    print(Fore.CYAN + "Adding this extra security to your firewall is recommended.")
    print("If you choose yes, the script will detect you modem IP and place it in the firewall.")
    print("This will cause the firewall to deny access to your server from anyone outside of your home network." + Style.RESET_ALL)
    print("")
    restrict_ssh = input("Do you want to add extra security by limiting SSH access to specific IP addresses? (y/n) \n"
                        f"  [default: y]: ").strip().lower() or 'y'
    if restrict_ssh == 'y':
        print("")
        user_input = input(f"Enter additional IP addresses separated by commas,\n" +
                           f"or press enter to use only your existing Internet IP \n" +
                           f"  [default: {public_ip}]: ").strip() or public_ip
        source_ips = [ip.strip() if '/' in ip else ip.strip() + '/32' for ip in user_input.split(',')]
    else:
        source_ips = ['0.0.0.0/0', '::/0']  # Allow all IPv4 and IPv6 if no restriction is specified


    # Check if the firewall exists and get ID
    firewalls_response = requests.get(url, headers=headers)
    firewalls_data = firewalls_response.json()
    firewall_id = None
    for fw in firewalls_data.get('firewalls', []):
        if fw['name'] == firewall_name:
            firewall_id = fw['id']
            break

    # Define the firewall rules
    rules = [{'direction': 'in', 'protocol': 'tcp', 'port': '22', 'source_ips': source_ips},
             {'direction': 'in', 'protocol': 'icmp', 'source_ips': ['0.0.0.0/0', '::/0']}]
    rules += [{'direction': 'in', 'protocol': 'tcp', 'port': port, 'source_ips': ['0.0.0.0/0', '::/0']}
              for port in inbound_ports.split(',') if port.strip() != '22']

    if firewall_id:
        response = requests.put(f"{url}/{firewall_id}", headers=headers, json={'rules': rules})
    else:
        response = requests.post(url, headers=headers, json={'name': firewall_name, 'rules': rules})
        if response.status_code == 201:
            firewall_id = response.json().get('firewall', {}).get('id')

    print("")
    if response.status_code in [200, 201]:
        print("Firewall created/updated successfully.")
        return firewall_id  # Return the firewall_id to ensure it's captured
    else:
        print("Failed to create/update firewall.")
        print("Error details:", response.json())
        return None

def fetch_and_display_server_types():
    global api_key
    url = 'https://api.hetzner.cloud/v1/server_types'
    headers = {'Authorization': f'Bearer {api_key}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        server_types = response.json().get('server_types', [])
        sorted_server_types = sorted(server_types, key=lambda x: float(x['prices'][0]['price_monthly']['net']))
        for server in sorted_server_types:
            name = Fore.CYAN + Style.BRIGHT + server['name'] + Style.RESET_ALL
            monthly_price = round(float(server['prices'][0]['price_monthly']['net']), 2)
            cpu = server['cores']
            ram = server['memory']
            storage = server['disk']
            print(f"Name: {name}, Monthly Price: {monthly_price} (Net), CPU: {cpu} Cores, RAM: {ram} GB, Storage: {storage} GB")
        return sorted_server_types
    else:
        print('Failed to fetch server types.')
        return []

def fetch_and_display_firewalls():
    global api_key
    url = 'https://api.hetzner.cloud/v1/firewalls'
    headers = {'Authorization': f'Bearer {api_key}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        firewalls = response.json().get('firewalls', [])
        for fw in firewalls:
            name = Fore.CYAN + Style.BRIGHT + fw['name'] + Style.RESET_ALL
            print(f"Name: {name}")
        return firewalls
    else:
        print('Failed to fetch firewalls.')
        return []

def fetch_and_display_ssh_keys():
    global api_key
    url = 'https://api.hetzner.cloud/v1/ssh_keys'
    headers = {'Authorization': f'Bearer {api_key}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        ssh_keys = response.json().get('ssh_keys', [])
        for key in ssh_keys:
            name = Fore.CYAN + Style.BRIGHT + key['name'] + Style.RESET_ALL
            print(f"Name: {name}")
        return ssh_keys
    else:
        print('Failed to fetch SSH keys.')
        return []

def get_ssh_key_name(ssh_key_id):
    global api_key
    url = f'https://api.hetzner.cloud/v1/ssh_keys/{ssh_key_id}'
    headers = {'Authorization': f'Bearer {api_key}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['ssh_key']['name']
    else:
        print('Failed to fetch SSH key name.')
        return None

def fetch_and_display_locations():
    global api_key
    url = 'https://api.hetzner.cloud/v1/locations'
    headers = {'Authorization': f'Bearer {api_key}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        locations = response.json().get('locations', [])
        for loc in locations:
            name = Fore.CYAN + Style.BRIGHT + loc['name'] + Style.RESET_ALL
            description = loc['description']
            print(f"Name: {name}, Description: {description}")
        return locations
    else:
        print('Failed to fetch locations.')
        return []

def create_server(server_name, server_type_id, image, location, firewall_id, ssh_key_name):
    global api_key, global_passphrase
    url = 'https://api.hetzner.cloud/v1/servers'
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    ssh_key_id, private_key_path = create_and_upload_ssh_key(ssh_key_name)

    if not ssh_key_id:
        print("SSH key setup failed.")
        return

    data = {
        'name': server_name,
        'server_type': server_type_id,
        'image': image,
        'location': location,
        'firewalls': [{'firewall': firewall_id}],
        'ssh_keys': [ssh_key_id]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        server_data = response.json()
        print('Server created successfully.')
        print(f"Server Name: {server_data['server']['name']}")
        print(f"Host IP: {server_data['server']['public_net']['ipv4']['ip']}")
        print("SSH Port: 22")
        print(f"SSH Key Name: {ssh_key_name}")
        print("")

        if os.name == 'nt':  # Only proceed with PuTTY export on Windows
            export_decision = input("Do you want to export the Server details to PuTTY? (y/n): ").lower()
            if export_decision == 'y':
                while not check_winscp_and_putty_installed():
                    print("WinSCP and/or PuTTY is not installed. Please install them from their official websites:")
                    print("WinSCP: https://winscp.net/eng/download.php")
                    print("PuTTY: https://www.putty.org")
                    input("Press any key once WinSCP and PuTTY are installed to continue...")

                winscp_path = get_winscp_path()
                if winscp_path:
                    server_details = {
                        'server_name': server_data['server']['name'],
                        'host_ip': server_data['server']['public_net']['ipv4']['ip'],
                        'ssh_key_name': ssh_key_name
                    }
                    export_server_details_to_putty(server_details, winscp_path, global_passphrase)
                else:
                    print("Unable to find the WinSCP installation path.")
            else:
                print("Export to PuTTY skipped.")
    else:
        print('Failed to create server.')
        print(response.text)

def clear_input_buffer():
    sys.stdin.flush()

def check_server_name_availability(server_name):
    url = f"https://api.hetzner.cloud/v1/servers"
    headers = {'Authorization': f'Bearer {api_key}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        servers = response.json().get('servers', [])
        return not any(srv['name'] == server_name for srv in servers)
    else:
        print("Failed to fetch server list:", response.text)
        return False  # Assume not available if the API call fails

def get_api_key():
    global api_key
    if api_key is None:
        print(Fore.LIGHTWHITE_EX + "Hetzner Cloud Management Tool (HCMT) - " + version)
        print("This script was written by " + Fore.CYAN + "@Proph151Music" + Fore.LIGHTWHITE_EX + " for the Constellation Network ecosystem." + Style.RESET_ALL)
        print("")
        print("Don't forget to tip the bar tender!"+ Style.RESET_ALL)
        print("----> " + Fore.YELLOW + "DAG0Zyq8XPnDKRB3wZaFcFHjL4seCLSDtHbUcYq3" + Style.RESET_ALL)
        print("")
        print(Fore.LIGHTGREEN_EX + "Receive a €20 credit in your Hetzner account by using this unique promo link when you sign up:" + Style.RESET_ALL)
        print(Fore.LIGHTCYAN_EX + "https://hetzner.cloud/?ref=2tjBU33OPhv6" + Style.RESET_ALL)
        print("")
        print("")
        print(f"-===[ HETZNER API KEY ]===-")
        print("")
        print("To create a Hetzner Cloud API token, follow these steps:")
        print(Fore.CYAN + "1. Log in to your Hetzner Cloud account.")
        print('2. Navigate to the "API Tokens" section. (It is inside the Security section.)')
        print("   https://console.hetzner.cloud/projects")
        print("   You may need to create a New Project. Then go into the project.")
        print("   Once inside the project click on Security at the bottom left. Then API tokens.")
        print('3. Click "Generate API Token". Provide any name for the token and choose Read and Write.')
        print("4. Copy the generated API key and paste it below." + Style.RESET_ALL)
        print("")
        api_key = input("Enter your Hetzner API Key: ")
    return api_key

def check_for_updates():
    logger.debug("Checking for updates")
    current_hash = calculate_hash(__file__)
    print(f"Current version: {version}")
    print(f"Current hash: {current_hash}")
    check_update = input("Do you want to check for updates? (y/n): ").strip().lower()
    
    if check_update == 'y':
        response = requests.get("https://raw.githubusercontent.com/Proph151Music/Hetzner-Cloud-Management-Tool-HCMT-/main/versions.txt")
        if response.status_code == 200:
            latest_version, latest_hash = response.text.splitlines()[0].split()
            print(f"Latest version: {latest_version}")
            print(f"Latest hash: {latest_hash}")
            
            if version != latest_version or current_hash != latest_hash:
                update = input("A new version is available. Do you want to update? (y/n): ").strip().lower()
                if update == 'y':
                    script_path = os.path.realpath(__file__)
                    new_script_path = script_path + '.new'
                    
                    try:
                        download_file("https://raw.githubusercontent.com/Proph151Music/Hetzner-Cloud-Management-Tool-HCMT-/main/hcmt.py", new_script_path)
                        logger.debug(f"New script downloaded: {new_script_path}")
                        
                        downloaded_hash = calculate_hash(new_script_path)
                        logger.debug(f"Expected hash: {latest_hash}")
                        logger.debug(f"Downloaded hash: {downloaded_hash}")
                        
                        if downloaded_hash == latest_hash:
                            create_updater_script()
                            logger.debug("Updater script created")
                            print("Update downloaded. Running updater...")
                            try:
                                os.execv(sys.executable, ['python', 'updater.py', script_path, new_script_path])
                            except Exception as e:
                                logger.error(f"Failed to execute updater script: {e}")
                        else:
                            print("Hash mismatch after download. Update aborted.")
                            logger.error("Hash mismatch after download. Update aborted.")
                            if not compare_files(script_path, new_script_path):
                                logger.error("File contents do not match, potential download issue.")
                    except Exception as e:
                        logger.error(f"Failed to download the latest version: {e}")
            else:
                print("You already have the latest version.")
                logger.debug("You already have the latest version.")
        else:
            print("Failed to check for updates.")
            logger.error("Failed to check for updates.")

# Main interaction and menu
def main_menu():
    logging.debug("Entered main_menu function")
    global api_key
    clear_screen()
    print("")
    get_api_key()

    clear_screen()
    print("")
    print("")
    print(Fore.CYAN + "Hetzner Cloud Management Tool" + Style.RESET_ALL)
    print("\nPlease choose an option:")
    print("F) Setup Firewall")
    print("S) Create SSH Key Pair")
    print("C) Create Cloud Server")
    print("X) Exit")
    choice = input("\nEnter your choice: ").upper()
    logging.debug(f"User choice: {choice}")

    try:
        if choice == 'F':
            logging.debug("User selected to setup firewall")
            clear_screen()
            firewall_name = input("Enter the firewall name [DAG Validator Node]:") or 'DAG Validator Node'
            inbound_ports = input("Enter the inbound ports [9000-9001,9010-9011]: ") or '9000-9001,9010-9011'
            logging.debug(f"Firewall name: {firewall_name}, inbound ports: {inbound_ports}")
            create_or_update_firewall(firewall_name, inbound_ports)
            print("")
            pause_and_return()
        elif choice == 'S':
            logging.debug("User selected to create SSH key pair")
            create_and_upload_ssh_key()
            print("")
            pause_and_return()
        elif choice == 'C':
            logging.debug("User selected to create cloud server")
            # Server Name
            print("")
            print("Don't forget to tip the bar tender!"+ Style.RESET_ALL)
            print("----> " + Fore.YELLOW + "DAG0Zyq8XPnDKRB3wZaFcFHjL4seCLSDtHbUcYq3" + Style.RESET_ALL)
            print("")
            print(f"-===[ SERVER NAME ]===-")
            print("")
            print(Fore.CYAN + "A valid server name must be a non-empty string, ")
            print("contain only alphanumeric characters and hyphens, not start or end with a hyphen." + Style.RESET_ALL)
            print("")
            while True:
                server_name = input("Enter the server name: ")
                if is_valid_hostname(server_name):
                    if check_server_name_availability(server_name):
                        break
                    else:
                        print(f"Server name '{server_name}' is already used. Please choose a different name.")
                else:
                    print(Fore.LIGHTRED_EX + "Invalid server name. A valid server name must be a non-empty string, ")
                    print("contain only alphanumeric characters and hyphens, not start or end with a hyphen." + Style.RESET_ALL)
            logging.debug(f"Server name: {server_name}")

            # Server OS
            print("")
            print(f"-===[ SERVER OPERATING SYSTEM ]===-")
            print("")
            print(Fore.CYAN + "Ubuntu-22.04 is the recommended OS. ")
            print("By default You can just press ENTER to choose it.")
            print("Or you are welcome to type a different OS if instructions have changed." + Style.RESET_ALL)
            print("")
            image = input("Enter the image you want to use \n"
                          f"  [default: ubuntu-22.04]: ") or "ubuntu-22.04"
            logging.debug(f"Server OS image: {image}")

            # Server location
            print("")
            print(f"-===[ SERVER LOCATION ]===-")
            print("")
            print(Fore.CYAN + "Here you can select the location where your server will reside.")
            print("By default You can just press ENTER to choose Ashburn, Virgina (ash).")
            print("Or you can type a different location code that you see highlighted in the list below." + Style.RESET_ALL)
            print("")
            locations = fetch_and_display_locations()
            logging.debug(f"Locations fetched: {locations}")
            if not locations:
                logging.error("No locations available.")
                print("No locations available.")
                input("Press Enter to exit...")
                sys.exit()
            print("")
            default_location_name = 'ash'
            location_name = input(f"Enter the name of the location you want to use \n"
                                  f"  [default: {default_location_name}]: ") or default_location_name
            # Find the ID of the chosen location
            chosen_location = next((loc for loc in locations if loc['name'] == location_name), None)
            if chosen_location:
                location_id = chosen_location['id']
            else:
                print(f"Location '{location_name}' not found. Defaulting to 'ash'.")
                chosen_location = next(loc for loc in locations if loc['name'] == 'ash')
                location_id = chosen_location['id'] if chosen_location else None

            location = location_name if chosen_location else 'ash'
            logging.debug(f"Chosen location: {location}")

            # Server Specs
            # Fetch and display server specs
            print("")
            print(f"-===[ SERVER SPECS ]===-")
            print("")
            print(Fore.CYAN + "You can either press enter to choose the default server specs shown ")
            print("or you can type the code to select different specs.")
            print("")
            print("Do NOT choose any codes that have an `a` in the code. This means `ARM chip` and is not compatible at this time." + Style.RESET_ALL)
            print("")
            server_types = fetch_and_display_server_types()
            logging.debug(f"Server types fetched: {server_types}")
            if not server_types:
                logging.error("No server types available.")
                print("No server types available.")
                input("Press Enter to exit...")
                sys.exit()
            print("")
            server_type_name = input("Enter the name of the server type you want to use \n"
                                     f"  [default: cpx41]: ") or "cpx41"
            chosen_server_type = next((st for st in server_types if st['name'] == server_type_name), None)
            if chosen_server_type:
                server_type_id = chosen_server_type['id']
            else:
                print(f"Server type '{server_type_name}' not found. Defaulting to 'cpx41'.")
                chosen_server_type = next((st for st in server_types if st['name'] == 'cpx41'), None)
                server_type_id = chosen_server_type['id'] if chosen_server_type else None
            logging.debug(f"Chosen server type: {server_type_name}")

            # Server firewall
            print("")
            print(f"-===[ SERVER FIREWALL ]===-")
            print("")
            print(Fore.CYAN + "You need to have a firewall setup to properly run your node.")
            print("Select yes or no.  The default options are the best for most users." + Style.RESET_ALL)
            print("")
            print("Do you want to create a new Firewall?")
            choice = input("    y - Create a new firewall. \n"
                           "    n - Choose an existing firewall. \n"
                           "    Please make a selection (y/n): ").strip().lower()
            logging.debug(f"Firewall choice: {choice}")

            if choice == 'y':
                print("")
                print(Fore.CYAN + "By default the name is the same as your Server Name with -fw added to the end.")
                print("If this name is fine, then press ENTER. Or type a new name for this firewall." + Style.RESET_ALL)
                print("")
                default_firewall_name = re.sub(r"[^a-zA-Z0-9]", "-", server_name.lower()) + "-fw"
                firewall_name = input(f"Enter the firewall name \n  [default: {default_firewall_name}]: ").strip() or default_firewall_name
                print("")
                print(Fore.CYAN + "The ports needed for a DAG Validator node are already here in the defaults.")
                print("If you don't need to make any changes then press ENTER. Otherwise you can ")
                print("input different ports seperated by commas or port ranges with a dash." + Style.RESET_ALL)
                print("")
                inbound_ports = input("Enter the inbound ports \n"
                                      f"  [default: 9000-9001,9010-9011]: ") or '9000-9001,9010-9011'
                firewall_id = create_or_update_firewall(firewall_name, inbound_ports)
            else:
                print("")
                firewalls = fetch_and_display_firewalls()
                logging.debug(f"Firewalls fetched: {firewalls}")
                if not firewalls:
                    logging.error("No firewalls available.")
                    print("No firewalls available.")
                    input("Press Enter to exit...")
                    sys.exit()
                print("")
                firewall_name = input("Choose a firewall from the list above: ")
                print("")
                firewall_id = next((fw['id'] for fw in firewalls if fw['name'] == firewall_name), None)
            logging.debug(f"Chosen firewall ID: {firewall_id}")

            # Server SSH key
            print("")
            print(f"-===[ SERVER SSH KEY ]===-")
            print("")
            print(Fore.CYAN + "You need to use an SSH key pair to secure access to your server.")
            print("Selecting yes will allow the script to create an SSH key pair for you." + Style.RESET_ALL)
            print("")
            print("Do you want to create a new SSH Key?")
            choice = input("    y - Create a new SSH Key. \n"
                           "    n - Choose an existing SSH Key. \n"
                           "    Please make a selection (y/n): ").strip().lower()
            logging.debug(f"SSH key choice: {choice}")

            ssh_key_id = None  # Ensure ssh_key_id is initialized
            if choice == 'y':
                print("")
                default_ssh_name = re.sub(r"[^a-zA-Z0-9]", "-", server_name.lower()) + "-ssh"
                ssh_key_name = input(f"Enter the SSH key name \n "
                                     f"  [default: {default_ssh_name}]: ") or default_ssh_name
                ssh_key_id = create_and_upload_ssh_key(ssh_key_name)
            else:
                print("")
                ssh_keys = fetch_and_display_ssh_keys()
                logging.debug(f"SSH keys fetched: {ssh_keys}")
                if not ssh_keys:
                    logging.error("No SSH keys available.")
                    print("No SSH keys available.")
                    input("Press Enter to exit...")
                    sys.exit()
                print("")
                ssh_key_name = input("Choose an SSH key from the list above: ")
                print("")
                ssh_key_id = next((key['id'] for key in ssh_keys if key['name'] == ssh_key_name), None)
            logging.debug(f"Chosen SSH key ID: {ssh_key_id}")

            print("")
            print(f"-===[ SERVER CREATION ]===-")
            print("")
            print(Fore.CYAN + "Make sure you document all of the server configuration that is shown after the server creation is completed!")
            print("You will need these details to properly connect to your server." + Style.RESET_ALL)
            print("")
            create_server(server_name, server_type_id, image, location, firewall_id, ssh_key_name)
            print("")
            pause_and_return()
        elif choice == 'X':
            logging.debug("User selected to exit")
            print("Exiting...")
            sys.exit()
    except Exception as e:
        logging.error(f"An error occurred in main_menu: {e}", exc_info=True)
        print(f"An error occurred: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    if '--no-update' not in sys.argv:
        check_for_updates()
    try:
        logging.debug("Program started")
        if sys.platform == 'darwin':
            setup_virtual_environment()
            install_required_packages()
        else:
            for package in required_packages:
                install_and_reload(package)
        main_menu()
    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)
        print(f"An error occurred: {e}")
        input("Press Enter to exit...")
