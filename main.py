#!/usr/bin/env python3

import os
import sys
import json
import time
import subprocess
from typing import Dict, List, Tuple, Optional

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def color_print(text: str, color: str = '', end: str = '\n') -> None:
    """Print colored text using ANSI escape codes."""
    print(f"{color}{text}{Colors.RESET}", end=end)

def load_apps() -> Dict:
    """Load apps from JSON file."""
    try:
        with open('apps.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        color_print(f"Error loading apps: {str(e)}", Colors.RED)
        return {}

def display_title() -> None:
    """Display the title."""
    os.system('clear')
    color_print("\n=== ZortosHub ===", Colors.CYAN + Colors.BOLD)
    color_print("Your Mac App Hub\n", Colors.YELLOW)

def is_app_installed(app_name: str) -> bool:
    """Check if an app is already installed."""
    applications_dir = "/Applications"
    app_path = os.path.join(applications_dir, f"{app_name}.app")
    return os.path.exists(app_path)

def download_file(url: str, filepath: str, app_name: str) -> bool:
    """Download a file using curl with progress tracking."""
    try:
        color_print(f"\n📥 Downloading {app_name}...")
        
        # Prepare curl command with progress bar
        curl_cmd = [
            'curl', '-L', '-o', filepath,
            '--progress-bar',  # Show progress bar
            '--create-dirs',   # Create directories if needed
            '--retry', '3',    # Retry up to 3 times
            url
        ]
        
        # Execute curl command
        process = subprocess.Popen(
            curl_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for download to complete
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            color_print(f"\n❌ Download failed: {stderr.decode()}", Colors.RED)
            return False
            
        color_print(f"✨ Download complete!", Colors.GREEN)
        return True
        
    except Exception as e:
        color_print(f"\nError downloading file: {str(e)}", Colors.RED)
        return False

def mount_dmg(filepath: str, app_name: str) -> Optional[str]:
    """Mount a DMG file and return the volume path."""
    try:
        color_print(f"\n💿 Mounting {app_name}...")
        
        # Verify file exists
        if not os.path.exists(filepath):
            color_print(f"\n❌ DMG file not found: {filepath}", Colors.RED)
            return None
            
        # Get currently mounted volumes
        mounted_volumes = os.popen('hdiutil info').read()
        
        # Check if DMG is already mounted and force detach it
        if filepath in mounted_volumes:
            color_print("Previous mount detected, cleaning up...", Colors.YELLOW)
            for line in mounted_volumes.split('\n'):
                if line.startswith('/Volumes/'):
                    volume_path = line.strip()
                    color_print("Detaching previous mount...", Colors.YELLOW)
                    detach_result = os.system(f'hdiutil detach "{volume_path}" -force 2>/dev/null')
                    if detach_result != 0:
                        color_print("Warning: Failed to detach previous mount", Colors.YELLOW)
                    time.sleep(2)
        
        # Try mounting up to 3 times
        max_retries = 3
        for attempt in range(max_retries):
            try:
                color_print(f"Mount attempt {attempt + 1}/{max_retries}...", Colors.YELLOW)
                
                # Mount the DMG file with verbose output
                mount_cmd = f'hdiutil attach "{filepath}" -verbose 2>&1'
                mount_output = os.popen(mount_cmd).read()
                
                if "resource busy" in mount_output.lower():
                    if attempt < max_retries - 1:
                        color_print("Resource busy, waiting and retrying...", Colors.YELLOW)
                        time.sleep(3)
                        continue
                    else:
                        color_print(f"\n❌ DMG is still in use. Please try closing any applications using it and try again.", Colors.RED)
                        return None
                
                # Look for /Volumes/ path in the output
                volume_path = None
                for line in mount_output.split('\n'):
                    if '/Volumes/' in line:
                        parts = line.split('/Volumes/')
                        if len(parts) > 1:
                            volume_path = parts[-1].strip()
                            break
                
                if volume_path:
                    # Verify the volume exists
                    full_path = f"/Volumes/{volume_path}"
                    if os.path.exists(full_path):
                        color_print(f"✨ Successfully mounted at: {full_path}", Colors.GREEN)
                        return volume_path
                    else:
                        color_print(f"Warning: Mount path not found: {full_path}", Colors.YELLOW)
                
                if attempt < max_retries - 1:
                    color_print("Mount failed, retrying...", Colors.YELLOW)
                    time.sleep(2)
                else:
                    color_print(f"\nMount output for debugging:", Colors.YELLOW)
                    print(mount_output)
            
            except Exception as mount_error:
                if attempt < max_retries - 1:
                    color_print(f"Mount error: {str(mount_error)}", Colors.YELLOW)
                    time.sleep(2)
                else:
                    color_print(f"\n❌ Failed to mount {app_name}: {str(mount_error)}", Colors.RED)
                    return None
        
        color_print(f"\n❌ Failed to mount {app_name} after {max_retries} attempts.", Colors.RED)
        return None
        
    except Exception as e:
        color_print(f"\nError mounting DMG: {str(e)}", Colors.RED)
        return None

def download_and_install(app: Dict) -> bool:
    """Download and install the selected app."""
    try:
        os.system('clear')
        color_print(f"Installing {app['name']}...\n", Colors.CYAN + Colors.BOLD)
        
        if is_app_installed(app['name']):
            if not get_user_choice(f"{app['name']} is already installed. Would you like to reinstall it? [Y/n]", yes_no=True):
                return False
        
        # Create downloads directory
        downloads_dir = os.path.expanduser('~/Downloads/ZortosHub')
        os.makedirs(downloads_dir, exist_ok=True)
        filepath = os.path.join(downloads_dir, app['filename'])
        
        # Download the file
        if not download_file(app['url'], filepath, app['name']):
            return False
        
        # Mount DMG and show in Finder
        volume_path = mount_dmg(filepath, app['name'])
        if volume_path:
            os.system('clear')
            color_print(f"Installing {app['name']}...\n", Colors.CYAN + Colors.BOLD)
            os.system(f'open "/Volumes/{volume_path}"')
            color_print(f"✨ {app['name']} has been mounted! Follow the installation instructions in Finder.", Colors.GREEN + Colors.BOLD)
            
            # Handle unmounting
            color_print("\nPress Enter to unmount the installer (or 'n' to keep it mounted): ", Colors.CYAN, end='')
            if input().strip().lower() != 'n':
                os.system(f'hdiutil detach "/Volumes/{volume_path}" -force 2>/dev/null')
                color_print(f"✨ {app['name']} installer has been unmounted.", Colors.GREEN)
            return True
            
        color_print(f"\n❌ Failed to mount {app['name']}. Please try again.", Colors.RED + Colors.BOLD)
        return False
        
    except Exception as e:
        color_print(f"\nError: {str(e)}", Colors.RED + Colors.BOLD)
        return False

def get_user_choice(prompt: str, valid_range: Optional[range] = None, yes_no: bool = False) -> Optional[int]:
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

def display_apps(apps: Dict, search_term: Optional[str] = None) -> List[Tuple[str, Dict]]:
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
        
        # Create status indicators
        installed = "✓" if is_app_installed(app['name']) else " "
        status = "🏴‍☠️" if app['status'] == 'cracked' else "💰"
        
        # Print app info
        app_text = f"{installed} {app_id:<20} {app['name']} {status} - {app['description']}"
        if installed == "✓":
            color_print(app_text, Colors.GREEN)
        else:
            print(app_text)
        
        app_list.append((app_id, app))
    
    return app_list

def print_usage() -> None:
    """Print command-line usage information."""
    color_print("\nZortosHub - Mac App Manager", Colors.CYAN + Colors.BOLD)
    color_print("\nCommands:", Colors.YELLOW)
    print("  python main.py                    # Run in interactive mode")
    print("  python main.py install <app_id>   # Install specific app")
    print("  python main.py list               # List all available apps with IDs")
    print("  python main.py help               # Show this help message")
    print("\nExample:")
    print("  python main.py install firefox")

def install_app(app_id: str, interactive: bool = True) -> bool:
    """Install an app by its ID."""
    apps = load_apps()
    if app_id not in apps:
        color_print(f"Error: App '{app_id}' not found.", Colors.RED)
        return False
    
    app = apps[app_id]
    if not interactive:
        return download_and_install(app)
    else:
        if get_user_choice(f"Ready to install {app['name']}? [Y/n]", yes_no=True):
            return download_and_install(app)
    return False

def list_available_apps() -> None:
    """List all available apps with their IDs."""
    apps = load_apps()
    if not apps:
        color_print("\nNo apps available.", Colors.RED)
        return
    
    color_print("\nAvailable Apps:", Colors.CYAN + Colors.BOLD)
    display_apps(apps)

def main() -> None:
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
            apps = load_apps()
            app_list = display_apps(apps)
            if not app_list:
                color_print("\nNo apps available.", Colors.RED)
                continue
            
            app_choice = get_user_choice(f"Select an app [1-{len(app_list)}]", range(1, len(app_list) + 1))
            if not app_choice:
                continue
            
            selected_app = app_list[app_choice - 1][1]
            if get_user_choice(f"Ready to install {selected_app['name']}? [Y/n]", yes_no=True):
                download_and_install(selected_app)
            
        elif choice == 2:
            os.system('clear')
            display_title()
            color_print("\nEnter search term: ", Colors.CYAN, end='')
            search_term = input().strip()
            apps = load_apps()
            display_apps(apps, search_term)
            
        elif choice == 3:
            color_print("\nRefreshing apps list...", Colors.YELLOW)
            load_apps()
            color_print("Apps refreshed!", Colors.GREEN)
            time.sleep(1)
            os.system('clear')
            
        elif choice == 4:
            os.system('clear')
            color_print("\nGoodbye! 👋", Colors.CYAN + Colors.BOLD)
            break
        
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