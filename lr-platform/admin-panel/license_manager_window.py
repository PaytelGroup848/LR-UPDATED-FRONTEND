import tkinter as tk
from tkinter import messagebox, ttk

from resources.styles import BORDER, DANGER, HEADER_BG, MUTED, PRIMARY, SUCCESS, SURFACE, TEXT, button


class LicenseManagerWindow(tk.Toplevel):
    def __init__(self, parent, client):
        super().__init__(parent)
        self.client = client
        self.title('LR Licence Manage')
        self.geometry('940x620')
        self.minsize(820, 540)
        self.configure(bg='#f6faf8')
        self.transient(parent)

        self._build()
        self.load_keys()

    def _build(self):
        header = tk.Frame(self, bg=HEADER_BG, highlightbackground=BORDER, highlightthickness=1)
        header.pack(fill=tk.X)

        title_box = tk.Frame(header, bg=HEADER_BG)
        title_box.pack(side=tk.LEFT, padx=18, pady=14)
        tk.Label(title_box, text='Licence Manage', bg=HEADER_BG, fg=TEXT, font=('Segoe UI', 18, 'bold')).pack(anchor=tk.W)
        tk.Label(title_box, text='Generate and revoke LR product keys', bg=HEADER_BG, fg=MUTED, font=('Segoe UI', 9)).pack(anchor=tk.W)

        button(header, 'Logout', self.destroy, DANGER).pack(side=tk.RIGHT, padx=18, pady=14)

        form = ttk.LabelFrame(self, text='Generate Product Key(s)', padding=14)
        form.pack(fill=tk.X, padx=18, pady=(18, 10))

        self.plan_name = tk.StringVar(value='STANDARD')
        self.valid_days = tk.IntVar(value=365)
        self.issued_to = tk.StringVar()
        self.quantity = tk.IntVar(value=1)

        self._entry(form, 'Plan name', self.plan_name, 0, 0)
        ttk.Label(form, text='VM limit').grid(row=1, column=0, sticky=tk.W, pady=8)
        ttk.Label(form, text='1 VM per key, transfer after 90 days').grid(row=1, column=1, sticky=tk.W, padx=(10, 20), pady=8)
        self._spin(form, 'Valid days', self.valid_days, 0, 2, 1, 3650)
        self._spin(form, 'Quantity', self.quantity, 1, 2, 1, 500)
        self._entry(form, 'Issued to', self.issued_to, 2, 0, columnspan=3)
        button(form, 'Generate', self.generate_keys, SUCCESS).grid(row=2, column=3, sticky=tk.E, padx=(12, 0), pady=8)

        table_wrap = ttk.Frame(self, padding=(18, 8, 18, 12))
        table_wrap.pack(fill=tk.BOTH, expand=True)

        actions = ttk.Frame(table_wrap)
        actions.pack(fill=tk.X, pady=(0, 8))
        button(actions, 'Refresh', self.load_keys, PRIMARY).pack(side=tk.LEFT, padx=(0, 8))
        button(actions, 'Revoke Selected', self.revoke_selected, DANGER).pack(side=tk.LEFT)

        columns = ('key_code', 'plan_name', 'vm_limit', 'valid_days', 'issued_to', 'status')
        self.tree = ttk.Treeview(table_wrap, columns=columns, show='headings', selectmode='browse')
        headings = {
            'key_code': ('Key', 260),
            'plan_name': ('Plan', 120),
            'vm_limit': ('VM Limit', 100),
            'valid_days': ('Valid Days', 100),
            'issued_to': ('Issued To', 180),
            'status': ('Status', 90),
        }
        for column, (label, width) in headings.items():
            self.tree.heading(column, text=label)
            self.tree.column(column, width=width, anchor=tk.W)

        scroll = ttk.Scrollbar(table_wrap, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _entry(self, parent, label, variable, row, column, columnspan=1):
        ttk.Label(parent, text=label).grid(row=row, column=column, sticky=tk.W, pady=8)
        ttk.Entry(parent, textvariable=variable, width=28).grid(
            row=row,
            column=column + 1,
            columnspan=columnspan,
            sticky=tk.EW,
            padx=(10, 20),
            pady=8,
        )

    def _spin(self, parent, label, variable, row, column, start, end):
        ttk.Label(parent, text=label).grid(row=row, column=column, sticky=tk.W, pady=8)
        ttk.Spinbox(parent, textvariable=variable, from_=start, to=end, width=10).grid(
            row=row,
            column=column + 1,
            sticky=tk.W,
            padx=(10, 20),
            pady=8,
        )

    def load_keys(self):
        try:
            keys = self.client.list_product_keys()
        except Exception as error:
            messagebox.showerror('Licence Manage', str(error), parent=self)
            return

        self.tree.delete(*self.tree.get_children())
        for key in keys:
            status = 'REVOKED' if key.get('is_revoked') else 'ACTIVE'
            self.tree.insert('', tk.END, values=(
                key.get('key_code', ''),
                key.get('plan_name', ''),
                '1',
                key.get('valid_days', ''),
                key.get('issued_to') or '',
                status,
            ))

    def generate_keys(self):
        try:
            keys = self.client.create_product_keys(
                plan_name=self.plan_name.get().strip() or 'STANDARD',
                max_activations=1,
                valid_days=int(self.valid_days.get()),
                issued_to=self.issued_to.get().strip() or None,
                quantity=int(self.quantity.get()),
            )
        except Exception as error:
            messagebox.showerror('Licence Manage', str(error), parent=self)
            return

        codes = '\n'.join(key.get('key_code', '') for key in keys)
        messagebox.showinfo('Product key(s) generated', codes or 'Keys generated.', parent=self)
        self.load_keys()

    def revoke_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo('Licence Manage', 'Select a key first.', parent=self)
            return

        key_code = self.tree.item(selected[0], 'values')[0]
        if not messagebox.askyesno('Revoke key', f'Revoke product key {key_code}?', parent=self):
            return

        try:
            self.client.revoke_product_key(key_code)
        except Exception as error:
            messagebox.showerror('Licence Manage', str(error), parent=self)
            return

        self.load_keys()
