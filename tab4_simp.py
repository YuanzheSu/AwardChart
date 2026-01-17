"""
tab4_v2.py: Earning Partner Finder - Find which carriers can earn points on an FFP
Similar to Tab 1 (redeem), but shows earning partnerships instead.
Also displays family pooling and expiration info in a table.
"""

import tkinter as tk
from tkinter import ttk, messagebox

class Tab4Frame(ttk.Frame):
    """Tab 4: Earning Partner Finder"""
    
    def __init__(self, parent, carriers_country_tab1, carrierlist_tab1, ffp_dict_earn, ffp_dict):
        super().__init__(parent)
        
        # Store pre-processed data
        self.carriers_country_tab1 = carriers_country_tab1
        self.carrierlist_tab1 = carrierlist_tab1
        self.ffp_dict_earn = ffp_dict_earn  # Pre-processed with earn_partner
        self.ffp_dict = ffp_dict  # Full FFP data for family_pooling and expiration
        
        # Current filter states
        self.alliance_filtered = []
        self.carrierlist_tab1_filtered = []
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Build the user interface"""
        
        # Main container
        container = ttk.Frame(self, padding="20")
        container.pack(fill='both', expand=True)
        
        # Title
        title = ttk.Label(container, text="Earning Partner Finder",
                         font=('Helvetica', 16, 'bold'))
        title.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky='w')
        
        # Instructions
        instructions = ttk.Label(container,
                                text="Find which frequent flyer programs can earn points when flying on a specific carrier",
                                foreground='gray')
        instructions.grid(row=1, column=0, columnspan=3, pady=(0, 20), sticky='w')
        
        # ==================== Row 1: Country Selection ====================
        
        ttk.Label(container, text="1. Select Country:", font=('Helvetica', 10, 'bold')).grid(
            row=2, column=0, sticky='w', pady=(0, 5))
        
        # Country dropdown with search functionality
        self.country_var = tk.StringVar()
        self.country_combo = ttk.Combobox(container, textvariable=self.country_var,
                                         state='normal', width=40)
        self.country_combo['values'] = self.carriers_country_tab1
        self.country_combo.grid(row=3, column=0, sticky='ew', pady=(0, 15))
        self.country_combo.bind('<<ComboboxSelected>>', self._on_country_selected)
        self.country_combo.bind('<KeyRelease>', self._on_country_search)
        
        # ==================== Row 2: Alliance Selection ====================
        
        ttk.Label(container, text="2. Select Alliance:", font=('Helvetica', 10, 'bold')).grid(
            row=4, column=0, sticky='w', pady=(0, 5))
        
        self.alliance_var = tk.StringVar()
        self.alliance_combo = ttk.Combobox(container, textvariable=self.alliance_var,
                                          state='disabled', width=40)
        self.alliance_combo.grid(row=5, column=0, sticky='ew', pady=(0, 15))
        self.alliance_combo.bind('<<ComboboxSelected>>', self._on_alliance_selected)
        
        # ==================== Row 3: Carrier Selection ====================
        
        ttk.Label(container, text="3. Select Carrier:", font=('Helvetica', 10, 'bold')).grid(
            row=6, column=0, sticky='w', pady=(0, 5))
        
        self.carrier_var = tk.StringVar()
        self.carrier_combo = ttk.Combobox(container, textvariable=self.carrier_var,
                                         state='disabled', width=40)
        self.carrier_combo.grid(row=7, column=0, sticky='ew', pady=(0, 15))
        self.carrier_combo.bind('<<ComboboxSelected>>', self._on_carrier_selected)
        
        # ==================== Results Display (Treeview for table) ====================
        
        ttk.Label(container, text="Available FFPs:", font=('Helvetica', 10, 'bold')).grid(
            row=8, column=0, sticky='w', pady=(10, 5))
        
        # Create Treeview with columns
        columns = ('FFP Name', 'Family Pooling', 'Points Expiration')
        self.results_tree = ttk.Treeview(container, columns=columns, height=10, show='headings')
        
        # Define column headings and widths
        self.results_tree.column('FFP Name', width=250, anchor='w')
        self.results_tree.column('Family Pooling', width=150, anchor='center')
        self.results_tree.column('Points Expiration', width=180, anchor='center')
        
        self.results_tree.heading('FFP Name', text='FFP Name')
        self.results_tree.heading('Family Pooling', text='Family Pooling')
        self.results_tree.heading('Points Expiration', text='Points Expiration')
        
        self.results_tree.grid(row=9, column=0, columnspan=2, sticky='nsew', pady=(0, 10))
        
        # Scrollbar for results
        scrollbar = ttk.Scrollbar(container, orient='vertical', command=self.results_tree.yview)
        scrollbar.grid(row=9, column=2, sticky='ns', pady=(0, 10))
        self.results_tree.config(yscrollcommand=scrollbar.set)
        
        # Configure grid weights
        container.columnconfigure(0, weight=1)
        container.rowconfigure(9, weight=1)
    
    def _on_country_search(self, event):
        """Filter country dropdown as user types"""
        
        typed = self.country_var.get().lower()
        if not typed:
            self.country_combo['values'] = self.carriers_country_tab1
            return
        
        # Filter countries that match typed text (code or name)
        filtered = [country for country in self.carriers_country_tab1
                   if typed in country.lower()]
        self.country_combo['values'] = filtered
    
    def _on_country_selected(self, event):
        """Handle country selection - filter alliances"""
        
        selected_country = self.country_var.get()
        if not selected_country:
            return
        
        # Filter carriers for this country
        self.carrierlist_tab1_filtered = [
            carrier for carrier in self.carrierlist_tab1
            if carrier['country'] == selected_country
        ]
        
        # Get unique alliances in this country
        self.alliance_filtered = []
        for carrier in self.carrierlist_tab1_filtered:
            alliance = carrier['alliance']
            if alliance not in self.alliance_filtered:
                self.alliance_filtered.append(alliance)
        
        # Update alliance dropdown
        self.alliance_combo['values'] = self.alliance_filtered
        self.alliance_combo['state'] = 'readonly'
        self.alliance_var.set('')
        
        # Reset downstream selections
        self.carrier_combo['state'] = 'disabled'
        self.carrier_var.set('')
        self._clear_results()
    
    def _on_alliance_selected(self, event):
        """Handle alliance selection - filter carriers"""
        
        selected_alliance = self.alliance_var.get()
        if not selected_alliance:
            return
        
        selected_country = self.country_var.get()
        
        # Filter carriers by country and alliance
        carriers_filtered = [
            carrier for carrier in self.carrierlist_tab1
            if carrier['country'] == selected_country and carrier['alliance'] == selected_alliance
        ]
        
        # Extract carrier names for display
        carriers_name_display = [carrier['name'] for carrier in carriers_filtered]
        
        # Update carrier dropdown
        self.carrier_combo['values'] = carriers_name_display
        self.carrier_combo['state'] = 'readonly'
        self.carrier_var.set('')
        
        # Clear results
        self._clear_results()
    
    def _on_carrier_selected(self, event):
        """Handle carrier selection - find available FFPs for earning"""
        
        selected_carrier = self.carrier_var.get()
        if not selected_carrier:
            return
        
        # Extract carrier code from display name (format: "CODE - Name")
        carrier_code = selected_carrier.split('-')[0].strip()
        
        # Find FFPs that can earn on this carrier
        display_ffps_available = []
        
        for ffp_name, ffp_value in self.ffp_dict_earn.items():
            if (ffp_value.get('earn_partner') and carrier_code in ffp_value.get('earn_partner')) or \
               (ffp_value.get('carriers') and carrier_code in ffp_value.get('carriers')):
                
                # Get full FFP info for family pooling and expiration
                ffp_full = self.ffp_dict.get(ffp_name, {})
                ffp_name_display = ffp_full.get('name', ffp_name)
                family_pooling = ffp_full.get('family_pooling', 'Unknown')
                expiration = ffp_full.get('expiration', 'Unknown')
                
                display_ffps_available.append({
                    'name': ffp_name_display,
                    'family_pooling': family_pooling,
                    'expiration': expiration
                })
        
        # Display results
        self._display_results(display_ffps_available, selected_carrier)
    
    def _display_results(self, ffps, carrier_name):
        """Display FFP results in Treeview table"""
        
        # Clear existing items
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        if ffps:
            # Insert FFP data as rows
            for ffp_data in ffps:
                self.results_tree.insert('', 'end', values=(
                    ffp_data['name'],
                    ffp_data['family_pooling'],
                    ffp_data['expiration']
                ))
        else:
            # Show empty message by inserting a single row
            self.results_tree.insert('', 'end', values=(
                f"No FFPs found that can earn on {carrier_name}",
                "",
                ""
            ))
    
    def _clear_results(self):
        """Clear results tree"""
        
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)