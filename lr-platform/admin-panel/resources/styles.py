import tkinter as tk
from tkinter import ttk
from pathlib import Path


BG = '#f6faf8'
SURFACE = '#ffffff'
TEXT = '#10231c'
MUTED = '#5f7068'
BORDER = '#dce8e2'
HEADER_BG = '#ffffff'
PRIMARY = '#0b6bdc'
SUCCESS = '#05a85c'
DANGER = '#d64545'
WARNING = '#b7791f'
SOFT_GREEN = '#eaf8f1'


def resource_path(name):
    return Path(__file__).resolve().parent / name


def apply_style(root):
    root.configure(bg=BG)
    style = ttk.Style(root)
    try:
        style.theme_use('clam')
    except tk.TclError:
        pass
    style.configure('.', font=('Segoe UI', 10), foreground=TEXT)
    style.configure('TFrame', background=BG)
    style.configure('Surface.TFrame', background=SURFACE)
    style.configure('Card.TFrame', background=SURFACE, relief='flat')
    style.configure('TLabel', background=BG, foreground=TEXT)
    style.configure('Muted.TLabel', background=BG, foreground=MUTED)
    style.configure('Header.TLabel', background=HEADER_BG, foreground=TEXT, font=('Segoe UI', 17, 'bold'))
    style.configure('Treeview', rowheight=30, fieldbackground=SURFACE, background=SURFACE, foreground=TEXT, bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER)
    style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'), background='#eef5f1', foreground=TEXT, relief='flat')
    style.map('Treeview', background=[('selected', SUCCESS)], foreground=[('selected', '#ffffff')])
    style.configure('TNotebook', background=BG, borderwidth=0, tabmargins=(0, 0, 0, 0))
    style.configure('TNotebook.Tab', padding=(16, 9), font=('Segoe UI', 10, 'bold'), background='#edf5f1', foreground=MUTED, borderwidth=0)
    style.map('TNotebook.Tab', background=[('selected', SUCCESS), ('active', SOFT_GREEN)], foreground=[('selected', '#ffffff'), ('active', TEXT)])
    style.configure('TLabelframe', background=BG, foreground=TEXT, bordercolor=BORDER)
    style.configure('TLabelframe.Label', background=BG, foreground=TEXT, font=('Segoe UI', 10, 'bold'))
    style.configure('TEntry', fieldbackground=SURFACE, bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER)
    style.configure('TCombobox', fieldbackground=SURFACE, bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER)
    style.configure('TCheckbutton', background=BG, foreground=TEXT)


def button(parent, text, command, color=PRIMARY):
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg=color,
        fg='white',
        activebackground=color,
        activeforeground='white',
        relief=tk.FLAT,
        borderwidth=0,
        highlightthickness=0,
        padx=14,
        pady=7,
        cursor='hand2',
        font=('Segoe UI', 9, 'bold'),
    )


def plain_button(parent, text, command):
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg='#edf5f1',
        fg=TEXT,
        activebackground='#dbece5',
        relief=tk.FLAT,
        borderwidth=0,
        highlightthickness=0,
        padx=12,
        pady=7,
        cursor='hand2',
        font=('Segoe UI', 9, 'bold'),
    )
