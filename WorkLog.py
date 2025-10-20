import tkinter as tk
from tkinter import messagebox, filedialog
from tkcalendar import Calendar
from openpyxl import Workbook
from openpyxl.styles import Font
from datetime import datetime, timedelta
import webbrowser

entries, last_selected_date = [], None
lunch_used = False

def add_entry():
    global lunch_used
    date, start, end = date_entry.get(), start_entry.get(), end_entry.get()
    lunch = lunch_entry.get().strip()
    if ":" not in start: start += ":00"
    if ":" not in end: end += ":00"
    try:
        t1, t2 = datetime.strptime(start, "%H:%M"), datetime.strptime(end, "%H:%M")
        total_minutes = (t2 - t1).seconds // 60
        duration = f"{total_minutes // 60}:{total_minutes % 60:02d}"
    except:
        messagebox.showerror("Error", "Invalid time format (HH:MM)"); return
    lunch_formatted, lunch_minutes = "", 0
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
            messagebox.showerror("Error", "Lunch must be minutes or HH:MM"); return
    net_minutes = max(total_minutes - lunch_minutes, 0)
    net_duration = f"{net_minutes // 60}:{net_minutes % 60:02d}"
    entries.append([date, start, end, duration, lunch_formatted, net_duration])
    refresh_listbox(); clear_fields()

def add_holiday_entry():
    global last_selected_date
    d = last_selected_date or datetime.today()
    entries.append([d.strftime("%d.%m.%Y") + " (Holiday)", "00:00", "00:00", "0:00", "0:00", "0:00"])
    refresh_listbox()

def refresh_listbox():
    listbox.delete(0, tk.END)
    for i, e in enumerate(entries):
        line = f"{i+1}. {e[0]} | {e[1]}–{e[2]} → {e[3]}"
        if lunch_used and e[4]: line += f" | Lunch: {e[4]} | Net: {e[5]}"
        listbox.insert(tk.END, line)
    total_minutes = sum(int(h)*60+int(m) for h,m in (e[5].split(":") for e in entries))
    total_label.config(text=f"Net Total: {total_minutes//60} hours and {total_minutes%60} minutes")

def clear_fields():
    date_entry.delete(0, tk.END); start_entry.delete(0, tk.END)
    end_entry.delete(0, tk.END); lunch_entry.delete(0, tk.END)

def delete_entry():
    idx = listbox.curselection()
    if idx: entries.pop(idx[0]); refresh_listbox()

def edit_entry():
    idx = listbox.curselection()
    if idx:
        e = entries[idx[0]]
        date_entry.delete(0, tk.END); date_entry.insert(0, e[0])
        start_entry.delete(0, tk.END); start_entry.insert(0, e[1])
        end_entry.delete(0, tk.END); end_entry.insert(0, e[2])
        lunch_entry.delete(0, tk.END); lunch_entry.insert(0, e[4])
        entries.pop(idx[0]); refresh_listbox()

def move_up():
    idx = listbox.curselection()
    if idx and idx[0] > 0:
        entries[idx[0]-1], entries[idx[0]] = entries[idx[0]], entries[idx[0]-1]
        refresh_listbox(); listbox.select_set(idx[0]-1)

def move_down():
    idx = listbox.curselection()
    if idx and idx[0] < len(entries)-1:
        entries[idx[0]+1], entries[idx[0]] = entries[idx[0]], entries[idx[0]+1]
        refresh_listbox(); listbox.select_set(idx[0]+1)

def calculate_total():
    if listbox.size() > len(entries): listbox.delete(tk.END)
    total_minutes = sum(int(h)*60+int(m) for h,m in (e[5].split(":") for e in entries))
    listbox.insert(tk.END, f"▶ Net Total: {total_minutes//60} hours and {total_minutes%60} minutes")

def export_excel():
    path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
    if not path: return
    wb = Workbook(); ws = wb.active; ws.title = "Worklog"
    lunch_present = any(e[4] and "Holiday" not in e[0] for e in entries)
    headers = ["Date", "Start", "End", "Duration", "Lunch", "Net Duration"] if lunch_present else ["Date", "Start", "End", "Duration", "Net Duration"]
    ws.append(headers); [setattr(c, 'font', Font(bold=True)) for c in ws[1]]
    for e in entries:
        ws.append(e if lunch_present else [e[0], e[1], e[2], e[3], e[5]])
    ws.append([])
    total_minutes = sum(int(h)*60+int(m) for h,m in (e[5].split(":") for e in entries))
    total_str = f"{total_minutes//60}:{total_minutes%60:02d}"
    total_row = ["▶ Net Total", "", "", "", "", total_str] if lunch_present else ["▶ Net Total", "", "", "", total_str]
    ws.append(total_row); wb.save(path)
    messagebox.showinfo("Success", f"Excel file saved: {path}")

def show_donation_popup():
    top = tk.Toplevel(root); top.title("Support the Developer"); top.resizable(False, False); top.update_idletasks()
    root.update_idletasks()
    cx = root.winfo_x() + root.winfo_width()//2 - 210
    cy = root.winfo_y() + root.winfo_height()//2 - 110
    top.geometry(f"420x220+{cx}+{cy}")
    tk.Label(top, text="If this tool helps you, consider supporting:", font=("Arial", 10, "bold")).pack(pady=10)
    wallets = [("Bitcoin (BTC)", "15grt9PYYdYmtQ9GSZRpSCwLrT4VrEcdyy"), ("TRON (TRX) trc20", "TMrApSKQGTnakEm1kVstWD65qsDHpAejEp"), ("WebMoney (WMZ)", "Z655601632616")]
    for label, value in wallets:
        f = tk.Frame(top); f.pack(pady=4)
        tk.Label(f, text=label+":", font=("Arial", 9)).pack(side=tk.LEFT)
        e = tk.Entry(f, width=34, font=("Arial", 9), justify="left"); e.pack(side=tk.LEFT, padx=5)
        e.insert(0, value); e.config(state="readonly")
    tk.Label(top, text="Thank you for your support 🦾", font=("Arial", 10, "italic"), fg="gray").pack(pady=10)

def open_calendar():
    global last_selected_date
    root.update_idletasks()
    popup_x = root.winfo_x() + root.winfo_width() - 250
    popup_y = root.winfo_y()
    top = tk.Toplevel(root); top.title("Select Date")
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

# GUI
root = tk.Tk(); root.title("Worklog Dashboard")

tk.Label(root, text="Date (DD.MM.YYYY):").grid(row=0, column=0, sticky="e")
date_entry = tk.Entry(root); date_entry.grid(row=0, column=1, sticky="w")
calendar_btn = tk.Button(root, text="📅", font=("Arial", 12), width=6, height=1, command=open_calendar)
calendar_btn.grid(row=0, column=2, padx=(5, 10), pady=1, sticky="w")


tk.Label(root, text="Start (HH:MM):").grid(row=1, column=0, sticky="e")
start_entry = tk.Entry(root); start_entry.grid(row=1, column=1, columnspan=2, sticky="w")

tk.Label(root, text="End (HH:MM):").grid(row=2, column=0, sticky="e")
end_entry = tk.Entry(root); end_entry.grid(row=2, column=1, columnspan=2, sticky="w")

tk.Label(root, text="Lunch (min or HH:MM):").grid(row=3, column=0, sticky="e")
lunch_frame = tk.Frame(root)
lunch_frame.grid(row=3, column=1, columnspan=2, sticky="w", padx=(0,10))
lunch_entry = tk.Entry(lunch_frame, width=8)
lunch_entry.grid(row=0, column=0, sticky="w")
tk.Button(lunch_frame, text="Holiday", font=("Arial", 9), width=8, command=add_holiday_entry).grid(row=0, column=1, padx=(10,0), sticky="w")

tk.Button(root, text="Add Entry", width=20, command=add_entry).grid(row=4, column=0, columnspan=3, pady=5)

action_frame = tk.Frame(root); action_frame.grid(row=5, column=0, columnspan=3, pady=5)
tk.Button(action_frame, text="🗑️ Delete Selected", width=18, command=delete_entry).pack(side=tk.LEFT, padx=5)
tk.Button(action_frame, text="✏️ Edit Selected", width=18, command=edit_entry).pack(side=tk.LEFT, padx=5)

listbox = tk.Listbox(root, width=60); listbox.grid(row=6, column=0, columnspan=3, pady=5)

total_label = tk.Label(root, text="Net Total: 0 hours and 0 minutes", font=("Arial", 10, "bold"))
total_label.grid(row=7, column=0, columnspan=3, pady=(0, 10))

move_frame = tk.Frame(root); move_frame.grid(row=8, column=0, columnspan=3)
tk.Button(move_frame, text="⬆ Move Up", width=12, command=move_up).pack(side=tk.LEFT, padx=10)
tk.Button(move_frame, text="⬇ Move Down", width=12, command=move_down).pack(side=tk.LEFT, padx=10)

bottom_row1 = tk.Frame(root); bottom_row1.grid(row=9, column=0, columnspan=3, pady=(5, 0))
tk.Button(bottom_row1, text="GitHub ↗", font=("Arial", 9, "italic"), fg="#0066cc", bd=0, cursor="hand2",
          command=lambda: webbrowser.open("https://github.com/trafficit/worklog_dashboard.git")).pack(side=tk.LEFT, padx=(0, 10))
tk.Button(bottom_row1, text="Calculate Total", width=20, command=calculate_total).pack(side=tk.LEFT)

bottom_row2 = tk.Frame(root); bottom_row2.grid(row=10, column=0, columnspan=3, pady=(5, 10))
tk.Button(bottom_row2, text="Donate 🦾", font=("Arial", 9, "italic"), fg="#0066cc", bd=0, cursor="hand2",
          command=show_donation_popup).pack(side=tk.LEFT, padx=(0, 10))
tk.Button(bottom_row2, text="Export to Excel", width=20, command=export_excel).pack(side=tk.LEFT)

root.mainloop()
