import os
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Define the directory for saving videos
DATA_FOLDER = "data"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# Function to upload an MP4
def upload_mp4():
    file_path = filedialog.askopenfilename(filetypes=[("MP4 files", "*.mp4")])
    if not file_path:
        return

    file_name = os.path.basename(file_path)
    destination = os.path.join(DATA_FOLDER, file_name)

    if os.path.exists(destination):
        messagebox.showerror("Error", "File already exists!")
        return

    shutil.copy(file_path, destination)
    messagebox.showinfo("Success", f"Uploaded: {file_name}")

    # Automatically process the video
    process_video(destination)

    # Refresh the file list
    list_videos()

# Function to process an MP4 (runs two scripts)
def process_video(video_path):
    try:
        subprocess.run(["python", "script1.py", video_path], check=True)
        subprocess.run(["python", "script2.py", video_path], check=True)
        messagebox.showinfo("Processing Complete", f"Processed: {os.path.basename(video_path)}")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Processing Error", f"Error processing {video_path}: {e}")

# Function to remove an MP4
def remove_mp4():
    selected_item = video_listbox.selection()
    if not selected_item:
        messagebox.showerror("Error", "No file selected!")
        return

    file_name = video_listbox.item(selected_item, "values")[0]
    file_path = os.path.join(DATA_FOLDER, file_name)

    if os.path.exists(file_path):
        os.remove(file_path)
        messagebox.showinfo("Deleted", f"Removed: {file_name}")
        list_videos()
    else:
        messagebox.showerror("Error", "File not found!")

# Function to list MP4s in the folder
def list_videos():
    video_listbox.delete(*video_listbox.get_children())
    files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".mp4")]

    for file in files:
        video_listbox.insert("", "end", values=[file])

# Function to switch menu
def switch_menu(menu_name):
    for frame in all_frames:
        frame.pack_forget()

    menu_frames[menu_name].pack(fill="both", expand=True)

# Create main window
root = tk.Tk()
root.title("MP4 Manager")
root.geometry("600x400")

# Create a menu bar
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

# Define frames
main_frame = tk.Frame(root)
upload_frame = tk.Frame(root)
delete_frame = tk.Frame(root)

all_frames = [main_frame, upload_frame, delete_frame]
menu_frames = {"Main Menu": main_frame, "Upload Video": upload_frame, "Delete Video": delete_frame}

# Main Menu
tk.Label(main_frame, text="Welcome to MP4 Manager", font=("Arial", 14)).pack(pady=20)
tk.Button(main_frame, text="Upload Video", command=lambda: switch_menu("Upload Video")).pack(pady=5)
tk.Button(main_frame, text="Delete Video", command=lambda: switch_menu("Delete Video")).pack(pady=5)
tk.Button(main_frame, text="Exit", command=root.quit).pack(pady=20)

# Upload Video Menu
tk.Label(upload_frame, text="Upload an MP4 File", font=("Arial", 14)).pack(pady=20)
tk.Button(upload_frame, text="Select MP4", command=upload_mp4).pack(pady=5)
tk.Button(upload_frame, text="Back to Menu", command=lambda: switch_menu("Main Menu")).pack(pady=20)

# Delete Video Menu
tk.Label(delete_frame, text="Delete an MP4 File", font=("Arial", 14)).pack(pady=20)
video_listbox = ttk.Treeview(delete_frame, columns=("File Name"), show="headings")
video_listbox.heading("File Name", text="File Name")
video_listbox.pack(pady=5)
list_videos()

tk.Button(delete_frame, text="Remove Selected", command=remove_mp4).pack(pady=5)
tk.Button(delete_frame, text="Back to Menu", command=lambda: switch_menu("Main Menu")).pack(pady=20)

# Start in the main menu
switch_menu("Main Menu")

# Run the application
root.mainloop()
