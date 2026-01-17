"""
tab3.py - UPDATED v3:

- Accepts Tab2-passed results as a list of dicts:
    {
        'ffp_disp_name': 'Program Name',
        'award_miles': 50000 or 'Dynamic',
        'ffp': 'AA',
        ...
    }

- Adds load_data(results) so gui_v2.App.update_tab3_data() can call Tab3 directly.

- Converts award_miles (raw miles) -> k-miles for display/cost:
    50000 -> 50.00

- Keeps existing UI behavior:
  * first row cash price is editable and syncs to all rows
  * editable: k Miles, YQ, Mile Evaluation, Cash Price (first row only)
  * total cost auto-calculates when possible
"""

import tkinter as tk
from tkinter import ttk, messagebox


class Tab3Frame(ttk.Frame):
    """Tab 3: Award vs Cash Price Comparison"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.shared_cash_price = 0.0  # Shared across all programs

        try:
            self._setup_ui()
            parent.bind('<<NotebookTabChanged>>', self._on_tab_shown)
        except Exception as e:
            messagebox.showerror("Tab 3 Error", str(e))
            raise

    # ---------- Public API for Tab2/App communication ----------

    def load_data(self, results):
        """
        Called by App.update_tab3_data(results).
        Stores results in app.search_context and refreshes the table.
        """
        if not hasattr(self.app, 'search_context') or not isinstance(self.app.search_context, dict):
            self.app.search_context = {}

        self.app.search_context['results'] = results
        self._refresh_from_context()

    # ---------- Tab shown / refresh ----------

    def _on_tab_shown(self, event=None):
        """Called when any tab is shown - refresh if this is Tab 3"""
        notebook = self.master
        selected_index = notebook.index(notebook.select())
        our_index = notebook.index(self)
        if selected_index == our_index:
            self._refresh_from_context()

    def _refresh_from_context(self):
        """Refresh the display based on current search_context"""
        if hasattr(self.app, 'search_context') and self.app.search_context.get('results'):
            self._load_previous_search()
        else:
            self._show_no_search_message()

    # ---------- UI ----------

    def _setup_ui(self):
        """Setup main UI layout"""
        # Search summary frame
        summary_frame = ttk.LabelFrame(self, text="Previous Search Summary", padding=10)
        summary_frame.pack(fill=tk.BOTH, padx=5, pady=5)

        self.summary_label = ttk.Label(
            summary_frame,
            text="No search data yet",
            wraplength=900,
            justify=tk.LEFT
        )
        self.summary_label.pack(fill=tk.BOTH, expand=True)

        # Instructions
        instructions_frame = ttk.LabelFrame(self, text="Instructions", padding=10)
        instructions_frame.pack(fill=tk.X, padx=5, pady=5)

        instructions = ttk.Label(
            instructions_frame,
            text=("Enter the cash price (top row only). Blue columns are editable. "
                  "Double-click to edit k Miles, YQ, or Mile Evaluation. "
                  "Total Cost auto-calculates. Cash price syncs to all programs."),
            wraplength=900,
            justify=tk.LEFT
        )
        instructions.pack(fill=tk.X)

        # Comparison table frame
        table_frame = ttk.LabelFrame(self, text="Award vs Cash Price Comparison", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ('Program', 'k Miles', 'YQ', 'Mile Evaluation', 'Total Cost', 'Cash Price', 'Worth it?')
        self.tree = ttk.Treeview(table_frame, columns=columns, height=12, show='headings')

        column_widths = {
            'Program': 220,
            'k Miles': 90,
            'YQ': 90,
            'Mile Evaluation': 120,
            'Total Cost': 110,
            'Cash Price': 110,
            'Worth it?': 90
        }

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths[col], anchor=tk.CENTER)

        self.tree.tag_configure('editable', background='#E0F0FF')

        vsb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        new_search_button = ttk.Button(
            button_frame,
            text="New Search (Back to Tab 2)",
            command=self._new_search
        )
        new_search_button.pack(side=tk.LEFT, padx=5)

        self.program_rows = {}
        self.first_row_id = None

        self.tree.bind('<Double-1>', self._on_cell_click)

    def _show_no_search_message(self):
        """Show message when no previous search"""
        self.summary_label.config(
            text="No previous search found.\nPlease use Tab 2 to search for award programs first."
        )

    # ---------- Data normalization ----------

    def _normalize_results(self, results):
        """
        Accept either:
          - list of dicts from Tab2 (current)
          - list of tuples (legacy): (program_name, k_miles_or_miles, ffp_code)
        Returns a list of dicts:
          { program_name, k_miles, ffp_code }
        """
        normalized = []
        if not isinstance(results, list):
            return normalized

        for item in results:
            # Current format: dict from Tab2
            if isinstance(item, dict):
                program_name = item.get('ffp_disp_name') or item.get('program_name') or "Unknown"
                ffp_code = item.get('ffp') or item.get('ffp_code') or "UNKNOWN"
                miles = item.get('award_miles')

                k_miles = miles
                if isinstance(miles, (int, float)):
                    # Tab2 sends raw miles; Tab3 uses k-miles
                    k_miles = float(miles) / 1000.0

                normalized.append({
                    'program_name': program_name,
                    'k_miles': k_miles,
                    'ffp_code': ffp_code
                })
                continue

            # Legacy format: tuple/list
            if isinstance(item, (tuple, list)) and len(item) >= 3:
                program_name = item[0]
                miles_or_k = item[1]
                ffp_code = item[2]

                k_miles = miles_or_k
                if isinstance(miles_or_k, (int, float)):
                    # Heuristic: if > 1000 assume raw miles; else assume already k-miles
                    k_miles = float(miles_or_k) / 1000.0 if miles_or_k > 1000 else float(miles_or_k)

                normalized.append({
                    'program_name': program_name,
                    'k_miles': k_miles,
                    'ffp_code': ffp_code
                })

        return normalized

    # ---------- Load / render ----------

    def _load_previous_search(self):
        """Load results from previous Tab 2 search"""
        context = self.app.search_context if hasattr(self.app, 'search_context') else {}

        # Summary: be robust if Tab2 did not populate these fields
        carrier = context.get('carrier_code', 'N/A')
        origin = context.get('origin', 'N/A')
        dest = context.get('destination', 'N/A')
        distance = context.get('distance', 'N/A')
        cabin = context.get('cabin', 'N/A')

        results_raw = context.get('results', [])
        results = self._normalize_results(results_raw)

        summary_text = (
            f"Carrier: {carrier} | Cabin: {cabin}\n"
            f"Route: {origin} → {dest} | Distance: {distance} miles\n"
            f"Programs received: {len(results)}"
        )
        self.summary_label.config(text=summary_text)

        # Clear table
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.program_rows = {}
        self.first_row_id = None
        self.shared_cash_price = 0.0

        # Populate
        for idx, r in enumerate(results):
            program_name = r['program_name']
            k_miles = r['k_miles']
            ffp_code = r['ffp_code']

            valuation = self._get_valuation(ffp_code)

            if isinstance(k_miles, (int, float)):
                k_miles_display = f"{float(k_miles):.2f}"
            else:
                k_miles_display = str(k_miles)  # Dynamic / other strings

            cash_price_display = "0.00" if idx == 0 else f"{self.shared_cash_price:.2f}"

            if isinstance(k_miles, (int, float)) and valuation is not None:
                total_cost = (float(k_miles) * 10 * float(valuation)) + 0.0  # YQ default 0
                total_cost_display = f"${total_cost:.2f}"
            else:
                total_cost_display = "---"

            row_id = self.tree.insert(
                '',
                'end',
                tags=('editable',),
                values=(
                    program_name,
                    k_miles_display,
                    "0.00",  # YQ
                    f"{valuation:.2f}" if valuation is not None else "ERROR",
                    total_cost_display,
                    cash_price_display,
                    "-"  # Worth it?
                )
            )

            if idx == 0:
                self.first_row_id = row_id

            self.program_rows[row_id] = {
                'ffp_code': ffp_code,
                'program_name': program_name,
                'k_miles': k_miles,
                'valuation': valuation,
                'is_first_row': idx == 0
            }

    def _get_valuation(self, ffp_code):
        """Get valuation (cpp) for FFP from valuations.json (supports dict or list formats)"""
        if not hasattr(self.app, 'valuations'):
            return None

        valuations = self.app.valuations

        # Common case: dict like { "AA": 1.5, ... }
        if isinstance(valuations, dict):
            return valuations.get(ffp_code)

        # Fallback: list of dicts like [{ "ffp": "AA", "value": 1.5 }, ...]
        if isinstance(valuations, list):
            for v in valuations:
                if isinstance(v, dict) and (v.get('ffp') == ffp_code or v.get('code') == ffp_code):
                    return v.get('value') or v.get('valuation') or v.get('cpp')
        return None

    # ---------- Editing / calculations ----------

    def _on_cell_click(self, event):
        """Handle double-click on cell for editing"""
        item = self.tree.identify_row(event.y)
        if not item:
            return

        column_id = self.tree.identify_column(event.x)
        if not column_id:
            return

        col_index = int(column_id.lstrip('#')) - 1
        row_data = self.program_rows.get(item)
        is_first_row = row_data['is_first_row'] if row_data else False

        # Editable columns: 1 (k Miles), 2 (YQ), 3 (Mile Evaluation), 5 (Cash Price)
        editable_cols = [1, 2, 3, 5]

        if col_index == 5 and not is_first_row:
            messagebox.showinfo("Read-Only", "Cash Price is only editable in the first row.")
            return

        if col_index not in editable_cols:
            messagebox.showinfo("Read-Only", "This column is read-only.")
            return

        values = list(self.tree.item(item, 'values'))
        current_value = values[col_index]

        x, y, width, height = self.tree.bbox(item, column_id)
        if x <= 0:
            return

        entry = ttk.Entry(self.tree, width=10)
        entry.insert(0, str(current_value))
        entry.place(x=x, y=y, width=width, height=height)

        def save_edit(event=None):
            new_value = entry.get().strip()

            # Allow non-numeric ONLY for k Miles (e.g., "Dynamic")
            if col_index != 1:
                try:
                    float(new_value)
                except ValueError:
                    messagebox.showerror("Input Error", "Please enter a valid number")
                    entry.focus()
                    return

            values[col_index] = new_value
            self.tree.item(item, values=values)
            entry.destroy()

            # If Cash Price edited in first row => sync
            if col_index == 5 and is_first_row:
                try:
                    self.shared_cash_price = float(new_value)
                except ValueError:
                    self.shared_cash_price = 0.0
                self._sync_cash_price_all_rows()

            self._recalculate_row(item)

        def cancel_edit(event=None):
            entry.destroy()

        entry.bind('<Return>', save_edit)
        entry.bind('<Escape>', cancel_edit)
        entry.focus()
        entry.select_range(0, tk.END)

    def _sync_cash_price_all_rows(self):
        """Update Cash Price display in all non-first rows with the shared value"""
        for item in self.tree.get_children():
            row_data = self.program_rows.get(item)
            if not row_data or row_data['is_first_row']:
                continue

            values = list(self.tree.item(item, 'values'))
            values[5] = f"{self.shared_cash_price:.2f}"
            self.tree.item(item, values=values)
            self._recalculate_row(item)

    def _recalculate_row(self, row_id):
        """Recalculate Total Cost and Worth it? for a row"""
        values = list(self.tree.item(row_id, 'values'))

        # k Miles
        try:
            k_miles = float(values[1])  # thousands
        except ValueError:
            values[4] = "---"
            values[6] = "-"
            self.tree.item(row_id, values=values)
            return

        try:
            yq = float(values[2])
            cash_price = float(values[5])
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numbers")
            return

        try:
            valuation = float(values[3])
        except ValueError:
            values[4] = "ERROR"
            values[6] = "ERROR"
            self.tree.item(row_id, values=values)
            return

        total_cost = (k_miles * 10 * valuation) + yq
        worth_it = "Y" if total_cost <= cash_price else "N"

        values[4] = f"${total_cost:.2f}"
        values[6] = worth_it
        self.tree.item(row_id, values=values)

    def _new_search(self):
        """Return to Tab 2 for new search"""
        self.app.search_context = {
            'carrier_code': None,
            'origin': None,
            'destination': None,
            'distance': None,
            'cabin': None,
            'results': []
        }
        notebook = self.master
        notebook.select(1)
