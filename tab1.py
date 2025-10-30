"""
tab1.py: Eligibility Finder - UPDATED

"""

import tkinter as tk
from tkinter import ttk, messagebox

class Tab1Frame(ttk.Frame):
    """Tab 1: Eligibility Finder"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        try:
            # Process shared data (no file loading)
            self._process_data()
            # Setup UI
            self._setup_ui()
        except Exception as e:
            messagebox.showerror("Tab 1 Error", str(e))
            raise

    def _process_data(self):
        """
        Process shared data from app into internal structures.
        """
        # ==================== Carriers ====================
        carriers_data = self.app.carriers['carriers']
        self.carriers = carriers_data
        carrier_codes = {c['code'] for c in carriers_data}

        # ==================== Alliances ====================
        alli_data = self.app.alliance['alliances']
        self.alli_map = {}  # Maps alliance code -> set of member carriers
        self.alli_countries = {}  # Maps alliance code -> set of countries in that alliance
        self.alliances = []
        carrier_to_alliances = {}

        for a in alli_data:
            alliance_code = a['code']
            self.alli_map[alliance_code] = set()
            self.alli_countries[alliance_code] = set()

            for m in a['members']:
                # Check if carrier exists
                if m not in carrier_codes:
                    raise ValueError(f"Alliance '{alliance_code}' has unknown carrier '{m}'")

                # Check if carrier is in multiple alliances
                if m in carrier_to_alliances:
                    raise ValueError(
                        f"Carrier '{m}' is in multiple alliances: "
                        f"{carrier_to_alliances[m]} and '{alliance_code}'"
                    )

                carrier_to_alliances[m] = alliance_code
                self.alli_map[alliance_code].add(m)

                # Add this carrier's country to the alliance's countries
                carrier_obj = next((c for c in carriers_data if c['code'] == m), None)
                if carrier_obj:
                    self.alli_countries[alliance_code].add(carrier_obj['country'])

            self.alliances.append(alliance_code)

        self.alliances.append('None')  # Option for carriers not in any alliance

        # Build set of all carriers in any alliance
        self.carriers_in_alliances = set()
        for members in self.alli_map.values():
            self.carriers_in_alliances.update(members)

        # ==================== Country-to-Alliance Mapping ====================
        # NEW: Build mapping of countries to alliances that operate there
        self.country_alliances = {}  # Maps country -> list of alliance codes
        for country in {c['country'] for c in carriers_data}:
            self.country_alliances[country] = []
            # Check which alliances have carriers in this country
            for alliance_code in self.alliances:
                if alliance_code == 'None':
                    # Check if country has carriers not in any alliance
                    has_non_alliance = any(
                        c['country'] == country and c['code'] not in self.carriers_in_alliances
                        for c in carriers_data
                    )
                    if has_non_alliance:
                        self.country_alliances[country].append('None')
                else:
                    if country in self.alli_countries.get(alliance_code, set()):
                        self.country_alliances[country].append(alliance_code)

        # ==================== FFPs ====================
        self.ffps = self.app.ffp['ffps']

        # Validate FFPs - check that carriers exist
        for ffp_code, ffp_info in self.ffps.items():
            for carrier in ffp_info.get('carriers', []):
                if carrier not in carrier_codes:
                    raise ValueError(f"FFP '{ffp_code}' uses unknown carrier '{carrier}'")

        # ==================== Partners ====================
        partners_data = self.app.partners['programs']
        self.partners_raw = partners_data
        self.ffp_redeem_partners = {}  # Maps FFP code -> set of carriers that can redeem

        # Validate and expand partners
        for p in partners_data:
            ffp_code = p['ffp']

            # Validate FFP exists
            if ffp_code not in self.ffps:
                raise ValueError(f"Unknown FFP code '{ffp_code}' in partners")

            # Initialize set for this FFP if not exists
            if ffp_code not in self.ffp_redeem_partners:
                self.ffp_redeem_partners[ffp_code] = set()

            # Only process redeem relationships
            if p['relationship'] not in ['both', 'redeem_only']:
                continue

            if p['type'] == 'alliance':
                # Expand alliance to individual carriers
                alliance_code = p['alliance']
                if alliance_code not in self.alli_map:
                    raise ValueError(
                        f"Unknown alliance code '{alliance_code}' in partners for FFP '{ffp_code}'"
                    )

                # Add all carriers in this alliance as redeem partners
                self.ffp_redeem_partners[ffp_code].update(self.alli_map[alliance_code])

            elif p['type'] == 'individual':
                # Add individual carriers as redeem partners
                for carrier in p.get('carriers', []):
                    if carrier not in carrier_codes:
                        raise ValueError(
                            f"Unknown carrier '{carrier}' in partner entry for FFP '{ffp_code}'"
                        )
                    self.ffp_redeem_partners[ffp_code].add(carrier)

        # ==================== Countries ====================
        # All countries available in the dataset
        self.all_countries = sorted({c['country'] for c in carriers_data})

    def _setup_ui(self):
        """Setup user interface"""
        self.country_var = tk.StringVar(value='')
        self.alliance_var = tk.StringVar(value='')
        self.carrier_var = tk.StringVar(value='')

        # Country dropdown (FIRST)
        ttk.Label(self, text="Select Country:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.country_combo = ttk.Combobox(self, textvariable=self.country_var,
                                         values=self.all_countries, state='readonly', width=40)
        self.country_combo.grid(row=1, column=0, sticky='ew', padx=5, pady=2)
        self.country_combo.bind('<<ComboboxSelected>>', lambda e: self._on_country_change())

        # Alliance dropdown (SECOND)
        ttk.Label(self, text="Select Alliance:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.alliance_combo = ttk.Combobox(self, textvariable=self.alliance_var,
                                          state='readonly', width=40)
        self.alliance_combo.grid(row=3, column=0, sticky='ew', padx=5, pady=2)
        self.alliance_combo.bind('<<ComboboxSelected>>', lambda e: self._on_alliance_change())

        # Carrier dropdown (THIRD)
        ttk.Label(self, text="Select Carrier:").grid(row=4, column=0, sticky='w', padx=5, pady=2)
        self.carrier_combo = ttk.Combobox(self, textvariable=self.carrier_var,
                                         state='readonly', width=40)
        self.carrier_combo.grid(row=5, column=0, sticky='ew', padx=5, pady=2)
        self.carrier_combo.bind('<<ComboboxSelected>>', lambda e: self._update_results())

        # Results label
        ttk.Label(self, text="Available FFPs to Redeem:").grid(row=6, column=0, sticky='w', padx=5, pady=2)

        # Results listbox
        self.result_box = tk.Listbox(self, height=12, font=("Courier", 9))
        self.result_box.grid(row=7, column=0, sticky='nsew', padx=5, pady=2)

        # Configure grid weights
        self.columnconfigure(0, weight=1)
        self.rowconfigure(7, weight=1)

        # Initial populate - set first country and cascade
        if self.all_countries:
            self.country_var.set(self.all_countries[0])
            self._populate_alliances()
            self._build_carrier_menu()
            self._update_results()

    def _on_country_change(self):
        """Handle country selection change - update alliance dropdown"""
        self._populate_alliances()
        self.alliance_var.set('')
        self.carrier_var.set('')
        self.result_box.delete(0, tk.END)

    def _populate_alliances(self):
        """Populate alliance dropdown based on selected country"""
        country = self.country_var.get()

        if not country:
            self.alliance_combo['values'] = []
            self.alliance_var.set('')
            return

        # Get alliances that have carriers in this country
        alliances = self.country_alliances.get(country, [])

        self.alliance_combo['values'] = alliances

        # Set first alliance if available
        if alliances:
            self.alliance_var.set(alliances[0])
            self._build_carrier_menu()
        else:
            self.alliance_var.set('')

    def _on_alliance_change(self):
        """Handle alliance selection change - update carrier dropdown"""
        self._build_carrier_menu()
        self._update_results()

    def _build_carrier_menu(self):
        """Build list of carriers based on selected country and alliance"""
        country = self.country_var.get()
        alliance = self.alliance_var.get()

        if not country or not alliance:
            self.carrier_combo['values'] = []
            self.carrier_var.set('')
            return

        # Filter carriers by country and alliance
        if alliance == 'None':
            # Only carriers NOT in any alliance
            items = [cc for cc in self.carriers
                    if cc['code'] not in self.carriers_in_alliances
                    and cc['country'] == country]
        else:
            # Only carriers in the selected alliance
            members = self.alli_map.get(alliance, set())
            items = [cc for cc in self.carriers
                    if cc['code'] in members and cc['country'] == country]

        items.sort(key=lambda x: x['code'])

        # NEW: Display both code and name, like in tab2
        carrier_list = [f"{i['code']} - {i['name']}" for i in items]

        self.carrier_combo['values'] = carrier_list

        # Set first carrier if available
        if carrier_list:
            self.carrier_var.set(carrier_list[0])
        else:
            self.carrier_var.set('')

    def _update_results(self):
        """Update the results listbox based on selected carrier"""
        self.result_box.delete(0, tk.END)

        carrier_str = self.carrier_var.get()
        if not carrier_str:
            return

        # Extract carrier code from "CODE - Name" format
        carrier = carrier_str.split(' - ')[0]

        ffp_results = self._find_redeem_ffps(carrier)

        # Display results (already sorted with self FFP first)
        for ffp_name in ffp_results:
            self.result_box.insert(tk.END, ffp_name)

    def _find_redeem_ffps(self, carrier_code):
        """
        Find all FFPs that can redeem the specified carrier.

        Args:
            carrier_code: Two-letter carrier code (e.g., 'AA', 'UA')

        Returns:
            List of FFP names, sorted with self FFPs first, then partners
        """
        self_ffps = []
        partner_ffps = []

        # Step 1: Find self FFPs (where carrier is registered in FFP)
        for ffp_code, ffp_info in self.ffps.items():
            if carrier_code in ffp_info.get('carriers', []):
                self_ffps.append(ffp_info['name'])

        # Step 2: Find partner FFPs (where carrier can redeem via partnership)
        for ffp_code, redeem_partners in self.ffp_redeem_partners.items():
            if carrier_code in redeem_partners:
                # Don't add if already in self FFPs (avoid duplicates)
                ffp_name = self.ffps[ffp_code]['name']
                if ffp_name not in self_ffps:
                    partner_ffps.append(ffp_name)

        # Sort and combine: self FFPs first, then partner FFPs
        self_ffps.sort()
        partner_ffps.sort()

        return self_ffps + partner_ffps
