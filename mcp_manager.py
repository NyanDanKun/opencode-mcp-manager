"""
OpenCode MCP Manager
Simple GUI to toggle MCP servers on/off in opencode.json
Supports both global (~/.config/opencode/) and local project configs

Design: Y2K Clinical with Light/Dark theme toggle
"""

import json
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import os

VERSION = "0.3.0"

# Config locations
GLOBAL_CONFIG = Path.home() / ".config" / "opencode" / "opencode.json"
LOCAL_CONFIG = Path("opencode.json")

# Color Schemes
COLORS_LIGHT = {
    "bg": "#e8e8e8",
    "window": "#f7f7f7",
    "header": "#ffffff",
    "panel": "#ffffff",
    "text": "#2a2a2a",
    "text_dim": "#888888",
    "border": "#a0a0a0",
    "accent_on": "#2a2a2a",
    "accent_off": "#d0d0d0",
    "accent_glow": "#2a2a2a",
}

COLORS_DARK = {
    "bg": "#0f0f0f",
    "window": "#1a1a1a",
    "header": "#141414",
    "panel": "#222222",
    "text": "#e0e0e0",
    "text_dim": "#5c5c5c",
    "border": "#333333",
    "accent_on": "#00bcd4",
    "accent_off": "#333333",
    "accent_glow": "#00bcd4",
}


class MCPManager:
    def __init__(self, root):
        self.root = root
        self.root.title("MCP Manager")
        self.root.geometry("550x420")
        self.root.resizable(True, True)
        self.root.minsize(400, 300)

        # Theme state
        self.current_theme = "light"
        self.colors = COLORS_LIGHT.copy()

        # Store toggle variables and configs
        self.toggles = {}
        self.buttons = {}
        self.server_rows = []
        self.global_config = {}
        self.local_config = {}
        self.global_modified = 0
        self.local_modified = 0

        # Build UI
        self.build_ui()

        # Load configs
        self.load_configs()

        # Auto-refresh every 2 seconds
        self.check_for_updates()

    def build_ui(self):
        """Build the main UI structure"""
        # Main container
        self.main_frame = tk.Frame(self.root, bg=self.colors["window"])
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Header
        self.header = tk.Frame(self.main_frame, bg=self.colors["header"], height=48)
        self.header.pack(fill=tk.X)
        self.header.pack_propagate(False)

        # Title with square indicator
        title_frame = tk.Frame(self.header, bg=self.colors["header"])
        title_frame.pack(side=tk.LEFT, padx=20, pady=12)

        # Square indicator
        self.indicator = tk.Canvas(
            title_frame,
            width=10,
            height=10,
            bg=self.colors["header"],
            highlightthickness=0,
        )
        self.indicator.create_rectangle(
            0, 0, 10, 10, fill=self.colors["text"], outline="", tags="indicator"
        )
        self.indicator.pack(side=tk.LEFT, padx=(0, 10))

        self.title_label = tk.Label(
            title_frame,
            text="MCP MANAGER",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["header"],
            fg=self.colors["text"],
        )
        self.title_label.pack(side=tk.LEFT)

        # Theme toggle button (right side of header)
        self.theme_btn = tk.Button(
            self.header,
            text="DARK",
            font=("Consolas", 9, "bold"),
            width=6,
            bg=self.colors["panel"],
            fg=self.colors["text_dim"],
            activebackground=self.colors["border"],
            activeforeground=self.colors["text"],
            relief="flat",
            cursor="hand2",
            bd=0,
            command=self.toggle_theme,
        )
        self.theme_btn.pack(side=tk.RIGHT, padx=20)

        # Header separator
        self.header_sep = tk.Frame(self.main_frame, height=1, bg=self.colors["border"])
        self.header_sep.pack(fill=tk.X)

        # Content area
        self.content = tk.Frame(
            self.main_frame, bg=self.colors["window"], padx=25, pady=20
        )
        self.content.pack(fill=tk.BOTH, expand=True)

        # Scrollable frame
        self.canvas = tk.Canvas(
            self.content, bg=self.colors["window"], highlightthickness=0
        )
        self.scrollbar = ttk.Scrollbar(
            self.content, orient="vertical", command=self.canvas.yview
        )
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.colors["window"])

        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw"
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.canvas.pack(side="left", fill="both", expand=True)
        # Scrollbar packed later only if needed

        # Footer
        self.footer = tk.Frame(self.main_frame, bg=self.colors["window"], height=30)
        self.footer.pack(fill=tk.X, padx=25, pady=(0, 10))

        self.status_left = tk.Label(
            self.footer,
            text="SYS.STATUS: NORMAL",
            font=("Consolas", 9),
            bg=self.colors["window"],
            fg=self.colors["text_dim"],
        )
        self.status_left.pack(side=tk.LEFT)

        self.status_right = tk.Label(
            self.footer,
            text=f"v{VERSION}",
            font=("Consolas", 9),
            bg=self.colors["window"],
            fg=self.colors["text_dim"],
        )
        self.status_right.pack(side=tk.RIGHT)

    def _on_frame_configure(self, event):
        """Update scroll region and check if scrollbar needed"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._update_scrollbar()

    def _on_canvas_configure(self, event):
        """Resize canvas window width and check scrollbar"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        self._update_scrollbar()

    def _update_scrollbar(self):
        """Show/hide scrollbar based on content height"""
        self.root.update_idletasks()

        canvas_height = self.canvas.winfo_height()
        content_height = self.scrollable_frame.winfo_reqheight()

        if content_height > canvas_height:
            if not self.scrollbar.winfo_ismapped():
                self.scrollbar.pack(side="right", fill="y")
        else:
            if self.scrollbar.winfo_ismapped():
                self.scrollbar.pack_forget()

    def _on_mousewheel(self, event):
        # Only scroll if scrollbar is visible
        if self.scrollbar.winfo_ismapped():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def toggle_theme(self):
        """Switch between light and dark themes"""
        if self.current_theme == "light":
            self.current_theme = "dark"
            self.colors = COLORS_DARK.copy()
            self.theme_btn.config(text="LIGHT")
        else:
            self.current_theme = "light"
            self.colors = COLORS_LIGHT.copy()
            self.theme_btn.config(text="DARK")

        self.apply_theme()

    def apply_theme(self):
        """Apply current theme colors to all widgets"""
        # Root and main frame
        self.root.configure(bg=self.colors["bg"])
        self.main_frame.configure(bg=self.colors["window"])

        # Header
        self.header.configure(bg=self.colors["header"])
        for widget in self.header.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.configure(bg=self.colors["header"])
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label):
                        child.configure(
                            bg=self.colors["header"], fg=self.colors["text"]
                        )
                    elif isinstance(child, tk.Canvas):
                        child.configure(bg=self.colors["header"])
                        child.delete("indicator")
                        # Use accent color for indicator in dark mode
                        indicator_color = (
                            self.colors["accent_glow"]
                            if self.current_theme == "dark"
                            else self.colors["text"]
                        )
                        child.create_rectangle(
                            0,
                            0,
                            10,
                            10,
                            fill=indicator_color,
                            outline="",
                            tags="indicator",
                        )

        self.title_label.configure(bg=self.colors["header"], fg=self.colors["text"])
        self.indicator.configure(bg=self.colors["header"])

        # Theme button
        self.theme_btn.configure(
            bg=self.colors["panel"],
            fg=self.colors["text_dim"],
            activebackground=self.colors["border"],
            activeforeground=self.colors["text"],
        )

        # Header separator
        self.header_sep.configure(bg=self.colors["border"])

        # Content
        self.content.configure(bg=self.colors["window"])
        self.canvas.configure(bg=self.colors["window"])
        self.scrollable_frame.configure(bg=self.colors["window"])

        # Footer
        self.footer.configure(bg=self.colors["window"])
        self.status_left.configure(bg=self.colors["window"], fg=self.colors["text_dim"])
        self.status_right.configure(
            bg=self.colors["window"], fg=self.colors["text_dim"]
        )

        # Re-render server list with new colors
        self.render_toggles()

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
        total = global_count + local_count
        self.status_left.config(text=f"SYS.STATUS: {total} SERVER(S) LOADED")

    def render_toggles(self):
        """Render toggle switches for each MCP"""
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.toggles.clear()
        self.buttons.clear()
        self.server_rows.clear()

        has_any = False

        # Global MCPs
        global_mcps = self.global_config.get("mcp", {})
        if global_mcps:
            has_any = True
            self.create_section_header("// GLOBAL CONFIG")
            for name, settings in global_mcps.items():
                self.create_server_row(name, settings, "global")

        # Local MCPs
        local_mcps = self.local_config.get("mcp", {})
        if local_mcps:
            has_any = True
            self.create_section_header("// LOCAL CONFIG")
            for name, settings in local_mcps.items():
                self.create_server_row(name, settings, "local")

        if not has_any:
            self.create_section_header("// NO MCP SERVERS FOUND")
            info = tk.Label(
                self.scrollable_frame,
                text=f"Checked paths:\n  {GLOBAL_CONFIG}\n  {LOCAL_CONFIG.absolute()}",
                font=("Consolas", 9),
                bg=self.colors["window"],
                fg=self.colors["text_dim"],
                justify=tk.LEFT,
            )
            info.pack(anchor="w", pady=10)

        # Update scrollbar visibility after rendering
        self.root.after(100, self._update_scrollbar)

    def create_section_header(self, text):
        """Create a section header label"""
        sep_frame = tk.Frame(self.scrollable_frame, bg=self.colors["window"])
        sep_frame.pack(fill="x", pady=(15, 5))

        header = tk.Label(
            sep_frame,
            text=text,
            font=("Consolas", 10),
            bg=self.colors["window"],
            fg=self.colors["text_dim"],
        )
        header.pack(side=tk.LEFT)

    def create_server_row(self, name, settings, scope):
        """Create a styled server row"""
        # Container
        container = tk.Frame(self.scrollable_frame, bg=self.colors["panel"])
        container.pack(fill="x", pady=5)

        # Left accent bar
        accent = tk.Frame(container, width=3, bg=self.colors["text_dim"])
        accent.pack(side=tk.LEFT, fill="y")

        # Content area - use grid for proper expansion
        content = tk.Frame(container, bg=self.colors["panel"], padx=15, pady=12)
        content.pack(side=tk.LEFT, fill="both", expand=True)
        content.columnconfigure(0, weight=1)  # Info column expands
        content.columnconfigure(1, weight=0)  # Button column fixed

        # Server info (left side) - expands
        info_frame = tk.Frame(content, bg=self.colors["panel"])
        info_frame.grid(row=0, column=0, sticky="ew")

        # Server name
        name_label = tk.Label(
            info_frame,
            text=name.upper(),
            font=("Segoe UI", 13, "bold"),
            bg=self.colors["panel"],
            fg=self.colors["text"],
            anchor="w",
        )
        name_label.pack(anchor="w")

        # Meta info - now can expand properly
        mcp_type = settings.get("type", "unknown").upper()
        command = settings.get("command", [])
        cmd_preview = ""
        if command:
            cmd_text = " ".join(command) if isinstance(command, list) else str(command)
            if len(cmd_text) > 50:
                cmd_text = cmd_text[:47] + "..."
            cmd_preview = f" :: {cmd_text}"

        meta_label = tk.Label(
            info_frame,
            text=f"TYPE: {mcp_type}{cmd_preview}",
            font=("Consolas", 9),
            bg=self.colors["panel"],
            fg=self.colors["text_dim"],
            anchor="w",
        )
        meta_label.pack(anchor="w", pady=(3, 0), fill="x")

        # Toggle button (right side) - fixed width
        is_enabled = settings.get("enabled", True)
        key = f"{scope}:{name}"
        self.toggles[key] = is_enabled

        btn_bg = self.colors["accent_on"] if is_enabled else self.colors["accent_off"]
        btn_fg = "#ffffff" if is_enabled else self.colors["text_dim"]

        # Special glow effect for dark theme ON state
        if self.current_theme == "dark" and is_enabled:
            btn_bg = self.colors["accent_glow"]

        toggle_btn = tk.Button(
            content,
            text="ON" if is_enabled else "OFF",
            font=("Consolas", 10, "bold"),
            width=6,
            bg=btn_bg,
            fg=btn_fg,
            activebackground=self.colors["text"]
            if self.current_theme == "light"
            else self.colors["accent_glow"],
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            bd=0,
            command=lambda n=name, s=scope: self.toggle_mcp(n, s),
        )
        toggle_btn.grid(row=0, column=1, padx=(15, 0), sticky="e")
        self.buttons[key] = toggle_btn

        # Store row data for hover effects
        row_data = {
            "container": container,
            "accent": accent,
            "content": content,
            "info_frame": info_frame,
            "name_label": name_label,
            "meta_label": meta_label,
        }
        self.server_rows.append(row_data)

        # Hover effects
        def on_enter(e):
            accent.config(
                bg=self.colors["accent_glow"]
                if self.current_theme == "dark"
                else self.colors["text"]
            )

        def on_leave(e):
            accent.config(bg=self.colors["text_dim"])

        for widget in [container, content, info_frame, name_label, meta_label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

    def toggle_mcp(self, name, scope):
        """Toggle MCP enabled state and save"""
        key = f"{scope}:{name}"
        if key not in self.toggles:
            return

        new_state = not self.toggles[key]
        self.toggles[key] = new_state

        # Update button appearance
        btn = self.buttons[key]

        if new_state:
            btn_bg = (
                self.colors["accent_glow"]
                if self.current_theme == "dark"
                else self.colors["accent_on"]
            )
            btn_fg = "#ffffff"
        else:
            btn_bg = self.colors["accent_off"]
            btn_fg = self.colors["text_dim"]

        btn.config(
            text="ON" if new_state else "OFF",
            bg=btn_bg,
            fg=btn_fg,
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
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)

            if scope == "global":
                self.global_modified = os.path.getmtime(path)
            else:
                self.local_modified = os.path.getmtime(path)

            self.status_left.config(text=f"SYS.STATUS: SAVED TO {scope.upper()}")
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
            self.status_left.config(text="SYS.STATUS: CONFIG RELOADED")

        self.root.after(2000, self.check_for_updates)


def main():
    root = tk.Tk()

    try:
        root.iconbitmap("icon.ico")
    except:
        pass

    app = MCPManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()
