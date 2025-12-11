# File Structure Creator

A GUI tool to visualize folder structures, search files, and save the structure as text files.

Made by .nikye. on Discord

## What it does

1. Shows folder trees with nice formatting
2. Lets you search for files by name or pattern
3. Saves the structure to a text file
4. Has a progress bar so you know it's working

## Requirements

- Python 3.7 or newer
- Tkinter (comes with Python on Windows, needs install on Linux/Mac)

### Install Tkinter if needed:

On Ubuntu/Debian:
sudo apt-get install python3-tk

text

On macOS:
brew install python-tk

text

On Windows: It's already there.

## How to install

1. Download the file_structure_creator.py file
2. Open terminal or command prompt
3. Go to where you saved the file
4. Run: python file_structure_creator.py

That's it. No extra packages to install.

## How to use

### Basic use

1. Run the program
2. Click "Select Folder" button
3. Pick any folder on your computer
4. The folder tree shows up automatically

### Options

- Show hidden files: Check this to see files starting with . (like .git)
- Max depth: How many folder levels to show. "Unlimited" shows everything.
- Exclude patterns: Things to skip. Default: .git, __pycache__, node_modules

### Search files

1. Select a folder first
2. Type what you want to find in the search box
3. Click "Search Files"
4. Results show in the Search Results tab

Search examples:
- *.py = all Python files
- test* = files starting with "test"
- config = files with "config" in the name
- main.* = files named main with any ending

In the search results, double-click any file to open its folder.

### Save the structure

1. Generate a tree first (select a folder)
2. Click "Save Structure As..."
3. Pick where to save and what to name it
4. It saves as a .txt file with the tree and info

## What the colors mean

- Blue = folders
- Green = Python files (.py)
- Orange = JavaScript files (.js, .ts)
- Red = HTML files (.html)
- Purple = CSS files (.css)
- Dark blue = Markdown files (.md)
- Brown = config files (.json, .yaml, .ini)

## If something goes wrong

"ModuleNotFoundError: No module named 'tkinter'"
- Install tkinter using the commands above

Program is slow with big folders:
- Use "Max depth" to limit how deep it goes
- Add more things to "Exclude patterns"

Permission errors:
- Shows "[Permission Denied]" for folders you can't access
- Keeps going with other folders

## Credits

Made by .nikye. on Discord
GitHub: https://github.com/nikyebabft

No license.
