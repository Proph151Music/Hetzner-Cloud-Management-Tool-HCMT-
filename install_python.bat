@echo off
setlocal enabledelayedexpansion

set LOGFILE=c:\hetzner\install_python_log.txt

echo Log file location: %LOGFILE% > %LOGFILE%
echo Starting script... >> %LOGFILE%
echo Starting script...

REM Check if Python is already installed
echo Checking if Python is installed... >> %LOGFILE%
echo Checking if Python is installed...
python --version >> %LOGFILE% 2>>&1
set PYTHON_ERRORLEVEL=%errorlevel%
echo Python command errorlevel: %PYTHON_ERRORLEVEL% >> %LOGFILE%

if "%PYTHON_ERRORLEVEL%"=="0" (
    echo Inside if statement for Python found >> %LOGFILE%
    for /f "tokens=2 delims= " %%A in ('python --version 2^>^&1') do (
        set "PYTHON_VERSION=%%A"
        echo Inside for loop, found Python version %%A >> %LOGFILE%
    )
    echo Python version !PYTHON_VERSION! is already installed. >> %LOGFILE%
    echo Python version !PYTHON_VERSION! is already installed.

    REM Check for pip installation
    echo Checking if pip is installed... >> %LOGFILE%
    pip --version >> %LOGFILE% 2>>&1
    set PIP_ERRORLEVEL=%errorlevel%
    echo pip command errorlevel: !PIP_ERRORLEVEL! >> %LOGFILE%

    if "!PIP_ERRORLEVEL!"=="0" (
        echo pip found. >> %LOGFILE%
        echo pip is installed. >> %LOGFILE%
        echo pip is installed.
    ) else (
        echo pip not found. >> %LOGFILE%
        echo pip is not installed. >> %LOGFILE%
        echo pip is not installed.
    )
    
    @REM REM Prompt for uninstallation
    @REM echo User prompt for uninstallation... >> %LOGFILE%
    @REM set /p uninstall="Do you want to uninstall Python and pip? (y/n): "
    @REM echo User chose to !uninstall! >> %LOGFILE%
    @REM if /i "!uninstall!"=="y" (
    @REM     echo Uninstalling selected by user... >> %LOGFILE%
    @REM     goto :uninstall_python
    @REM ) else (
    @REM     echo Exiting... >> %LOGFILE%
    @REM     echo Exiting...
    @REM     exit /b
    @REM )
) else (
    echo Python not found in PATH, searching all possible locations... >> %LOGFILE%
    echo Python not found in PATH, searching all possible locations...
    call :find_python_in_common_locations
)

goto end

:find_python_in_common_locations
set PYTHON_FOUND=0
for %%D in (
    "%LocalAppData%\Programs\Python\Python3*"
    "%ProgramFiles%\Python3*"
    "%ProgramFiles(x86)%\Python3*"
    "%LOCALAPPDATA%\Microsoft\WindowsApps"
) do (
    echo Checking %%D for Python... >> %LOGFILE%
    if exist "%%D\python.exe" (
        set "PYTHON_DIR=%%D"
        echo Found Python installation in %%D >> %LOGFILE%
        echo Found Python installation in %%D
        setx PATH "%%D;%%D\Scripts;%PATH%" >> %LOGFILE% 2>>&1
        set PYTHON_FOUND=1
        goto check_python
    )
)
if !PYTHON_FOUND! equ 0 (
    echo No Python installations found in common locations. >> %LOGFILE%
    echo No Python installations found in common locations.
    echo Python is not installed.
    set /p install="Do you want to install Python and pip? (y/n): "
    echo User chose to !install! >> %LOGFILE%
    if /i "!install!"=="y" (
        echo User chose to install >> %LOGFILE%
        goto install_python
    ) else (
        echo Exiting... >> %LOGFILE%
        echo Exiting...
        exit /b
    )
)

:check_python
python --version >> %LOGFILE% 2>>&1
set CHECK_PYTHON_ERRORLEVEL=%errorlevel%
echo Check Python errorlevel: %CHECK_PYTHON_ERRORLEVEL% >> %LOGFILE%

if "%CHECK_PYTHON_ERRORLEVEL%"=="0" (
    echo Python successfully added to PATH. >> %LOGFILE%
    echo Python successfully added to PATH.
    goto end
) else (
    echo Python was not found even after adding to PATH. >> %LOGFILE%
    echo Python was not found even after adding to PATH.
    exit /b
)

REM Function to uninstall Python
:uninstall_python
echo Uninstalling Python... >> %LOGFILE%
echo Uninstalling Python...

REM Get the uninstall strings for all Python components from the registry using PowerShell and execute them
for /f "usebackq tokens=*" %%i in (`powershell -Command "Get-ItemProperty -Path HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | Where-Object { $_.DisplayName -like 'Python *' } | Select-Object -ExpandProperty UninstallString"`) do (
    set "uninstallString=%%i"
    echo Found uninstall string: !uninstallString! >> %LOGFILE%
    if defined uninstallString (
        set "uninstallString=!uninstallString:/I=/X!"
        echo Uninstalling with command: "!uninstallString! /passive /norestart" >> %LOGFILE%
        call !uninstallString! /passive /norestart >> %LOGFILE% 2>>&1
        echo Python uninstallation command executed: !uninstallString! >> %LOGFILE%
    ) else (
        echo No uninstall string found for %%i >> %LOGFILE%
    )
)

REM Check if the uninstallation was successful
for /f "usebackq tokens=*" %%i in (`powershell -Command "Get-ItemProperty -Path HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | Where-Object { $_.DisplayName -like 'Python *' } | Select-Object DisplayName"`) do (
    echo Still found an installed Python entry: %%i >> %LOGFILE%
    echo Still found an installed Python entry: %%i
)

echo Python uninstalled. >> %LOGFILE%
goto end

REM Proceed with installation
:install_python
echo Downloading and installing the latest Python version... >> %LOGFILE%

REM Define the URL for the Python FTP page
set "FTP_PAGE=https://www.python.org/ftp/python/"
echo FTP_PAGE = %FTP_PAGE% >> %LOGFILE%

REM Create a temporary PowerShell script to handle the FTP scraping
set PS_SCRIPT=%TEMP%\get_latest_python.ps1

echo $ErrorActionPreference = "Stop" > %PS_SCRIPT%
echo try { >> %PS_SCRIPT%
echo     $htmlContent = Invoke-WebRequest -Uri %FTP_PAGE% >> %PS_SCRIPT%
echo     $versions = $htmlContent.Links ^| Where-Object { $_.href -match '^(\d+\.\d+\.\d+)/$' } ^| ForEach-Object { $_.href -replace '/$' } >> %PS_SCRIPT%
echo     $sortedVersions = $versions ^| Sort-Object { [System.Version]::Parse($_) } >> %PS_SCRIPT%
echo     $latestStableVersion = $sortedVersions[-2] >> %PS_SCRIPT%
echo     $latestStableUrl = "$FTP_PAGE$latestStableVersion/python-$latestStableVersion-amd64.exe" >> %PS_SCRIPT%
echo     $latestStableUrl ^| Out-File %TEMP%\latest_stable_url.txt -Encoding ascii >> %PS_SCRIPT%
echo } catch { >> %PS_SCRIPT%
echo     Write-Error "Failed to retrieve Python versions: $_" >> %PS_SCRIPT%
echo     exit 1 >> %PS_SCRIPT%
echo } >> %PS_SCRIPT%

powershell -ExecutionPolicy Bypass -File %PS_SCRIPT% >> %LOGFILE% 2>>&1

if %ERRORLEVEL% neq 0 (
    echo PowerShell script failed. See log for details. >> %LOGFILE%
    goto end
)

if not exist %TEMP%\latest_stable_url.txt (
    echo Failed to retrieve the latest stable version from the FTP page. >> %LOGFILE%
    goto end
)

set /p LATEST_VERSION_URL=<%TEMP%\latest_stable_url.txt

echo LATEST_VERSION_URL before extraction: !LATEST_VERSION_URL! >> %LOGFILE%

REM Check if LATEST_VERSION_URL is not empty
if "!LATEST_VERSION_URL!"=="" (
    echo Failed to detect the latest Python version URL. >> %LOGFILE%
    echo Exiting...
    goto end
)

echo Detected latest Python version URL: !LATEST_VERSION_URL! >> %LOGFILE%

REM Construct the full URL for the installer
set "fullUrl=https://www.python.org/ftp/python/!LATEST_VERSION_URL!"
set "pythonInstallerPath=%TEMP%\python-installer.exe"

REM Download the Python installer using PowerShell with a progress bar
powershell -Command "Invoke-WebRequest -Uri '%fullUrl%' -OutFile '%pythonInstallerPath%' -UseBasicParsing -Verbose" >> %LOGFILE% 2>>&1

REM Verify the download
if exist "!pythonInstallerPath!" (
    echo Python installer downloaded successfully. >> %LOGFILE%
    echo Proceeding with installation of Python... >> %LOGFILE%
) else (
    echo Failed to download Python installer. >> %LOGFILE%
    echo Exiting...
    goto end
)

REM Install Python unattended
start /wait "" "!pythonInstallerPath!" /passive InstallAllUsers=1 PrependPath=1 Include_pip=1

REM Install pip if not already installed
python -m ensurepip --upgrade >> %LOGFILE% 2>>&1
python -m pip install --upgrade pip >> %LOGFILE% 2>>&1

REM Detect Python installation path
for /f "delims=" %%A in ('powershell -command "(Get-Command python).Path"') do set "pythonPath=%%A"
set "pythonDir=%pythonPath:\python.exe=%"
set "scriptDir=%pythonDir%\Scripts"
echo Detected Python directory: %pythonDir% >> %LOGFILE%
echo Detected Scripts directory: %scriptDir% >> %LOGFILE%

REM Remove only invalid Python paths from PATH
for %%P in ("%PATH:;=" "%") do (
    if exist "%%~P\python.exe" (
        if "!newPath!" == "" (
            set "newPath=%%~P"
        ) else (
            set "newPath=!newPath!;%%~P"
        )
    )
)

REM Add the new Python paths
set "newPath=%pythonDir%;%scriptDir%;!newPath!"
echo New PATH: !newPath! >> %LOGFILE%

REM Update the system PATH
powershell -command "[System.Environment]::SetEnvironmentVariable('Path', '%newPath%', [System.EnvironmentVariableTarget]::Machine)" >> %LOGFILE% 2>>&1

REM Verify the installation
echo Verifying Python installation... >> %LOGFILE%
python --version >> %LOGFILE% 2>>&1
echo Verifying pip installation... >> %LOGFILE%
pip --version >> %LOGFILE% 2>>&1

REM Ensure pip is included in the PATH
set "scriptDir=%pythonDir%\Scripts"
if not exist "%scriptDir%\pip.exe" (
    echo Pip installation failed. >> %LOGFILE%
    echo Pip installation failed.
    goto end
)
set "newPath=!newPath!;%scriptDir%"

REM Clean up
del /f "!pythonInstallerPath!" >> %LOGFILE%
del /f "%PS_SCRIPT%" >> %LOGFILE%

:end
echo Script ended. >> %LOGFILE%
pause
exit
endlocal
