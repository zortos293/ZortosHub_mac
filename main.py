#!/usr/bin/env python3

import os
import sys
import json
import time
import requests
from PyInquirer import prompt, Separator
from pyfiglet import Figlet
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from tqdm import tqdm
from fuzzywuzzy import fuzz
from termcolor import colored

def load_apps():
    """Load apps from JSON file."""
    try:
        with open('apps.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(colored(f"Error loading apps: {str(e)}", 'red'))
        return {}

def display_title():
    """Display the arcade-style title."""
    os.system('clear')
    f = Figlet(font='slant')
    title = f.renderText('ZortosHub')
    print(colored(title, 'cyan'))
    print(colored('🎮 Your Mac App Arcade 🕹️', 'yellow').center(80))
    print()

def is_app_installed(app_name):
    """Check if an app is already installed."""
    applications_dir = "/Applications"
    app_path = os.path.join(applications_dir, f"{app_name}.app")
    return os.path.exists(app_path)

def create_app_choices(apps, search_term=None):
    """Create choices for the app selection menu."""
    choices = []
    current_category = None
    
    # Sort apps by category and name
    sorted_apps = sorted(apps.items(), key=lambda x: (x[1]['category'], x[1]['name']))
    
    # Filter apps if search term is provided
    if search_term:
        filtered_apps = []
        for app_id, app in sorted_apps:
            name_match = fuzz.partial_ratio(search_term.lower(), app['name'].lower())
            desc_match = fuzz.partial_ratio(search_term.lower(), app['description'].lower())
            if name_match > 60 or desc_match > 60:
                filtered_apps.append((app_id, app))
        sorted_apps = filtered_apps
    
    for app_id, app in sorted_apps:
        if current_category != app['category']:
            current_category = app['category']
            choices.append(Separator(f"\n{colored(current_category, 'cyan')}"))
        
        # Check if app is installed
        installed = is_app_installed(app['name'])
        
        # Create status text
        status_text = ""
        if app['status'] == 'paid':
            status_text = f" {colored('[PAID]', 'green')}"
        elif app['status'] == 'cracked':
            status_text = f" {colored('[CRACKED]', 'yellow')}"
        
        # Create app display name
        installed_mark = colored('✓', 'green') + ' ' if installed else '  '
        app_name = colored(app['name'], attrs=['bold'])
        app_text = f"{installed_mark}{app['icon']} {app_name}{status_text} - {app['description']}"
        
        choices.append({
            'name': app_text,
            'value': app_id
        })
    
    return choices

def download_and_install(app):
    """Download and install the selected app."""
    try:
        if is_app_installed(app['name']):
            if not prompt([{
                'type': 'confirm',
                'name': 'reinstall',
                'message': f"{app['name']} is already installed. Would you like to reinstall it?",
                'default': False
            }])['reinstall']:
                return False
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            
            # Download
            download_task = progress.add_task(f"📥 Downloading {app['name']}...", total=100)
            
            response = requests.get(app['url'], stream=True)
            total_size = int(response.headers.get('content-length', 0))
            
            downloads_dir = os.path.expanduser("~/Downloads")
            filepath = os.path.join(downloads_dir, app['filename'])
            
            downloaded = 0
            with open(filepath, 'wb') as f:
                for data in response.iter_content(chunk_size=4096):
                    size = f.write(data)
                    downloaded += size
                    progress.update(download_task, completed=(downloaded / total_size) * 100 if total_size > 0 else 0)

            # Install
            install_task = progress.add_task(f"💿 Installing {app['name']}...", total=100)
            progress.update(install_task, completed=0)
            
            mount_point = "/Volumes/ZortosHub_temp"

            if filepath.endswith('.dmg'):
                os.system(f"hdiutil attach '{filepath}' -mountpoint '{mount_point}' -nobrowse")
                progress.update(install_task, completed=33)
                
                for root, dirs, files in os.walk(mount_point):
                    for item in dirs + files:
                        if item.endswith('.app'):
                            app_path = os.path.join(root, item)
                            os.system(f"cp -r '{app_path}' /Applications/")
                            progress.update(install_task, completed=66)
                            break
                
                os.system(f"hdiutil detach '{mount_point}' -force")
                progress.update(install_task, completed=100)
            
            # Cleanup
            os.remove(filepath)
            
        print(f"\n{colored('✓', 'green')} {colored(app['name'] + ' installed successfully!', 'green')}")
        return True
        
    except Exception as e:
        print(f"\n{colored('✗', 'red')} {colored('Error: ' + str(e), 'red')}")
        return False

def main():
    """Main application loop."""
    while True:
        display_title()
        
        apps = load_apps()
        if not apps:
            return
        
        # Main menu
        questions = [
            {
                'type': 'list',
                'name': 'action',
                'message': 'Select an action:',
                'choices': [
                    {'name': colored('🎯 Install App', 'green'), 'value': 'install'},
                    {'name': colored('🔍 Search Apps', 'yellow'), 'value': 'search'},
                    {'name': colored('🔄 Refresh Apps', 'blue'), 'value': 'refresh'},
                    {'name': colored('👋 Exit', 'red'), 'value': 'exit'}
                ]
            }
        ]
        
        action = prompt(questions)['action']
        
        if action == 'exit':
            print(f"\n{colored('Thanks for using ZortosHub! 👋', 'yellow')}")
            break
            
        elif action == 'refresh':
            continue
            
        elif action == 'search':
            search_term = prompt([{
                'type': 'input',
                'name': 'term',
                'message': '🔍 Enter search term:'
            }])['term']
            
            app_question = [
                {
                    'type': 'list',
                    'name': 'app_id',
                    'message': '🎯 Select an app to install:',
                    'choices': create_app_choices(apps, search_term)
                }
            ]
            
            app_id = prompt(app_question)['app_id']
            app = apps[app_id]
            
            if prompt([{
                'type': 'confirm',
                'name': 'proceed',
                'message': f"Ready to install {app['name']}?",
                'default': True
            }])['proceed']:
                download_and_install(app)
            
        elif action == 'install':
            app_question = [
                {
                    'type': 'list',
                    'name': 'app_id',
                    'message': '🎯 Select an app to install:',
                    'choices': create_app_choices(apps)
                }
            ]
            
            app_id = prompt(app_question)['app_id']
            app = apps[app_id]
            
            if prompt([{
                'type': 'confirm',
                'name': 'proceed',
                'message': f"Ready to install {app['name']}?",
                'default': True
            }])['proceed']:
                download_and_install(app)
                
                if not prompt([{
                    'type': 'confirm',
                    'name': 'continue',
                    'message': 'Would you like to install another app?',
                    'default': True
                }])['continue']:
                    print(f"\n{colored('Thanks for using ZortosHub! 👋', 'yellow')}")
                    break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{colored('Thanks for using ZortosHub! 👋', 'yellow')}")
        sys.exit(0)