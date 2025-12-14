"""
tab3.py - UPDATED v2: 
1. Miles column renamed to "k Miles" (receives k-miles from tab2)
2. Auto-populates Total Cost on load (formula: k_miles * 10 * valuation + YQ)
3. Mile Evaluation changes trigger Total Cost recalculation
4. No error on 'Dynamic' miles - just shows '---' for Total Cost
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

    def _on_tab_shown(self, event=None):
        """Called when any tab is shown - refresh if this is Tab 3"""
        notebook = self.master
        selected_index = notebook.index(notebook.select())
        our_index = notebook.index(self)
        if selected_index == our_index:
            self._refresh_from_context()

    def _refresh_from_context(self):
        """Refresh the display based on current search_context"""
        if self.app.search_context.get('results'):
            self._load_previous_search()
        else:
            self._show_no_search_message()

    def _setup_ui(self):
        """Setup main UI layout"""
        # Search summary frame
        summary_frame = ttk.LabelFrame(self, text="Previous Search Summary", padding=10)
        summary_frame.pack(fill=tk.BOTH, padx=5, pady=5)
        self.summary_label = ttk.Label(summary_frame, text="No search data yet",
                                       wraplength=400, justify=tk.LEFT)
        self.summary_label.pack(fill=tk.BOTH, expand=True)

        # Instructions
        instructions_frame = ttk.LabelFrame(self, text="Instructions", padding=10)
        instructions_frame.pack(fill=tk.X, padx=5, pady=5)
        instructions = ttk.Label(
            instructions_frame,
            text="Enter the cash price (top row only). Blue columns are editable. Double-click to edit k Miles, YQ, or Mile Evaluation. Total Cost auto-calculates. Cash price syncs to all programs.",
            wraplength=400,
            justify=tk.LEFT
        )
        instructions.pack(fill=tk.X)

        # Comparison table frame
        table_frame = ttk.LabelFrame(self, text="Award vs Cash Price Comparison", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create Treeview for the comparison table
        # CHANGE: Renamed "Miles" to "k Miles" to reflect k-miles format
        columns = ('Program', 'k Miles', 'YQ', 'Mile Evaluation', 'Total Cost', 'Cash Price', 'Worth it?')
        self.tree = ttk.Treeview(table_frame, columns=columns, height=10, show='headings')

        # Define column headings and widths
        column_widths = {
            'Program': 150,
            'k Miles': 80,  # Changed from 'Miles'
            'YQ': 80,
            'Mile Evaluation': 100,
            'Total Cost': 100,
            'Cash Price': 100,
            'Worth it?': 80
        }
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths[col], anchor=tk.CENTER)

        # Configure tag styles
        self.tree.tag_configure('editable', background='#E0F0FF')
        self.tree.tag_configure('first_row', background='#D0E8FF')

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        # Button frame
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        new_search_button = ttk.Button(button_frame, text="New Search (Back to Tab 2)",
                                       command=self._new_search)
        new_search_button.pack(side=tk.LEFT, padx=5)

        self.program_rows = {}
        self.first_row_id = None

        # Bind double-click to edit
        self.tree.bind('<Double-1>', self._on_cell_click)

    def _show_no_search_message(self):
        """Show message when no previous search"""
        self.summary_label.config(text="No previous search found.\nPlease use Tab 2 to search for award programs first.")

    def _load_previous_search(self):
        """Load results from previous Tab 2 search"""
        context = self.app.search_context

        # Build summary text
        route = context.get('route_type', 'N/A')
        carrier = context.get('carrier_code', 'N/A')
        origin = context.get('origin', 'N/A')
        dest = context.get('destination', 'N/A')
        distance = context.get('distance', 'N/A')
        cabin = context.get('cabin', 'N/A')
        summary_text = (f"Route Type: {route} | Carrier: {carrier}\n"
                       f"Route: {origin} → {dest} | Distance: {distance} miles\n"
                       f"Cabin: {cabin}")
        self.summary_label.config(text=summary_text)

        # Clear previous table entries and reset
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.program_rows = {}
        self.first_row_id = None
        self.shared_cash_price = 0.0

        # Populate table with programs
        results = context.get('results', [])
        for idx, result in enumerate(results):
            # Unpack tuple format from Tab2 (already in k-miles)
            program_name, k_miles, ffp_code = result

            # Get valuation
            valuation = self._get_valuation(ffp_code)

            # FIX: Handle both numeric k_miles and "Dynamic" string
            if isinstance(k_miles, (int, float)):
                k_miles_display = f"{k_miles:.2f}"
            else:
                k_miles_display = str(k_miles)  # "Dynamic" or other strings

            # For first row: Cash Price is editable
            # For other rows: Cash Price displays the shared value (read-only)
            if idx == 0:
                cash_price_display = "0.00"
            else:
                cash_price_display = f"{self.shared_cash_price:.2f}"

            # CHANGE 2: Auto-calculate Total Cost on load
            # Formula: k_miles * 10 * valuation + YQ
            # If k_miles is not numeric or valuation is None, show "---"
            if isinstance(k_miles, (int, float)) and valuation is not None:
                # k_miles is in thousands, valuation is in cents per point
                # 10 is the conversion factor (cpp to dollars)
                total_cost = (k_miles * 10 * valuation) + 0.0  # YQ default is 0
                total_cost_display = f"${total_cost:.2f}"
            else:
                # If Dynamic or no valuation, show "---"
                total_cost_display = "---"

            # Create row
            row_id = self.tree.insert('', 'end', tags=('editable',), values=(
                program_name,
                k_miles_display,  # k Miles (already in k format from tab2)
                "0.00",  # YQ default
                f"{valuation:.2f}" if valuation is not None else "ERROR",
                total_cost_display,  # Auto-populated Total Cost
                cash_price_display,
                "-"  # Worth it (will be calculated when cash price is entered)
            ))

            if idx == 0:
                self.first_row_id = row_id

            self.program_rows[row_id] = {
                'ffp_code': ffp_code,
                'program_name': program_name,
                'k_miles': k_miles,  # Store original k-miles value
                'valuation': valuation,
                'is_first_row': idx == 0
            }

    def _get_valuation(self, ffp_code):
        """Get valuation (cpp) for FFP from valuations.json"""
        valuations = self.app.valuations
        if ffp_code not in valuations:
            return None
        return valuations[ffp_code]

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

        # Special rule: Only first row can edit Cash Price
        if col_index == 5 and not is_first_row:
            messagebox.showinfo("Read-Only", "Cash Price is only editable in the first row.")
            return

        if col_index not in editable_cols:
            messagebox.showinfo("Read-Only", "This column is read-only.")
            return

        # Get current value
        values = list(self.tree.item(item, 'values'))
        current_value = values[col_index]

        # Get the bounding box for this cell
        x, y, width, height = self.tree.bbox(item, column_id)
        if x <= 0:
            return

        # Create entry widget for editing
        entry = ttk.Entry(self.tree, width=10)
        entry.insert(0, str(current_value))
        entry.place(x=x, y=y, width=width, height=height)

        def save_edit(event=None):
            new_value = entry.get()
            try:
                float(new_value)
                values[col_index] = new_value
                self.tree.item(item, values=values)
                entry.destroy()

                # If Cash Price was edited (first row, col 5), sync to all other rows
                if col_index == 5 and is_first_row:
                    self.shared_cash_price = float(new_value)
                    self._sync_cash_price_all_rows()

                # CHANGE 3: If Mile Evaluation (col 3) was edited, recalculate Total Cost
                if col_index == 3:
                    self._recalculate_row(item)

                # Recalculate this row (handles all edits)
                self._recalculate_row(item)

            except ValueError:
                messagebox.showerror("Input Error", "Please enter a valid number")
                entry.focus()

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
                continue  # Skip first row

            # Update Cash Price column (index 5)
            values = list(self.tree.item(item, 'values'))
            values[5] = f"{self.shared_cash_price:.2f}"
            self.tree.item(item, values=values)

            # Recalculate Worth it? for this row
            self._recalculate_row(item)

    def _recalculate_row(self, row_id):
        """Recalculate Total Cost and Worth it? for a row"""
        values = list(self.tree.item(row_id, 'values'))
        row_data = self.program_rows[row_id]

        # CHANGE 4: Handle non-numeric k_miles (like "Dynamic")
        try:
            k_miles = float(values[1])  # k Miles (in thousands)
        except ValueError:
            # If k_miles is "Dynamic" or text, just show "---" for Total Cost
            values[4] = "---"  # Total Cost
            values[6] = "-"  # Worth it?
            self.tree.item(row_id, values=values)
            return

        try:
            yq = float(values[2])  # YQ in dollars
            cash_price = float(values[5])  # Cash price in dollars
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numbers")
            return

        valuation = float(values[3])

        # Check if valuation exists
        if valuation is None:
            messagebox.showerror("Valuation Error",
                               f"No valuation found for {row_data['ffp_code']} in valuations.json")
            values[4] = "ERROR"
            values[6] = "ERROR"
            self.tree.item(row_id, values=values)
            return

        # Calculate total cost: k_miles * 10 * valuation + YQ
        # k_miles is in thousands, valuation is in cents per point
        # 10 converts from cpp to dollars (divide by 100, multiply by 1000)
        total_cost = (k_miles * 10 * valuation) + yq

        # Calculate worth it
        worth_it = "Y" if total_cost <= cash_price else "N"

        # Update row
        values[4] = f"${total_cost:.2f}"
        values[6] = worth_it

        self.tree.item(row_id, values=values)

    def _new_search(self):
        """Return to Tab 2 for new search"""
        self.app.search_context = {
            'route_type': None,
            'carrier_code': None,
            'origin': None,
            'destination': None,
            'distance': None,
            'cabin': None,
            'results': []
        }
        notebook = self.master
        notebook.select(1)
