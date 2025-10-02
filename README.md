# worklog_dashboard
Assistant for recording working hours at work

Worklog Dashboard is a lightweight desktop application built with Python and Tkinter for tracking daily work sessions. 
It allows users to log start and end times, optionally include lunch breaks, and automatically calculates net working hours. 
Entries can be sorted, edited, deleted, and exported to CSV.

Requirements
Python 3.8+

tkinter (included with Python)

tkcalendar for the date picker

Install tkcalendar via pip:

bash
pip install tkcalendar
Calendar Setup Note
The calendar widget (tkcalendar) must be installed and properly configured. 
The application assumes Wednesday is the central anchor of the week view. 
This is important for consistent weekday alignment across different locales. 
If your system uses a different first day of the week, adjust your locale settings or calendar configuration accordingly.
CSV Export Format

<img width="484" height="601" alt="Dashboard" src="https://github.com/user-attachments/assets/0efce686-bdca-4c79-8ecc-3537455cc4b6" />


Depending on whether lunch is used:

With lunch:

Date | Start | End | Duration | Lunch | Net Duration
...
▶ Net Total: HH:MM
Without lunch:

Date | Start | End | Duration | Net Duration
...
▶ Net Total: HH:MM

    python worklog_dashboard.py



