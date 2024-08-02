# Hetzner Cloud Management Tool (HCMT)

## Overview

The Hetzner Cloud Management Tool (HCMT) is a powerful script designed to manage various operations in Hetzner Cloud. It streamlines tasks such as setting up firewalls, creating SSH key pairs, and managing cloud servers through an easy-to-use command-line interface.

## Features

- **Firewall Management:** Create and update firewalls with customizable rules.
- **SSH Key Management:** Generate and upload SSH key pairs securely.
- **Server Creation:** Create and configure cloud servers with specific specifications.
- **Cross-Platform Support:** Works on Windows, macOS, and Linux.

## Prerequisites

- Python 3.x
- `pip` for managing Python packages

--------------------
## Installation
--------------------

#### Windows
--------------------

**Download and Extract the hcmt_launcher.zip file**

1. **Download the File:**
   - [Right-click here and select "Save As"](https://github.com/Proph151Music/Hetzner-Cloud-Management-Tool-HCMT-/raw/main/Windows/hcmt_launcher.zip) to download the `hcmt_launcher.zip` file.
   - Save the file in your desired location, such as the `C:\Users\YourUsername\Downloads` directory.

2. **Extract the File:**
   - Browse to the location where you downloaded the `hcmt_launcher.zip` file.
   - Right-click on `hcmt_launcher.zip` and select "Extract All...".
   - Choose your desired extraction location and click "Extract".

3. **Run the File:**
   - Navigate to the extracted folder.
   - Right-click on `hcmt_launcher.bat` and select "Run as Administrator".

   **Script Behavior:**
   - The `hcmt_launcher.bat` file will check if you have Python and pip installed. If not, it will ask if you want the script to download and set them up for you automatically.
   - If `hcmt_launcher.bat` detects that you already have Python and pip installed properly, it will ask if you'd like to launch the `hcmt.py` file.

   **Direct Execution:**
   - Alternatively, if Python and pip are already installed and properly set up in the PATH, the `hcmt.py` file can be launched directly from a CMD prompt using the following command:
     ```sh
     python hcmt.py
     ```

--------------------

#### macOS

By default Mac should already have Python installed. 

1. **Download the [hcmt.py](https://github.com/Proph151Music/Hetzner-Cloud-Management-Tool-HCMT-/raw/main/hcmt.py) file:**

    Open Terminal and Use `curl` to download the latest version of `hcmt.py` to ensure you get the most recent non-cached version. Open Terminal and run:

    ```sh
    curl -o hcmt.py -L -H "Cache-Control: no-cache" https://raw.githubusercontent.com/Proph151Music/Hetzner-Cloud-Management-Tool-HCMT-/main/hcmt.py
    ```
    
2. **Run the script:**
   
    This command should run the hcmt.py file in a virtual environment:
    ```sh
    python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python hcmt.py
    ```
    
--------------------

#### Linux
   
1. Install Python using your package manager:

    - **Debian/Ubuntu:**

        ```sh
        sudo apt-get update
        sudo apt-get install python3
        ```

2. **Download the `hcmt.py` file:**

    Use `curl` to download the latest version of `hcmt.py` to ensure you get the most recent non-cached version. Open Terminal and run:

    ```sh
    curl -o hcmt.py -L -H "Cache-Control: no-cache" https://raw.githubusercontent.com/Proph151Music/Hetzner-Cloud-Management-Tool-HCMT-/main/hcmt.py
    ```

3. **Run the script:**

    ```sh
    python3 hcmt.py
    ```
--------------------

--------------------
## Usage
--------------------

The script automatically installs the required packages (`requests`, `colorama`, `paramiko`). Simply run the script, and it will take care of the rest.

Create a Hetzner API Key

C) **Create Cloud Server:** (Recommended) Create a new cloud server with the specified configurations. This is where I recommend everyone start. It will walk you through all steps.
X) **Exit:** Exit the tool.

## Logging

The script logs its operations and errors to a file named `hetzner_debug.log` when running in debug mode. This log can be useful for troubleshooting issues.

## Debug Mode

To enable debug mode, set the `DEBUG_MODE` variable to `True` at the beginning of the script:

```python
DEBUG_MODE = True
```

In debug mode, all operations are logged to `hetzner_debug.log`.

## Contributing

If you would like to contribute to the development of HCMT, please fork the repository and submit a pull request. We welcome all contributions and improvements.

## Acknowledgments
This script was written by @Proph151Music for the Constellation Network ecosystem. 
Don't forget to tip the bar tender! 

**DAG Wallet Address for sending tips:**
`DAG0Zyq8XPnDKRB3wZaFcFHjL4seCLSDtHbUcYq3`

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
