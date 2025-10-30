"""
tab4.py - UPDATED: Match by both cabin_class AND cabin booking code

Key changes:
1. Cabin Letter Code is now REQUIRED (not optional)
2. Accrual rules have booking_codes array - must match user's entry
3. Lookup logic: Find rule where booking_codes includes user's cabin code
4. Display earning_rate as percentage for clarity (e.g., 150% = 1.5 earning_rate)
"""

import tkinter as tk
from tkinter import ttk, messagebox


class Tab4Frame(ttk.Frame):
    """Tab 4: Mile Accrual Calculator"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        try:
            self._setup_ui()
        except Exception as e:
            messagebox.showerror("Tab 4 Error", str(e))
            raise
    
    def _setup_ui(self):
        """Setup main UI layout"""
        
        # Input section frame
        input_frame = ttk.LabelFrame(self, text="Accrual Parameters", padding=10)
        input_frame.pack(fill=tk.BOTH, padx=5, pady=5)
        
        # Row 0: Alliance selection
        ttk.Label(input_frame, text="Alliance:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.alliance_var = tk.StringVar(value="")
        alliances = [a['name'] for a in self.app.alliance['alliances']]
        alliance_dropdown = ttk.Combobox(input_frame, textvariable=self.alliance_var,
                                        values=alliances, state="readonly", width=30)
        alliance_dropdown.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        alliance_dropdown.bind("<<ComboboxSelected>>", self._on_alliance_change)
        
        # Row 1: Country selection
        ttk.Label(input_frame, text="Country:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.country_var = tk.StringVar(value="")
        self.country_dropdown = ttk.Combobox(input_frame, textvariable=self.country_var,
                                            state="readonly", width=30)
        self.country_dropdown.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        self.country_dropdown.bind("<<ComboboxSelected>>", self._on_country_change)
        
        # Row 2: Carrier selection
        ttk.Label(input_frame, text="Carrier:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.carrier_var = tk.StringVar(value="")
        self.carrier_dropdown = ttk.Combobox(input_frame, textvariable=self.carrier_var,
                                            state="readonly", width=30)
        self.carrier_dropdown.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Row 3: Cabin class
        ttk.Label(input_frame, text="Cabin Class:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.cabin_class_var = tk.StringVar(value="economy")
        cabin_class_dropdown = ttk.Combobox(input_frame, textvariable=self.cabin_class_var,
                                           values=["first", "business", "premium_economy", "economy"],
                                           state="readonly", width=30)
        cabin_class_dropdown.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Row 4: Cabin letter code (NOW REQUIRED)
        ttk.Label(input_frame, text="Cabin Letter Code:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.cabin_code_var = tk.StringVar(value="")
        cabin_code_entry = ttk.Entry(input_frame, textvariable=self.cabin_code_var, width=30)
        cabin_code_entry.grid(row=4, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Row 5: Travel distance
        ttk.Label(input_frame, text="Travel Distance (miles):").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        self.distance_var = tk.StringVar(value="")
        distance_entry = ttk.Entry(input_frame, textvariable=self.distance_var, width=30)
        distance_entry.grid(row=5, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Row 6: Fare price (optional, for future use)
        ttk.Label(input_frame, text="Fare Price ($):").grid(row=6, column=0, sticky=tk.W, padx=5, pady=5)
        self.fare_var = tk.StringVar(value="")
        fare_entry = ttk.Entry(input_frame, textvariable=self.fare_var, width=30)
        fare_entry.grid(row=6, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Row 7: Calculate button
        calc_button = ttk.Button(input_frame, text="Calculate Accrual", command=self._calculate)
        calc_button.grid(row=7, column=0, columnspan=2, sticky=tk.EW, pady=10, padx=5)
        
        input_frame.columnconfigure(1, weight=1)
        
        # Results section frame
        results_frame = ttk.LabelFrame(self, text="Accrual Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create Treeview for results
        columns = ('Program', 'Miles Accrued', 'Earning Rate', 'Family Pooling', 'Expiration')
        
        self.tree = ttk.Treeview(results_frame, columns=columns, height=10, show='headings')
        
        column_widths = {
            'Program': 180,
            'Miles Accrued': 130,
            'Earning Rate': 120,
            'Family Pooling': 130,
            'Expiration': 150
        }
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths[col], anchor=tk.CENTER)
        
        # Scrollbars
        vsb = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
    
    def _on_alliance_change(self, event=None):
        """When alliance is selected, update country dropdown"""
        
        alliance_name = self.alliance_var.get()
        if not alliance_name:
            return
        
        # Find alliance code
        alliance_code = None
        for alliance in self.app.alliance['alliances']:
            if alliance['name'] == alliance_name:
                alliance_code = alliance['code']
                break
        
        if not alliance_code:
            return
        
        # Get all carriers in this alliance
        alliance_carriers = []
        for alliance in self.app.alliance['alliances']:
            if alliance['code'] == alliance_code:
                alliance_carriers = alliance.get('members', [])
                break
        
        # Get countries of these carriers
        countries = set()
        for carrier_code in alliance_carriers:
            for carrier in self.app.carriers['carriers']:
                if carrier['code'] == carrier_code:
                    countries.add(carrier['country'])
                    break
        
        # Update country dropdown
        self.country_dropdown['values'] = sorted(list(countries))
        self.country_var.set("")
        self.carrier_dropdown['values'] = []
        self.carrier_var.set("")
    
    def _on_country_change(self, event=None):
        """When country is selected, update carrier dropdown"""
        
        alliance_name = self.alliance_var.get()
        country = self.country_var.get()
        
        if not alliance_name or not country:
            return
        
        # Find alliance code and members
        alliance_code = None
        alliance_members = []
        for alliance in self.app.alliance['alliances']:
            if alliance['name'] == alliance_name:
                alliance_code = alliance['code']
                alliance_members = alliance.get('members', [])
                break
        
        if not alliance_code:
            return
        
        # Filter carriers by country and alliance membership
        carriers = []
        for carrier_code in alliance_members:
            for carrier in self.app.carriers['carriers']:
                if carrier['code'] == carrier_code and carrier['country'] == country:
                    carriers.append((carrier['code'], carrier['name']))
                    break
        
        # Update carrier dropdown
        carrier_list = [f"{code} - {name}" for code, name in carriers]
        self.carrier_dropdown['values'] = carrier_list
        self.carrier_var.set("")
    
    def _calculate(self):
        """Calculate mile accrual for all eligible FFPs"""
        
        try:
            # Validate inputs
            carrier_str = self.carrier_var.get()
            cabin_class = self.cabin_class_var.get()
            cabin_code = self.cabin_code_var.get().upper()
            distance_str = self.distance_var.get()
            
            if not all([carrier_str, cabin_class, cabin_code, distance_str]):
                messagebox.showwarning("Input Error", 
                    "Please fill in Carrier, Cabin Class, Cabin Letter Code, and Distance")
                return
            
            # Extract carrier code
            carrier_code = carrier_str.split(" - ")[0]
            
            # Parse distance
            try:
                distance = float(distance_str)
            except ValueError:
                messagebox.showerror("Input Error", "Distance must be a number")
                return
            
            # Clear previous results
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Calculate accrual for each FFP
            accrual_results = []
            
            for ffp_code, ffp_info in self.app.ffp['ffps'].items():
                # Step 1: Check if FFP can earn on this carrier
                if not self._can_earn_on_carrier(ffp_code, carrier_code):
                    continue
                
                # Step 2: Look up accrual rule (matching cabin_class AND cabin_code)
                accrual_data = self._calculate_accrual(ffp_code, carrier_code, cabin_class, cabin_code, distance)
                
                if accrual_data is None:
                    continue
                
                miles_accrued = accrual_data['miles']
                earning_rate = accrual_data['earning_rate']
                
                # Step 3: Get pooling and expiration
                family_pooling = ffp_info.get('family_pooling', False)
                expiration = ffp_info.get('expiration', 'N/A')
                
                # Format display strings
                pooling_str = "Yes" if family_pooling else "No"
                expiration_str = expiration.replace("_", " ").title()
                earning_rate_str = f"{earning_rate * 100:.0f}%"
                miles_display = f"{int(miles_accrued):,}" if miles_accrued > 0 else "0"
                
                accrual_results.append({
                    'program': ffp_info['name'],
                    'miles': miles_accrued,
                    'miles_display': miles_display,
                    'earning_rate_str': earning_rate_str,
                    'pooling': pooling_str,
                    'expiration': expiration_str
                })
            
            # Sort by miles (high to low)
            accrual_results.sort(key=lambda x: -x['miles'])
            
            # Display results
            for result in accrual_results:
                self.tree.insert('', 'end', values=(
                    result['program'],
                    result['miles_display'],
                    result['earning_rate_str'],
                    result['pooling'],
                    result['expiration']
                ))
            
            if not accrual_results:
                messagebox.showinfo("No Results", 
                    "No programs can earn on this carrier with booking code " + cabin_code)
        
        except Exception as e:
            messagebox.showerror("Error", f"Calculation failed: {str(e)}")
    
    def _can_earn_on_carrier(self, ffp_code, carrier_code):
        """Check if FFP can earn miles on the specified carrier"""
        
        # Check if FFP's own carrier matches
        if ffp_code in self.app.ffp['ffps']:
            ffp_carriers = self.app.ffp['ffps'][ffp_code].get('carriers', [])
            if carrier_code in ffp_carriers:
                return True
        
        # Check partnerships
        partners_data = self.app.partners['programs']
        
        for partner in partners_data:
            if partner['ffp'] != ffp_code:
                continue
            
            # Only consider earn relationships
            if partner['relationship'] not in ['both', 'earn_only']:
                continue
            
            # Check if carrier is in this partnership
            if partner['type'] == 'alliance':
                alliance_code = partner['alliance']
                for alliance in self.app.alliance['alliances']:
                    if alliance['code'] == alliance_code:
                        if carrier_code in alliance.get('members', []):
                            return True
                        break
            
            elif partner['type'] == 'individual':
                if carrier_code in partner.get('carriers', []):
                    return True
        
        return False
    
    def _calculate_accrual(self, ffp_code, carrier_code, cabin_class, cabin_code, distance):
        """
        Calculate mile accrual for FFP on carrier in given cabin class with booking code
        
        Returns:
        - Dict with {'miles': accrued_miles, 'earning_rate': rate} 
        - None if no matching rule found
        """
        
        # Check if accrual_rules has this FFP
        if ffp_code not in self.app.accrual_rules:
            return None
        
        ffp_rules = self.app.accrual_rules[ffp_code]
        
        # Check if carrier exists for this FFP
        if carrier_code not in ffp_rules:
            return None
        
        carrier_rules = ffp_rules[carrier_code]
        
        # Check if cabin_class exists for this carrier
        if cabin_class not in carrier_rules:
            return None
        
        cabin_rules = carrier_rules[cabin_class]  # This is now an array of rule objects
        
        # Find rule matching the cabin_code
        matching_rule = None
        for rule in cabin_rules:
            if cabin_code in rule.get('booking_codes', []):
                matching_rule = rule
                break
        
        if not matching_rule:
            # Cabin class exists but booking code doesn't match any rule
            return None
        
        # Calculate based on type
        rule_type = matching_rule.get('type', 'distance')
        
        if rule_type == 'distance':
            earning_rate = matching_rule.get('earning_rate', 0)
            minimum = matching_rule.get('minimum', 0)
            
            miles = distance * earning_rate
            miles = max(miles, minimum)  # Apply minimum
            
            return {
                'miles': miles,
                'earning_rate': earning_rate
            }
        
        elif rule_type == 'revenue':
            # For future: revenue-based earning
            pass
        
        return None
