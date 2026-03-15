# Wrangler Desktop

A modern PySide6 desktop GUI for Cloudflare Workers Wrangler CLI, designed to simplify the development and deployment of Cloudflare Workers with a beautiful, intuitive interface.

**Repository**: https://github.com/taco-jpg/Wrangler-GUI

## ✨ Features

### 🚀 Core Functionality
- **Project Management**: Open and browse Cloudflare Workers projects with integrated file tree
- **Command Execution**: Execute all major `wrangler` commands directly from the GUI
- **Real-time Output**: View command outputs with ANSI color support and live updates
- **Code Editor**: Built-in code editor for editing Worker files with syntax highlighting

### ⚙️ Configuration & Secrets
- **Settings Panel**: Edit `wrangler.toml` configuration directly in the GUI
- **Secrets Management**: Add, delete, and bulk import secrets with a visual interface
- **Account Authentication**: Login/logout to Cloudflare with a single click

### 🔄 Deployment & Version Control
- **Deployment History**: View all deployed versions with timestamps and status
- **One-click Rollback**: Rollback to any previous version with confirmation dialog
- **Dev/Deploy Buttons**: Start development server or deploy with single-click actions

### 📊 Monitoring & Logs
- **Live Tail Logs**: Monitor real-time Worker logs with colored output for different event types
- **Output Panel**: Dedicated panel for command outputs with tabbed interface

### 🎨 User Experience
- **Cloudflare-inspired Dark Theme**: Professional dark theme with orange accent colors
- **Responsive Layout**: Dockable panels, resizable splits, and intuitive navigation
- **System Tray Integration**: Run in background with system tray icon
- **Keyboard Shortcuts**: Common actions accessible via keyboard shortcuts

## 🚀 Quick Start

### Prerequisites
1. **Python 3.13+** (Tested with Python 3.13)
2. **Node.js & npm**: Required for Wrangler CLI
3. **Wrangler CLI**: Install globally via npm:
   ```bash
   npm install -g wrangler
   ```

### Installation & Running
1. **Clone the repository**
   ```bash
   git clone https://github.com/taco-jpg/Wrangler-GUI.git
   cd Wrangler-GUI
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

## 📁 Project Structure

```
Wrangler-GUI/
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── assets/
│   └── style.qss              # Qt stylesheet (Cloudflare dark theme)
├── core/                       # Core business logic
│   ├── config_manager.py      # wrangler.toml configuration management
│   └── processor.py           # Command execution with ANSI-to-HTML conversion
├── ui/                         # PySide6 UI components
│   ├── main_window.py         # Main window with toolbar, file tree, editor
│   ├── welcome_screen.py      # Welcome screen for first-time users
│   ├── settings_panel.py      # Settings and secrets management panel
│   ├── code_editor.py         # Code editor component
│   ├── terminal.py            # Terminal output display
│   ├── theme.py               # Color and font definitions
│   ├── animated_button.py     # Animated button component
│   ├── breathing_dot.py       # Breathing dot animation for status
│   └── add_secret_dialog.py   # Dialog for adding secrets
└── example-worker/            # Example Worker configuration
    └── wrangler.toml          # Example wrangler.toml file
```

## 🛠️ Development

### Technology Stack
- **GUI Framework**: PySide6 (Qt for Python)
- **Language**: Python 3.13+
- **Configuration**: TOML (via `toml` library)
- **Theme**: Qt Style Sheets (QSS) with custom CSS-like syntax

### Key Architecture Patterns
- **Command Pattern**: `CommandManager` class handles all wrangler command execution
- **Model-View-Controller**: Separation between UI components and business logic
- **Signal/Slot**: Qt's event-driven communication between components
- **Dockable UI**: Resizable and dockable panels for flexible workspace

### Module Implementation Status
- ✅ **Module 1**: Secrets management (add, delete, bulk import)
- ✅ **Module 2**: Tail logs with real-time colored output
- ✅ **Module 3**: Version management and rollback functionality
- 🔄 **Future Modules**: Project templates, enhanced keyboard shortcuts, i18n support

## 📋 Usage Guide

### Opening a Project
1. Launch the application
2. Click "Open Project" or use `Cmd+O`
3. Select a directory containing a `wrangler.toml` file
4. The file tree will populate, and settings will load automatically

### Deploying Your Worker
1. Ensure you're logged in (`Settings → Login`)
2. Click the **Deploy** button in the toolbar
3. Watch real-time output in the log panel
4. Check deployment status in the status bar

### Managing Secrets
1. Navigate to **Settings** tab
2. Go to **Secrets** section
3. Use **Add Secret** for single secrets or **Bulk Import** for `.env` files
4. Delete secrets using the delete button next to each entry

### Viewing Deployment History
1. Click the **Versions** button in the toolbar (orange button)
2. A panel will open showing all deployment versions
3. Active versions are highlighted in orange
4. Click **Rollback** on any previous version to revert

### Tailing Logs
1. Click the **Tail** button in the output panel
2. Real-time logs will stream with color-coded events
3. Click again to stop tailing

## 🐛 Troubleshooting

### Common Issues
- **"wrangler command not found"**: Ensure `wrangler` is installed globally (`npm install -g wrangler`)
- **Font issues on macOS**: The app uses system fonts; ensure you have standard fonts installed
- **Permission errors**: Make sure you have write access to the project directory

### Logging
- Application logs are displayed in the output panel
- Command outputs show real-time with ANSI color conversion
- Error messages appear in red with detailed context

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Report bugs**: Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md) with detailed reproduction steps
2. **Suggest features**: Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md) to propose new features
3. **Submit pull requests**: Fork the repo, make changes, and submit a PR

For detailed guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

### Development Setup
```bash
# Clone the repository
git clone https://github.com/taco-jpg/Wrangler-GUI.git
cd Wrangler-GUI

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run in development mode
python main.py
```

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- **Cloudflare** for the amazing Wrangler CLI
- **Qt/PySide6** for the powerful GUI framework
- **All contributors** who help improve this project

---

**Note**: This project is not officially affiliated with Cloudflare. It's a community-built GUI wrapper for the Wrangler CLI.
