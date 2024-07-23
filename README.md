# Hetzner Cloud Management Tool (HCMT)

## Overview

The Hetzner Cloud Management Tool (HCMT) is a powerful and efficient script designed to manage various operations in Hetzner Cloud. It provides functionalities such as setting up firewalls, creating SSH key pairs, and managing cloud servers. This tool is particularly useful for developers and system administrators who want to streamline their Hetzner Cloud management tasks through an easy-to-use command-line interface.

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

1. Visit the [Python downloads page](https://www.python.org/downloads/).
2. Download the installer for the latest version of Python.
3. Run the installer and follow the instructions. Make sure to check the box that says "Add Python to PATH".

#### macOS

1. Open Terminal.
2. Install Homebrew if you haven't already:

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

    - **Fedora:**

        ```sh
        sudo dnf install python3
        ```

    - **Arch Linux:**

        ```sh
        sudo pacman -S python
        ```

### Step 2: Download the Script

#### Windows

1. Open your web browser.
2. Navigate to the [GitHub repository](https://github.com/Proph151Music/Hetzner-Cloud-Management-Tool-HCMT-).
3. Click on the `hcmt.py` file.
4. Click on the "Raw" button to view the raw file.
5. Right-click on the page and select "Save As" or "Save Page As".
6. Save the file as `hcmt.py` in your desired location, such as the `C:\Users\YourUsername\Downloads\` directory.

### Ensure Python is in PATH (Windows Only)
If Python is installed but not recognized in Command Prompt, run the following PowerShell command to add Python to your PATH. Open PowerShell as an administrator and run:

```$pythonPath = (Get-Command python).Path; $pythonDir = Split-Path $pythonPath; $env:Path += ";$pythonDir;$pythonDir\Scripts"; [Environment]::SetEnvironmentVariable("Path", $env:Path, [System.EnvironmentVariableTarget]::Machine)```

#### macOS

1. Open your web browser.
2. Navigate to the [GitHub repository](https://github.com/Proph151Music/Hetzner-Cloud-Management-Tool-HCMT-).
3. Click on the `hcmt.py` file.
4. Click on the "Raw" button to view the raw file.
5. Right-click on the page and select "Download Linked File As".
6. Save the file as `hcmt.py` in your desired location, such as the `Downloads` folder.

#### Linux

1. Open your web browser.
2. Navigate to the [GitHub repository](https://github.com/Proph151Music/Hetzner-Cloud-Management-Tool-HCMT-).
3. Click on the `hcmt.py` file.
4. Click on the "Raw" button to view the raw file.
5. Right-click on the page and select "Save Link As".
6. Save the file as `hcmt.py` in your desired location, such as the `~/Downloads` directory.

Alternatively, you can use the terminal to download the file:

```wget https://raw.githubusercontent.com/Proph151Music/Hetzner-Cloud-Management-Tool-HCMT-/main/hcmt.py -O ~/Downloads/hcmt.py```


### Step 3: Run the Script

The script automatically installs the required packages (`requests`, `colorama`, `paramiko`). Simply run the script, and it will take care of the rest.

```sh
python hcmt.py
```

## Usage

When you run the script, you will be presented with a menu to choose from various options:

1. **Setup Firewall:** Create or update a firewall with specific rules.
2. **Create SSH Key Pair:** Generate and upload an SSH key pair to Hetzner Cloud.
3. **Create Cloud Server:** Create a new cloud server with the specified configurations.
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
