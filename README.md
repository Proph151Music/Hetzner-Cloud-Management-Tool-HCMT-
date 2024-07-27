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

## Installation

### Step 1: Install Python

#### Windows

1. Open your web browser.
2. Navigate to the [GitHub repository](https://github.com/Proph151Music/Hetzner-Cloud-Management-Tool-HCMT-).
3. Click on the `install_python.bat` file.
4. Click on the "Raw" button to view the raw file.
5. Right-click on the page and select "Save As" or "Save Page As".
6. Save the file as `install_python.bat` in your desired location, such as the `C:\Users\YourUsername\Downloads\` directory.
7. Browse to the location you downloaded the file and right click on it to choose run as Administrator.

This will check if you have Python and PUP installed.  If not it will ask if you want the script to download and set it up for you automatically.

#### macOS

1. Open Terminal.
2. Install Homebrew if not already installed:

    ```sh
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    ```

3. Install Python using Homebrew:

    ```sh
    brew install python
    ```

#### Linux

1. Open Terminal.
2. Install Python using your package manager:

    - **Debian/Ubuntu:**

        ```sh
        sudo apt-get update
        sudo apt-get install python3
        ```

### Step 2: Download the Script

#### Windows

1. Download the `hcmt.py` file from the [GitHub repository](https://github.com/Proph151Music/Hetzner-Cloud-Management-Tool-HCMT-).
   - Click on the file, then click "Raw", and save the file as `hcmt.py`.
2. Open Command Prompt and navigate to the directory where `hcmt.py` is saved.
3. Run the script by typing this command in the CMD window:

    ```sh
    python hcmt.py
    ```

#### macOS and Linux

1. Download the `hcmt.py` file using a web browser or terminal:

    ```sh
    wget https://raw.githubusercontent.com/Proph151Music/Hetzner-Cloud-Management-Tool-HCMT-/main/hcmt.py -O ~/Downloads/hcmt.py
    ```

2. Open Terminal and navigate to the directory where `hcmt.py` is saved.
3. Run the script:

    ```sh
    python3 ~/Downloads/hcmt.py
    ```
    
### Step 3: Run the Script

The script automatically installs the required packages (`requests`, `colorama`, `paramiko`). Simply run the script, and it will take care of the rest.

```sh
python hcmt.py
```

## Usage

## Creating a Hetzner API Key

1. Log in to your Hetzner Cloud account.
2. Navigate to the "API Tokens" section. (It is inside the Security section.)
3. Click "Generate API Token". Provide any name for the token and choose Read and Write.
4. Copy the generated API key and use it when prompted by the script.

Follow the on-screen instructions to perform your desired operations.

When you run the script, you will be presented with a menu to choose from various options:

1. **Setup Firewall:** Create or update a firewall with specific rules.
2. **Create SSH Key Pair:** Generate and upload an SSH key pair to Hetzner Cloud.
3. **Create Cloud Server:** Create a new cloud server with the specified configurations. This is where I recommend everyone start. It will walk you through all steps.
4. **Exit:** Exit the tool.

Follow the on-screen instructions to perform your desired operations.

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

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
