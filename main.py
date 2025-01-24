#!/usr/bin/env python3

import os
import sys
import json
import time
import urllib.request
import urllib.error
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
    """Load apps from all enabled repositories."""
    all_apps = {}
    repositories = load_repositories()
    
    for repo in repositories:
        if not repo.enabled:
            continue
            
        try:
            if repo.url.startswith(('http://', 'https://')):
                with urllib.request.urlopen(repo.url) as response:
                    repo_apps = json.loads(response.read().decode())
            else:
                with open(repo.url, 'r') as f:
                    repo_apps = json.load(f)
                    
            # Add repository information to each app
            for app_id, app_data in repo_apps.items():
                app_data['repository'] = repo.name
                all_apps[app_id] = app_data
                
        except Exception as e:
            color_print(f"Error loading apps from repository '{repo.name}': {str(e)}", Colors.RED)
            
    return all_apps

class Repository:
    def __init__(self, name: str, url: str, enabled: bool = True):
        self.name = name
        self.url = url
        self.enabled = enabled

def load_repositories() -> List[Repository]:
    """Load repositories from repositories.json file."""
    try:
        with open('repositories.json', 'r') as f:
            repos_data = json.load(f)
            return [Repository(**repo) for repo in repos_data]
    except FileNotFoundError:
        # Create default repository file if it doesn't exist
        default_repos = [
            {
                "name": "official",
                "url": "https://raw.githubusercontent.com/zortos293/ZortosHub_mac/main/apps.json",
                "enabled": True
            }
        ]
        with open('repositories.json', 'w') as f:
            json.dump(default_repos, f, indent=4)
        return [Repository(**repo) for repo in default_repos]
    except Exception as e:
        color_print(f"Error loading repositories: {str(e)}", Colors.RED)
        return []

def save_repositories(repositories: List[Repository]) -> bool:
    """Save repositories to repositories.json file."""
    try:
        repos_data = [{"name": repo.name, "url": repo.url, "enabled": repo.enabled} 
                     for repo in repositories]
        with open('repositories.json', 'w') as f:
            json.dump(repos_data, f, indent=4)
        return True
    except Exception as e:
        color_print(f"Error saving repositories: {str(e)}", Colors.RED)
        return False

def add_repository(name: str, url: str) -> bool:
    """Add a new repository."""
    try:
        # Validate URL by trying to fetch it
        try:
            with urllib.request.urlopen(url) as response:
                if response.getcode() != 200:
                    raise ValueError("Invalid repository URL")
                # Try to parse as JSON to validate format
                json.loads(response.read().decode())
        except Exception as e:
            color_print(f"Invalid repository URL or format: {str(e)}", Colors.RED)
            return False

        repositories = load_repositories()
        
        # Check if repository with same name already exists
        if any(repo.name == name for repo in repositories):
            color_print(f"Repository with name '{name}' already exists", Colors.RED)
            return False
            
        repositories.append(Repository(name, url))
        return save_repositories(repositories)
    except Exception as e:
        color_print(f"Error adding repository: {str(e)}", Colors.RED)
        return False

def remove_repository(name: str) -> bool:
    """Remove a repository by name."""
    try:
        repositories = load_repositories()
        repositories = [repo for repo in repositories if repo.name != name]
        return save_repositories(repositories)
    except Exception as e:
        color_print(f"Error removing repository: {str(e)}", Colors.RED)
        return False

def list_repositories() -> None:
    """List all repositories."""
    repositories = load_repositories()
    if not repositories:
        color_print("No repositories configured", Colors.YELLOW)
        return

    color_print("\n📚 Configured Repositories:", Colors.CYAN + Colors.BOLD)
    for repo in repositories:
        status = "✅ Enabled" if repo.enabled else "❌ Disabled"
        color_print(f"\n• {repo.name}", Colors.BLUE + Colors.BOLD)
        color_print(f"  URL: {repo.url}")
        color_print(f"  Status: {status}", Colors.GREEN if repo.enabled else Colors.RED)

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
    """Download a file using urllib with progress tracking and optimized speed."""
    try:
        color_print(f"\n📥 Downloading {app_name}...")
        
        def show_progress(count, block_size, total_size):
            if total_size > 0:
                percent = int(count * block_size * 100 / total_size)
                # Update progress every 5%
                if percent % 5 == 0:
                    os.system('clear')
                    color_print(f"Installing {app_name}...\n", Colors.CYAN + Colors.BOLD)
                    color_print(f"📥 Downloading: {percent}% complete", Colors.YELLOW)
        
        # Create parent directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Create opener with optimized settings
        opener = urllib.request.build_opener()
        opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0'),
            ('Accept', '*/*'),
            ('Connection', 'keep-alive'),
            ('Accept-Encoding', 'gzip, deflate')
        ]
        
        # Set socket timeout and buffer size
        import socket
        socket.setdefaulttimeout(15)  # 15 seconds timeout
        
        # Use a larger buffer size (8MB)
        BLOCK_SIZE = 8 * 1024 * 1024
        
        urllib.request.install_opener(opener)
        
        # Get base URL for handling relative redirects
        base_url = '/'.join(url.split('/')[:-1]) + '/'
        
        # Download with progress tracking
        try:
            # Custom retrieval with larger buffer
            with urllib.request.urlopen(url) as response, open(filepath, 'wb') as out_file:
                total_size = int(response.headers.get('content-length', 0))
                block_count = 0
                while True:
                    block = response.read(BLOCK_SIZE)
                    if not block:
                        break
                    out_file.write(block)
                    block_count += 1
                    show_progress(block_count, BLOCK_SIZE, total_size)
            
            color_print(f"✨ Download complete!", Colors.GREEN)
            return True
            
        except urllib.error.HTTPError as e:
            if e.code == 308:  # Permanent Redirect
                try:
                    # Get the new location
                    new_url = e.headers.get('Location')
                    if new_url:
                        # Handle relative URLs
                        if new_url.startswith('/'):
                            # Get the domain from original URL
                            domain = '/'.join(url.split('/')[:3])
                            new_url = domain + new_url
                        color_print(f"Following redirect to: {new_url}", Colors.YELLOW)
                        
                        # Download from redirect with same optimized settings
                        with urllib.request.urlopen(new_url) as response, open(filepath, 'wb') as out_file:
                            total_size = int(response.headers.get('content-length', 0))
                            block_count = 0
                            while True:
                                block = response.read(BLOCK_SIZE)
                                if not block:
                                    break
                                out_file.write(block)
                                block_count += 1
                                show_progress(block_count, BLOCK_SIZE, total_size)
                        
                        color_print(f"✨ Download complete!", Colors.GREEN)
                        return True
                except Exception as redirect_error:
                    color_print(f"\n❌ Download failed after redirect: {str(redirect_error)}", Colors.RED)
                    return False
            color_print(f"\n❌ Download failed: {str(e)}", Colors.RED)
            return False
        except urllib.error.URLError as e:
            color_print(f"\n❌ Download failed: {str(e)}", Colors.RED)
            return False
            
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
        
        # Check if DMG is already mounted and force detach it
        mounted_volumes = os.popen('hdiutil info').read()
        if filepath in mounted_volumes:
            color_print("Previous mount detected, cleaning up...", Colors.YELLOW)
            # Parse the output to find mounted volumes from our DMG
            current_image = None
            current_volume = None
            for line in mounted_volumes.split('\n'):
                if filepath in line:
                    current_image = True
                elif current_image and '/Volumes/' in line:
                    # This volume belongs to our DMG
                    volume_path = line.split('/Volumes/')[-1].strip()
                    full_path = f"/Volumes/{volume_path}"
                    color_print(f"Detaching: {full_path}", Colors.YELLOW)
                    detach_result = os.system(f'hdiutil detach "{full_path}" -force 2>/dev/null')
                    if detach_result != 0:
                        color_print("Warning: Failed to detach previous mount", Colors.YELLOW)
                    time.sleep(2)
                    break
                elif line.strip() == '':
                    current_image = False
        
        # Mount the DMG file
        mount_cmd = f'hdiutil attach "{filepath}" 2>&1'
        mount_output = os.popen(mount_cmd).read()
        
        # Wait a moment for the volume to appear
        time.sleep(2)
        
        # Parse the mount output to find the volume path
        volume_path = None
        for line in mount_output.split('\n'):
            if '/Volumes/' in line:
                # Extract the volume path after /Volumes/
                parts = line.split('/Volumes/')
                if len(parts) > 1:
                    volume_path = parts[-1].strip()
                    # If we found a path, verify it exists
                    full_path = f"/Volumes/{volume_path}"
                    if os.path.exists(full_path):
                        color_print(f"✨ Successfully mounted at: {full_path}", Colors.GREEN)
                        return volume_path
        
        # If we get here, check for specific errors in the output
        if "resource busy" in mount_output.lower():
            color_print(f"\n❌ DMG is in use. Please try closing any applications using it and try again.", Colors.RED)
        elif "no mountable file systems" in mount_output.lower():
            color_print(f"\n❌ Invalid DMG file: No mountable file systems", Colors.RED)
        elif "image not recognized" in mount_output.lower():
            color_print(f"\n❌ Invalid DMG file: Image not recognized", Colors.RED)
        else:
            color_print(f"\nMount output for debugging:", Colors.YELLOW)
            print(mount_output)
        
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
    color_print("\nUsage:", Colors.CYAN + Colors.BOLD)
    color_print("  python main.py <command> [options]\n")
    color_print("Commands:", Colors.YELLOW)
    color_print("  list                     List all available applications")
    color_print("  install <app_id>         Install an application")
    color_print("  repo list                List configured repositories")
    color_print("  repo add <name> <url>    Add a new repository")
    color_print("  repo remove <name>       Remove a repository")
    color_print("  help                     Show this help message\n")

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
            
            if command == "list":
                list_available_apps()
            elif command == "install" and len(sys.argv) > 2:
                install_app(sys.argv[2])
            elif command == "repo":
                if len(sys.argv) < 3:
                    print_usage()
                else:
                    repo_command = sys.argv[2].lower()
                    if repo_command == "list":
                        list_repositories()
                    elif repo_command == "add" and len(sys.argv) > 4:
                        name = sys.argv[3]
                        url = sys.argv[4]
                        if add_repository(name, url):
                            color_print(f"✨ Repository '{name}' added successfully!", Colors.GREEN)
                    elif repo_command == "remove" and len(sys.argv) > 3:
                        name = sys.argv[3]
                        if remove_repository(name):
                            color_print(f"✨ Repository '{name}' removed successfully!", Colors.GREEN)
                    else:
                        print_usage()
            elif command == "help":
                print_usage()
            else:
                print_usage()
        else:
            main()
    except KeyboardInterrupt:
        color_print("\n\nExiting...", Colors.YELLOW)
        sys.exit(0)
    except Exception as e:
        color_print(f"\nAn error occurred: {str(e)}", Colors.RED)
        sys.exit(1)