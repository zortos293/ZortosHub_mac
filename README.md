# ZortosHub

A command-line tool for downloading and installing Mac applications directly to your Applications folder.

## Installation

1. Clone this repository
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### List available applications
```bash
python main.py list
```

### Install an application
```bash
python main.py install <app_id>
```

For example, to install Firefox:
```bash
python main.py install firefox
```

## Available Applications

- Firefox
- Google Chrome
- Visual Studio Code

More applications will be added in future updates.

## Features

- Easy to use command-line interface
- Automatic download with progress bar
- Direct installation to Applications folder
- Automatic cleanup after installation

## Requirements

- macOS
- Python 3.6 or higher
- Internet connection
