import tkinter as tk
from tkinter import messagebox, filedialog
from tkcalendar import Calendar
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font
from datetime import datetime, timedelta

entries = []
last_selected_date = None

def add_entry():
    date = date_entry.get()
    start = start_entry.get()
    end = end_entry.get()
    lunch = lunch_entry.get().strip()
    comment = day_comment.get().strip()
    if comment == "comment...": comment = ""
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
    lunch_formatted, lunch_minutes = "", 0
    if lunch:
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
    net_duration = f"{net_minutes // 60}:{net_minutes % 60:02d}" if lunch else duration
    entries.append([date, start, end, duration, lunch_formatted, net_duration, comment])
    refresh_listbox()
    clear_fields()

def add_holiday_entry():
    global last_selected_date
    d = last_selected_date or datetime.today()
    comment = holiday_comment.get().strip()
    label = f"{d.strftime('%d.%m.%Y')} (Holiday)"
    if comment:
        label += f" — {comment}"
    entries.append([label, "00:00", "00:00", "0:00", "", "0:00", comment])
    refresh_listbox()

def refresh_listbox():
    listbox.delete(0, tk.END)
    total_minutes = 0
    for i, e in enumerate(entries):
        line = f"{i+1}. {e[0]} | {e[1]}–{e[2]} → {e[3]}"
        if e[4]: line += f" | Lunch: {e[4]} | Net: {e[5]}"
        elif e[5] != e[3]: line += f" | Net: {e[5]}"
        is_holiday = "(Holiday)" in str(e[0])
        if e[6] and not is_holiday: line += f" | {e[6]}"
        listbox.insert(tk.END, line)
        try:
            h, m = map(int, e[5].split(":"))
            total_minutes += h * 60 + m
        except (ValueError, AttributeError):
            pass  # Skip if net duration is invalid
    total_label.config(text=f"Net Total: {total_minutes//60} hours and {total_minutes%60} minutes")

def clear_fields():
    date_entry.delete(0, tk.END)
    start_entry.delete(0, tk.END)
    end_entry.delete(0, tk.END)
    lunch_entry.delete(0, tk.END)
    day_comment.delete(0, tk.END)
    day_comment.insert(0, "comment...")
    day_comment.config(fg="gray")
    holiday_comment.delete(0, tk.END)

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
        day_comment.delete(0, tk.END); day_comment.insert(0, e[6])
        day_comment.config(fg="black")
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
    total_minutes = sum(int(h)*60+int(m) for h,m in (e[5].split(":") for e in entries))
    listbox.insert(tk.END, f"▶ Net Total: {total_minutes//60} hours and {total_minutes%60} minutes")

def export_excel():
    path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
    if not path: return
    wb = Workbook(); ws = wb.active; ws.title = "Worklog"
    headers = ["Date", "Start", "End", "Duration", "Lunch", "Net Duration", "Comment"]
    ws.append(headers); [setattr(c, 'font', Font(bold=True)) for c in ws[1]]
    for e in entries:
        row = [e[0], e[1], e[2], e[3]]
        row += [e[4], e[5]] if e[4] else ["", e[5] if e[5] != e[3] else ""]
        row.append(e[6] if e[6] else "")
        ws.append(row)
    total_minutes = sum(int(h)*60+int(m) for h,m in (e[5].split(":") for e in entries))
    ws.append([])
    ws.append(["▶ Net Total", "", "", "", "", f"{total_minutes//60}:{total_minutes%60:02d}", ""])
    wb.save(path)
    messagebox.showinfo("Success", f"Excel file saved:\n{path}")

def load_file():
    path = filedialog.askopenfilename(title="Open Excel file", filetypes=[("Excel files", "*.xlsx")])
    if not path: return
    try:
        wb = load_workbook(path)
        ws = wb.active
        entries.clear()
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or not row[0]: continue
            if str(row[0]).startswith("▶"): continue  # Skip total row
            safe_row = ["" if v is None else str(v) for v in row[:7]]
            while len(safe_row) < 7:
                safe_row.append("")
            # Check if lunch should be cleared (if duration equals net duration and lunch is non-empty)
            if safe_row[4] and safe_row[3] == safe_row[5]:
                safe_row[4] = ""
            # Reconstruct net duration if lunch is empty
            if not safe_row[4] and not safe_row[5]:
                safe_row[5] = safe_row[3]
            entries.append(safe_row)
        refresh_listbox()
        messagebox.showinfo("Imported", f"Loaded entries from:\n{path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load file:\n{e}")

def open_calendar():
    global last_selected_date
    root.update_idletasks()
    x = calendar_btn.winfo_rootx() + calendar_btn.winfo_width() + 10
    y = calendar_btn.winfo_rooty()
    top = tk.Toplevel(root)
    top.geometry("1x1+{}+{}".format(x, y))
    top.overrideredirect(True)

    # Set next day for second or third opening
    open_count = getattr(open_calendar, 'count', 0) + 1
    setattr(open_calendar, 'count', open_count)
    if open_count >= 2 and last_selected_date:
        next_date = last_selected_date + timedelta(days=1)
    else:
        next_date = datetime.today()

    def animate(w=1, h=1):
        if w < 250:
            w += 20
            h += 20
            top.geometry(f"{w}x{h}+{x}+{y}")
            top.after(10, lambda: animate(w, h))
        else:
            top.overrideredirect(False)
            cal = Calendar(top, selectmode="day", year=next_date.year, month=next_date.month, day=next_date.day)
            cal.pack(padx=10, pady=10)
            cal.bind("<<CalendarSelected>>", lambda e: select_date(cal))
            tk.Button(top, text="Close", command=top.destroy, width=5).pack(pady=(0, 5))

    def select_date(cal):
        global last_selected_date
        last_selected_date = cal.selection_get()
        date_entry.delete(0, tk.END)
        date_entry.insert(0, last_selected_date.strftime("%d.%m.%Y"))
        top.destroy()

    animate()

# === GUI ===
root = tk.Tk()
root.title(" Work Log")
root.configure(bg="#f3f3f3")

# Main frame for dynamic resizing
main_frame = tk.Frame(root, bg="#f3f3f3")
main_frame.pack(padx=10, pady=10, fill="both", expand=True)

# Row 0 — Date + 📅 + 📂
tk.Label(main_frame, text="Date (DD.MM.YYYY):", bg="#f3f3f3").grid(row=0, column=0, sticky="e", padx=(0, 5), pady=5)
date_entry = tk.Entry(main_frame, width=20)
date_entry.grid(row=0, column=1, sticky="w", pady=5)

calendar_btn = tk.Button(main_frame, text="📅", font=("Segoe UI", 11), command=open_calendar)
calendar_btn.grid(row=0, column=2, padx=(10, 10), sticky="w")  # Added padding for professional gap

load_icon_btn = tk.Button(main_frame, text="📂", font=("Segoe UI", 11), command=load_file)
load_icon_btn.grid(row=0, column=3, padx=(0, 0), sticky="w")  # Adjusted position with gap

def show_tooltip(event):
    tooltip = tk.Toplevel(root)
    tooltip.wm_overrideredirect(True)
    tooltip.geometry(f"+{event.x_root+10}+{event.y_root+10}")
    label = tk.Label(tooltip, text="Open file", bg="lightyellow", relief="solid", borderwidth=1, font=("Segoe UI", 8))
    label.pack()
    load_icon_btn.tooltip = tooltip

def hide_tooltip(event):
    if hasattr(load_icon_btn, 'tooltip'):
        load_icon_btn.tooltip.destroy()
        del load_icon_btn.tooltip

load_icon_btn.bind("<Enter>", show_tooltip)
load_icon_btn.bind("<Leave>", hide_tooltip)

# Row 1 — Start
tk.Label(main_frame, text="Start (HH:MM):", bg="#f3f3f3").grid(row=1, column=0, sticky="e", padx=(0, 5), pady=5)
start_entry = tk.Entry(main_frame, width=20)
start_entry.grid(row=1, column=1, columnspan=2, sticky="w", pady=5)

# Row 2 — End
tk.Label(main_frame, text="End (HH:MM):", bg="#f3f3f3").grid(row=2, column=0, sticky="e", padx=(0, 5), pady=5)
end_entry = tk.Entry(main_frame, width=20)
end_entry.grid(row=2, column=1, columnspan=2, sticky="w", pady=5)

# Row 3 — Comment
tk.Label(main_frame, text="Comment:", bg="#f3f3f3").grid(row=3, column=0, sticky="e", padx=(0, 5), pady=5)
day_comment = tk.Entry(main_frame, width=20, fg="gray")
day_comment.grid(row=3, column=1, columnspan=2, sticky="w", pady=5)
day_comment.insert(0, "comment...")

def clear_placeholder(event):
    if day_comment.get() == "comment...":
        day_comment.delete(0, tk.END)
        day_comment.config(fg="black")

def restore_placeholder(event):
    if not day_comment.get():
        day_comment.insert(0, "comment...")
        day_comment.config(fg="gray")

day_comment.bind("<FocusIn>", clear_placeholder)
day_comment.bind("<FocusOut>", restore_placeholder)

# Row 4 — Lunch + Holiday + Holiday comment
tk.Label(main_frame, text="Lunch (min or HH:MM):", bg="#f3f3f3").grid(row=4, column=0, sticky="e", padx=(0, 5), pady=5)
lunch_frame = tk.Frame(main_frame, bg="#f3f3f3")
lunch_frame.grid(row=4, column=1, columnspan=2, sticky="w", pady=5)
lunch_entry = tk.Entry(lunch_frame, width=8)
lunch_entry.grid(row=0, column=0, sticky="w")

tk.Button(lunch_frame, text="Holiday", font=("Segoe UI", 9), command=add_holiday_entry).grid(row=0, column=1, padx=(10, 0), sticky="w")

holiday_comment = tk.Entry(lunch_frame, width=20, fg="black")
holiday_comment.grid(row=0, column=2, padx=(10, 0), sticky="w")

# Row 5 — Add Entry
tk.Button(main_frame, text="Add Entry", command=add_entry).grid(row=5, column=0, columnspan=3, pady=10)

# Row 6 — Edit/Delete
action_frame = tk.Frame(main_frame, bg="#f3f3f3")
action_frame.grid(row=6, column=0, columnspan=3, pady=5)
tk.Button(action_frame, text="🗑️ Delete Selected", command=delete_entry).pack(side=tk.LEFT, padx=5)
tk.Button(action_frame, text="✏️ Edit Selected", command=edit_entry).pack(side=tk.LEFT, padx=5)

# Row 7 — Listbox with Scrollbar
listbox_frame = tk.Frame(main_frame)
listbox_frame.grid(row=7, column=0, columnspan=3, pady=5, sticky="nsew")
scrollbar = tk.Scrollbar(listbox_frame, orient="vertical")
listbox = tk.Listbox(listbox_frame, width=55, yscrollcommand=scrollbar.set, justify="left")
scrollbar.config(command=listbox.yview)
scrollbar.pack(side=tk.RIGHT, fill="y")
listbox.pack(side=tk.LEFT, fill="both", expand=True)

# Row 8 — Total
total_label = tk.Label(main_frame, text="Net Total: 0 hours and 0 minutes", font=("Segoe UI", 10, "bold"), bg="#f3f3f3")
total_label.grid(row=8, column=0, columnspan=3, pady=(0, 10))

# Row 9 — Move Up/Down
move_frame = tk.Frame(main_frame, bg="#f3f3f3")
move_frame.grid(row=9, column=0, columnspan=3)
tk.Button(move_frame, text="⬆ Move Up", command=move_up).pack(side=tk.LEFT, padx=10)
tk.Button(move_frame, text="⬇ Move Down", command=move_down).pack(side=tk.LEFT, padx=10)

# Row 10 — Bottom row
bottom_row = tk.Frame(main_frame, bg="#f3f3f3")
bottom_row.grid(row=10, column=0, columnspan=3, pady=(5, 10))
tk.Button(bottom_row, text="Calculate Total", command=calculate_total).pack(side=tk.LEFT, padx=(0, 10))
tk.Button(bottom_row, text="Export to Excel", command=export_excel).pack(side=tk.LEFT)

# Configure grid to expand with window
main_frame.columnconfigure(1, weight=1)
main_frame.rowconfigure(7, weight=1)  # Let listbox row expand

root.mainloop()