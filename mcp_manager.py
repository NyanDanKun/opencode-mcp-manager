"""
OpenCode MCP Manager
Simple GUI to toggle MCP servers on/off in opencode.json
Supports both global (~/.config/opencode/) and local project configs
"""

import json
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import os

VERSION = "0.1.0"

# Config locations
GLOBAL_CONFIG = Path.home() / ".config" / "opencode" / "opencode.json"
LOCAL_CONFIG = Path("opencode.json")


class MCPManager:
    def __init__(self, root):
        self.root = root
        self.root.title(f"OpenCode MCP Manager v{VERSION}")
        self.root.geometry("500x400")
        self.root.resizable(True, True)
        self.root.configure(bg="#1e1e1e")

        # Store toggle variables and configs
        self.toggles = {}
        self.global_config = {}
        self.local_config = {}
        self.global_modified = 0
        self.local_modified = 0

        # Style
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Dark.TFrame", background="#1e1e1e")
        self.style.configure(
            "Dark.TLabel",
            background="#1e1e1e",
            foreground="#ffffff",
            font=("Segoe UI", 11),
        )
        self.style.configure(
            "Title.TLabel",
            background="#1e1e1e",
            foreground="#569cd6",
            font=("Segoe UI", 14, "bold"),
        )
        self.style.configure(
            "Section.TLabel",
            background="#1e1e1e",
            foreground="#dcdcaa",
            font=("Segoe UI", 10, "bold"),
        )
        self.style.configure(
            "Status.TLabel",
            background="#1e1e1e",
            foreground="#6a9955",
            font=("Segoe UI", 9),
        )
        self.style.configure(
            "Command.TLabel",
            background="#1e1e1e",
            foreground="#808080",
            font=("Consolas", 8),
        )

        # Main container
        self.main_frame = ttk.Frame(root, style="Dark.TFrame", padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title = ttk.Label(self.main_frame, text="MCP Servers", style="Title.TLabel")
        title.pack(anchor="w", pady=(0, 15))

        # Scrollable frame for MCPs
        self.canvas = tk.Canvas(self.main_frame, bg="#1e1e1e", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(
            self.main_frame, orient="vertical", command=self.canvas.yview
        )
        self.scrollable_frame = ttk.Frame(self.canvas, style="Dark.TFrame")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(
            root, textvariable=self.status_var, style="Status.TLabel"
        )
        self.status_label.pack(side="bottom", fill="x", padx=10, pady=5)

        # Load configs
        self.load_configs()

        # Auto-refresh every 2 seconds
        self.check_for_updates()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def load_config_file(self, path):
        """Load a single config file"""
        if not path.exists():
            return {}, 0
        try:
            modified = os.path.getmtime(path)
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f), modified
        except (json.JSONDecodeError, Exception):
            return {}, 0

    def load_configs(self):
        """Load both global and local configs"""
        self.global_config, self.global_modified = self.load_config_file(GLOBAL_CONFIG)
        self.local_config, self.local_modified = self.load_config_file(LOCAL_CONFIG)

        self.render_toggles()

        global_count = len(self.global_config.get("mcp", {}))
        local_count = len(self.local_config.get("mcp", {}))
        self.status_var.set(f"Global: {global_count} | Local: {local_count} server(s)")

    def render_toggles(self):
        """Render toggle switches for each MCP"""
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.toggles.clear()

        has_any = False

        # Global MCPs
        global_mcps = self.global_config.get("mcp", {})
        if global_mcps:
            has_any = True
            section = ttk.Label(
                self.scrollable_frame,
                text=f"Global ({GLOBAL_CONFIG.parent})",
                style="Section.TLabel",
            )
            section.pack(anchor="w", pady=(5, 10))

            for name, settings in global_mcps.items():
                self.create_toggle_row(name, settings, "global")

        # Local MCPs
        local_mcps = self.local_config.get("mcp", {})
        if local_mcps:
            has_any = True
            section = ttk.Label(
                self.scrollable_frame,
                text=f"Local ({Path.cwd()})",
                style="Section.TLabel",
            )
            section.pack(anchor="w", pady=(15, 10))

            for name, settings in local_mcps.items():
                self.create_toggle_row(name, settings, "local")

        if not has_any:
            no_mcp = ttk.Label(
                self.scrollable_frame,
                text="No MCP servers found\n\nChecked:\n"
                + f"  Global: {GLOBAL_CONFIG}\n"
                + f"  Local: {LOCAL_CONFIG.absolute()}",
                style="Dark.TLabel",
            )
            no_mcp.pack(pady=20)

    def create_toggle_row(self, name, settings, scope):
        """Create a row with MCP name, details and toggle"""
        # Container for the MCP entry
        container = ttk.Frame(self.scrollable_frame, style="Dark.TFrame")
        container.pack(fill="x", pady=4)

        # Main row
        row_frame = ttk.Frame(container, style="Dark.TFrame")
        row_frame.pack(fill="x")

        # MCP name
        name_label = ttk.Label(row_frame, text=name, style="Dark.TLabel", width=20)
        name_label.pack(side="left")

        # Toggle switch
        is_enabled = settings.get("enabled", True)
        key = f"{scope}:{name}"
        var = tk.BooleanVar(value=is_enabled)
        self.toggles[key] = var

        toggle_btn = tk.Button(
            row_frame,
            text="ON" if is_enabled else "OFF",
            bg="#4ec9b0" if is_enabled else "#d16969",
            fg="#1e1e1e",
            font=("Segoe UI", 9, "bold"),
            width=5,
            relief="flat",
            cursor="hand2",
            command=lambda n=name, s=scope: self.toggle_mcp(n, s),
        )
        toggle_btn.pack(side="right", padx=5)
        var.button = toggle_btn

        # Type label
        mcp_type = settings.get("type", "unknown")
        type_label = ttk.Label(row_frame, text=f"[{mcp_type}]", style="Status.TLabel")
        type_label.pack(side="right", padx=10)

        # Command details (second line)
        command = settings.get("command", [])
        if command:
            cmd_text = " ".join(command) if isinstance(command, list) else str(command)
            if len(cmd_text) > 60:
                cmd_text = cmd_text[:57] + "..."
            cmd_label = ttk.Label(
                container, text=f"  → {cmd_text}", style="Command.TLabel"
            )
            cmd_label.pack(anchor="w", padx=(20, 0))

    def toggle_mcp(self, name, scope):
        """Toggle MCP enabled state and save"""
        key = f"{scope}:{name}"
        if key not in self.toggles:
            return

        var = self.toggles[key]
        new_state = not var.get()
        var.set(new_state)

        # Update button appearance
        var.button.config(
            text="ON" if new_state else "OFF", bg="#4ec9b0" if new_state else "#d16969"
        )

        # Update correct config
        if scope == "global":
            config = self.global_config
            path = GLOBAL_CONFIG
        else:
            config = self.local_config
            path = LOCAL_CONFIG

        if "mcp" in config and name in config["mcp"]:
            config["mcp"][name]["enabled"] = new_state
            self.save_config(config, path, scope)

    def save_config(self, config, path, scope):
        """Save config back to file"""
        try:
            # Ensure directory exists for global config
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)

            # Update modification time
            if scope == "global":
                self.global_modified = os.path.getmtime(path)
            else:
                self.local_modified = os.path.getmtime(path)

            self.status_var.set(f"Saved to {scope}!")
            self.root.after(2000, self.load_configs)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")

    def check_for_updates(self):
        """Check if files were modified externally"""
        reload_needed = False

        if GLOBAL_CONFIG.exists():
            current = os.path.getmtime(GLOBAL_CONFIG)
            if current > self.global_modified:
                reload_needed = True

        if LOCAL_CONFIG.exists():
            current = os.path.getmtime(LOCAL_CONFIG)
            if current > self.local_modified:
                reload_needed = True

        if reload_needed:
            self.load_configs()
            self.status_var.set("Config reloaded (external change)")

        self.root.after(2000, self.check_for_updates)


def main():
    root = tk.Tk()

    # Set icon if available
    try:
        root.iconbitmap("icon.ico")
    except:
        pass

    app = MCPManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()
