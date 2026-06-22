# ==========================================================
# ECOCLEAN SL
# Smart Waste Management & Collection Tracking System
# PROG103 Final Project
#
# v2 changes:
#   - Role-based access control (Administrator / Supervisor / Operator)
#     each see a different sidebar and a different set of pages
#   - Input validation for phone number and quantity
#   - Status + priority filters on the Collection Queue
#   - Click-to-sort columns on Queue / Search / Activity Log tables
#   - "Assigned To" field for collector/team assignment
#   - Overdue tracking (Pending requests older than OVERDUE_DAYS)
#   - Total KG Collected metric + simple waste-type breakdown chart
#   - Activity log now records WHICH user performed each action
#   - Empty-state messages instead of blank tables
#   - Safer (atomic) JSON saving
# ==========================================================
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import csv
import os
from datetime import datetime
# ==========================================================
# APPLICATION SETTINGS
# ==========================================================
APP_TITLE = "EcoClean SL - Smart Waste Management System"
DATA_FILE = "data.json"
WINDOW_BG = "#ECF0F1"
PRIMARY_COLOR = "#145A32"
SECONDARY_COLOR = "#196F3D"
ACCENT_COLOR = "#F4D03F"
OVERDUE_DAYS = 3
# ==========================================================
# SYSTEM LISTS
# ==========================================================
WASTE_TYPES = [
    "Household",
    "Plastic",
    "Organic",
    "Electronic",
    "Construction"
]
PRIORITY_LEVELS = [
    "Normal",
    "Urgent"
]
STATUS_OPTIONS = [
    "Pending",
    "Assigned",
    "Collected",
    "Completed"
]
STATUS_FILTER_OPTIONS = ["All"] + STATUS_OPTIONS
PRIORITY_FILTER_OPTIONS = ["All"] + PRIORITY_LEVELS
# ==========================================================
# USER ACCOUNTS
# ==========================================================
# NOTE: USER_ACCOUNTS is mutable at runtime (accounts can be added or
# removed by an Administrator via the User Management page) and is
# persisted to data.json alongside requests/activity_log so changes
# survive a restart.
# ==========================================================
USER_ACCOUNTS = {
    "admin": {
        "password": "admin123",
        "role": "Administrator"
    },
    "supervisor": {
        "password": "eco2026",
        "role": "Supervisor"
    },
    "operator": {
        "password": "waste123",
        "role": "Operator"
    }
}
# ==========================================================
# ROLE-BASED ACCESS CONTROL
# ==========================================================
ROLE_PERMISSIONS = {
    "Administrator": {"dashboard", "register", "queue", "search", "status", "reports", "activity", "users", "audit"},
    "Supervisor":     {"dashboard", "register", "queue", "search", "status", "reports"},
    "Operator":       {"dashboard", "register", "queue", "search", "status"}
}
ROLE_OPTIONS = ["Administrator", "Supervisor", "Operator"]
ROLE_BADGE_COLOR = {
    "Administrator": "#F4D03F",
    "Supervisor": "#85C1E9",
    "Operator": "#D5DBDB"
}
NAV_PAGES = [
    ("dashboard", "Dashboard"),
    ("register", "Register Request"),
    ("queue", "Collection Queue"),
    ("search", "Search Records"),
    ("status", "Update Status"),
    ("reports", "Reports"),
    ("activity", "Activity Log"),
    ("users", "User Management"),
    ("audit", "Staff Audit")
]
# ==========================================================
# GLOBAL DATA
# ==========================================================
requests_data = []
activity_log = []
next_id = [1]
# ==========================================================
# SAVE DATA (atomic write so a crash mid-save can't corrupt the file)
# ==========================================================
def save_data():
    try:
        data = {
            "requests": requests_data,
            "activity_log": activity_log,
            "next_id": next_id[0],
            "user_accounts": USER_ACCOUNTS
        }
        temp_path = DATA_FILE + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        os.replace(temp_path, DATA_FILE)
    except Exception as error:
        print("Save Error:", error)
# ==========================================================
# LOAD DATA
# ==========================================================
def load_data():
    global requests_data
    global activity_log
    if not os.path.exists(DATA_FILE):
        return
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        requests_data[:] = data.get("requests", [])
        activity_log[:] = data.get("activity_log", [])
        next_id[0] = data.get("next_id", 1)
        saved_accounts = data.get("user_accounts")
        if saved_accounts:
            USER_ACCOUNTS.clear()
            USER_ACCOUNTS.update(saved_accounts)
    except Exception as error:
        print("Load Error:", error)
# ==========================================================
# ACTIVITY LOGGER
# ==========================================================
def log_activity(request_id, resident_name, action, performed_by="Unknown"):
    activity_log.append({
        "request_id": request_id,
        "resident_name": resident_name,
        "action": action,
        "performed_by": performed_by,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_data()
# ==========================================================
# GENERATE REQUEST ID
# ==========================================================
def generate_request_id():
    request_id = f"WM{next_id[0]:04d}"
    next_id[0] += 1
    return request_id
# ==========================================================
# VALIDATION HELPERS
# ==========================================================
def is_valid_phone(phone):
    digits = "".join(ch for ch in phone if ch.isdigit())
    return len(digits) >= 7
def is_valid_quantity(quantity_str):
    try:
        value = float(quantity_str)
        return value > 0
    except ValueError:
        return False
def is_overdue(record):
    if record.get("status") != "Pending":
        return False
    try:
        record_date = datetime.strptime(record["date"], "%Y-%m-%d")
    except (ValueError, KeyError):
        return False
    return (datetime.now() - record_date).days >= OVERDUE_DAYS
# ==========================================================
# REGISTER REQUEST
# ==========================================================
def register_request(resident_name, phone, community, waste_type, quantity, priority, performed_by="Unknown"):
    resident_name = resident_name.strip()
    phone = phone.strip()
    community = community.strip()
    quantity = quantity.strip()
    if resident_name == "":
        return False, "Resident name is required."
    if phone == "":
        return False, "Phone number is required."
    if not is_valid_phone(phone):
        return False, "Phone number must contain at least 7 digits."
    if community == "":
        return False, "Community is required."
    if quantity == "":
        return False, "Quantity is required."
    if not is_valid_quantity(quantity):
        return False, "Quantity must be a positive number (e.g. 12.5)."
    request_id = generate_request_id()
    now = datetime.now()
    record = {
        "id": request_id,
        "name": resident_name,
        "phone": phone,
        "community": community,
        "waste_type": waste_type,
        "quantity": quantity,
        "priority": priority,
        "status": "Pending",
        "assigned_to": "",
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S")
    }
    requests_data.append(record)
    log_activity(request_id, resident_name, "New Waste Collection Request Registered", performed_by)
    save_data()
    return True, f"{request_id} registered successfully."
# ==========================================================
# SEARCH REQUESTS
# ==========================================================
def search_requests(keyword):
    keyword = keyword.lower().strip()
    results = []
    for record in requests_data:
        if (
            keyword in record["id"].lower()
            or keyword in record["name"].lower()
            or keyword in record["phone"].lower()
            or keyword in record["community"].lower()
        ):
            results.append(record)
    return results
# ==========================================================
# GET REQUEST BY ID
# ==========================================================
def get_request_by_id(request_id):
    for record in requests_data:
        if record["id"] == request_id:
            return record
    return None
# ==========================================================
# UPDATE STATUS (optionally also sets/updates the assigned collector)
# ==========================================================
def update_request_status(request_id, new_status, performed_by="Unknown", assigned_to=None):
    for record in requests_data:
        if record["id"] == request_id:
            old_status = record["status"]
            record["status"] = new_status
            action_message = f"Status Changed: {old_status} -> {new_status}"
            if assigned_to:
                record["assigned_to"] = assigned_to
                action_message += f" (Assigned to {assigned_to})"
            log_activity(request_id, record["name"], action_message, performed_by)
            save_data()
            return True
    return False
# ==========================================================
# DELETE REQUEST (Administrator only - enforced at the GUI layer)
# ==========================================================
def delete_request(request_id, performed_by="Unknown"):
    for index, record in enumerate(requests_data):
        if record["id"] == request_id:
            resident_name = record["name"]
            requests_data.pop(index)
            log_activity(request_id, resident_name, "Request Deleted From System", performed_by)
            save_data()
            return True
    return False
# ==========================================================
# DASHBOARD STATISTICS
# ==========================================================
def get_dashboard_statistics():
    total = len(requests_data)
    pending = 0
    assigned = 0
    collected = 0
    completed = 0
    urgent = 0
    overdue = 0
    total_kg_completed = 0.0
    for record in requests_data:
        status = record["status"]
        if status == "Pending":
            pending += 1
        elif status == "Assigned":
            assigned += 1
        elif status == "Collected":
            collected += 1
        elif status == "Completed":
            completed += 1
            try:
                total_kg_completed += float(record["quantity"])
            except (ValueError, TypeError):
                pass
        if record["priority"] == "Urgent":
            urgent += 1
        if is_overdue(record):
            overdue += 1
    return {
        "total": total,
        "pending": pending,
        "assigned": assigned,
        "collected": collected,
        "completed": completed,
        "urgent": urgent,
        "overdue": overdue,
        "total_kg_completed": total_kg_completed
    }
# ==========================================================
# USER ACCOUNT MANAGEMENT (Administrator only)
# ==========================================================
def count_administrators():
    return sum(1 for account in USER_ACCOUNTS.values() if account["role"] == "Administrator")
def create_user_account(username, password, role, performed_by="Unknown"):
    username = username.strip()
    password = password.strip()
    if username == "":
        return False, "Username is required."
    if password == "":
        return False, "Password is required."
    if len(password) < 4:
        return False, "Password must be at least 4 characters."
    if username in USER_ACCOUNTS:
        return False, f"Username '{username}' already exists."
    if role not in ROLE_OPTIONS:
        return False, "Invalid role selected."
    USER_ACCOUNTS[username] = {"password": password, "role": role}
    log_activity("-", username, f"User Account Created (Role: {role})", performed_by)
    save_data()
    return True, f"Account '{username}' created successfully."
def delete_user_account(username, performed_by="Unknown"):
    if username not in USER_ACCOUNTS:
        return False, "Account not found."
    if username == performed_by:
        return False, "You cannot delete your own account while logged in."
    if USER_ACCOUNTS[username]["role"] == "Administrator" and count_administrators() <= 1:
        return False, "Cannot delete the last remaining Administrator account."
    del USER_ACCOUNTS[username]
    log_activity("-", username, "User Account Deleted", performed_by)
    save_data()
    return True, f"Account '{username}' deleted successfully."
def change_user_role(username, new_role, performed_by="Unknown"):
    if username not in USER_ACCOUNTS:
        return False, "Account not found."
    if new_role not in ROLE_OPTIONS:
        return False, "Invalid role selected."
    old_role = USER_ACCOUNTS[username]["role"]
    if old_role == "Administrator" and new_role != "Administrator" and count_administrators() <= 1:
        return False, "Cannot change the role of the last remaining Administrator."
    USER_ACCOUNTS[username]["role"] = new_role
    log_activity("-", username, f"Role Changed: {old_role} -> {new_role}", performed_by)
    save_data()
    return True, f"'{username}' role changed to {new_role}."
# ==========================================================
# STAFF PERFORMANCE / AUDIT STATISTICS
# ==========================================================
def get_staff_statistics():
    stats = {}
    for username in USER_ACCOUNTS:
        stats[username] = {
            "role": USER_ACCOUNTS[username]["role"],
            "requests_registered": 0,
            "status_updates": 0,
            "total_actions": 0
        }
    for log in activity_log:
        performer = log.get("performed_by", "Unknown")
        if performer not in stats:
            stats[performer] = {
                "role": "Unknown / Removed",
                "requests_registered": 0,
                "status_updates": 0,
                "total_actions": 0
            }
        stats[performer]["total_actions"] += 1
        action = log.get("action", "")
        if "Registered" in action:
            stats[performer]["requests_registered"] += 1
        elif "Status Changed" in action:
            stats[performer]["status_updates"] += 1
    return stats
def get_activity_by_user(username):
    return [log for log in activity_log if log.get("performed_by", "Unknown") == username]
# ==========================================================
# DAILY REPORT GENERATOR
# ==========================================================
def generate_daily_report():
    stats = get_dashboard_statistics()
    report = []
    report.append("=" * 60)
    report.append(" ECOCLEAN SL DAILY REPORT ")
    report.append("=" * 60)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    report.append(f"Total Requests: {stats['total']}")
    report.append(f"Pending Requests: {stats['pending']}")
    report.append(f"Assigned Requests: {stats['assigned']}")
    report.append(f"Collected Requests: {stats['collected']}")
    report.append(f"Completed Requests: {stats['completed']}")
    report.append(f"Urgent Requests: {stats['urgent']}")
    report.append(f"Overdue Requests (Pending {OVERDUE_DAYS}+ days): {stats['overdue']}")
    report.append(f"Total KG Collected (Completed): {stats['total_kg_completed']:.1f} KG")
    report.append("")
    report.append("RECENT ACTIVITY")
    report.append("-" * 60)
    for item in activity_log[-15:]:
        report.append(
            f"{item['timestamp']} | {item['request_id']} | "
            f"{item['resident_name']} | by {item.get('performed_by', 'Unknown')} | "
            f"{item['action']}"
        )
    return "\n".join(report)
# ==========================================================
# EXPORT REPORT
# ==========================================================
def export_report(filepath):
    report = generate_daily_report()
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(report)
# ==========================================================
# EXPORT CSV
# ==========================================================
def export_csv(filepath):
    with open(filepath, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "Request ID", "Resident Name", "Phone Number", "Community",
            "Waste Type", "Quantity", "Priority", "Status", "Assigned To",
            "Date", "Time"
        ])
        for record in requests_data:
            writer.writerow([
                record["id"], record["name"], record["phone"], record["community"],
                record["waste_type"], record["quantity"], record["priority"],
                record["status"], record.get("assigned_to", ""),
                record["date"], record["time"]
            ])
# ==========================================================
# LOAD SAVED DATA ON STARTUP
# ==========================================================
load_data()
# =============================================================================
# LOGIN WINDOW
# =============================================================================
class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("EcoClean SL Login")
        self.root.geometry("1000x600")
        self.root.configure(bg=PRIMARY_COLOR)
        self.root.resizable(False, False)
        left_panel = tk.Frame(root, bg=PRIMARY_COLOR, width=500)
        left_panel.pack(side="left", fill="both")
        left_panel.pack_propagate(False)
        tk.Label(
            left_panel, text="\u267b", font=("Segoe UI", 80),
            bg=PRIMARY_COLOR, fg="white"
        ).pack(pady=(70, 10))
        tk.Label(
            left_panel, text="ECOCLEAN SL", font=("Segoe UI", 28, "bold"),
            bg=PRIMARY_COLOR, fg="white"
        ).pack()
        tk.Label(
            left_panel, text="SMART WASTE MANAGEMENT\n& COLLECTION TRACKING SYSTEM",
            font=("Segoe UI", 15), bg=PRIMARY_COLOR, fg=ACCENT_COLOR, justify="center"
        ).pack(pady=20)
        tk.Label(
            left_panel, text="PROG103 FINAL PROJECT", font=("Segoe UI", 12, "bold"),
            bg=PRIMARY_COLOR, fg="white"
        ).pack(pady=5)
        tk.Label(
            left_panel, text="Faculty of ICT\nLimkokwing University",
            font=("Segoe UI", 11), bg=PRIMARY_COLOR, fg="white", justify="center"
        ).pack()
        tk.Label(
            left_panel, text="Supporting SDG 11:\nSustainable Cities & Communities",
            font=("Segoe UI", 11), bg=PRIMARY_COLOR, fg="#AED6F1", justify="center"
        ).pack(pady=40)
        right_panel = tk.Frame(root, bg="white")
        right_panel.pack(side="right", fill="both", expand=True)
        login_frame = tk.Frame(right_panel, bg="white")
        login_frame.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(
            login_frame, text="LOGIN", font=("Segoe UI", 26, "bold"),
            bg="white", fg=PRIMARY_COLOR
        ).grid(row=0, column=0, columnspan=2, pady=20)
        tk.Label(
            login_frame, text="Username", font=("Segoe UI", 11), bg="white"
        ).grid(row=1, column=0, sticky="w", pady=10)
        self.username_entry = tk.Entry(login_frame, width=30, font=("Segoe UI", 12))
        self.username_entry.grid(row=2, column=0, pady=5)
        tk.Label(
            login_frame, text="Password", font=("Segoe UI", 11), bg="white"
        ).grid(row=3, column=0, sticky="w", pady=10)
        self.password_entry = tk.Entry(
            login_frame, width=30, show="*", font=("Segoe UI", 12)
        )
        self.password_entry.grid(row=4, column=0, pady=5)
        self.password_entry.bind("<Return>", lambda event: self.login())
        self.login_button = tk.Button(
            login_frame, text="LOGIN", width=25, bg=PRIMARY_COLOR, fg="white",
            font=("Segoe UI", 11, "bold"), cursor="hand2", command=self.login
        )
        self.login_button.grid(row=5, column=0, pady=25)
        self.result_label = tk.Label(
            login_frame, text="", bg="white", fg="red", font=("Segoe UI", 10)
        )
        self.result_label.grid(row=6, column=0)
        info_frame = tk.LabelFrame(
            right_panel, text="Demo Accounts", bg="white", fg=PRIMARY_COLOR,
            font=("Segoe UI", 10, "bold")
        )
        info_frame.place(relx=0.5, rely=0.85, anchor="center")
        tk.Label(
            info_frame, text="Admin : admin / admin123  (full access + audit log)",
            bg="white", font=("Segoe UI", 9)
        ).pack(anchor="w", padx=10)
        tk.Label(
            info_frame, text="Supervisor : supervisor / eco2026  (no audit log)",
            bg="white", font=("Segoe UI", 9)
        ).pack(anchor="w", padx=10)
        tk.Label(
            info_frame, text="Operator : operator / waste123  (no reports/audit log)",
            bg="white", font=("Segoe UI", 9)
        ).pack(anchor="w", padx=10)
    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if username == "" or password == "":
            self.result_label.config(text="Please enter username and password.")
            return
        if username not in USER_ACCOUNTS:
            self.result_label.config(text="Invalid username.")
            return
        if USER_ACCOUNTS[username]["password"] != password:
            self.result_label.config(text="Incorrect password.")
            return
        role = USER_ACCOUNTS[username]["role"]
        messagebox.showinfo("Login Successful", f"Welcome {username}\nRole: {role}")
        self.root.destroy()
        dashboard_root = tk.Tk()
        EcoCleanApp(dashboard_root, username, role)
        dashboard_root.mainloop()
# =============================================================================
# MAIN APPLICATION CLASS
# =============================================================================
class EcoCleanApp:
    def __init__(self, root, username, role):
        self.root = root
        self.username = username
        self.role = role
        self.root.title(APP_TITLE)
        try:
            self.root.state("zoomed")
        except tk.TclError:
            self.root.geometry("1300x800")
        self.root.configure(bg=WINDOW_BG)
        self.build_header()
        self.body_frame = tk.Frame(self.root, bg=WINDOW_BG)
        self.body_frame.pack(fill="both", expand=True)
        self.build_sidebar()
        self.build_main_area()
        self.update_clock()
    def has_access(self, page_key):
        return page_key in ROLE_PERMISSIONS.get(self.role, set())
    def access_denied(self):
        messagebox.showerror(
            "Access Denied",
            "Your account role does not have permission to view this page."
        )
    def build_header(self):
        self.header = tk.Frame(self.root, bg=PRIMARY_COLOR, height=80)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)
        tk.Label(
            self.header, text="\u267b ECOCLEAN SL", font=("Segoe UI", 22, "bold"),
            bg=PRIMARY_COLOR, fg="white"
        ).pack(side="left", padx=20)
        self.clock_label = tk.Label(
            self.header, text="", font=("Segoe UI", 11), bg=PRIMARY_COLOR, fg="white"
        )
        self.clock_label.pack(side="right", padx=20)
        self.user_label = tk.Label(
            self.header, text=f"{self.username} ({self.role})",
            font=("Segoe UI", 11, "bold"), bg=PRIMARY_COLOR,
            fg=ROLE_BADGE_COLOR.get(self.role, ACCENT_COLOR)
        )
        self.user_label.pack(side="right", padx=20)
    def build_sidebar(self):
        self.sidebar = tk.Frame(self.body_frame, bg=SECONDARY_COLOR, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        page_commands = {
            "dashboard": self.show_dashboard,
            "register": self.show_register_page,
            "queue": self.show_queue_page,
            "search": self.show_search_page,
            "status": self.show_status_page,
            "reports": self.show_reports_page,
            "activity": self.show_activity_page,
            "users": self.show_users_page,
            "audit": self.show_audit_page
        }
        allowed = ROLE_PERMISSIONS.get(self.role, set())
        for key, label in NAV_PAGES:
            if key not in allowed:
                continue
            tk.Button(
                self.sidebar,
                text=label,
                command=page_commands[key],
                font=("Segoe UI", 11, "bold"),
                bg=SECONDARY_COLOR,
                fg="white",
                relief="flat",
                activebackground="#27AE60",
                activeforeground="white",
                width=22,
                pady=12
            ).pack(pady=5)
        tk.Frame(self.sidebar, bg=SECONDARY_COLOR, height=2).pack(fill="x", pady=10)
        tk.Button(
            self.sidebar,
            text="Logout",
            command=self.logout,
            font=("Segoe UI", 11, "bold"),
            bg="#7B241C",
            fg="white",
            relief="flat",
            activebackground="#C0392B",
            activeforeground="white",
            width=22,
            pady=12
        ).pack(pady=5)
    def build_main_area(self):
        self.main_frame = tk.Frame(self.body_frame, bg=WINDOW_BG)
        self.main_frame.pack(side="left", fill="both", expand=True)
        self.show_dashboard()
    def update_clock(self):
        self.clock_label.config(text=datetime.now().strftime("%d %B %Y | %H:%M:%S"))
        self.root.after(1000, self.update_clock)
    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
    def make_sortable(self, tree, columns):
        for col in columns:
            tree.heading(col, command=lambda c=col, t=tree: self.sort_tree_column(t, c, False))
    def sort_tree_column(self, tree, col, reverse):
        items = [(tree.set(item, col), item) for item in tree.get_children("")]
        def sort_key(pair):
            value = pair[0]
            try:
                return (0, float(value))
            except (ValueError, TypeError):
                return (1, str(value).lower())
        items.sort(key=sort_key, reverse=reverse)
        for index, (_, item) in enumerate(items):
            tree.move(item, "", index)
        tree.heading(col, command=lambda: self.sort_tree_column(tree, col, not reverse))
    def show_dashboard(self):
        if not self.has_access("dashboard"):
            self.access_denied()
            return
        self.clear_main_frame()
        self.build_dashboard()
    def build_dashboard(self):
        title = tk.Label(
            self.main_frame, text="EcoClean SL Management Dashboard",
            font=("Segoe UI", 24, "bold"), bg=WINDOW_BG, fg=PRIMARY_COLOR
        )
        title.pack(pady=(20, 10))
        cards_frame = tk.Frame(self.main_frame, bg=WINDOW_BG)
        cards_frame.pack(fill="x", padx=20, pady=5)
        self.total_card = self.create_card(cards_frame, "TOTAL REQUESTS", "#2471A3")
        self.pending_card = self.create_card(cards_frame, "PENDING", "#E67E22")
        self.completed_card = self.create_card(cards_frame, "COMPLETED", "#1E8449")
        self.urgent_card = self.create_card(cards_frame, "URGENT", "#C0392B")
        cards_frame2 = tk.Frame(self.main_frame, bg=WINDOW_BG)
        cards_frame2.pack(fill="x", padx=20, pady=(5, 10))
        self.overdue_card = self.create_card(
            cards_frame2, f"OVERDUE ({OVERDUE_DAYS}+ DAYS)", "#922B21"
        )
        self.kg_card = self.create_card(cards_frame2, "TOTAL KG COLLECTED", "#117864")
        middle_frame = tk.Frame(self.main_frame, bg=WINDOW_BG)
        middle_frame.pack(fill="both", expand=True, padx=20, pady=5)
        activity_frame = tk.LabelFrame(
            middle_frame, text="Recent Activities", font=("Segoe UI", 11, "bold"),
            bg="white"
        )
        activity_frame.pack(side="left", fill="both", expand=True, padx=10)
        self.activity_text = tk.Text(activity_frame, height=14, font=("Consolas", 10))
        self.activity_text.pack(fill="both", expand=True)
        community_frame = tk.LabelFrame(
            middle_frame, text="Community Statistics", font=("Segoe UI", 11, "bold"),
            bg="white"
        )
        community_frame.pack(side="left", fill="both", expand=True, padx=10)
        columns = ("Community", "Requests")
        self.community_tree = ttk.Treeview(
            community_frame, columns=columns, show="headings", height=11
        )
        for col in columns:
            self.community_tree.heading(col, text=col)
            self.community_tree.column(col, width=180, anchor="center")
        self.community_tree.pack(fill="both", expand=True)
        charts_row = tk.Frame(self.main_frame, bg=WINDOW_BG)
        charts_row.pack(fill="x", padx=20, pady=(5, 10))
        chart_frame = tk.LabelFrame(
            charts_row, text="Waste Type Breakdown", font=("Segoe UI", 11, "bold"),
            bg="white"
        )
        chart_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.waste_chart_canvas = tk.Canvas(
            chart_frame, height=170, bg="white", highlightthickness=0
        )
        self.waste_chart_canvas.pack(fill="x", expand=True, padx=10, pady=10)
        self.waste_chart_canvas.bind("<Configure>", lambda event: self.draw_waste_chart())
        status_chart_frame = tk.LabelFrame(
            charts_row, text="Request Status Breakdown", font=("Segoe UI", 11, "bold"),
            bg="white"
        )
        status_chart_frame.pack(side="left", fill="both", expand=True, padx=(10, 0))
        self.status_chart_canvas = tk.Canvas(
            status_chart_frame, height=170, bg="white", highlightthickness=0
        )
        self.status_chart_canvas.pack(fill="x", expand=True, padx=10, pady=10)
        self.status_chart_canvas.bind("<Configure>", lambda event: self.draw_status_chart())
        if self.has_access("audit"):
            staff_chart_frame = tk.LabelFrame(
                self.main_frame, text="Staff Performance (Total Actions Logged)",
                font=("Segoe UI", 11, "bold"), bg="white"
            )
            staff_chart_frame.pack(fill="x", padx=20, pady=(0, 10))
            self.staff_chart_canvas = tk.Canvas(
                staff_chart_frame, height=140, bg="white", highlightthickness=0
            )
            self.staff_chart_canvas.pack(fill="x", expand=True, padx=10, pady=10)
            self.staff_chart_canvas.bind("<Configure>", lambda event: self.draw_staff_chart())
        tk.Button(
            self.main_frame, text="Refresh Dashboard", font=("Segoe UI", 11, "bold"),
            bg=PRIMARY_COLOR, fg="white", command=self.refresh_dashboard
        ).pack(pady=10)
        self.refresh_dashboard()
    def create_card(self, parent, title, color):
        frame = tk.Frame(parent, bg=color, width=250, height=120)
        frame.pack(side="left", expand=True, fill="both", padx=10)
        frame.pack_propagate(False)
        tk.Label(
            frame, text=title, font=("Segoe UI", 11, "bold"), bg=color, fg="white",
            wraplength=230, justify="center"
        ).pack(pady=10)
        value_label = tk.Label(
            frame, text="0", font=("Segoe UI", 28, "bold"), bg=color, fg="white"
        )
        value_label.pack()
        return value_label
    def draw_waste_chart(self):
        if not hasattr(self, "waste_chart_canvas"):
            return
        canvas = self.waste_chart_canvas
        canvas.delete("all")
        counts = {waste_type: 0 for waste_type in WASTE_TYPES}
        for record in requests_data:
            waste_type = record.get("waste_type", "")
            if waste_type in counts:
                counts[waste_type] += 1
        max_count = max(counts.values()) if counts else 0
        width = canvas.winfo_width()
        if width <= 1:
            width = 800
        bar_colors = ["#2471A3", "#1E8449", "#B7950B", "#7D3C98", "#C0392B"]
        row_height = 30
        label_width = 110
        top_margin = 10
        for index, waste_type in enumerate(WASTE_TYPES):
            y = top_margin + index * row_height
            count = counts[waste_type]
            bar_max_width = max(width - label_width - 70, 10)
            bar_width = 0 if max_count == 0 else int((count / max_count) * bar_max_width)
            color = bar_colors[index % len(bar_colors)]
            canvas.create_text(
                10, y + 12, anchor="w", text=waste_type, font=("Segoe UI", 10)
            )
            canvas.create_rectangle(
                label_width, y, label_width + max(bar_width, 2), y + 18,
                fill=color, outline=color
            )
            canvas.create_text(
                label_width + bar_width + 10, y + 9, anchor="w",
                text=str(count), font=("Segoe UI", 10, "bold")
            )
    def draw_status_chart(self):
        if not hasattr(self, "status_chart_canvas"):
            return
        canvas = self.status_chart_canvas
        canvas.delete("all")
        counts = {status: 0 for status in STATUS_OPTIONS}
        for record in requests_data:
            status = record.get("status", "")
            if status in counts:
                counts[status] += 1
        max_count = max(counts.values()) if counts else 0
        width = canvas.winfo_width()
        if width <= 1:
            width = 800
        status_colors = {
            "Pending": "#E67E22", "Assigned": "#2471A3",
            "Collected": "#7D3C98", "Completed": "#1E8449"
        }
        row_height = 35
        label_width = 100
        top_margin = 10
        for index, status in enumerate(STATUS_OPTIONS):
            y = top_margin + index * row_height
            count = counts[status]
            bar_max_width = max(width - label_width - 70, 10)
            bar_width = 0 if max_count == 0 else int((count / max_count) * bar_max_width)
            color = status_colors.get(status, "#7F8C8D")
            canvas.create_text(
                10, y + 12, anchor="w", text=status, font=("Segoe UI", 10)
            )
            canvas.create_rectangle(
                label_width, y, label_width + max(bar_width, 2), y + 20,
                fill=color, outline=color
            )
            canvas.create_text(
                label_width + bar_width + 10, y + 10, anchor="w",
                text=str(count), font=("Segoe UI", 10, "bold")
            )
    def draw_staff_chart(self):
        if not hasattr(self, "staff_chart_canvas"):
            return
        canvas = self.staff_chart_canvas
        canvas.delete("all")
        stats = get_staff_statistics()
        usernames = sorted(stats.keys(), key=lambda u: stats[u]["total_actions"], reverse=True)
        max_count = max((stats[u]["total_actions"] for u in usernames), default=0)
        width = canvas.winfo_width()
        if width <= 1:
            width = 1100
        bar_colors = ["#145A32", "#B7950B", "#2471A3", "#7D3C98", "#922B21", "#1E8449"]
        row_height = 26
        label_width = 150
        top_margin = 8
        for index, username in enumerate(usernames):
            y = top_margin + index * row_height
            count = stats[username]["total_actions"]
            role = stats[username]["role"]
            bar_max_width = max(width - label_width - 90, 10)
            bar_width = 0 if max_count == 0 else int((count / max_count) * bar_max_width)
            color = bar_colors[index % len(bar_colors)]
            canvas.create_text(
                10, y + 11, anchor="w", text=f"{username} ({role})", font=("Segoe UI", 9)
            )
            canvas.create_rectangle(
                label_width, y, label_width + max(bar_width, 2), y + 16,
                fill=color, outline=color
            )
            canvas.create_text(
                label_width + bar_width + 10, y + 8, anchor="w",
                text=str(count), font=("Segoe UI", 9, "bold")
            )
    def refresh_dashboard(self):
        if not hasattr(self, "total_card"):
            return
        stats = get_dashboard_statistics()
        self.total_card.config(text=str(stats["total"]))
        self.pending_card.config(text=str(stats["pending"]))
        self.completed_card.config(text=str(stats["completed"]))
        self.urgent_card.config(text=str(stats["urgent"]))
        self.overdue_card.config(text=str(stats["overdue"]))
        self.kg_card.config(text=f"{stats['total_kg_completed']:.1f}")
        self.activity_text.delete("1.0", tk.END)
        recent_logs = activity_log[-20:]
        for log in reversed(recent_logs):
            line = (
                f"{log['timestamp']} | {log['request_id']} | "
                f"{log.get('performed_by', 'Unknown')} | {log['action']}\n"
            )
            self.activity_text.insert(tk.END, line)
        for item in self.community_tree.get_children():
            self.community_tree.delete(item)
        community_stats = {}
        for record in requests_data:
            community = record["community"]
            if community not in community_stats:
                community_stats[community] = 0
            community_stats[community] += 1
        for community, count in community_stats.items():
            self.community_tree.insert("", "end", values=(community, count))
        self.draw_waste_chart()
        self.draw_status_chart()
        if hasattr(self, "staff_chart_canvas"):
            self.draw_staff_chart()
    def show_register_page(self):
        if not self.has_access("register"):
            self.access_denied()
            return
        self.clear_main_frame()
        self.build_register_page()
    def build_register_page(self):
        title = tk.Label(
            self.main_frame, text="Register Waste Collection Request",
            font=("Segoe UI", 22, "bold"), bg=WINDOW_BG, fg=PRIMARY_COLOR
        )
        title.pack(pady=20)
        form_frame = tk.Frame(self.main_frame, bg="white", padx=30, pady=30)
        form_frame.pack(pady=10)
        tk.Label(
            form_frame, text="Resident Name", font=("Segoe UI", 11), bg="white"
        ).grid(row=0, column=0, sticky="w", pady=10, padx=10)
        self.name_entry = tk.Entry(form_frame, width=40, font=("Segoe UI", 11))
        self.name_entry.grid(row=0, column=1, pady=10)
        tk.Label(
            form_frame, text="Phone Number (digits only)", font=("Segoe UI", 11), bg="white"
        ).grid(row=1, column=0, sticky="w", pady=10, padx=10)
        self.phone_entry = tk.Entry(form_frame, width=40, font=("Segoe UI", 11))
        self.phone_entry.grid(row=1, column=1, pady=10)
        tk.Label(
            form_frame, text="Community", font=("Segoe UI", 11), bg="white"
        ).grid(row=2, column=0, sticky="w", pady=10, padx=10)
        self.community_entry = tk.Entry(form_frame, width=40, font=("Segoe UI", 11))
        self.community_entry.grid(row=2, column=1, pady=10)
        tk.Label(
            form_frame, text="Waste Type", font=("Segoe UI", 11), bg="white"
        ).grid(row=3, column=0, sticky="w", pady=10, padx=10)
        self.waste_combo = ttk.Combobox(
            form_frame, values=WASTE_TYPES, width=37, state="readonly"
        )
        self.waste_combo.grid(row=3, column=1, pady=10)
        self.waste_combo.set(WASTE_TYPES[0])
        tk.Label(
            form_frame, text="Quantity in KG (numbers only)", font=("Segoe UI", 11), bg="white"
        ).grid(row=4, column=0, sticky="w", pady=10, padx=10)
        self.quantity_entry = tk.Entry(form_frame, width=40, font=("Segoe UI", 11))
        self.quantity_entry.grid(row=4, column=1, pady=10)
        tk.Label(
            form_frame, text="Priority", font=("Segoe UI", 11), bg="white"
        ).grid(row=5, column=0, sticky="w", pady=10, padx=10)
        self.priority_combo = ttk.Combobox(
            form_frame, values=PRIORITY_LEVELS, width=37, state="readonly"
        )
        self.priority_combo.grid(row=5, column=1, pady=10)
        self.priority_combo.set(PRIORITY_LEVELS[0])
        button_frame = tk.Frame(self.main_frame, bg=WINDOW_BG)
        button_frame.pack(pady=20)
        tk.Button(
            button_frame, text="Register Request", bg=PRIMARY_COLOR, fg="white",
            width=20, font=("Segoe UI", 11, "bold"), command=self.submit_request
        ).pack(side="left", padx=10)
        tk.Button(
            button_frame, text="Clear Form", bg="#7F8C8D", fg="white", width=20,
            font=("Segoe UI", 11, "bold"), command=self.clear_form
        ).pack(side="left", padx=10)
    def submit_request(self):
        success, message = register_request(
            self.name_entry.get(),
            self.phone_entry.get(),
            self.community_entry.get(),
            self.waste_combo.get(),
            self.quantity_entry.get(),
            self.priority_combo.get(),
            performed_by=self.username
        )
        if success:
            messagebox.showinfo("Success", message)
            self.clear_form()
            self.refresh_dashboard()
        else:
            messagebox.showerror("Validation Error", message)
    def clear_form(self):
        self.name_entry.delete(0, tk.END)
        self.phone_entry.delete(0, tk.END)
        self.community_entry.delete(0, tk.END)
        self.quantity_entry.delete(0, tk.END)
        self.waste_combo.set(WASTE_TYPES[0])
        self.priority_combo.set(PRIORITY_LEVELS[0])
    def show_queue_page(self):
        if not self.has_access("queue"):
            self.access_denied()
            return
        self.clear_main_frame()
        self.build_queue_page()
    def build_queue_page(self):
        title = tk.Label(
            self.main_frame, text="Collection Queue & Registered Requests",
            font=("Segoe UI", 22, "bold"), bg=WINDOW_BG, fg=PRIMARY_COLOR
        )
        title.pack(pady=15)
        filter_frame = tk.Frame(self.main_frame, bg=WINDOW_BG)
        filter_frame.pack(fill="x", padx=15, pady=(0, 5))
        tk.Label(
            filter_frame, text="Filter by Status:", bg=WINDOW_BG, font=("Segoe UI", 10)
        ).pack(side="left", padx=(0, 5))
        self.queue_status_filter = ttk.Combobox(
            filter_frame, values=STATUS_FILTER_OPTIONS, width=15, state="readonly"
        )
        self.queue_status_filter.set("All")
        self.queue_status_filter.pack(side="left", padx=(0, 15))
        self.queue_status_filter.bind("<<ComboboxSelected>>", lambda event: self.refresh_records())
        tk.Label(
            filter_frame, text="Filter by Priority:", bg=WINDOW_BG, font=("Segoe UI", 10)
        ).pack(side="left", padx=(0, 5))
        self.queue_priority_filter = ttk.Combobox(
            filter_frame, values=PRIORITY_FILTER_OPTIONS, width=15, state="readonly"
        )
        self.queue_priority_filter.set("All")
        self.queue_priority_filter.pack(side="left")
        self.queue_priority_filter.bind("<<ComboboxSelected>>", lambda event: self.refresh_records())
        table_frame = tk.Frame(self.main_frame, bg=WINDOW_BG)
        table_frame.pack(fill="both", expand=True, padx=15, pady=10)
        columns = (
            "Request ID", "Resident Name", "Phone", "Community", "Waste Type",
            "Quantity", "Priority", "Status", "Assigned To", "Date", "Time"
        )
        self.records_tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", height=18
        )
        widths = [100, 170, 110, 140, 110, 90, 90, 110, 130, 100, 80]
        for col, width in zip(columns, widths):
            self.records_tree.heading(col, text=col)
            self.records_tree.column(col, width=width, anchor="center")
        self.make_sortable(self.records_tree, columns)
        y_scroll = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.records_tree.yview
        )
        x_scroll = ttk.Scrollbar(
            table_frame, orient="horizontal", command=self.records_tree.xview
        )
        self.records_tree.configure(
            yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set
        )
        self.records_tree.pack(side="top", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")
        x_scroll.pack(side="bottom", fill="x")
        self.records_tree.tag_configure("overdue", background="#F1948A")
        self.records_tree.tag_configure("urgent", background="#FADBD8")
        self.records_tree.tag_configure("completed", background="#D5F5E3")
        self.records_tree.tag_configure("pending", background="#FCF3CF")
        self.queue_empty_label = tk.Label(
            self.main_frame, text="No requests match the current filters.",
            font=("Segoe UI", 11, "italic"), bg=WINDOW_BG, fg="#7F8C8D"
        )
        button_frame = tk.Frame(self.main_frame, bg=WINDOW_BG)
        button_frame.pack(pady=10)
        tk.Button(
            button_frame, text="Refresh Queue", bg=PRIMARY_COLOR, fg="white",
            width=18, font=("Segoe UI", 11, "bold"), command=self.refresh_records
        ).pack(side="left", padx=10)
        tk.Button(
            button_frame, text="Export CSV", bg="#2471A3", fg="white", width=18,
            font=("Segoe UI", 11, "bold"), command=self.export_records_csv
        ).pack(side="left", padx=10)
        if self.role == "Administrator":
            tk.Button(
                button_frame, text="Delete Selected", bg="#7B241C", fg="white", width=18,
                font=("Segoe UI", 11, "bold"), command=self.delete_selected_request
            ).pack(side="left", padx=10)
        self.refresh_records()
    def refresh_records(self):
        if not hasattr(self, "records_tree"):
            return
        for item in self.records_tree.get_children():
            self.records_tree.delete(item)
        status_filter = self.queue_status_filter.get() if hasattr(self, "queue_status_filter") else "All"
        priority_filter = self.queue_priority_filter.get() if hasattr(self, "queue_priority_filter") else "All"
        filtered = []
        for record in requests_data:
            if status_filter != "All" and record["status"] != status_filter:
                continue
            if priority_filter != "All" and record["priority"] != priority_filter:
                continue
            filtered.append(record)
        for record in filtered:
            if is_overdue(record):
                tag = "overdue"
            elif record["priority"] == "Urgent":
                tag = "urgent"
            elif record["status"] == "Completed":
                tag = "completed"
            else:
                tag = "pending"
            self.records_tree.insert(
                "", "end",
                values=(
                    record["id"], record["name"], record["phone"], record["community"],
                    record["waste_type"], record["quantity"], record["priority"],
                    record["status"], record.get("assigned_to", ""), record["date"],
                    record["time"]
                ),
                tags=(tag,)
            )
        if hasattr(self, "queue_empty_label"):
            if len(filtered) == 0:
                self.queue_empty_label.pack(pady=5)
            else:
                self.queue_empty_label.pack_forget()
    def export_records_csv(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV Files", "*.csv")]
        )
        if not filepath:
            return
        try:
            export_csv(filepath)
            messagebox.showinfo("Export Successful", "Records exported successfully.")
        except Exception as error:
            messagebox.showerror("Export Error", str(error))
    def delete_selected_request(self):
        selection = self.records_tree.selection()
        if not selection:
            messagebox.showerror("Selection Error", "Please select a request in the table to delete.")
            return
        values = self.records_tree.item(selection[0], "values")
        request_id = values[0]
        resident_name = values[1]
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Permanently delete request {request_id} ({resident_name})?\n\n"
            "This cannot be undone, but it will be recorded in the Activity Log."
        )
        if not confirm:
            return
        success = delete_request(request_id, performed_by=self.username)
        if success:
            messagebox.showinfo("Deleted", f"Request {request_id} has been deleted.")
            self.refresh_records()
            self.refresh_dashboard()
        else:
            messagebox.showerror("Delete Error", "Request not found.")
    def show_search_page(self):
        if not self.has_access("search"):
            self.access_denied()
            return
        self.clear_main_frame()
        self.build_search_page()
    def build_search_page(self):
        title = tk.Label(
            self.main_frame, text="Search Waste Collection Records",
            font=("Segoe UI", 22, "bold"), bg=WINDOW_BG, fg=PRIMARY_COLOR
        )
        title.pack(pady=20)
        search_panel = tk.Frame(self.main_frame, bg="white", padx=20, pady=20)
        search_panel.pack(fill="x", padx=20)
        tk.Label(
            search_panel, text="Search by ID, Name, Phone or Community",
            font=("Segoe UI", 11), bg="white"
        ).grid(row=0, column=0, padx=10)
        self.search_entry = tk.Entry(search_panel, width=40, font=("Segoe UI", 12))
        self.search_entry.grid(row=0, column=1, padx=10)
        self.search_entry.bind("<Return>", lambda event: self.search_records_page())
        tk.Button(
            search_panel, text="Search", bg=PRIMARY_COLOR, fg="white",
            font=("Segoe UI", 11, "bold"), command=self.search_records_page
        ).grid(row=0, column=2, padx=5)
        tk.Button(
            search_panel, text="Clear", bg="#7F8C8D", fg="white",
            font=("Segoe UI", 11, "bold"), command=self.clear_search
        ).grid(row=0, column=3, padx=5)
        self.search_status_label = tk.Label(
            self.main_frame,
            text="Enter a keyword and click Search, or leave it blank to list all records.",
            font=("Segoe UI", 10, "italic"), bg=WINDOW_BG, fg="#7F8C8D"
        )
        self.search_status_label.pack(pady=5)
        columns = ("ID", "Resident", "Phone", "Community", "Waste", "Priority", "Status")
        self.search_tree = ttk.Treeview(
            self.main_frame, columns=columns, show="headings", height=16
        )
        for col in columns:
            self.search_tree.heading(col, text=col)
            self.search_tree.column(col, width=150, anchor="center")
        self.make_sortable(self.search_tree, columns)
        self.search_tree.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    def search_records_page(self):
        keyword = self.search_entry.get().strip()
        for item in self.search_tree.get_children():
            self.search_tree.delete(item)
        results = search_requests(keyword)
        for record in results:
            self.search_tree.insert(
                "", "end",
                values=(
                    record["id"], record["name"], record["phone"],
                    record["community"], record["waste_type"], record["priority"],
                    record["status"]
                )
            )
        if len(results) == 0:
            self.search_status_label.config(text="No matching records found.")
        else:
            self.search_status_label.config(text=f"{len(results)} record(s) found.")
    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        for item in self.search_tree.get_children():
            self.search_tree.delete(item)
        self.search_status_label.config(
            text="Enter a keyword and click Search, or leave it blank to list all records."
        )
    def show_status_page(self):
        if not self.has_access("status"):
            self.access_denied()
            return
        self.clear_main_frame()
        self.build_status_page()
    def build_status_page(self):
        title = tk.Label(
            self.main_frame, text="Update Collection Status",
            font=("Segoe UI", 22, "bold"), bg=WINDOW_BG, fg=PRIMARY_COLOR
        )
        title.pack(pady=20)
        form_frame = tk.Frame(self.main_frame, bg="white", padx=30, pady=30)
        form_frame.pack(pady=20)
        tk.Label(
            form_frame, text="Select Request", font=("Segoe UI", 11), bg="white"
        ).grid(row=0, column=0, padx=10, pady=15, sticky="w")
        self.status_request_combo = ttk.Combobox(form_frame, width=45, state="readonly")
        self.status_request_combo.grid(row=0, column=1, padx=10, pady=15)
        self.status_request_combo.bind(
            "<<ComboboxSelected>>", lambda event: self.on_status_request_selected()
        )
        tk.Label(
            form_frame, text="New Status", font=("Segoe UI", 11), bg="white"
        ).grid(row=1, column=0, padx=10, pady=15, sticky="w")
        self.status_combo = ttk.Combobox(
            form_frame, values=STATUS_OPTIONS, width=42, state="readonly"
        )
        self.status_combo.grid(row=1, column=1, padx=10, pady=15)
        self.status_combo.set(STATUS_OPTIONS[0])
        tk.Label(
            form_frame, text="Assigned To\n(Collector / Team)", font=("Segoe UI", 11),
            bg="white", justify="left"
        ).grid(row=2, column=0, padx=10, pady=15, sticky="w")
        self.assigned_to_entry = tk.Entry(form_frame, width=45, font=("Segoe UI", 11))
        self.assigned_to_entry.grid(row=2, column=1, padx=10, pady=15)
        button_frame = tk.Frame(self.main_frame, bg=WINDOW_BG)
        button_frame.pack(pady=20)
        tk.Button(
            button_frame, text="Update Status", bg=PRIMARY_COLOR, fg="white",
            width=18, font=("Segoe UI", 11, "bold"), command=self.update_status_action
        ).pack(side="left", padx=10)
        tk.Button(
            button_frame, text="Refresh List", bg="#2471A3", fg="white", width=18,
            font=("Segoe UI", 11, "bold"), command=self.load_status_dropdown
        ).pack(side="left", padx=10)
        self.load_status_dropdown()
    def load_status_dropdown(self):
        if not hasattr(self, "status_request_combo"):
            return
        values = [f"{record['id']} - {record['name']}" for record in requests_data]
        self.status_request_combo["values"] = values
    def on_status_request_selected(self):
        selected = self.status_request_combo.get()
        if selected == "":
            return
        request_id = selected.split(" - ")[0]
        record = get_request_by_id(request_id)
        if record is None:
            return
        self.status_combo.set(record["status"])
        self.assigned_to_entry.delete(0, tk.END)
        self.assigned_to_entry.insert(0, record.get("assigned_to", ""))
    def update_status_action(self):
        selected = self.status_request_combo.get()
        if selected == "":
            messagebox.showerror("Selection Error", "Please select a request.")
            return
        request_id = selected.split(" - ")[0]
        new_status = self.status_combo.get()
        assigned_to_input = self.assigned_to_entry.get().strip()
        record = get_request_by_id(request_id)
        if record is None:
            messagebox.showerror("Update Error", "Request not found.")
            return
        effective_assigned_to = assigned_to_input if assigned_to_input != "" else record.get("assigned_to", "")
        if new_status == "Assigned" and effective_assigned_to == "":
            messagebox.showerror(
                "Missing Information",
                "Please specify who this request is assigned to before setting status to Assigned."
            )
            return
        success = update_request_status(
            request_id,
            new_status,
            performed_by=self.username,
            assigned_to=(assigned_to_input if assigned_to_input != "" else None)
        )
        if success:
            messagebox.showinfo("Success", f"Request {request_id} updated to {new_status}.")
            self.refresh_dashboard()
            self.refresh_records()
            self.load_status_dropdown()
        else:
            messagebox.showerror("Update Error", "Request not found.")
    def show_reports_page(self):
        if not self.has_access("reports"):
            self.access_denied()
            return
        self.clear_main_frame()
        self.build_reports_page()
    def build_reports_page(self):
        title = tk.Label(
            self.main_frame, text="Reports & Data Export",
            font=("Segoe UI", 22, "bold"), bg=WINDOW_BG, fg=PRIMARY_COLOR
        )
        title.pack(pady=20)
        report_frame = tk.Frame(self.main_frame, bg="white", padx=20, pady=20)
        report_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.report_text = tk.Text(report_frame, font=("Consolas", 10), wrap="word")
        self.report_text.pack(fill="both", expand=True)
        button_frame = tk.Frame(self.main_frame, bg=WINDOW_BG)
        button_frame.pack(pady=15)
        tk.Button(
            button_frame, text="Generate Report", bg=PRIMARY_COLOR, fg="white",
            font=("Segoe UI", 11, "bold"), width=18, command=self.show_report
        ).pack(side="left", padx=5)
        tk.Button(
            button_frame, text="Export Report", bg="#2471A3", fg="white",
            font=("Segoe UI", 11, "bold"), width=18, command=self.export_report_file
        ).pack(side="left", padx=5)
        tk.Button(
            button_frame, text="Export CSV", bg="#7D3C98", fg="white",
            font=("Segoe UI", 11, "bold"), width=18, command=self.export_csv_file
        ).pack(side="left", padx=5)
        self.show_report()
    def show_report(self):
        report = generate_daily_report()
        self.report_text.delete("1.0", tk.END)
        self.report_text.insert(tk.END, report)
    def export_report_file(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("Text Files", "*.txt")]
        )
        if not filepath:
            return
        try:
            export_report(filepath)
            messagebox.showinfo("Success", "Report exported successfully.")
        except Exception as error:
            messagebox.showerror("Export Error", str(error))
    def export_csv_file(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV Files", "*.csv")]
        )
        if not filepath:
            return
        try:
            export_csv(filepath)
            messagebox.showinfo("Success", "CSV exported successfully.")
        except Exception as error:
            messagebox.showerror("Export Error", str(error))
    def show_activity_page(self):
        if not self.has_access("activity"):
            self.access_denied()
            return
        self.clear_main_frame()
        self.build_activity_page()
    def build_activity_page(self):
        title = tk.Label(
            self.main_frame, text="System Activity Log (Administrator Only)",
            font=("Segoe UI", 22, "bold"), bg=WINDOW_BG, fg=PRIMARY_COLOR
        )
        title.pack(pady=20)
        log_frame = tk.Frame(self.main_frame, bg="white")
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        columns = ("Request ID", "Resident", "Action", "Performed By", "Timestamp")
        self.activity_tree = ttk.Treeview(log_frame, columns=columns, show="headings")
        widths = [110, 160, 320, 130, 200]
        for col, width in zip(columns, widths):
            self.activity_tree.heading(col, text=col)
            self.activity_tree.column(col, width=width, anchor="center")
        self.activity_tree.column("Action", anchor="w")
        self.make_sortable(self.activity_tree, columns)
        scrollbar = ttk.Scrollbar(
            log_frame, orient="vertical", command=self.activity_tree.yview
        )
        self.activity_tree.configure(yscrollcommand=scrollbar.set)
        self.activity_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        btn_frame = tk.Frame(self.main_frame, bg=WINDOW_BG)
        btn_frame.pack(pady=10)
        tk.Button(
            btn_frame, text="Refresh Activity Log", bg=PRIMARY_COLOR, fg="white",
            font=("Segoe UI", 11, "bold"), width=20, command=self.refresh_activity_log
        ).pack()
        self.refresh_activity_log()
    def refresh_activity_log(self):
        if not hasattr(self, "activity_tree"):
            return
        for item in self.activity_tree.get_children():
            self.activity_tree.delete(item)
        for log in reversed(activity_log):
            self.activity_tree.insert(
                "", "end",
                values=(
                    log["request_id"], log["resident_name"], log["action"],
                    log.get("performed_by", "Unknown"), log["timestamp"]
                )
            )
    # ==========================================================
    # USER MANAGEMENT PAGE (ADMINISTRATOR ONLY)
    # ==========================================================
    def show_users_page(self):
        if not self.has_access("users"):
            self.access_denied()
            return
        self.clear_main_frame()
        self.build_users_page()
    def build_users_page(self):
        title = tk.Label(
            self.main_frame, text="User Account Management (Administrator Only)",
            font=("Segoe UI", 22, "bold"), bg=WINDOW_BG, fg=PRIMARY_COLOR
        )
        title.pack(pady=20)
        body = tk.Frame(self.main_frame, bg=WINDOW_BG)
        body.pack(fill="both", expand=True, padx=20, pady=5)
        # Left: existing accounts table
        list_frame = tk.LabelFrame(
            body, text="Existing Accounts", font=("Segoe UI", 11, "bold"), bg="white"
        )
        list_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        columns = ("Username", "Role")
        self.users_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=14)
        for col in columns:
            self.users_tree.heading(col, text=col)
            self.users_tree.column(col, width=160, anchor="center")
        self.users_tree.pack(fill="both", expand=True, padx=10, pady=10)
        list_btn_frame = tk.Frame(list_frame, bg="white")
        list_btn_frame.pack(pady=(0, 10))
        tk.Button(
            list_btn_frame, text="Delete Selected Account", bg="#7B241C", fg="white",
            font=("Segoe UI", 10, "bold"), command=self.delete_selected_user
        ).pack(side="left", padx=5)
        tk.Button(
            list_btn_frame, text="Change Role of Selected", bg="#2471A3", fg="white",
            font=("Segoe UI", 10, "bold"), command=self.change_role_of_selected
        ).pack(side="left", padx=5)
        # Right: create new account form
        form_frame = tk.LabelFrame(
            body, text="Create New Account", font=("Segoe UI", 11, "bold"), bg="white"
        )
        form_frame.pack(side="left", fill="y", padx=(10, 0))
        inner = tk.Frame(form_frame, bg="white", padx=20, pady=20)
        inner.pack()
        tk.Label(inner, text="Username", font=("Segoe UI", 10), bg="white").grid(
            row=0, column=0, sticky="w", pady=8
        )
        self.new_username_entry = tk.Entry(inner, width=28, font=("Segoe UI", 11))
        self.new_username_entry.grid(row=1, column=0, pady=(0, 10))
        tk.Label(inner, text="Password", font=("Segoe UI", 10), bg="white").grid(
            row=2, column=0, sticky="w", pady=8
        )
        self.new_password_entry = tk.Entry(inner, width=28, font=("Segoe UI", 11), show="*")
        self.new_password_entry.grid(row=3, column=0, pady=(0, 10))
        tk.Label(inner, text="Role", font=("Segoe UI", 10), bg="white").grid(
            row=4, column=0, sticky="w", pady=8
        )
        self.new_role_combo = ttk.Combobox(
            inner, values=ROLE_OPTIONS, width=25, state="readonly"
        )
        self.new_role_combo.set(ROLE_OPTIONS[-1])
        self.new_role_combo.grid(row=5, column=0, pady=(0, 15))
        tk.Button(
            inner, text="Create Account", bg=PRIMARY_COLOR, fg="white", width=24,
            font=("Segoe UI", 10, "bold"), command=self.create_account_action
        ).grid(row=6, column=0, pady=5)
        tk.Label(
            inner, text="Note: you cannot delete your own\naccount or the last Administrator.",
            font=("Segoe UI", 8, "italic"), bg="white", fg="#7F8C8D", justify="left"
        ).grid(row=7, column=0, pady=(15, 0), sticky="w")
        self.refresh_users_table()
    def refresh_users_table(self):
        if not hasattr(self, "users_tree"):
            return
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        for username, info in sorted(USER_ACCOUNTS.items()):
            self.users_tree.insert("", "end", values=(username, info["role"]))
    def create_account_action(self):
        success, message = create_user_account(
            self.new_username_entry.get(),
            self.new_password_entry.get(),
            self.new_role_combo.get(),
            performed_by=self.username
        )
        if success:
            messagebox.showinfo("Success", message)
            self.new_username_entry.delete(0, tk.END)
            self.new_password_entry.delete(0, tk.END)
            self.new_role_combo.set(ROLE_OPTIONS[-1])
            self.refresh_users_table()
        else:
            messagebox.showerror("Validation Error", message)
    def delete_selected_user(self):
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showerror("Selection Error", "Please select an account to delete.")
            return
        target_username = self.users_tree.item(selection[0], "values")[0]
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Permanently delete the account '{target_username}'?\nThis cannot be undone."
        )
        if not confirm:
            return
        success, message = delete_user_account(target_username, performed_by=self.username)
        if success:
            messagebox.showinfo("Success", message)
            self.refresh_users_table()
        else:
            messagebox.showerror("Cannot Delete", message)
    def change_role_of_selected(self):
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showerror("Selection Error", "Please select an account to change.")
            return
        target_username = self.users_tree.item(selection[0], "values")[0]
        current_role = USER_ACCOUNTS.get(target_username, {}).get("role", ROLE_OPTIONS[-1])
        new_role = self._prompt_role_choice(target_username, current_role)
        if new_role is None:
            return
        success, message = change_user_role(target_username, new_role, performed_by=self.username)
        if success:
            messagebox.showinfo("Success", message)
            self.refresh_users_table()
        else:
            messagebox.showerror("Cannot Change Role", message)
    def _prompt_role_choice(self, target_username, current_role):
        chooser = tk.Toplevel(self.root)
        chooser.title("Change Role")
        chooser.geometry("320x180")
        chooser.configure(bg="white")
        chooser.resizable(False, False)
        tk.Label(
            chooser, text=f"New role for '{target_username}'", font=("Segoe UI", 11, "bold"),
            bg="white"
        ).pack(pady=(20, 10))
        role_combo = ttk.Combobox(chooser, values=ROLE_OPTIONS, width=25, state="readonly")
        role_combo.set(current_role)
        role_combo.pack(pady=5)
        result = {"role": None}
        def confirm_choice():
            result["role"] = role_combo.get()
            chooser.destroy()
        tk.Button(
            chooser, text="Confirm", bg=PRIMARY_COLOR, fg="white", font=("Segoe UI", 10, "bold"),
            command=confirm_choice
        ).pack(pady=15)
        chooser.transient(self.root)
        chooser.grab_set()
        self.root.wait_window(chooser)
        return result["role"]
    # ==========================================================
    # STAFF AUDIT PAGE (ADMINISTRATOR ONLY)
    # ==========================================================
    def show_audit_page(self):
        if not self.has_access("audit"):
            self.access_denied()
            return
        self.clear_main_frame()
        self.build_audit_page()
    def build_audit_page(self):
        title = tk.Label(
            self.main_frame, text="Staff Audit & Performance (Administrator Only)",
            font=("Segoe UI", 22, "bold"), bg=WINDOW_BG, fg=PRIMARY_COLOR
        )
        title.pack(pady=20)
        summary_frame = tk.LabelFrame(
            self.main_frame, text="Performance Summary", font=("Segoe UI", 11, "bold"), bg="white"
        )
        summary_frame.pack(fill="x", padx=20, pady=(0, 10))
        columns = ("Username", "Role", "Requests Registered", "Status Updates", "Total Actions")
        self.staff_summary_tree = ttk.Treeview(
            summary_frame, columns=columns, show="headings", height=6
        )
        widths = [160, 140, 180, 150, 130]
        for col, width in zip(columns, widths):
            self.staff_summary_tree.heading(col, text=col)
            self.staff_summary_tree.column(col, width=width, anchor="center")
        self.staff_summary_tree.pack(fill="x", padx=10, pady=10)
        self.staff_summary_tree.bind("<<TreeviewSelect>>", lambda event: self.on_staff_selected())
        detail_frame = tk.LabelFrame(
            self.main_frame, text="Activity History for Selected User",
            font=("Segoe UI", 11, "bold"), bg="white"
        )
        detail_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        detail_columns = ("Request ID", "Resident", "Action", "Timestamp")
        self.staff_detail_tree = ttk.Treeview(
            detail_frame, columns=detail_columns, show="headings", height=10
        )
        detail_widths = [100, 160, 350, 180]
        for col, width in zip(detail_columns, detail_widths):
            self.staff_detail_tree.heading(col, text=col)
            self.staff_detail_tree.column(col, width=width, anchor="center")
        self.staff_detail_tree.column("Action", anchor="w")
        self.staff_detail_tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.staff_detail_empty_label = tk.Label(
            self.main_frame, text="Select a user above to view their full activity history.",
            font=("Segoe UI", 10, "italic"), bg=WINDOW_BG, fg="#7F8C8D"
        )
        self.staff_detail_empty_label.pack(pady=5)
        tk.Button(
            self.main_frame, text="Refresh Audit Data", bg=PRIMARY_COLOR, fg="white",
            font=("Segoe UI", 11, "bold"), command=self.refresh_audit_page
        ).pack(pady=10)
        self.refresh_audit_page()
    def refresh_audit_page(self):
        if not hasattr(self, "staff_summary_tree"):
            return
        for item in self.staff_summary_tree.get_children():
            self.staff_summary_tree.delete(item)
        stats = get_staff_statistics()
        for username in sorted(stats.keys(), key=lambda u: stats[u]["total_actions"], reverse=True):
            data = stats[username]
            self.staff_summary_tree.insert(
                "", "end",
                values=(
                    username, data["role"], data["requests_registered"],
                    data["status_updates"], data["total_actions"]
                )
            )
        for item in self.staff_detail_tree.get_children():
            self.staff_detail_tree.delete(item)
    def on_staff_selected(self):
        selection = self.staff_summary_tree.selection()
        if not selection:
            return
        username = self.staff_summary_tree.item(selection[0], "values")[0]
        for item in self.staff_detail_tree.get_children():
            self.staff_detail_tree.delete(item)
        history = get_activity_by_user(username)
        for log in reversed(history):
            self.staff_detail_tree.insert(
                "", "end",
                values=(log["request_id"], log["resident_name"], log["action"], log["timestamp"])
            )
        if hasattr(self, "staff_detail_empty_label"):
            if len(history) == 0:
                self.staff_detail_empty_label.config(text=f"No activity recorded for '{username}'.")
                self.staff_detail_empty_label.pack(pady=5)
            else:
                self.staff_detail_empty_label.pack_forget()
    def logout(self):
        answer = messagebox.askyesno("Logout", "Are you sure you want to logout?")
        if answer:
            self.root.destroy()
            login_root = tk.Tk()
            LoginWindow(login_root)
            login_root.mainloop()
# ==========================================================
# START APPLICATION
# ==========================================================
if __name__ == "__main__":
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()
