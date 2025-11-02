"""

tab2.py: Award Chart Lookup - WITH SEARCHABLE DEPARTURE/ARRIVAL DROPDOWNS

Key changes:

1. Departure and Arrival dropdowns are now searchable (state="normal")
2. Supports dual-field matching: match both airport code (CA) and full name (California)
3. Real-time filtering as user types


"""

import tkinter as tk
from tkinter import ttk, messagebox


class Tab2Frame(ttk.Frame):
    """Tab 2: Award Chart Lookup"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        try:
            self._setup_ui()
        except Exception as e:
            messagebox.showerror("Tab 2 Error", str(e))
            raise

    def _setup_ui(self):
        """Setup main UI layout"""
        
        # Route selection frame
        route_frame = ttk.LabelFrame(self, text="Route Selection", padding=10)
        route_frame.pack(fill=tk.BOTH, padx=5, pady=5)

        # Route type (US, EU, US-EU, etc.)
        ttk.Label(route_frame, text="Route Type:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.route_var = tk.StringVar(value="US Domestic")

        # Get available route categories from zone_systems
        route_categories = self.app.zone_systems.get('route_categories', {})
        route_options = [route_categories[k]['name'] for k in sorted(route_categories.keys())]

        route_dropdown = ttk.Combobox(route_frame, textvariable=self.route_var,
                                      values=route_options, state="readonly", width=25)
        route_dropdown.grid(row=0, column=1, sticky=tk.EW, padx=5)
        route_dropdown.bind("<<ComboboxSelected>>", self._on_route_change)

        # Carrier selection
        ttk.Label(route_frame, text="Carrier:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.carrier_var = tk.StringVar()

        self.carrier_dropdown = ttk.Combobox(route_frame, textvariable=self.carrier_var,
                                             state="readonly", width=25)
        self.carrier_dropdown.grid(row=1, column=1, sticky=tk.EW, padx=5)
        self.carrier_dropdown.bind("<<ComboboxSelected>>", self._on_carrier_change)

        route_frame.columnconfigure(1, weight=1)

        # Details frame (populated dynamically)
        self.details_frame = ttk.LabelFrame(self, text="Route Details", padding=10)
        self.details_frame.pack(fill=tk.BOTH, padx=5, pady=5)

        # Results frame
        results_frame = ttk.LabelFrame(self, text="Award Options", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollable listbox for results
        scrollbar = ttk.Scrollbar(results_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.results_listbox = tk.Listbox(results_frame, yscrollcommand=scrollbar.set,
                                          height=10, font=("Courier", 10))
        self.results_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.results_listbox.yview)

        # Initial population
        self._populate_carriers()

    def _on_route_change(self, event=None):
        """Route type changed - repopulate carriers and details"""
        self._populate_carriers()
        self.carrier_var.set("")
        self._clear_details()

    def _populate_carriers(self):
        """
        Filter carriers by operating_region CODE matching the route_category KEY.
        Logic:
        - User selects "US Domestic"
        - This maps to route_category KEY "US"
        - Filter carriers where "US" is in their operating_region
        """
        route_name = self.route_var.get()

        # Get route category key from name
        route_categories = self.app.zone_systems.get('route_categories', {})
        route_key = None
        for key, data in route_categories.items():
            if data['name'] == route_name:
                route_key = key  # e.g., "US"
                break

        if not route_key:
            self.carrier_dropdown['values'] = []
            return

        # Filter carriers by operating_region CODE
        carriers = []
        for c in self.app.carriers['carriers']:
            operating_region = c.get("operating_region")
            if operating_region is None:
                continue

            # Convert string to list for uniform handling
            if isinstance(operating_region, str):
                operating_region = [operating_region]

            # CHECK: Does carrier's operating_region include the route_key?
            # e.g., does ["US", "US-EU"] include "US"?
            if route_key in operating_region:
                carriers.append(c)

        # Create display strings
        carrier_list = [f"{c['code']} - {c['name']}" for c in carriers]
        self.carrier_dropdown['values'] = carrier_list

    def _on_carrier_change(self, event=None):
        """Carrier selected - setup route details"""
        self._setup_route_details()

    def _clear_details(self):
        """Clear details frame"""
        for widget in self.details_frame.winfo_children():
            widget.destroy()

    def _setup_route_details(self):
        """
        Setup UI for entering route details.
        Uses origin_region and destination_region to get location lists from destinations.
        """
        self._clear_details()

        carrier_str = self.carrier_var.get()
        if not carrier_str:
            return

        # Get route type info
        route_name = self.route_var.get()
        route_categories = self.app.zone_systems.get('route_categories', {})
        route_key = None
        for key, data in route_categories.items():
            if data['name'] == route_name:
                route_key = key
                break

        if not route_key:
            return

        route_data = route_categories[route_key]
        origin_region_key = route_data['origin_region']  # e.g., "US" or "NA"
        destination_region_key = route_data['destination_region']  # e.g., "US" or "EU"

        # Get all locations available for origin and destination regions
        destinations = self.app.zone_systems.get('destinations', {})

        # Get origin locations from destinations[origin_region_key]
        origin_locations = []
        if origin_region_key in destinations:
            origin_locs_dict = destinations[origin_region_key].get('locations', {})
            origin_locations = [f"{code} - {info['name']}"
                                for code, info in sorted(origin_locs_dict.items())]

        # Get destination locations from destinations[destination_region_key]
        dest_locations = []
        if destination_region_key in destinations:
            dest_locs_dict = destinations[destination_region_key].get('locations', {})
            dest_locations = [f"{code} - {info['name']}"
                              for code, info in sorted(dest_locs_dict.items())]

        # Get region names
        origin_name = destinations.get(origin_region_key, {}).get('name', origin_region_key)
        dest_name = destinations.get(destination_region_key, {}).get('name', destination_region_key)

        # Create details widgets
        ttk.Label(self.details_frame, text=f"Depart ({origin_name}):").grid(row=0, column=0, sticky=tk.W, padx=5)

        self.origin_var = tk.StringVar()
        self.origin_full_list = origin_locations  # Store full list for filtering
        
        origin_dropdown = ttk.Combobox(self.details_frame, textvariable=self.origin_var,
                                       values=origin_locations, state="normal", width=25)
        origin_dropdown.grid(row=0, column=1, sticky=tk.EW, padx=5)
        
        # Bind key release event for origin filtering
        origin_dropdown.bind("<KeyRelease>", lambda e: self._filter_origin_dropdown(origin_dropdown))

        ttk.Label(self.details_frame, text=f"Arrive ({dest_name}):").grid(row=1, column=0, sticky=tk.W, padx=5)

        self.dest_var = tk.StringVar()
        self.dest_full_list = dest_locations  # Store full list for filtering
        
        dest_dropdown = ttk.Combobox(self.details_frame, textvariable=self.dest_var,
                                     values=dest_locations, state="normal", width=25)
        dest_dropdown.grid(row=1, column=1, sticky=tk.EW, padx=5)
        
        # Bind key release event for destination filtering
        dest_dropdown.bind("<KeyRelease>", lambda e: self._filter_dest_dropdown(dest_dropdown))

        ttk.Label(self.details_frame, text="Distance (miles):").grid(row=2, column=0, sticky=tk.W, padx=5)

        self.distance_var = tk.StringVar()
        distance_entry = ttk.Entry(self.details_frame, textvariable=self.distance_var, width=25)
        distance_entry.grid(row=2, column=1, sticky=tk.EW, padx=5)

        ttk.Label(self.details_frame, text="Cabin Class:").grid(row=3, column=0, sticky=tk.W, padx=5)

        self.cabin_var = tk.StringVar(value="economy")

        # Get all possible cabin classes from ALL award charts
        all_cabins = set()
        for chart_id, chart_data in self.app.award_charts['award_charts'].items():
            cabins = chart_data.get('cabins', {})
            all_cabins.update(cabins.keys())

        # Sort cabin classes in standard order
        cabin_order = ["economy", "premium_economy", "business", "first"]
        available_cabins = [c for c in cabin_order if c in all_cabins]

        cabin_dropdown = ttk.Combobox(self.details_frame, textvariable=self.cabin_var,
                                      values=available_cabins, state="readonly", width=25)
        cabin_dropdown.grid(row=3, column=1, sticky=tk.EW, padx=5)

        # Search button
        search_button = ttk.Button(self.details_frame, text="Search Awards",
                                   command=self._search_awards)
        search_button.grid(row=4, column=0, columnspan=2, sticky=tk.EW, pady=10, padx=5)

        self.details_frame.columnconfigure(1, weight=1)

    def _filter_origin_dropdown(self, dropdown):
        """Filter origin dropdown based on user input (code or full name matching)"""
        self._filter_dropdown_generic(dropdown, self.origin_full_list, self.origin_var)

    def _filter_dest_dropdown(self, dropdown):
        """Filter destination dropdown based on user input (code or full name matching)"""
        self._filter_dropdown_generic(dropdown, self.dest_full_list, self.dest_var)

    def _filter_dropdown_generic(self, dropdown, full_list, var):
        """
        Generic filter logic for searchable dropdowns.
        
        Supports dual-field matching:
        - Match airport code (e.g., "CA")
        - Match full name (e.g., "california")
        - Case-insensitive matching
        
        Args:
            dropdown: The Combobox widget
            full_list: List of all available options (e.g., ["CA - California", "NY - New York"])
            var: The StringVar associated with the dropdown
        """
        user_input = var.get().strip().lower()
        
        if not user_input:
            # Empty input: show all options
            dropdown['values'] = full_list
            return
        
        # Filter options matching user input (code OR full name)
        filtered_options = []
        for option in full_list:
            # Option format: "CA - California"
            parts = option.split(" - ", 1)  # Split on first " - " only
            if len(parts) == 2:
                code, full_name = parts
                code_lower = code.lower()
                name_lower = full_name.lower()
                
                # Match if user input is in code OR in full name
                if user_input in code_lower or user_input in name_lower:
                    filtered_options.append(option)
            else:
                # Fallback: match anywhere in option string
                if user_input in option.lower():
                    filtered_options.append(option)
        
        # Update dropdown with filtered options
        dropdown['values'] = filtered_options
        


    def _extract_locations_from_zones(self, zones_dict):
        """
        Extract location codes and names from zone definitions.
        zones_dict = {
            "zone_1": {"locations": ["CA", "TX", "FL"]},
            "zone_2": {"locations": ["NY", "MA"]}
        }
        Returns: ["CA", "TX", "FL", "NY", "MA"] (all locations across zones)
        """
        all_locations = []
        for zone_name, zone_data in zones_dict.items():
            locations = zone_data.get('locations', [])
            all_locations.extend(locations)
        return sorted(list(set(all_locations)))

    def _search_awards(self):
        """Main search logic"""
        try:
            # Validate inputs
            origin_str = self.origin_var.get()
            dest_str = self.dest_var.get()
            distance_str = self.distance_var.get()
            cabin = self.cabin_var.get()
            carrier_str = self.carrier_var.get()

            if not all([origin_str, dest_str, distance_str]):
                messagebox.showwarning("Input Error", "Please fill all fields")
                return

            # Extract codes
            origin = origin_str.split(" - ")[0]  # "CA - California" → "CA"
            dest = dest_str.split(" - ")[0]  # "NY - New York" → "NY"
            carrier_code = carrier_str.split(" - ")[0]

            # Parse distance
            try:
                distance = int(distance_str)
            except ValueError:
                messagebox.showerror("Input Error", "Distance must be a number")
                return

            # Get route_category key (not used for chart selection, just for reference)
            route_name = self.route_var.get()
            route_categories = self.app.zone_systems.get('route_categories', {})
            route_category = None
            for key, data in route_categories.items():
                if data['name'] == route_name:
                    route_category = key
                    break

            if not route_category:
                messagebox.showerror("Error", "Route category not found")
                return

            # Step 1: Find all programs that can redeem this carrier
            applicable_ffps = self._find_programs_for_carrier(carrier_code)

            if not applicable_ffps:
                messagebox.showinfo("No Options", f"No programs found for {carrier_code}")
                return

            # Step 2: For each program, get appropriate award chart and calculate miles
            results = []

            for ffp_code in applicable_ffps:
                # Get appropriate chart for this FFP + carrier combination + route
                award_chart = self._get_award_chart(ffp_code, carrier_code, route_category)

                # NEW: If no chart found, display "No chart defined" instead of skipping
                if award_chart is None:
                    ffp_name = self.app.ffp['ffps'][ffp_code].get('name', ffp_code)
                    results.append((ffp_name, "No chart defined", ffp_code))
                    continue

                if cabin not in award_chart.get("cabins", {}):
                    continue

                miles = self._calculate_award_miles(
                    ffp_code, award_chart, origin, dest, distance, cabin
                )

                if miles is not None:
                    # Get FFP name from ffp.json
                    ffp_name = self.app.ffp['ffps'][ffp_code].get('name', ffp_code)

                    # Convert miles to kmiles if not "Dynamic"
                    if miles != "Dynamic":
                        miles_kmiles = miles / 1000
                    else:
                        miles_kmiles = miles

                    results.append((ffp_name, miles_kmiles, ffp_code))

            # Save results to app.search_context
            self.app.search_context['route_type'] = self.route_var.get()
            self.app.search_context['carrier_code'] = carrier_code
            self.app.search_context['origin'] = origin
            self.app.search_context['destination'] = dest
            self.app.search_context['distance'] = distance
            self.app.search_context['cabin'] = cabin
            self.app.search_context['results'] = [
                {
                    'ffp_code': result[2],
                    'program_name': result[0],
                    'miles': result[1]
                }
                for result in results
            ]

            # Display results
            self._display_results(results)

        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {str(e)}")

    def _find_programs_for_carrier(self, carrier_code):
        """
        Find all FFP programs that can redeem the specified carrier.
        Returns list of FFP codes (e.g., ['AA', 'AS', 'AV'])
        """
        # DEBUG LOGGING
        print(f"\n[DEBUG] Looking for programs that can redeem carrier: {carrier_code}")

        ffps = self.app.ffp['ffps']
        partners_data = self.app.partners['programs']
        alliances_data = self.app.alliance['alliances']

        print(f"[DEBUG] Available FFPs: {list(ffps.keys())}")
        print(f"[DEBUG] All FFP objects: {ffps}")

        results = []

        # Step 1: Self FFP
        if carrier_code in ffps:
            print(f"[DEBUG] ✓ Found self FFP: {carrier_code}")
            results.append(carrier_code)
        else:
            print(f"[DEBUG] ✗ No self FFP for {carrier_code}")

        # Step 2: Partner FFPs
        for partner_entry in partners_data:
            if partner_entry['relationship'] not in ['both', 'redeem_only']:
                continue

            ffp_code = partner_entry['ffp']
            if ffp_code not in ffps:
                continue

            can_redeem = False

            if partner_entry['type'] == 'alliance':
                alliance_code = partner_entry['alliance']
                for alliance in alliances_data:
                    if alliance['code'] == alliance_code:
                        if carrier_code in alliance.get('members', []):
                            can_redeem = True
                            break
            elif partner_entry['type'] == 'individual':
                if carrier_code in partner_entry.get('carriers', []):
                    can_redeem = True

            if can_redeem and ffp_code not in results:
                print(f"[DEBUG] ✓ Found partner FFP via {partner_entry['type']}: {ffp_code}")
                results.append(ffp_code)

        print(f"[DEBUG] Final results: {results}")
        return results

    def _get_award_chart(self, ffp_code, carrier_code, route_category):
        """
        Get the appropriate award chart for an FFP when redeeming on a carrier.

        CORRECTED PRIORITY ORDER:
        1. Self chart ONLY when FFP == Carrier (returns immediately, no route check)
        2. Specific chart for this carrier (with route matching for distance-based)
        3. All partners chart with route category match (distance-based only)
        4. Default all partners chart (no route_categories constraint)

        Key fix: Self chart is ONLY checked when ffp_code == carrier_code!
        """
        award_charts = self.app.award_charts['award_charts']

        # Find all charts for this FFP
        ffp_charts = [
            (chart_id, chart_data)
            for chart_id, chart_data in award_charts.items()
            if chart_data.get('ffp_code') == ffp_code
        ]

        if not ffp_charts:
            return None

        # PRIORITY 1: SELF CHART (ONLY when ffp_code == carrier_code, e.g., AA == AA)
        # Return immediately without route filtering - no route check needed for self
        if ffp_code == carrier_code:
            for chart_id, chart in ffp_charts:
                if chart.get('applies_to') == 'self':
                    # Return self chart immediately, regardless of type or route
                    # AA redeeming on AA? Return AA_self (dynamic or zone-based)
                    return chart

        # PRIORITY 2: Specific chart for this carrier (partner-specific charts)
        for chart_id, chart in ffp_charts:
            if chart.get('applies_to') == 'specific':
                if carrier_code in chart.get('specific_partners', []):
                    # For distance-based, check route category match
                    if chart.get('type') == 'distance_based':
                        route_cats = chart.get('route_categories', [])
                        if route_cats and route_category in route_cats:
                            return chart
                    else:
                        # Zone-based or other types - return without route check
                        return chart

        # PRIORITY 3: All partners chart with route category match
        for chart_id, chart in ffp_charts:
            if chart.get('applies_to') == 'all_partners':
                if chart.get('type') == 'distance_based':
                    # Distance-based requires route category match
                    route_cats = chart.get('route_categories', [])
                    if route_cats and route_category in route_cats:
                        return chart
                elif chart.get('type') in ['zone_based', 'dynamic']:
                    # Zone-based or dynamic with route category constraint
                    route_cats = chart.get('route_categories', [])
                    if route_cats and route_category in route_cats:
                        return chart

        # PRIORITY 4: Default all partners chart (no route_categories defined)
        for chart_id, chart in ffp_charts:
            if chart.get('applies_to') == 'all_partners':
                if 'route_categories' not in chart:
                    # No route restriction - this is a catch-all chart
                    return chart

        return None

    def _calculate_award_miles(self, ffp_code, award_chart, origin, dest, distance, cabin):
        """Calculate award miles based on program type"""
        chart_type = award_chart.get("type")

        if chart_type == "dynamic":
            return "Dynamic"
        elif chart_type == "hybrid_distance_zone":
            # NEW: Check priority field to determine logic flow
            priority = award_chart.get("priority", "distance_first")  # Default

            cabin_data = award_chart.get("cabins", {}).get(cabin, {})

            if priority == "distance_first":
                # VS + AF/KLM: Try distance (if within threshold), then zone
                return self._hybrid_distance_first(award_chart, origin, dest, distance, cabin_data)
            elif priority == "zone_first":
                # VS + Delta: Try zone first, then distance fallback
                return self._hybrid_zone_first(award_chart, origin, dest, distance, cabin_data)
            else:
                print(f"[ERROR] Unknown hybrid priority: {priority}")
                return None

        elif chart_type == "distance_based":
            return self._lookup_distance_based(award_chart, distance, cabin)
        elif chart_type == "zone_based":
            return self._lookup_zone_based(award_chart, origin, dest, cabin)

        return None

    def _hybrid_distance_first(self, award_chart, origin, dest, distance, cabin_data):
        """
        Hybrid logic for distance-priority charts (e.g., VS + AF/KLM).
        Logic:
        1. IF distance <= threshold → Try distance_based
        2. ELSE or no match → Use zone_based

        Args:
            award_chart: The award chart dictionary
            origin: Origin location code
            dest: Destination location code
            distance: Flight distance in miles
            cabin_data: Cabin data containing distance_based and zone_based arrays

        Returns:
            Award miles (int) or None
        """
        threshold = award_chart.get("distance_threshold", 999999)

        # Step 1: Check distance if within threshold
        if distance <= threshold:
            distance_brackets = cabin_data.get("distance_based", [])
            for bracket in distance_brackets:
                if bracket["min_miles"] <= distance <= bracket["max_miles"]:
                    print(f"[HYBRID DEBUG] distance_first: Found distance match = {bracket['award_miles']}")
                    return bracket["award_miles"]

        # Step 2: Fall through to zone-based
        zone_pairs = cabin_data.get("zone_based", [])
        if zone_pairs:
            result = self._lookup_zone_based_from_pairs(award_chart, origin, dest, zone_pairs)
            if result is not None:
                print(f"[HYBRID DEBUG] distance_first: Found zone match = {result}")
                return result

        print(f"[HYBRID DEBUG] distance_first: No match found")
        return None

    def _hybrid_zone_first(self, award_chart, origin, dest, distance, cabin_data):
        """
        Hybrid logic for zone-priority charts (e.g., VS + Delta).
        Logic:
        1. Try zone_based first (check if zone pair exists)
        2. IF no zone match → Fall back to distance_based

        Args:
            award_chart: The award chart dictionary
            origin: Origin location code
            dest: Destination location code
            distance: Flight distance in miles
            cabin_data: Cabin data containing distance_based and zone_based arrays

        Returns:
            Award miles (int) or None
        """
        # Step 1: Try zone lookup first
        zone_pairs = cabin_data.get("zone_based", [])
        if zone_pairs:
            result = self._lookup_zone_based_from_pairs(award_chart, origin, dest, zone_pairs)
            if result is not None:
                # Found a matching zone pair, use it
                print(f"[HYBRID DEBUG] zone_first: Found zone match = {result}")
                return result

        # Step 2: Fall back to distance-based
        print(f"[HYBRID DEBUG] zone_first: No zone match, checking distance")
        distance_brackets = cabin_data.get("distance_based", [])
        for bracket in distance_brackets:
            if bracket["min_miles"] <= distance <= bracket["max_miles"]:
                print(f"[HYBRID DEBUG] zone_first: Found distance fallback = {bracket['award_miles']}")
                return bracket["award_miles"]

        print(f"[HYBRID DEBUG] zone_first: No match found")
        return None

    def _lookup_zone_based_from_pairs(self, award_chart, origin, dest, zone_pairs):
        """
        Lookup miles for zone-based awards from explicit zone pairs.
        Used by hybrid charts where zone pairs are nested under each cabin.

        Args:
            award_chart: The award chart dictionary
            origin: Origin location code (e.g., "FRA")
            dest: Destination location code (e.g., "NY")
            zone_pairs: List of zone pair dictionaries [{"from": "EU", "to": "US", "miles": 30000}, ...]

        Returns:
            Award miles (int) or None if no match found
        """
        zone_system_name = award_chart.get("zone_system")

        if not zone_system_name:
            print(f"[HYBRID DEBUG] No zone_system defined in chart")
            return None

        # Get zone definitions
        zone_definitions = self.app.zone_systems.get('zone_definitions', {})
        zone_system = zone_definitions.get(zone_system_name)

        if not zone_system:
            print(f"[HYBRID DEBUG] Zone system '{zone_system_name}' not found")
            return None

        # Map locations to zones
        origin_zone = self._get_zone_for_location(origin, zone_system)
        dest_zone = self._get_zone_for_location(dest, zone_system)

        print(f"[HYBRID DEBUG] {origin} → zone '{origin_zone}', {dest} → zone '{dest_zone}'")

        if not origin_zone or not dest_zone:
            print(f"[HYBRID DEBUG] Failed to map locations to zones")
            return None

        # Search zone pairs (bidirectional)
        for pair in zone_pairs:
            pair_from = pair.get("from")
            pair_to = pair.get("to")
            miles = pair.get("miles")

            # Forward match
            if pair_from == origin_zone and pair_to == dest_zone:
                print(f"[HYBRID DEBUG] ✓ Forward match: {origin_zone} → {dest_zone} = {miles}")
                return miles

            # Reverse match
            if pair_from == dest_zone and pair_to == origin_zone:
                print(f"[HYBRID DEBUG] ✓ Reverse match: {dest_zone} → {origin_zone} = {miles}")
                return miles

        print(f"[HYBRID DEBUG] ✗ No zone pair found for {origin_zone} ↔ {dest_zone}")
        return None

    def _lookup_distance_based(self, award_chart, distance, cabin):
        """Lookup miles for distance-based award chart"""
        brackets = award_chart.get("cabins", {}).get(cabin, [])

        if not brackets:
            return None

        for bracket in brackets:
            if bracket["min_miles"] <= distance <= bracket["max_miles"]:
                return bracket["award_miles"]

        return None

    def _lookup_zone_based(self, award_chart, origin, dest, cabin):
        """
        Lookup miles for zone-based award chart with DOMESTIC OVERRIDE support.
        Supports:
        - Default domestic override (all countries)
        - Per-country exceptions (e.g., MAR has different rate than FIN)
        """
        zone_system_name = award_chart.get("zone_system")

        print(f"\n[ZONE DEBUG] zone_system_name: {zone_system_name}")

        if not zone_system_name:
            print(f"[ZONE DEBUG] ✗ No zone_system defined")
            return None

        # Get zone definitions
        zone_definitions = self.app.zone_systems.get('zone_definitions', {})

        print(f"[ZONE DEBUG] Available zone systems: {list(zone_definitions.keys())}")

        zone_system = zone_definitions.get(zone_system_name)

        if not zone_system:
            print(f"[ZONE DEBUG] ✗ Zone system '{zone_system_name}' not found!")
            return None

        print(f"[ZONE DEBUG] ✓ Found zone_system '{zone_system_name}'")

        # ===== NEW: CHECK DOMESTIC OVERRIDE FIRST =====

        domestic_override = zone_system.get("domestic_override")

        if domestic_override and origin == dest:
            # Same location = domestic flight within same country
            print(f"[ZONE DEBUG] Checking domestic override for {origin}")

            # Check for country-specific exception first
            exceptions = domestic_override.get("exceptions", {})
            if origin in exceptions:
                country_miles = exceptions[origin].get(cabin)
                if country_miles is not None:
                    print(f"[ZONE DEBUG] ✓ DOMESTIC EXCEPTION! {origin} → {origin} ({cabin}) = {country_miles}")
                    return country_miles

            # Fall back to default domestic rate
            default_rates = domestic_override.get("default", {})
            default_miles = default_rates.get(cabin)
            if default_miles is not None:
                print(f"[ZONE DEBUG] ✓ DOMESTIC DEFAULT! {origin} → {origin} ({cabin}) = {default_miles}")
                return default_miles

        # ===== END DOMESTIC OVERRIDE CHECK =====

        # Continue with normal zone matching

        origin_zone = self._get_zone_for_location(origin, zone_system)
        dest_zone = self._get_zone_for_location(dest, zone_system)

        print(f"[ZONE DEBUG] origin '{origin}' → zone '{origin_zone}'")
        print(f"[ZONE DEBUG] dest '{dest}' → zone '{dest_zone}'")

        if not origin_zone or not dest_zone:
            print(f"[ZONE DEBUG] ✗ Failed to map locations to zones")
            return None

        print(f"[ZONE DEBUG] ✓ Both locations mapped successfully")

        # Lookup zone pair in award chart
        zone_pairs = award_chart.get("cabins", {}).get(cabin, [])

        print(f"[ZONE DEBUG] Looking for cabin '{cabin}'")
        print(f"[ZONE DEBUG] Found {len(zone_pairs)} zone pairs for {cabin}")

        if not zone_pairs:
            print(f"[ZONE DEBUG] ✗ No zone pairs for cabin '{cabin}'")
            return None

        # BIDIRECTIONAL MATCHING: Try both forward and reverse

        for i, pair in enumerate(zone_pairs):
            pair_from = pair.get("from")
            pair_to = pair.get("to")
            miles = pair.get("miles")

            print(f"[ZONE DEBUG] Pair {i}: {pair_from} → {pair_to} = {miles}")

            # Forward match
            if pair_from == origin_zone and pair_to == dest_zone:
                print(f"[ZONE DEBUG] ✓ FORWARD MATCH! {origin_zone} → {dest_zone} = {miles}")
                return miles

            # Reverse match
            if pair_from == dest_zone and pair_to == origin_zone:
                print(f"[ZONE DEBUG] ✓ REVERSE MATCH! {dest_zone} → {origin_zone} = {miles}")
                return miles

        print(f"[ZONE DEBUG] ✗ No matching zone pair for {origin_zone} ↔ {dest_zone} (bidirectional)")
        return None

    def _get_zone_for_location(self, location_code, zone_system):
        """
        Find which zone a location belongs to.

        IMPORTANT: Returns the FIRST (most specific) zone found.
        Zone order matters - specific zones (EU_ESP) must come BEFORE general zones (EU)!
        """
        zones = zone_system.get('zones', {})

        # Iterate through zones in order
        for zone_name, zone_data in zones.items():
            locations = zone_data.get('locations', [])

            # If location found in this zone, return IMMEDIATELY
            # Don't continue checking other zones
            if location_code in locations:
                print(f"[ZONE DEBUG] Found {location_code} in zone '{zone_name}'")
                return zone_name

        # Not found in any zone
        print(f"[ZONE DEBUG] Location '{location_code}' not found in any zone!")
        return None

    def _display_results(self, results):
        """Display search results in listbox, sorted by miles"""
        self.results_listbox.delete(0, tk.END)

        if not results:
            self.results_listbox.insert(tk.END, "No award options found")
            return

        # Sort results: numeric → "Dynamic" → "No chart defined"

        def sort_key(item):
            program_name, miles, ffp_code = item
            if miles == "No chart defined":
                return (2, 0)  # Show "No chart defined" last (highest priority to fix)
            elif miles == "Dynamic":
                return (1, float('inf'))  # Show "Dynamic" second-to-last
            else:
                return (0, miles)  # Numeric miles first, sorted ascending

        results.sort(key=sort_key)

        # Display header
        header = f"{'Program':<45} {'Miles (kmiles)':<20}"
        self.results_listbox.insert(tk.END, header)
        self.results_listbox.insert(tk.END, "-" * 65)

        # Display results
        for program_name, miles, ffp_code in results:
            if miles == "No chart defined":
                # NEW: Handle "No chart defined" display
                miles_str = "No chart defined"
            elif miles == "Dynamic":
                miles_str = "Dynamic"
            else:
                miles_str = f"{miles:.2f}"

            display_text = f"{program_name:<45} {miles_str:<20}"
            self.results_listbox.insert(tk.END, display_text)
