#!/usr/bin/env python3

import os
import sys
import json
import time
import requests
import warnings
import urllib3

# Suppress urllib3 warnings
warnings.filterwarnings("ignore", category=urllib3.exceptions.NotOpenSSLWarning)

# ANSI escape codes for colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def color_print(text, color='', end='\n'):
    """Print colored text using ANSI escape codes."""
    print(f"{color}{text}{Colors.RESET}", end=end)

def load_apps():
    """Load apps from JSON file."""
    try:
        with open('apps.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        color_print(f"Error loading apps: {str(e)}", Colors.RED)
        return {}

def display_title():
    """Display the title."""
    os.system('clear')
    color_print("\n=== ZortosHub ===", Colors.CYAN + Colors.BOLD)
    color_print("Your Mac App Hub\n", Colors.YELLOW)

def is_app_installed(app_name):
    """Check if an app is already installed."""
    applications_dir = "/Applications"
    app_path = os.path.join(applications_dir, f"{app_name}.app")
    return os.path.exists(app_path)

def display_apps(apps, search_term=None):
    """Display available apps."""
    # Sort apps by category
    sorted_apps = sorted(apps.items(), key=lambda x: (x[1]['category'], x[1]['name']))
    
    current_category = None
    app_list = []
    
    # Filter apps if search term is provided
    if search_term:
        search_term = search_term.lower()
        sorted_apps = [
            (app_id, app) for app_id, app in sorted_apps
            if search_term in app['name'].lower() or search_term in app['description'].lower()
        ]
    
    for i, (app_id, app) in enumerate(sorted_apps, 1):
        # Print category header if changed
        if current_category != app['category']:
            current_category = app['category']
            color_print(f"\n{current_category}:", Colors.BLUE + Colors.BOLD)
        
        # Create status indicator
        installed = "✓" if is_app_installed(app['name']) else " "
        status = "🏴‍☠️" if app['status'] == 'cracked' else "💰"
        
        # Print app info with colors
        app_text = f"{installed} {i}. {app['name']} {status} - {app['description']}"
        if installed == "✓":
            color_print(app_text, Colors.GREEN)
        else:
            print(app_text)
        
        app_list.append((app_id, app))
    
    return app_list

def get_user_choice(prompt, valid_range=None, yes_no=False):
    """Get user input with validation."""
    while True:
        try:
            color_print(f"\n{prompt}: ", Colors.CYAN, end='')
            choice = input().strip()
            
            if yes_no:
                if choice.lower() in ['y', 'yes', '']:
                    return True
                if choice.lower() in ['n', 'no']:
                    return False
            elif valid_range:
                if not choice:
                    return None
                num = int(choice)
                if num in valid_range:
                    return num
            
            color_print("Invalid choice. Please try again.", Colors.RED)
        except ValueError:
            color_print("Please enter a valid number.", Colors.RED)

def download_and_install(app):
    """Download and install the selected app."""
    try:
        os.system('clear')
        color_print(f"Installing {app['name']}...\n", Colors.CYAN + Colors.BOLD)
        
        if is_app_installed(app['name']):
            if not get_user_choice(f"{app['name']} is already installed. Would you like to reinstall it? [Y/n]", yes_no=True):
                return False
        
        # Create downloads directory if it doesn't exist
        downloads_dir = os.path.expanduser('~/Downloads/ZortosHub')
        os.makedirs(downloads_dir, exist_ok=True)
        
        filepath = os.path.join(downloads_dir, app['filename'])
        
        # Download the file
        color_print(f"\n📥 Downloading {app['name']}...")
        response = requests.get(app['url'], stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(filepath, 'wb') as f:
            if total_size == 0:
                f.write(response.content)
            else:
                downloaded = 0
                last_percentage = -1
                for data in response.iter_content(chunk_size=4096):
                    downloaded += len(data)
                    f.write(data)
                    
                    # Update progress every 10%
                    current_percentage = int((downloaded / total_size) * 100)
                    if current_percentage % 10 == 0 and current_percentage != last_percentage:
                        os.system('clear')
                        color_print(f"Installing {app['name']}...\n", Colors.CYAN + Colors.BOLD)
                        color_print(f"📥 Downloading: {current_percentage}% complete", Colors.YELLOW)
                        last_percentage = current_percentage
        
        os.system('clear')
        color_print(f"Installing {app['name']}...\n", Colors.CYAN + Colors.BOLD)
        color_print(f"✨ Download complete!", Colors.GREEN)
        
        # Mount DMG
        color_print(f"\n💿 Mounting {app['name']}...")
        
        # Get currently mounted volumes
        mounted_volumes = os.popen('hdiutil info').read()
        
        # Check if our DMG is already mounted and force detach it
        if filepath in mounted_volumes:
            for line in mounted_volumes.split('\n'):
                if line.startswith('/Volumes/'):
                    volume_path = line.strip()
                    color_print("Detaching previous mount...", Colors.YELLOW)
                    os.system(f'hdiutil detach "{volume_path}" -force 2>/dev/null')
                    time.sleep(2)  # Give it time to detach
        
        # Try mounting up to 3 times
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Mount the DMG file and capture the output
                mount_output = os.popen(f'hdiutil attach "{filepath}" 2>&1').read()
                
                # Check for errors
                if 'Resource busy' in mount_output:
                    if attempt < max_retries - 1:
                        color_print("Mount busy, retrying...", Colors.YELLOW)
                        time.sleep(2)
                        continue
                    else:
                        color_print(f"\n❌ DMG is still in use. Please try closing any applications using it and try again.", Colors.RED + Colors.BOLD)
                        return False
                
                # Parse the output to find the mounted volume path
                volume_path = None
                for line in mount_output.split('\n'):
                    if '/Volumes/' in line:
                        volume_path = line.split('/Volumes/')[-1].strip()
                        break
                
                if volume_path:
                    os.system('clear')
                    color_print(f"Installing {app['name']}...\n", Colors.CYAN + Colors.BOLD)
                    # Show in Finder
                    os.system(f'open "/Volumes/{volume_path}"')
                    color_print(f"✨ {app['name']} has been mounted! Follow the installation instructions in Finder.", Colors.GREEN + Colors.BOLD)
                    
                    # Wait for user to finish installation and handle unmounting
                    color_print("\nPress Enter to unmount the installer (or 'n' to keep it mounted): ", Colors.CYAN, end='')
                    unmount = input().strip().lower()
                    if unmount != 'n':
                        os.system(f'hdiutil detach "/Volumes/{volume_path}" -force 2>/dev/null')
                        color_print(f"✨ {app['name']} installer has been unmounted.", Colors.GREEN)
                    return True
                
            except Exception as mount_error:
                if attempt < max_retries - 1:
                    color_print("Mount failed, retrying...", Colors.YELLOW)
                    time.sleep(2)
                    continue
                else:
                    color_print(f"\n❌ Failed to mount {app['name']}: {str(mount_error)}", Colors.RED + Colors.BOLD)
                    return False
        
        color_print(f"\n❌ Failed to mount {app['name']}. Please try again.", Colors.RED + Colors.BOLD)
        return False
        
    except Exception as e:
        color_print(f"\nError: {str(e)}", Colors.RED + Colors.BOLD)
        return False

def install_app(app_id, interactive=True):
    """Install an app by its ID."""
    apps = load_apps()
    if app_id not in apps:
        color_print(f"Error: App '{app_id}' not found.", Colors.RED)
        return False
    
    app = apps[app_id]
    if not interactive:
        # Non-interactive mode, just download and mount
        return download_and_install(app)
    else:
        # Interactive mode, ask for confirmation
        if get_user_choice(f"Ready to install {app['name']}? [Y/n]", yes_no=True):
            return download_and_install(app)
    return False

def print_usage():
    """Print command-line usage information."""
    color_print("\nZortosHub - Mac App Manager", Colors.CYAN + Colors.BOLD)
    color_print("\nCommands:", Colors.YELLOW)
    print("  python main.py                    # Run in interactive mode")
    print("  python main.py install <app_id>   # Install specific app")
    print("  python main.py list               # List all available apps with IDs")
    print("  python main.py help               # Show this help message")
    print("\nExample:")
    print("  python main.py install firefox")

def list_available_apps():
    """List all available apps with their IDs."""
    apps = load_apps()
    if not apps:
        color_print("\nNo apps available.", Colors.RED)
        return
    
    color_print("\nAvailable Apps:", Colors.CYAN + Colors.BOLD)
    current_category = None
    
    # Sort apps by category and name
    sorted_apps = sorted(apps.items(), key=lambda x: (x[1]['category'], x[1]['name']))
    
    for app_id, app in sorted_apps:
        if current_category != app['category']:
            current_category = app['category']
            color_print(f"\n{current_category}:", Colors.BLUE + Colors.BOLD)
        
        installed = "✓" if is_app_installed(app['name']) else " "
        status = "🏴‍☠️" if app['status'] == 'cracked' else "💰"
        
        app_text = f"{installed} {app_id:<20} {app['name']} {status} - {app['description']}"
        if installed == "✓":
            color_print(app_text, Colors.GREEN)
        else:
            print(app_text)

def main():
    """Main application loop."""
    while True:
        display_title()
        
        # Main menu
        print("1. Install App")
        print("2. Search Apps")
        print("3. Refresh Apps")
        print("4. Exit")
        
        choice = get_user_choice("Select an option [1-4]", range(1, 5))
        
        if choice == 1:
            os.system('clear')
            display_title()
            # Show all apps
            apps = load_apps()
            app_list = display_apps(apps)
            if not app_list:
                color_print("\nNo apps available.", Colors.RED)
                continue
            
            # Get app selection
            app_choice = get_user_choice(f"Select an app [1-{len(app_list)}]", range(1, len(app_list) + 1))
            if not app_choice:
                continue
            
            selected_app = app_list[app_choice - 1][1]
            
            # Confirm installation
            if get_user_choice(f"Ready to install {selected_app['name']}? [Y/n]", yes_no=True):
                download_and_install(selected_app)
            
        elif choice == 2:
            os.system('clear')
            display_title()
            # Search apps
            color_print("\nEnter search term: ", Colors.CYAN, end='')
            search_term = input().strip()
            apps = load_apps()
            display_apps(apps, search_term)
            
        elif choice == 3:
            # Refresh apps
            color_print("\nRefreshing apps list...", Colors.YELLOW)
            load_apps()
            color_print("Apps refreshed!", Colors.GREEN)
            time.sleep(1)
            os.system('clear')
            
        elif choice == 4:
            os.system('clear')
            color_print("\nGoodbye! 👋", Colors.CYAN + Colors.BOLD)
            break
        
        # Ask to continue
        if not get_user_choice("\nWould you like to continue? [Y/n]", yes_no=True):
            os.system('clear')
            color_print("\nGoodbye! 👋", Colors.CYAN + Colors.BOLD)
            break

if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()
            
            if command == "install" and len(sys.argv) == 3:
                app_id = sys.argv[2].lower()
                install_app(app_id, interactive=False)
            elif command == "list":
                list_available_apps()
            elif command == "help":
                print_usage()
            else:
                print_usage()
        else:
            main()
    except KeyboardInterrupt:
        color_print("\nGoodbye! 👋", Colors.CYAN + Colors.BOLD)