import os
import subprocess
import sys

if sys.platform == "win32":
    import winreg

# Define the application paths based on the platform
if sys.platform == "win32":
    # Set the working directory to the module directory
    _module_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    os.chdir(_module_dir)
    app_path = os.path.join(_module_dir, 'sd-qt.exe')
    app_name = "TTim"
elif sys.platform == "darwin":
    app_path = "/Applications/TTim.app"
    app_name = "TTim"

def launch_app():
    """
    Add the application to the startup items on macOS.
    """
    if sys.platform == "darwin":
        cmd = f"osascript -e 'tell application \"System Events\" to make login item at end with properties {{path:\"{app_path}\", hidden:false}}'"
        subprocess.run(cmd, shell=True)

def delete_launch_app():
    """
    Remove the application from the startup items on macOS.
    """
    if sys.platform == "darwin":
        cmd = f"osascript -e 'tell application \"System Events\" to delete login item \"{app_name}\"'"
        subprocess.run(cmd, shell=True)

def get_login_items():
    """
    Check if the application is in the startup items on macOS.
    """
    if sys.platform == "darwin":
        cmd = "osascript -e 'tell application \"System Events\" to get the name of every login item'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        items = result.stdout.strip().split(", ")
        return app_name in items
    return False

def check_startup_status():
    """
    Check if the application is set to launch on startup.
    """
    if sys.platform == "darwin":
        return get_login_items()
    elif sys.platform == "win32":
        key_path = r'Software\Microsoft\Windows\CurrentVersion\Run'
        try:
            with winreg.OpenKey(
                    key=winreg.HKEY_CURRENT_USER,
                    sub_key=key_path,
                    reserved=0,
                    access=winreg.KEY_READ,
            ) as key:
                value, _ = winreg.QueryValueEx(key, app_name)
                return True
        except FileNotFoundError:
            return False
    return False

def set_autostart_registry(autostart: bool = True) -> bool:
    """
    Create, update, or delete the Windows autostart registry key.
    """
    if sys.platform == "win32":
        key_path = r'Software\Microsoft\Windows\CurrentVersion\Run'
        try:
            with winreg.OpenKey(
                    key=winreg.HKEY_CURRENT_USER,
                    sub_key=key_path,
                    reserved=0,
                    access=winreg.KEY_ALL_ACCESS,
            ) as key:
                if autostart:
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
                else:
                    winreg.DeleteValue(key, app_name)
        except OSError:
            return False
        return True
    return False

# Example usage:
if __name__ == "__main__":
    if sys.platform == "win32":
        # Set the application to start at login on Windows
        success = set_autostart_registry(autostart=True)
        if success:
            print(f"{app_name} has been added to startup.")
        else:
            print(f"Failed to add {app_name} to startup.")
    elif sys.platform == "darwin":
        # Check if the app is already in startup items on macOS
        if not check_startup_status():
            launch_app()
            print(f"{app_name} has been added to startup.")
        else:
            print(f"{app_name} is already set to start at login.")
