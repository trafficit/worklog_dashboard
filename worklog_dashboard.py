import tkinter as tk
from tkinter import messagebox, filedialog
from tkcalendar import Calendar
import csv
from datetime import datetime, timedelta

entries = []
last_selected_date = None
lunch_used = False

def add_entry():
    global lunch_used

    date = date_entry.get()
    start = start_entry.get()
    end = end_entry.get()
    lunch = lunch_entry.get().strip()

    if ":" not in start:
        start += ":00"
    if ":" not in end:
        end += ":00"

    try:
        t1 = datetime.strptime(start, "%H:%M")
        t2 = datetime.strptime(end, "%H:%M")
        delta = t2 - t1
        total_minutes = delta.seconds // 60
        duration = f"{total_minutes // 60}:{total_minutes % 60:02d}"
    except:
        messagebox.showerror("Error", "Invalid time format (HH:MM)")
        return

    lunch_formatted = ""
    lunch_minutes = 0
    if lunch:
        lunch_used = True
        if ":" in lunch:
            try:
                h, m = map(int, lunch.split(":"))
                lunch_minutes = h * 60 + m
                lunch_formatted = f"{h}:{m:02d}"
            except:
                messagebox.showerror("Error", "Lunch must be minutes or HH:MM")
                return
        else:
            try:
                lunch_minutes = int(lunch)
                lunch_formatted = f"{lunch_minutes // 60}:{lunch_minutes % 60:02d}"
            except:
                messagebox.showerror("Error", "Lunch must be minutes or HH:MM")
                return

    net_minutes = max(total_minutes - lunch_minutes, 0)
    net_duration = f"{net_minutes // 60}:{net_minutes % 60:02d}"

    entries.append([date, start, end, duration, lunch_formatted, net_duration])
    refresh_listbox()
    clear_fields()

def refresh_listbox():
    listbox.delete(0, tk.END)
    for i, entry in enumerate(entries):
        line = f"{i+1}. {entry[0]} | {entry[1]}–{entry[2]} → {entry[3]}"
        if lunch_used and entry[4]:
            line += f" | Lunch: {entry[4]} | Net: {entry[5]}"
        listbox.insert(tk.END, line)

    total_minutes = sum(int(h) * 60 + int(m) for h, m in (e[5].split(":") for e in entries))
    hours = total_minutes // 60
    minutes = total_minutes % 60
    total_label.config(text=f"Net Total: {hours} hours and {minutes} minutes")

def clear_fields():
    date_entry.delete(0, tk.END)
    start_entry.delete(0, tk.END)
    end_entry.delete(0, tk.END)
    lunch_entry.delete(0, tk.END)

def delete_entry():
    idx = listbox.curselection()
    if not idx:
        return
    entries.pop(idx[0])
    refresh_listbox()

def edit_entry():
    idx = listbox.curselection()
    if not idx:
        return
    entry = entries[idx[0]]
    date_entry.delete(0, tk.END)
    start_entry.delete(0, tk.END)
    end_entry.delete(0, tk.END)
    lunch_entry.delete(0, tk.END)
    date_entry.insert(0, entry[0])
    start_entry.insert(0, entry[1])
    end_entry.insert(0, entry[2])
    lunch_entry.insert(0, entry[4])
    entries.pop(idx[0])
    refresh_listbox()

def move_up():
    idx = listbox.curselection()
    if not idx or idx[0] == 0:
        return
    entries[idx[0]-1], entries[idx[0]] = entries[idx[0]], entries[idx[0]-1]
    refresh_listbox()
    listbox.select_set(idx[0]-1)

def move_down():
    idx = listbox.curselection()
    if not idx or idx[0] == len(entries)-1:
        return
    entries[idx[0]+1], entries[idx[0]] = entries[idx[0]], entries[idx[0]+1]
    refresh_listbox()
    listbox.select_set(idx[0]+1)

def calculate_total():
    if listbox.size() > len(entries):
        listbox.delete(tk.END)

    total_minutes = sum(int(h) * 60 + int(m) for h, m in (e[5].split(":") for e in entries))
    hours = total_minutes // 60
    minutes = total_minutes % 60
    summary = f"▶ Net Total: {hours} hours and {minutes} minutes"
    listbox.insert(tk.END, summary)

def export_csv():
    path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if not path:
        return

    total_minutes = sum(int(h) * 60 + int(m) for h, m in (e[5].split(":") for e in entries))
    total_str = f"{total_minutes // 60}:{total_minutes % 60:02d}"

    lunch_present = any(e[4] for e in entries)

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        if lunch_present:
            writer.writerow(["Date", "Start", "End", "Duration", "Lunch", "Net Duration"])
            for e in entries:
                writer.writerow(e)
            writer.writerow([])
            writer.writerow(["▶ Net Total", "", "", "", "", total_str])
        else:
            writer.writerow(["Date", "Start", "End", "Duration", "Net Duration"])
            for e in entries:
                writer.writerow([e[0], e[1], e[2], e[3], e[5]])
            writer.writerow([])
            writer.writerow(["▶ Net Total", "", "", "", total_str])
    # messagebox.showinfo("Success", f"Saved to {path}")

def open_calendar():
    global last_selected_date

    root.update_idletasks()
    main_x = root.winfo_x()
    main_y = root.winfo_y()
    main_width = root.winfo_width()

    calendar_width = 250
    calendar_height = 250
    popup_x = main_x + main_width - calendar_width
    popup_y = main_y

    top = tk.Toplevel(root)
    top.title("Select Date")
    top.geometry(f"{calendar_width}x{calendar_height}+{popup_x}+{popup_y}")

    today = datetime.today()
    default_date = last_selected_date + timedelta(days=1) if last_selected_date else today

    cal = Calendar(top, selectmode="day", year=default_date.year, month=default_date.month, day=default_date.day, showothermonthdays=True)
    cal.pack(padx=10, pady=10)

    def select_date():
        selected = cal.selection_get()
        last_selected_date = selected
        date_entry.delete(0, tk.END)
        date_entry.insert(0, selected.strftime("%d.%m.%Y"))
        top.destroy()

    tk.Button(top, text="Select", command=select_date).pack(pady=5)

# GUI
root = tk.Tk()
root.title("Worklog Dashboard")

tk.Label(root, text="Date (DD.MM.YYYY):").grid(row=0, column=0, sticky="e")
date_entry = tk.Entry(root)
date_entry.grid(row=0, column=1, sticky="w")
tk.Button(root, text="📅", command=open_calendar).grid(row=0, column=2, padx=5)

tk.Label(root, text="Start (HH:MM):").grid(row=1, column=0, sticky="e")
start_entry = tk.Entry(root)
start_entry.grid(row=1, column=1, columnspan=2, sticky="w")

tk.Label(root, text="End (HH:MM):").grid(row=2, column=0, sticky="e")
end_entry = tk.Entry(root)
end_entry.grid(row=2, column=1, columnspan=2, sticky="w")

tk.Label(root, text="Lunch (min or HH:MM):").grid(row=3, column=0, sticky="e")
lunch_entry = tk.Entry(root, width=5)
lunch_entry.grid(row=3, column=1, sticky="w")

tk.Button(root, text="Add Entry", width=20, command=add_entry).grid(row=4, column=0, columnspan=3, pady=5)

# Delete/Edit buttons side by side
action_frame = tk.Frame(root)
action_frame.grid(row=5, column=0, columnspan=3, pady=5)
tk.Button(action_frame, text="🗑️ Delete Selected", width=18, command=delete_entry).pack(side=tk.LEFT, padx=5)
tk.Button(action_frame, text="✏️ Edit Selected", width=18, command=edit_entry).pack(side=tk.LEFT, padx=5)

# Listbox to display entries
listbox = tk.Listbox(root, width=60)
listbox.grid(row=6, column=0, columnspan=3, pady=5)

# Total label
total_label = tk.Label(root, text="Net Total: 0 hours and 0 minutes", font=("Arial", 10, "bold"))
total_label.grid(row=7, column=0, columnspan=3, pady=(0, 10))

# Move Up/Down buttons
move_frame = tk.Frame(root)
move_frame.grid(row=8, column=0, columnspan=3)
tk.Button(move_frame, text="⬆ Move Up", width=12, command=move_up).pack(side=tk.LEFT, padx=10)
tk.Button(move_frame, text="⬇ Move Down", width=12, command=move_down).pack(side=tk.LEFT, padx=10)

# Calculate and Export buttons
tk.Button(root, text="Calculate Total", width=20, command=calculate_total).grid(row=9, column=0, columnspan=3, pady=5)
tk.Button(root, text="Export to CSV", width=20, command=export_csv).grid(row=10, column=0, columnspan=3)

# Start GUI loop
root.mainloop()
