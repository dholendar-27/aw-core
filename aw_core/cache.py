import json
import platform
import subprocess
from cachetools import TTLCache
import json
# Initialize a cache with a maximum size and a TTL (time-to-live) for cached items
credentials_cache = TTLCache(maxsize=100, ttl=3600)  # Adjust maxsize and ttl as needed

# Function to determine if the current OS is macOS
def is_macos():
    return platform.system() == 'Darwin'

def add_password_to_keychain(service, password):
    if is_macos():
        # Check if the item already exists in the Keychain
        existing_password = get_password_from_keychain(service)
        if existing_password is not None:
            # Item already exists, so update the password instead of adding a new one
            try:
                command = [
                    'security', 'add-generic-password',
                    '-s', service,
                    '-a', "com.ralvie.sundial",
                    '-w', json.dumps(password),
                    '-U'
                ]
                subprocess.run(command, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Failed to update password in Keychain. Error: {e}")
        else:
            # Item doesn't exist, so add a new password
            try:
                command = [
                    'security', 'add-generic-password',
                    '-s', service,
                    '-a', "com.ralvie.sundial",
                    '-w', json.dumps(password),
                    '-U'
                ]
                subprocess.run(command, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Failed to add password to Keychain. Error: {e}")


def get_password_from_keychain(service):
    account = "com.ralvie.sundial"
    if is_macos():
        try:
            command = [
                'security', 'find-generic-password',
                '-s', service,
                '-a', "com.ralvie.sundial",
                '-w'
            ]
            result = subprocess.run(command, check=True, text=True, capture_output=True)
            return json.loads(result.stdout.strip())
        except subprocess.CalledProcessError as e:
            print(f"Failed to retrieve password from Keychain. Error: {e}")
            return None

def store_credentials(key, credentials):
    credentials_cache[key] = credentials

def get_credentials(key):
    return credentials_cache.get(key)

def clear_credentials(key):
    if key in credentials_cache:
        del credentials_cache[key]

def clear_all_credentials():
    credentials_cache.clear()

def cache_user_credentials(cache_key, service):
    # Retrieve cached credentials if they exist
    cached_credentials = get_credentials(cache_key)
    if cached_credentials is None:
        if is_macos():
            credentials = get_password_from_keychain(service)
        else:
            import keyring
            credentials = keyring.get_password(service)
            if credentials:
                credentials = json.loads(credentials)

        if credentials:
            store_credentials(cache_key, credentials)
            return credentials

    return cached_credentials

