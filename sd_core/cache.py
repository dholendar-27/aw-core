import platform
import subprocess
import keyring
import json
from cachetools import TTLCache
import logging
from keyrings.alt.file import PlaintextKeyring

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

keyring.set_keyring(PlaintextKeyring())

# Initialize a cache with a maximum size and a TTL (time-to-live)
credentials_cache = TTLCache(maxsize=100, ttl=3600)

def is_macos():
    """Check if the current OS is macOS."""
    logger.info("Checking the operating system.")
    return platform.system() == 'Darwin'

def run_keychain_command(command):
    """Run a command for macOS Keychain."""
    try:
        logger.info(f"Running keychain command: {' '.join(command)}")
        subprocess.run(command, check=True, text=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Keychain command failed. Error: {e}")
        return False

def add_password(service, password):
    """Add or update a password in the system's secure storage."""
    logger.info(f"Adding/updating password for service {service}.")
    if is_macos():
        command = ['security', 'add-generic-password', '-s', service, '-a', service, '-w', password, '-U']
        return "Success" if run_keychain_command(command) else "Failed"
    else:
        keyring.set_password(service, service, password)
        return "Success"

def update_password(service, password):
    """Update an existing password in the system's secure storage."""
    logger.info(f"Updating password for service {service}.")
    if keychain_item_exists(service):
        return add_password(service, password)
    else:
        logger.warning(f"Password for service {service} does not exist. Cannot update.")
        return "Failed"

def keychain_item_exists(service):
    """Check if a keychain item exists in the system's secure storage."""
    logger.info(f"Checking if a keychain item exists for service {service}.")
    if is_macos():
        command = ['security', 'find-generic-password', '-s', service, '-a', service]
        try:
            subprocess.run(command, check=True, text=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False
    else:
        return keyring.get_password(service, service) is not None

def delete_password(service):
    """Delete a password from the system's secure storage if it exists."""
    logger.info(f"Deleting password for service {service}.")
    if keychain_item_exists(service):
        if is_macos():
            command = ['security', 'delete-generic-password', '-s', service, '-a', service]
            return "Success" if run_keychain_command(command) else "Failed"
        else:
            keyring.delete_password(service, service)
            return "Success"
    else:
        logger.warning("Keychain item not found.")
        return "Keychain item not found"

def get_password(service):
    """Retrieve a password from the system's secure storage."""
    logger.info(f"Retrieving password for service {service}.")
    if is_macos():
        command = ['security', 'find-generic-password', '-s', service, '-a', service, '-w']
        try:
            result = subprocess.run(command, check=True, text=True, capture_output=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None
    else:
        return keyring.get_password(service, service)

def store_credentials(service, credentials):
    """Store a service's credentials in the cache."""
    credentials_cache[service] = credentials

def get_credentials(service):
    """Retrieve a service's credentials from the cache."""
    return credentials_cache.get(service)

def clear_credentials(service):
    """Clear a service's credentials from the cache."""
    if service in credentials_cache:
        logger.info(f"Clearing credentials from cache for service: {service}")
        del credentials_cache[service]
    else:
        logger.info(f"No credentials found in cache for service: {service}")


def clear_all_credentials():
    """Clear all credentials from the cache."""
    logger.info("Clearing all credentials from cache.")
    credentials_cache.clear()


def cache_user_credentials(service):
    """Cache user credentials for the given service."""
    cached_credentials = get_credentials(service)
    if cached_credentials is None:
        credentials_str = get_password(service)
        if credentials_str:
            try:
                # Parse the JSON string to a dictionary
                credentials = json.loads(credentials_str)
                store_credentials(service, credentials)
                return credentials
            except json.JSONDecodeError:
                logger.error("Error decoding credentials from JSON.")
                return None
        else:
            logger.warning(f"No credentials found for service {service}.")
            return None
    else:
        return cached_credentials
