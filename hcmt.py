# Version of the script
version = "0.2.8.6"

import sys
import subprocess
import os
import logging

# Function to install missing packages
def install_package(package_name):
    try:
        print(f"Installing {package_name} package...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        print(f"Failed to install package {package_name}: {e}")
        sys.exit(1)

# Function to restart the script
def restart_script():
    try:
        # print("Restarting script...")
        subprocess.check_call([sys.executable] + sys.argv)
    except subprocess.CalledProcessError as e:
        print(f"Failed to restart script: {e}")
        sys.exit(1)

def install_required_packages():
    if os.name == 'nt':
        # Ensure pywin32 is installed on Windows
        try:
            import win32com.client
        except ImportError:
            install_package('pywin32')
            # Try running the post-install script for pywin32
            try:
                subprocess.check_call([sys.executable, "-m", "pywin32_postinstall", "-install"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                restart_script()
            except subprocess.CalledProcessError as e:
                # print(f"Failed to run pywin32_postinstall: {e}")
                restart_script()
            # Verify installation
            try:
                import win32com.client
            except ImportError as e:
                print(f"Failed to import win32com.client after installation: {e}")
                sys.exit(1)

    logging.debug("Entered install_required_packages function")
    required_packages = ["requests", "colorama", "paramiko>=3.0.0", "cryptography>=39.0.0"]
    for package in required_packages:
        package_name = package.split('>=')[0]
        try:
            __import__(package_name)
            logging.debug(f"Package '{package_name}' is already installed.")
        except ImportError:
            logging.info(f"Installing package '{package}'...")
            install_package(package)
            logging.info(f"Package '{package}' installed.")
        except Exception:
            logging.info(f"Reinstalling package '{package}'...")
            install_package(package + "--upgrade")
            logging.info(f"Package '{package}' reinstalled.")

install_required_packages()

import warnings
from cryptography.utils import CryptographyDeprecationWarning

# Suppress specific deprecation warnings
warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)

def clear_screen():
    logging.debug("Entered clear_screen function")
    if os.name == 'nt':
        _ = os.system('cls')
    else:
        _ = os.system('clear')
        
clear_screen()
print("")
print(f"Hetzner Cloud Management Tool v{version}")
print("")

import platform
import time
import hashlib
import getpass
import select
import requests
import paramiko
import re
from colorama import Fore, Style

easy_server = False

DEBUG_MODE = False

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)
console_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)

# Only add the file handler if DEBUG_MODE is True
if DEBUG_MODE:
    file_handler = logging.FileHandler('hetzner_debug.log')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
else:
    file_handler = None

# Remove existing handlers if any to avoid duplicate logging
if logger.hasHandlers():
    logger.handlers.clear()

logger.addHandler(console_handler)
if DEBUG_MODE:
    logger.addHandler(file_handler)

logger.debug("Starting Hetzner Cloud Management Tool")

# Check if running in a frozen state (compiled)
is_frozen = getattr(sys, 'frozen', False)

# Initialize global variables
api_key = None
winscp_path = None
nodeuser = "root"
ssh_shortcut_path = None
sftp_shortcut_path = None
folder_path = None
server_name = None
nodectl_version = "v2.14.1"

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
import hashlib
import subprocess

# Set up logging
logging.basicConfig(filename='updater.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

def calculate_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def main(script_path, new_script_path, *args):
    logging.debug("Updater script started with arguments: %s", sys.argv)
    
    # Give some time to ensure the main script has exited
    time.sleep(1)
    
    retries = 6  # Retry every 10 seconds up to 1 minute
    while retries > 0:
        try:
            # Verify the new script exists
            if not os.path.exists(new_script_path):
                logging.error(f"New script file does not exist: {new_script_path}")
                raise FileNotFoundError(f"No such file or directory: '{new_script_path}'")
            
            # Backup the old script
            backup_script_path = script_path + '.backup'
            if os.path.exists(script_path):
                shutil.move(script_path, backup_script_path)
                logging.debug(f"Moved old script to backup: {backup_script_path}")
            else:
                logging.debug(f"No existing script found at: {script_path}")
            
            # Move the new script to the original script's location
            shutil.move(new_script_path, script_path)
            logging.debug(f"Moved new script to: {script_path}")
            print("Update successful. Restarting script...")
            logging.debug("Update successful. Restarting script...")
            
            # Verify the hash of the new script
            new_hash = calculate_hash(script_path)
            expected_hash = sys.argv[4] if len(sys.argv) > 4 else new_hash
            logging.debug(f"Expected script hash: {expected_hash}")
            logging.debug(f"New script hash: {new_hash}")
            
            if expected_hash == new_hash:
                logging.debug("Hash verification successful.")
            else:
                logging.error("Hash verification failed. Reverting to backup...")
                shutil.move(backup_script_path, script_path)
                logging.debug("Reverted to backup script.")
                raise Exception("Hash verification failed.")
            
            # Ensure the new script is executable
            os.chmod(script_path, 0o755)
            logging.debug(f"Set executable permissions for: {script_path}")

            # Clean up the backup script after successful update
            if os.path.exists(backup_script_path):
                os.remove(backup_script_path)
                logging.debug(f"Backup script removed: {backup_script_path}")
            
            # Restart the script with '--no-update' flag and original script arguments
            exec_args = [sys.executable, script_path] + [arg for arg in args if arg != '--no-update']
            exec_args.append('--no-update')
            logging.debug(f"Executing new script with args: {exec_args}")
            subprocess.Popen([sys.executable, script_path, '--no-update'])
            logging.debug("New script launched. Exiting updater.")
            sys.exit(0)  # Exit updater script
        except Exception as e:
            logging.error(f"Failed to update the script: {e}", exc_info=True)
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
    if len(sys.argv) < 3:
        logging.error("Invalid usage. Exiting.")
        print("Usage: updater.py <script_path> <new_script_path> [additional args...]")
        sys.exit(1)
    
    script_path = os.path.abspath(sys.argv[1])
    new_script_path = os.path.abspath(sys.argv[2])
    additional_args = sys.argv[3:]
    
    main(script_path, new_script_path, *additional_args)
'''
    with open('updater.py', 'w') as f:
        f.write(updater_script_content)

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
    
def pause_and_return():
    input("Press any key to continue...")
    main_menu()

def format_path(path):
    if os.name == 'nt':
        # Normalize path for Windows, which converts forward slashes to backslashes
        return os.path.normpath(path)
    else:
        # Normalize path for non-Windows systems, ensuring correct slashes
        normalized_path = os.path.normpath(path)
        # Replace double forward slashes with a single slash
        return normalized_path.replace('//', '/')

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
    if response.status_code != 200:
        print("Failed to fetch existing SSH keys.")
        input("Press Enter to exit...")
        sys.exit(1)

    existing_keys = response.json().get('ssh_keys', [])
    for key in existing_keys:
        if key['name'] == ssh_key_name:
            logger.debug(f"SSH key '{ssh_key_name}' found.")
            logger.debug("")
            key_path = os.path.expanduser(f"~/.ssh/{ssh_key_name}")
            key_path = format_path(key_path)
            return key['id'], key_path 

    # Define the path for the new SSH key
    key_path = os.path.expanduser(f"~/.ssh/{ssh_key_name}")
    key_path = format_path(key_path)

    print(Fore.CYAN + "The SSH passphrase will be used whenever you log into your server.")
    print("Make sure you document this SSH passphrase so that you do not forget it." + Style.RESET_ALL)
    print("")

    while True:
        global_passphrase = getpass.getpass("Enter a passphrase for your new SSH key (cannot be blank): ")
        if not global_passphrase:
            print("The passphrase cannot be blank.")
            continue
        if re.search(r'[^\w@#$%^&+=!]', global_passphrase):
            print("The passphrase contains invalid characters. Only alphanumeric characters and @#$%^&+=! are allowed.")
            continue
        confirmation = getpass.getpass("Confirm your passphrase: ")
        if global_passphrase != confirmation:
            print("Passphrases do not match. Please try again.")
            continue
        break

    # Generate the SSH key with the provided passphrase
    cmd = f"ssh-keygen -t rsa -b 4096 -f \"{key_path}\" -N \"{global_passphrase}\" -C \"{ssh_key_name}\""
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print("Failed to create SSH key:", result.stderr.decode())
        input("Press Enter to exit...")
        sys.exit(1)

    print(f"{Fore.GREEN}SSH Key Pair successfully created.{Style.RESET_ALL}")
    print(f"SSH Private Key: {key_path}")
    print(f"SSH Public Key: {key_path}.pub")

    # Read the public key
    try:
        with open(f"{key_path}.pub", "r") as file:
            public_key = file.read().strip()
    except Exception as e:
        print(f"Failed to read the SSH public key: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

    # Attempt to upload the new SSH key to Hetzner
    data = {'name': ssh_key_name, 'public_key': public_key}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print("SSH Key is now available in the Hetzner account.")
        return response.json()['ssh_key']['id'], key_path
    else:
        print("Failed to upload SSH key.", response.text)
        input("Press Enter to exit...")
        sys.exit(1)

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
    return requests.get('https://ipv4.icanhazip.com').text.strip()

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
        user_input = input(f"Enter different IP addresses separated by commas,\n" +
                           f"or press enter to use only your existing local Internet IP \n" +
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

def fetch_and_display_server_types(location_name):
    global api_key
    url = 'https://api.hetzner.cloud/v1/server_types'
    headers = {'Authorization': f'Bearer {api_key}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        server_types = response.json().get('server_types', [])
        # Filter server types based on location and architecture
        filtered_server_types = [
            server for server in server_types
            if any(price['location'] == location_name for price in server['prices'])
            and server['architecture'] in ['x86', 'x64']
        ]
        sorted_server_types = sorted(filtered_server_types, key=lambda x: float(x['prices'][0]['price_monthly']['net']))
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

def create_shortcut(command, wdir, name, icon, nodeuser):
    import win32com.client
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortcut(name)
    shortcut.TargetPath = "cmd.exe"
    command = command.replace('root', nodeuser)
    shortcut.Arguments = f"/k {command}"
    shortcut.WorkingDirectory = wdir
    shortcut.IconLocation = icon
    shortcut.save()

def create_symlink(target, link_name):
    # Normalize the paths
    target = format_path(target)
    link_name = format_path(link_name)

    # Ensure the directory for the symlink exists
    link_dir = os.path.dirname(link_name)
    if not os.path.exists(link_dir):
        os.makedirs(link_dir)
        print(f"Created directory for symlink: {link_dir}")

    # Check if the target exists
    if not os.path.exists(target):
        print(f"Error: Target '{target}' does not exist. Symlink creation aborted.")
        return

    # If the symlink already exists, remove it
    if os.path.exists(link_name):
        os.remove(link_name)

    # Create the symlink
    os.symlink(target, link_name)
    print(f"Symlink created: {link_name} -> {target}")

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode().strip(), result.stderr.decode().strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit status {e.returncode}: {e.stderr.decode().strip()}")
        return None, f"Command failed with exit status {e.returncode}: {e.stderr.decode().strip()}"

def add_host_key_to_known_hosts(host_ip):
    try:
        known_hosts_path = os.path.expanduser(format_path("~/.ssh/known_hosts"))
        known_hosts_path = format_path(known_hosts_path)
        # Remove the existing host key if it exists
        remove_command = f'ssh-keygen -R {host_ip}'
        logger.debug(f"Running command: {remove_command}")
        output, error = run_command(remove_command)
        if error and 'not found' not in error:
            raise Exception(error)
        logger.debug(f"Command output: {output}")

        # Add the new host key
        add_command = f'ssh-keyscan -H {host_ip} >> "{known_hosts_path}"'
        logger.debug(f"Running command: {add_command}")
        output, error = run_command(add_command)
        if error:
            raise Exception(error)
        logger.debug(f"Command output: {output}")
    except Exception as e:
        logger.debug("")

def get_latest_nodectl_version():
    url = "https://api.github.com/repos/StardustCollective/nodectl/releases/latest"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        latest_release = response.json()
        return latest_release.get("tag_name", nodectl_version)
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch the latest nodectl version: {e}")
        return nodectl_version
    
def install_nodectl(host_ip, private_key_path):
    global ssh_shortcut_path, sftp_shortcut_path, folder_path, server_name, global_passphrase
    ssh_passphrase = global_passphrase

    if DEBUG_MODE:
        # Set up logging for Paramiko
        paramiko.util.log_to_file('hetzner_debug.log')

        # Define the handler to capture Paramiko logs
        class ParamikoLogHandler(logging.Handler):
            def emit(self, record):
                log_entry = self.format(record)
                logger.debug(log_entry)

        # Add the Paramiko log handler
        paramiko_log_handler = ParamikoLogHandler()
        paramiko_log_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        paramiko_log_handler.setFormatter(formatter)
        paramiko_logger = paramiko.util.get_logger('paramiko')
        paramiko_logger.addHandler(paramiko_log_handler)
        paramiko_logger.setLevel(logging.DEBUG)
        paramiko_logger.propagate = False

    # Prompt the user to select the network
    print("Please choose the network to set up for this node:")
    print("M) MainNet")
    print("I) IntegrationNet")
    print("T) TestNet")
    network_choice = input("Enter your choice: ").upper()

    if network_choice == 'M':
        network = 'mainnet'
        profile = 'dag-l0'
    elif network_choice == 'I':
        network = 'integrationnet'
        profile = 'intnet-l0'
    elif network_choice == 'T':
        network = 'testnet'
        profile = 'dag-l0'
    else:
        print("Invalid choice. Exiting nodectl installation.")
        return
    print("")

    # Prompt for P12 file
    use_p12 = input("Do you have a P12 file to import? (y/n): ").lower()
    p12file = None
    formatted_p12file = ""
    if use_p12 == 'y':
        while True:
            p12file = input("Enter the full path to your P12 file or type 'c' to cancel: ").strip().strip('"')
            if p12file.lower() == 'c':
                p12file = None
                break
            formatted_p12file = format_path(p12file)
            if os.path.isfile(formatted_p12file):
                logger.debug(f"File found: {formatted_p12file}")
                break
            else:
                print(f"Cannot find the P12 file at: {formatted_p12file}. The path to the P12 file is incorrect. Try again or type 'c' to cancel.")
    print("")

    if easy_server:
        nodeuser = "nodeadmin"
    else:
        # Prompt the user for the node username
        nodeuser = input("Enter the username for your node [default: nodeadmin]: ").strip()
        if not nodeuser:
            nodeuser = "nodeadmin"

    print(Fore.LIGHTGREEN_EX + f"Cloud Server Username: " + Style.RESET_ALL + nodeuser)
    print("")

    add_host_key_to_known_hosts(host_ip)

    # SFTP Upload using Paramiko
    if p12file:
        # Prompt for the SSH passphrase if needed
        if not ssh_passphrase:
            ssh_passphrase = getpass.getpass("Enter the SSH passphrase for your private key (leave blank if none): ")
        try:
            transport = paramiko.Transport((host_ip, 22))
            transport.connect(username='root', pkey=paramiko.RSAKey.from_private_key_file(private_key_path, password=ssh_passphrase))
            sftp = paramiko.SFTPClient.from_transport(transport)
            sftp.put(formatted_p12file, '/root/{}'.format(os.path.basename(formatted_p12file)))
            sftp.close()
            transport.close()
            print(Fore.LIGHTGREEN_EX + f"Successfully uploaded P12 file: " + Style.RESET_ALL)
            print(f"{formatted_p12file}")
            print("")
        except Exception as e:
            print(f"Failed to upload P12 file: {str(e)}")
            print("")
            return
    
    nodectl_version = get_latest_nodectl_version()
    print("")

    # Construct the full command
    if p12file:
        commands = (
            Fore.LIGHTGREEN_EX + f"sudo wget -N https://github.com/stardustcollective/nodectl/releases/download/" + Fore.LIGHTYELLOW_EX + nodectl_version + Style.RESET_ALL + Fore.LIGHTGREEN_EX + "/nodectl_x86_64 -P /usr/local/bin -O /usr/local/bin/nodectl && "
            f"sudo chmod +x /usr/local/bin/nodectl && "
            f"sudo nodectl install --quick-install --user {nodeuser} --p12-migration-path '/root/{os.path.basename(formatted_p12file)}' --cluster-config {network} --confirm && "
            f"sudo nodectl execute_starchiver -p {profile} --confirm && "
            f"sudo nodectl upgrade --ni" + Style.RESET_ALL
        )
        commands_txt = (
            f"sudo wget -N https://github.com/stardustcollective/nodectl/releases/download/" + nodectl_version + "/nodectl_x86_64 -P /usr/local/bin -O /usr/local/bin/nodectl && "
            f"sudo chmod +x /usr/local/bin/nodectl && "
            f"sudo nodectl install --quick-install --user {nodeuser} --p12-migration-path '/root/{os.path.basename(formatted_p12file)}' --cluster-config {network} --confirm && "
            f"sudo nodectl execute_starchiver -p {profile} --confirm && "
            f"sudo nodectl upgrade --ni"
        )
    else:
        commands = (
            Fore.LIGHTGREEN_EX + f"sudo wget -N https://github.com/stardustcollective/nodectl/releases/download/" + Fore.LIGHTYELLOW_EX + nodectl_version + Style.RESET_ALL + Fore.LIGHTGREEN_EX + "/nodectl_x86_64 -P /usr/local/bin -O /usr/local/bin/nodectl && "
            f"sudo chmod +x /usr/local/bin/nodectl && "
            f"sudo nodectl install --quick-install --user {nodeuser} --cluster-config {network} --confirm && "
            f"sudo nodectl execute_starchiver -p {profile} --confirm && "
            f"sudo nodectl upgrade --ni" + Style.RESET_ALL
        )
        commands_txt = (
            f"sudo wget -N https://github.com/stardustcollective/nodectl/releases/download/" + nodectl_version + "/nodectl_x86_64 -P /usr/local/bin -O /usr/local/bin/nodectl && "
            f"sudo chmod +x /usr/local/bin/nodectl && "
            f"sudo nodectl install --quick-install --user {nodeuser} --cluster-config {network} --confirm && "
            f"sudo nodectl execute_starchiver -p {profile} --confirm && "
            f"sudo nodectl upgrade --ni"
        )

    # Instructions for the user
    print(Fore.YELLOW + f"To install nodectl on your server, follow these steps:\n")
    print("")
    print(f'1. Open the shortcut located at: ' + Fore.LIGHTCYAN_EX + '"' + ssh_shortcut_path + '"' + Style.RESET_ALL)
    print("")
    print(Fore.YELLOW + f"2. Once connected, enter the SSH passphrase to authenticate access to the server.")
    print("")
    print(f"3. Copy and paste the following command to install nodectl:\n" + Style.RESET_ALL)
    print(Fore.LIGHTGREEN_EX + f"Latest nodectl version found: " + Style.RESET_ALL + nodectl_version)
    print('If you need to install a different version of nodectl, you can edit the below command with the version you need to install, by editing the ' + Fore.LIGHTYELLOW_EX + 'YELLOW ' + Style.RESET_ALL + 'area of the code, before pasting it into the terminal.')
    print("")
    print(f"{commands}\n")
    print("")
    print(Fore.YELLOW + f'Configuration and shortcuts have been saved to:')
    print(Fore.LIGHTWHITE_EX + folder_path + Style.RESET_ALL)
    print("")

    # Add the new details to the config file
    config_content = f"\n\nInstall your node after logging in with root and running the following command...\n\n{commands_txt}\n"

    config_path = format_path(os.path.join(folder_path, f"{server_name}_config.txt"))
    with open(config_path, 'a') as config_file:
        config_file.write(config_content + '\n')

    private_key_path = format_path(private_key_path)
    ssh_command_nodeuser = f"ssh -i {format_path(private_key_path)} {nodeuser}@{host_ip}"
    sftp_command_nodeuser = f"sftp -i {format_path(private_key_path)} {nodeuser}@{host_ip}"

    # Create SSH shortcut
    if os.name == 'nt':
        create_shortcut(f'ssh -i {private_key_path} {nodeuser}@{host_ip}', format_path(folder_path), f'{format_path(folder_path)}\\{server_name}_SSH_({nodeuser}).lnk', 'C:\\Windows\\System32\\shell32.dll,135', nodeuser)
        create_shortcut(f'sftp -i {private_key_path} {nodeuser}@{host_ip}', format_path(folder_path), f'{format_path(folder_path)}\\{server_name}_SFTP_({nodeuser}).lnk', 'C:\\Windows\\System32\\shell32.dll,146', nodeuser)
    elif os.name == 'posix' and platform.system() == 'Darwin':
        ssh_symlink_path = os.path.join(folder_path, f"SSH to {server_name}")
        sftp_symlink_path = os.path.join(folder_path, f"SFTP to {server_name}")
        create_symlink(ssh_command_nodeuser, ssh_symlink_path)
        create_symlink(sftp_command_nodeuser, sftp_symlink_path)

    # Add the new details to the config file
    config_content = f"\nCommands to access your server (Post-NodeCTL Installation):\nSSH Command:    {ssh_command_nodeuser}\nSFTP Command:   {sftp_command_nodeuser}\n"

    config_path = os.path.join(folder_path, f"{server_name}_config.txt")
    with open(config_path, 'a') as config_file:
        config_file.write(config_content + '\n')

    # Ask the user if they want to launch the terminal to access the server
    launch_terminal = input("Do you want the script to launch the terminal to access the server? (y/n): ").lower()
    if launch_terminal == 'y':
        try:
            if os.name == 'nt':
                subprocess.Popen(['cmd.exe', '/c', 'start', '', ssh_shortcut_path], shell=True)
            elif os.name == 'posix' and platform.system() == 'Darwin':
                subprocess.Popen(['open', ssh_shortcut_path], shell=True)
            else:
                subprocess.Popen(['gnome-terminal', '--', ssh_command_nodeuser], shell=True)
        except Exception as e:
            print(f"Failed to launch the terminal: {e}")
    print("")    

    print("Commands and shortcuts to access your server (Post-NodeCTL install):")
    print(Fore.LIGHTCYAN_EX + f'SSH Command:    {ssh_command_nodeuser}')
    print(f'SFTP Command:   {sftp_command_nodeuser}')
    print("")
    print(f'SSH Shortcut:    {format_path(folder_path)}\\{server_name}_SSH_({nodeuser}).lnk')
    print(f'SFTP Shortcut:   {format_path(folder_path)}\\{server_name}_SFTP_({nodeuser}).lnk' + Style.RESET_ALL)

def create_server(server_name_param, server_type_id, image, location, firewall_id, ssh_key_name):
    global api_key, global_passphrase, ssh_shortcut_path, sftp_shortcut_path, folder_path, nodeuser, server_name, easy_server
    server_name = server_name_param
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
        print(Fore.LIGHTGREEN_EX + 'Server created successfully.' + Style.RESET_ALL)
        print("")
        host_ip = server_data['server']['public_net']['ipv4']['ip']
        print(Fore.LIGHTCYAN_EX + f"Server Name:    {server_data['server']['name']}")
        print(f"Host IP:        {host_ip}")
        print("SSH Port:        22")
        print(f"SSH Key Name:   {ssh_key_name}" + Style.RESET_ALL)
        print("")

        # Add the new host key to known_hosts
        add_host_key_to_known_hosts(host_ip)

        # Format paths and commands
        private_key_path = format_path(private_key_path)
        ssh_command = f"ssh -i {private_key_path} root@{host_ip}"
        sftp_command = f"sftp -i {private_key_path} root@{host_ip}"

        print("Commands to access your server (Pre-NodeCTL Installation):")
        print(Fore.LIGHTCYAN_EX + f"SSH Command:    {ssh_command}")
        print(f"SFTP Command:   {sftp_command}" + Style.RESET_ALL)
        print("")

        # Create a config file with the server details
        config_content = f"""
Server Name:    {server_name}
Host IP:        {host_ip}
SSH Port:       22
SSH Key Name:   {ssh_key_name}

Commands to access your server (Pre-NodeCTL):
SSH Command:    {ssh_command}
SFTP Command:   {sftp_command}
        """

        # Path to save the config and shortcuts
        folder_path = os.path.join(os.getcwd(), server_name)
        folder_path = format_path(folder_path)
        folder_path_root = format_path(folder_path+"/root")

        os.makedirs(folder_path_root, exist_ok=True)

        # Paths for shortcuts
        ssh_shortcut_path = format_path(os.path.join(folder_path_root, f"{server_name}_SSH_(root).lnk"))
        sftp_shortcut_path = format_path(os.path.join(folder_path_root, f"{server_name}_SFTP_(root).lnk"))

        if os.name == 'nt':
            # Ensure pywin32 is installed on Windows
            try:
                import win32com.client
            except ImportError:
                def install_package(package_name):
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                install_package('pywin32')
                # Initialize pywin32 after installation
                try:
                    from pywin32_postinstall import install
                    install()
                except ImportError:
                    subprocess.check_call([sys.executable, os.path.join(sys.exec_prefix, 'Scripts', 'pywin32_postinstall.py'), '-install'])
                import win32com.client

            # Config file path
            config_path = os.path.join(folder_path, f"{server_name}_config.txt")
            with open(config_path, 'w') as config_file:
                config_file.write(config_content.strip())

            # Create SSH shortcut
            create_shortcut(f'ssh -i {private_key_path} root@{host_ip}', folder_path, ssh_shortcut_path, 'C:\\Windows\\System32\\shell32.dll,135', "root")

            # Create SFTP shortcut
            create_shortcut(f'sftp -i {private_key_path} root@{host_ip}', folder_path, sftp_shortcut_path, 'C:\\Windows\\System32\\shell32.dll,146', "root")

            print(Fore.YELLOW + f'Configuration and shortcuts have been saved to:')
            print(Fore.LIGHTWHITE_EX + folder_path + Style.RESET_ALL)
            print("")
        elif os.name == 'posix' and platform.system() == 'Darwin':
            # Paths for symlinks
            ssh_symlink_path = os.path.join(folder_path, f"SSH to {server_name}")
            sftp_symlink_path = os.path.join(folder_path, f"SFTP to {server_name}")

            # Create symlinks
            create_symlink(ssh_command, ssh_symlink_path)
            create_symlink(sftp_command, sftp_symlink_path)

            print(f"Configuration and symlinks saved to: {folder_path}")
        else:
            config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), f"{server_name}_config.txt")
            config_path = format_path(config_path)
            with open(config_path, 'w') as config_file:
                config_file.write(config_content.strip())

            print(f"Configuration saved to: {config_path}")
            print("")

        # Ask if the user wants to install nodectl
        install_nodectl_decision = input("Do you want to install nodectl on the server? (y/n): ").lower()
        if install_nodectl_decision == 'y':
            install_nodectl(host_ip, private_key_path)

        print("")

        if os.name == 'nt':
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
        return False

def get_api_key():
    global api_key
    if api_key is None:
        while True:
            clear_screen()
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
            api_key = input("Enter your Hetzner API Key: ").strip()

            if len(api_key) == 64 and api_key.isalnum():
                break
            else:
                print(Fore.RED + "Invalid API key. The key must be 64 characters long and contain only letters and numbers. Please try again." + Style.RESET_ALL)
                input("Press Enter to retry...")

    return api_key

def check_for_updates():
    logger.debug("Checking for updates")
    current_hash = calculate_hash(__file__)
    print(f"Current version: {version}")
    print(f"Current hash: {current_hash}")
    check_update = input("Do you want to check for updates? (y/n): ").strip().lower()

    if check_update == 'y':
        print("")
        response = requests.get("https://raw.githubusercontent.com/Proph151Music/Hetzner-Cloud-Management-Tool-HCMT-/main/versions.txt")
        if response.status_code == 200:
            lines = response.text.splitlines()
            latest_version, latest_hash = lines[0].split()
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
                                # Log before launching updater
                                logger.debug(f"Launching updater script: {[sys.executable, 'updater.py', script_path, new_script_path, '--no-update']}")
                                # Wait a bit to ensure file system is ready
                                time.sleep(2)
                                # Launch updater.py and exit hcmt.py
                                subprocess.Popen([sys.executable, 'updater.py', script_path, new_script_path, '--no-update'])
                                logger.debug("Updater script launched. Exiting hcmt.py")
                                sys.exit(0)  # Exit hcmt.py
                            except Exception as e:
                                logger.error(f"Failed to execute updater script: {e}")
                                print(f"Failed to execute updater script: {e}")
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
            print("")
            print("Failed to check for updates.")
            logger.error("Failed to check for updates.")

# Main interaction and menu
def main_menu():
    global api_key, nodeuser, easy_server
    logging.debug("Entered main_menu function")
    if '--no-update' in sys.argv:
        logger.handlers.clear()
        logger.addHandler(console_handler)
        if DEBUG_MODE and file_handler:
            logger.addHandler(file_handler)
    clear_screen()
    print("")
    get_api_key()

    clear_screen()
    print("")
    print("")
    print(Fore.CYAN + "Hetzner Cloud Management Tool" + Style.RESET_ALL)
    print("\nPlease choose an option:")
    ### print("F) Setup Firewall")
    ### print("S) Create SSH Key Pair")
    print("C) Create Cloud Server")
    print("E) Easy Cloud Server Creation")
    print("X) Exit")
    choice = input("\nEnter your choice: ").upper()
    logging.debug(f"User choice: {choice}")

    try:
        if choice == 'E':
            easy_server = True
            ## create_cloud_server()


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

            image = "ubuntu-22.04"
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
            print("or you can type the code to select different specs." + Style.RESET_ALL)
            print("")
            server_types = fetch_and_display_server_types(location_name)
            logging.debug(f"Server types fetched: {server_types}")
            if not server_types:
                logging.error("No server types available.")
                print("No server types available.")
                input("Press Enter to exit...")
                sys.exit()
            print("")

            # Default server type selection logic
            default_server_type_name = None
            if any(st['name'] == 'cx52' for st in server_types):
                default_server_type_name = 'cx52'
            elif any(st['name'] == 'cpx51' for st in server_types):
                default_server_type_name = 'cpx51'
                
            print("")
            server_type_name = input(f"Enter the name of the server type you want to use \n"  
                                     f" [default: {default_server_type_name if default_server_type_name else 'None'}]: ") or default_server_type_name
            if default_server_type_name and server_type_name == default_server_type_name:
                chosen_server_type = next(st for st in server_types if st['name'] == default_server_type_name)
            else:
                chosen_server_type = next((st for st in server_types if st['name'] == server_type_name), None)

            if chosen_server_type:
                server_type_id = chosen_server_type['id']
            else:
                print(f"Server type '{server_type_name}' not found. Exiting.")
                sys.exit()
            logging.debug(f"Chosen server type: {server_type_name}")

            # Server firewall
            print("")
            print(f"-===[ SERVER FIREWALL ]===-")
            print("")

            firewall_name = re.sub(r"[^a-zA-Z0-9]", "-", server_name.lower()) + "-fw"
            print(Fore.LIGHTGREEN_EX + f"Firewall Name: " + Style.RESET_ALL + firewall_name)
            inbound_ports = '9000-9001,9010-9011'
            print(Fore.LIGHTGREEN_EX + f"Inbound Ports: " + Style.RESET_ALL + inbound_ports)
            firewall_id = create_or_update_firewall(firewall_name, inbound_ports)
            logging.debug(f"Chosen firewall ID: {firewall_id}")

            # Server SSH key
            print("")
            print(f"-===[ SERVER SSH KEY ]===-")
            print("")

            ssh_key_name = re.sub(r"[^a-zA-Z0-9]", "-", server_name.lower()) + "-ssh"
            print(Fore.LIGHTGREEN_EX + f"SSH Key Pair: " + Style.RESET_ALL + ssh_key_name)
            ssh_key_id = create_and_upload_ssh_key(ssh_key_name)

            print("")
            print(f"-===[ SERVER CREATION ]===-")
            print("")
            create_server(server_name, server_type_id, image, location, firewall_id, ssh_key_name)
            pause_and_return()
        elif choice == 'F':
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
            easy_server = False
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
            ## print("")
            ## print(f"-===[ SERVER OPERATING SYSTEM ]===-")
            ## print("")
            ## print(Fore.CYAN + "Ubuntu-22.04 is the recommended OS.")
            ## print("By default You can just press ENTER to choose it.")
            ## print("Or you are welcome to type a different OS if instructions have changed." + Style.RESET_ALL)
            ## print("")
            ## image = input("Enter the image you want to use \n"
            ##               f"  [default: ubuntu-22.04]: ") or "ubuntu-22.04"
            image = "ubuntu-22.04"
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
            print("or you can type the code to select different specs." + Style.RESET_ALL)
            print("")
            server_types = fetch_and_display_server_types(location_name)
            logging.debug(f"Server types fetched: {server_types}")
            if not server_types:
                logging.error("No server types available.")
                print("No server types available.")
                input("Press Enter to exit...")
                sys.exit()

            # Default server type selection logic
            default_server_type_name = None
            if any(st['name'] == 'cx52' for st in server_types):
                default_server_type_name = 'cx52'
            elif any(st['name'] == 'cpx51' for st in server_types):
                default_server_type_name = 'cpx51'
                
            print("")
            server_type_name = input(f"Enter the name of the server type you want to use \n"  
                                     f" [default: {default_server_type_name if default_server_type_name else 'None'}]: ") or default_server_type_name
            if default_server_type_name and server_type_name == default_server_type_name:
                chosen_server_type = next(st for st in server_types if st['name'] == default_server_type_name)
            else:
                chosen_server_type = next((st for st in server_types if st['name'] == server_type_name), None)

            if chosen_server_type:
                server_type_id = chosen_server_type['id']
            else:
                print(f"Server type '{server_type_name}' not found. Exiting.")
                sys.exit()
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
            create_server(server_name, server_type_id, image, location, firewall_id, ssh_key_name)
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
    logger.debug(f"Main script started with arguments: {sys.argv}")
    if '--no-update' not in sys.argv:
        check_for_updates()
    try:
        logger.debug("Program started")
        main_menu()
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        print(f"An error occurred: {e}")
        input("Press Enter to exit...")

