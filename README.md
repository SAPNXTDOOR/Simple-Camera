# 📷 Webcam Viewer

A sleek, lightweight, and standalone camera application for Windows. Designed with a modern Windows 11 dark mode aesthetic, this app allows you to easily view your webcam feed, capture high-quality photos, and record videos. 

## ✨ Features

* **Modern UI:** Clean, dark-mode interface designed to blend seamlessly with Windows 11.
* **Smart Hardware Detection:** Automatically scans your camera to only show supported resolutions and framerates (supports up to 4K and 120 FPS, depending on your hardware).
* **Photo Capture:** Snap pictures and save them instantly. Choose between `PNG`, `JPEG`, or `WEBP` formats.
* **Video Recording:** Record camera feeds smoothly. Choose between `MP4` or `WEBM` formats.
* **Custom Save Directory:** easily pick the exact folder where you want your media to be saved.
* **Portable & Standalone:** Available as a single, portable `.exe` file that runs natively on any Windows PC without needing to install Python or external dependencies.
* **Custom Taskbar Integration:** Features native custom icons in the window title, taskbar, and hover preview.

## 🚀 Installation & Usage

### Option 1: Download the Portable Executable (Recommended)
1. Go to the [Releases](../../releases) page of this repository.
2. Download the latest `WebcamViewer.exe`.
3. Double-click to run! No installation or prerequisites required. 
*(Note: Because it is a bundled standalone executable, it may take a few seconds to extract and open on the very first launch).*

### Option 2: Build with Inno Setup (Full Installer)
If you prefer a standard Windows installation wizard:
1. Download `WebcamViewer_Setup.exe` from the Releases page.
2. Run the installer to add the app to your Start Menu, create a Desktop shortcut, and set up an uninstaller.

## 🛠️ Building from Source

If you want to modify the code and build your own executable, follow these steps:

### Prerequisites
* Python 3.8+
* PyQt6 (or your respective UI framework)
* PyInstaller

### Build Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/webcam-viewer.git
   cd webcam-viewer
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```

3. Compile into a single standalone executable:
   ```bash
   pyinstaller --noconsole --onefile --name "WebcamViewer" --icon="icon.ico" --add-data "icon.ico;." main.py
   ```

4. The compiled application will be located in the newly created `dist/` folder as `WebcamViewer.exe`.

## ⚙️ Settings Configuration
Click the **Settings (gear)** icon in the bottom right of the app to:
* Set your default **Save Directory**.
* Change the **Picture Format** (.png, .jpeg, .webp).
* Change the **Video Format** (.mp4, .webm).

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
