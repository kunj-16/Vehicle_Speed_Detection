# Save as dashboard.py
import time
import os
from utils.database import ViolationDatabase
import threading
import tkinter as tk
from tkinter import ttk
import datetime

class ViolationDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Vehicle Violation Dashboard")
        self.root.geometry("800x600")
        
        # Database connectionp
        self.db = ViolationDatabase()
        
        # Create UI elements
        self.create_widgets()
        
        # Start update thread
        self.running = True
        self.update_thread = threading.Thread(target=self.update_data_thread)
        self.update_thread.daemon = True
        self.update_thread.start()
    
    def create_widgets(self):
        # Frame for violation list
        list_frame = ttk.LabelFrame(self.root, text="Recent Violations")
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Treeview for violations
        self.tree = ttk.Treeview(list_frame, columns=("id", "plate", "speed", "limit", "over", "time", "location"))
        self.tree.heading("id", text="ID")
        self.tree.heading("plate", text="License Plate")
        self.tree.heading("speed", text="Speed")
        self.tree.heading("limit", text="Limit")
        self.tree.heading("over", text="Over By")
        self.tree.heading("time", text="Time")
        self.tree.heading("location", text="Location")
        
        # Configure columns
        self.tree.column("#0", width=0, stretch=tk.NO)
        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("plate", width=100)
        self.tree.column("speed", width=70, anchor=tk.CENTER)
        self.tree.column("limit", width=70, anchor=tk.CENTER)
        self.tree.column("over", width=70, anchor=tk.CENTER)
        self.tree.column("time", width=150)
        self.tree.column("location", width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Controls
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        # Refresh button
        refresh_btn = ttk.Button(control_frame, text="Refresh Now", command=self.update_data)
        refresh_btn.pack(side="left", padx=5)
        
        # Auto-refresh toggle
        self.auto_refresh = tk.BooleanVar(value=True)
        auto_cb = ttk.Checkbutton(control_frame, text="Auto Refresh", variable=self.auto_refresh)
        auto_cb.pack(side="left", padx=5)
        
        # Notification log viewer
        log_btn = ttk.Button(control_frame, text="View Notification Log", command=self.show_notification_log)
        log_btn.pack(side="right", padx=5)
    
    def update_data(self):
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get latest violations
        violations = self.db.get_violations(limit=100)
        
        # Insert into tree
        for v in violations:
            over_by = v.speed - v.speed_limit
            timestamp = v.timestamp.strftime("%Y-%m-%d %H:%M:%S") if v.timestamp else "Unknown"
            
            self.tree.insert("", 0, values=(
                v.id, 
                v.license_plate, 
                f"{v.speed:.1f}", 
                f"{v.speed_limit:.1f}", 
                f"+{over_by:.1f}", 
                timestamp, 
                v.location
            ))
        
        # Update status
        self.status_var.set(f"Last updated: {datetime.datetime.now().strftime('%H:%M:%S')} - {len(violations)} violations found")
    
    def update_data_thread(self):
        while self.running:
            if self.auto_refresh.get():
                # Schedule update on the main thread
                self.root.after(0, self.update_data)
            time.sleep(5)  # Update every 5 seconds
    
    def show_notification_log(self):
        log_window = tk.Toplevel(self.root)
        log_window.title("Notification Log")
        log_window.geometry("600x400")
        
        # Text widget for log
        log_text = tk.Text(log_window, wrap=tk.WORD)
        log_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(log_text, command=log_text.yview)
        log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load log content
        log_path = os.path.join("output", "notifications.log")
        if os.path.exists(log_path):
            with open(log_path, "r") as f:
                log_content = f.read()
                log_text.insert(tk.END, log_content)
        else:
            log_text.insert(tk.END, "No notification log found.")
    
    def on_closing(self):
        self.running = False
        self.db.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ViolationDashboard(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()