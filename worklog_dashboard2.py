import tkinter as tk
from tkinter import messagebox, filedialog
from tkcalendar import Calendar
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font
from datetime import datetime, timedelta
import webbrowser

entries = []
last_selected_date = None
lunch_used = False

def parse_time_string(value):
    try:
        h, m = str(value).split(":")
        return int(h) * 60 + int(m)
    except:
        return 0

def add_entry():
    global lunch_used
    date = date_entry.get()
    start = start_entry.get()
    end = end_entry.get()
    lunch = lunch_entry.get().strip()
    comment = comment_entry.get().strip()

    if ":" not in start: start += ":00"
    if ":" not in end: end += ":00"

    try:
        t1 = datetime.strptime(start, "%H:%M")
        t2 = datetime.strptime(end, "%H:%M")
        total_minutes = (t2 - t1).seconds // 60
        duration = f"{total_minutes // 60}:{total_minutes % 60:02d}"
    except:
        messagebox.showerror("Error", "Invalid time format (HH:MM)")
        return

    lunch_formatted = ""
    lunch_minutes = 0
    if lunch:
        lunch_used = True
        try:
            if ":" in lunch:
                h, m = map(int, lunch.split(":"))
                lunch_minutes = h * 60 + m
            else:
                lunch_minutes = int(lunch)
            lunch_formatted = f"{lunch_minutes // 60}:{lunch_minutes % 60:02d}"
        except:
            messagebox.showerror("Error", "Lunch must be minutes or HH:MM")
            return

    net_minutes = max(total_minutes - lunch_minutes, 0)
    net_duration = f"{net_minutes // 60}:{net_minutes % 60:02d}"
    entries.append([date, start, end, duration, lunch_formatted, net_duration, comment])
    refresh_listbox()
    clear_fields()

def add_holiday_entry():
    global last_selected_date
    d = last_selected_date or datetime.today()
    entries.append([d.strftime("%d.%m.%Y") + " (Holiday)", "00:00", "00:00", "0:00", "0:00", "0:00", ""])
    refresh_listbox()

def refresh_listbox():
    listbox.delete(0, tk.END)
    for i, e in enumerate(entries):
        line = f"{i+1}. {e[0]} | {e[1]}–{e[2]} → {e[3]}"
        if lunch_used and e[4]: line += f" | Lunch: {e[4]} | Net: {e[5]}"
        if len(e) > 6 and e[6]: line += f" | Note: {e[6]}"
        listbox.insert(tk.END, line)
    total_minutes = sum(parse_time_string(e[5]) for e in entries)
    total_label.config(text=f"Net Total: {total_minutes//60} hours and {total_minutes%60} minutes")

def clear_fields():
    date_entry.delete(0, tk.END)
    start_entry.delete(0, tk.END)
    end_entry.delete(0, tk.END)
    lunch_entry.delete(0, tk.END)
    comment_entry.delete(0, tk.END)

def delete_entry():
    idx = listbox.curselection()
    if idx:
        entries.pop(idx[0])
        refresh_listbox()

def edit_entry():
    idx = listbox.curselection()
    if idx:
        e = entries[idx[0]]
        date_entry.delete(0, tk.END); date_entry.insert(0, e[0])
        start_entry.delete(0, tk.END); start_entry.insert(0, e[1])
        end_entry.delete(0, tk.END); end_entry.insert(0, e[2])
        lunch_entry.delete(0, tk.END); lunch_entry.insert(0, e[4])
        comment_entry.delete(0, tk.END); comment_entry.insert(0, e[6])
        entries.pop(idx[0])
        refresh_listbox()

def move_up():
    idx = listbox.curselection()
    if idx and idx[0] > 0:
        entries[idx[0]-1], entries[idx[0]] = entries[idx[0]], entries[idx[0]-1]
        refresh_listbox()
        listbox.select_set(idx[0]-1)

def move_down():
    idx = listbox.curselection()
    if idx and idx[0] < len(entries)-1:
        entries[idx[0]+1], entries[idx[0]] = entries[idx[0]], entries[idx[0]+1]
        refresh_listbox()
        listbox.select_set(idx[0]+1)

def calculate_total():
    if listbox.size() > len(entries):
        listbox.delete(tk.END)
    total_minutes = sum(parse_time_string(e[5]) for e in entries)
    listbox.insert(tk.END, f"▶ Net Total: {total_minutes//60} hours and {total_minutes%60} minutes")

def export_excel():
    path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
    if not path: return
    wb = Workbook()
    ws = wb.active
    ws.title = "Worklog"
    lunch_present = any(e[4] and "Holiday" not in e[0] for e in entries)
    headers = ["Date", "Start", "End", "Duration", "Lunch", "Net Duration", "Comment"] if lunch_present else ["Date", "Start", "End", "Duration", "Net Duration", "Comment"]
    ws.append(headers)
    for cell in ws[1]: cell.font = Font(bold=True)
    for e in entries:
        ws.append(e if lunch_present else [e[0], e[1], e[2], e[3], e[5], e[6]])
    ws.append([])
    total_minutes = sum(parse_time_string(e[5]) for e in entries)
    total_str = f"{total_minutes//60}:{total_minutes%60:02d}"
    total_row = ["▶ Net Total", "", "", "", "", total_str, ""] if lunch_present else ["▶ Net Total", "", "", "", total_str, ""]
    ws.append(total_row)
    wb.save(path)
    messagebox.showinfo("Success", f"Excel file saved:\n{path}")

def import_from_excel():
    path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
    if not path: return
    try:
        wb = load_workbook(path)
        ws = wb.active
        entries.clear()
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or not row[0]: continue
            if str(row[0]).startswith("▶"): continue
            date = str(row[0])
            start = str(row[1]) if row[1] else "00:00"
            end = str(row[2]) if row[2] else "00:00"
            duration = str(row[3]) if row[3] else "0:00"
            lunch = str(row[4]) if len(row) > 4 and row[4] else ""
            net = str(row[5]) if len(row) > 5 and row[5] else duration
            comment = str(row[6]) if len(row) > 6 and row[6] else ""
            entries.append([date, start, end, duration, lunch, net, comment])
        refresh_listbox()
        messagebox.showinfo("Success", f"Imported {len(entries)} entries from Excel.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to import file:\n{e}")

def show_donation_popup():
    top = tk.Toplevel(root)
    top.title("Support the Developer")
    top.resizable(False, False)
    root.update_idletasks()
    cx = root.winfo_x() + root.winfo_width()//2 - 210
    cy = root.winfo_y() + root.winfo_height()//2 - 110
    top.geometry(f"420x220+{cx}+{cy}")
    tk.Label(top, text="If this tool helps you, consider supporting:", font=("Arial", 10, "bold")).pack(pady=10)
    wallets = [("Bitcoin (BTC)", "15grt9PYYdYmtQ9GSZRpSCwLrT4VrEcdyy"),
               ("TRON (TRX)", "TMrApSKQGTnakEm1kVstWD65qsDHpAejEp"),
               ("WebMoney (WMZ)", "Z655601632616")]
    for label, value in wallets:
        f = tk.Frame(top); f.pack(pady=4)
        e = tk.Entry(f, width=34, font=("Arial", 9), justify="left")
        e.pack(side=tk.LEFT, padx=5)
        e.insert(0, value)
        e.config(state="readonly")
    tk.Label(top, text="Thank you for your support 🦾", font=("Arial", 10, "italic"), fg="gray").pack(pady=10)

def open_calendar():
    global last_selected_date
    root.update_idletasks()
    popup_x = root.winfo_x() + root.winfo_width() - 250
    popup_y = root.winfo_y()
    top = tk.Toplevel(root)
    top.title("Select Date")
    top.geometry(f"250x250+{popup_x}+{popup_y}")
    d = last_selected_date + timedelta(days=1) if last_selected_date else datetime.today()
    cal = Calendar(top, selectmode="day", year=d.year, month=d.month, day=d.day, showothermonthdays=True)
    cal.pack(padx=10, pady=10)

    def select_date():
        global last_selected_date
        last_selected_date = cal.selection_get()
        date_entry.delete(0, tk.END)
        date_entry.insert(0, last_selected_date.strftime("%d.%m.%Y"))
        top.destroy()

    tk.Button(top, text="📅 Select", font=("Arial", 10), width=10, command=select_date).pack(pady=5)

# GUI Setup
root = tk.Tk()
root.title("Worklog Dashboard")
root.geometry("450x470")  # width x height in pixels

# Date input
tk.Label(root, text="Date (DD.MM.YYYY):").grid(row=0, column=0, sticky="e")
date_entry = tk.Entry(root)
date_entry.grid(row=0, column=1, sticky="w")
calendar_btn = tk.Button(root, text="📅", font=("Arial", 12), width=6, command=open_calendar)
calendar_btn.grid(row=0, column=2, padx=(5, 10), sticky="w")

# Time inputs
tk.Label(root, text="Start (HH:MM):").grid(row=1, column=0, sticky="e")
start_entry = tk.Entry(root, width=10)
start_entry.grid(row=1, column=1, sticky="w")

tk.Label(root, text="End (HH:MM):").grid(row=2, column=0, sticky="e")
end_entry = tk.Entry(root, width=10)
end_entry.grid(row=2, column=1, sticky="w")

# Comment field on its own row
tk.Label(root, text="Comment:").grid(row=2, column=0, sticky="e", padx=(10, 0))
comment_entry = tk.Entry(root, width=15)
comment_entry.grid(row=2, column=2, columnspan=3, sticky="w", padx=(0, 5))

# Comment note directly underneath the field
comment_note = tk.Label(root, text="Notes", font=("Arial", 9), fg="black")
comment_note.grid(row=3, column=2, columnspan=3, sticky="w", padx=(0, 5), pady=(0, 5))



# Lunch and holiday
tk.Label(root, text="Lunch (min or HH:MM):").grid(row=3, column=0, sticky="e")
lunch_frame = tk.Frame(root)
lunch_frame.grid(row=3, column=1, columnspan=3, sticky="w", padx=(0,10))
lunch_entry = tk.Entry(lunch_frame, width=8)
lunch_entry.grid(row=0, column=0, sticky="w")
tk.Button(lunch_frame, text="Holiday", font=("Arial", 9), width=8, command=add_holiday_entry).grid(row=0, column=1, padx=(10,0), sticky="w")

# Entry buttons
tk.Button(root, text="Add Entry", width=20, command=add_entry).grid(row=4, column=0, columnspan=4, pady=5)

action_frame = tk.Frame(root)
action_frame.grid(row=5, column=0, columnspan=4, pady=5)
tk.Button(action_frame, text="🗑️ Delete Selected", width=18, command=delete_entry).pack(side=tk.LEFT, padx=5)
tk.Button(action_frame, text="✏️ Edit Selected", width=18, command=edit_entry).pack(side=tk.LEFT, padx=5)

# Entry list
listbox = tk.Listbox(root, width=80)
listbox.grid(row=6, column=0, columnspan=4, pady=5)

# Total time
total_label = tk.Label(root, text="Net Total: 0 hours and 0 minutes", font=("Arial", 10, "bold"))
total_label.grid(row=7, column=0, columnspan=4, pady=(0, 5))



# Reorder buttons
move_frame = tk.Frame(root)
move_frame.grid(row=9, column=0, columnspan=4)
tk.Button(move_frame, text="⬆ Move Up", width=12, command=move_up).pack(side=tk.LEFT, padx=10)
tk.Button(move_frame, text="⬇ Move Down", width=12, command=move_down).pack(side=tk.LEFT, padx=10)

# Bottom row: Calculate Total centered
bottom_row = tk.Frame(root)
bottom_row.grid(row=10, column=0, columnspan=4, pady=(5, 0))
tk.Button(bottom_row, text="Calculate Total", width=20, command=calculate_total).pack()

# Sub-buttons below Calculate Total
sub_button_row = tk.Frame(root)
sub_button_row.grid(row=11, column=0, columnspan=4, pady=(5, 10))
tk.Button(sub_button_row, text="Import from Excel", font=("Arial", 9), width=18, command=import_from_excel).pack(side=tk.LEFT, padx=5)
tk.Button(sub_button_row, text="Export to Excel", font=("Arial", 9), width=18, command=export_excel).pack(side=tk.LEFT, padx=5)
tk.Button(sub_button_row, text="Donate 🦾", font=("Arial", 9, "italic"), fg="#0066cc", bd=0, cursor="hand2", command=show_donation_popup).pack(side=tk.LEFT, padx=5)


# Run the app
root.mainloop()
