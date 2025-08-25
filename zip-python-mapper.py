import os
import re
import datetime
from tkinter import Tk, filedialog

def extract_py_details(file_path):
    with open(file_path, 'r') as file:
        content = file.read()

        function_pattern = re.compile(r'def\s+(\w+)')
        class_pattern = re.compile(r'class\s+(\w+)')

        functions = re.findall(function_pattern, content)
        classes = re.findall(class_pattern, content)

        return {
            'file': file_path,
            'functions': functions,
            'classes': classes
        }

def extract_other_files(file_path):
    with open(file_path, 'r') as file:
        content = file.read()

    return {
        'file': file_path,
        'content': content
    }

def create_and_save_summary(folder_path):
    py_files = []
    other_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith('.py') and os.path.getsize(file_path) > 0:
                py_files.append(file_path)
            elif file in ['Dockerfile', 'docker-compose.yml', 'requirements.txt']:
                other_files.append(file_path)

    py_details = [extract_py_details(file) for file in py_files]
    other_file_details = [extract_other_files(file) for file in other_files]

    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    output_file_path = os.path.join(folder_path, f'map-{timestamp}.txt')

    with open(output_file_path, 'w') as summary_file:
        # Include the script's own file name
        script_file_name = os.path.basename(__file__)
        summary_file.write(f"---\nScript File: {script_file_name}\n---\n\n")

        for detail in py_details:
            summary_file.write(f"---\nFile: {detail['file']}\n---\n")
            summary_file.write(f"Functions: {', '.join(detail['functions']) if detail['functions'] else 'None'}\n")
            summary_file.write(f"Classes: {', '.join(detail['classes']) if detail['classes'] else 'None'}\n")
            summary_file.write("\nContents:\n")

            with open(detail['file'], 'r') as file:
                for line in file:
                    summary_file.write(line)
            
            summary_file.write("\n\n")
        
        for detail in other_file_details:
            summary_file.write(f"---\nFile: {detail['file']}\n---\n")
            summary_file.write("\nContents:\n")
            summary_file.write(detail['content'])
            summary_file.write("\n\n")

def select_folder():
    root = Tk()
    root.withdraw()  # Hide the main window

    # Start the file dialog one folder above where the script is running
    initial_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    folder_path = filedialog.askdirectory(initialdir=initial_dir)
    root.destroy()
    return folder_path

# Example usage
folder_path = select_folder()
if folder_path:
    create_and_save_summary(folder_path)
else:
    print("No folder selected.")
