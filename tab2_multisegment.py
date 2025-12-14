"""
tab2_multisegment.py: Award Chart Lookup - Multiple Segment Search (v4 - CRITICAL FIX)

ENHANCEMENTS v4 (LOGIC CORRECTION):
1. Display: "Miles" header, XX.XXk format (2 decimals)
2. Segment limit: Maximum 6 segments
3. Sub-itinerary search: All contiguous segment groups (no jumping)
4. FIXED: Subsegment search now uses SAME logic as full segment (reuses existing functions)
5. Subsegment results display: Show ALL subsegments with results (even if Dynamic/No chart)
6. Cheapest combo: Compare ONLY breakdown combinations (not vs full segment)
7. Graceful handling: Execute subsegment search even if full segment has no FFP
8. FIXED: Subsegment results sorted same as main results (numeric ascending, Dynamic, errors)

Changes from v3:
- Subsegment search REUSES _search_single_segment() and multi-segment pricing logic
- No separate range calculation functions (AC special case now works!)
- Results sorted identically to main results
- Guaranteed consistency between full and subsegment searches
"""

import tkinter as tk
from tkinter import ttk, messagebox
import math

class Tab2Frame(ttk.Frame):
    """Tab 2: Award Chart Lookup - Multiple Segment Search with Subsegment Analysis (v4)"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.segments = []
        self.subsegment_results = {}
        try:
            self._setup_ui()
        except Exception as e:
            messagebox.showerror("Tab 2 Error", str(e))
            raise

    def _setup_ui(self):
        """Setup main UI using ONLY GRID (no pack)"""
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        title_label = ttk.Label(self, text="Award Chart Search", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, padx=10, pady=10)

        left_frame = ttk.LabelFrame(self, text="Search Parameters", padding=10)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        self.segments_canvas = tk.Canvas(left_frame, bg="white", highlightthickness=0)
        segments_scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.segments_canvas.yview)
        self.segments_scrollable_frame = ttk.Frame(self.segments_canvas)
        self.segments_scrollable_frame.bind("<Configure>", lambda e: self.segments_canvas.configure(scrollregion=self.segments_canvas.bbox("all")))
        self.segments_canvas.create_window((0, 0), window=self.segments_scrollable_frame, anchor="nw")
        self.segments_canvas.configure(yscrollcommand=segments_scrollbar.set)

        self.segments_canvas.bind("<MouseWheel>", lambda e: self.segments_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        self.segments_canvas.bind("<Button-4>", lambda e: self.segments_canvas.yview_scroll(-1, "units"))
        self.segments_canvas.bind("<Button-5>", lambda e: self.segments_canvas.yview_scroll(1, "units"))

        self.segments_canvas.grid(row=0, column=0, sticky="nsew")
        segments_scrollbar.grid(row=0, column=1, sticky="ns")

        self.origin_full_list = []
        self.dest_full_list = []
        self.carrier_full_list = []

        self._populate_origin_destinations()
        self._populate_cabins()
        self._populate_carriers()

        self._add_segment_panel()

        buttons_frame = ttk.Frame(left_frame)
        buttons_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        buttons_frame.grid_columnconfigure(1, weight=1)

        search_button = ttk.Button(buttons_frame, text="Search Awards", command=self._on_search_awards)
        search_button.grid(row=0, column=0, sticky="ew", padx=5)

        add_segment_button = ttk.Button(buttons_frame, text="+ Add Segment", command=self._add_segment_click)
        add_segment_button.grid(row=0, column=1, sticky="ew", padx=5)

        delete_segment_button = ttk.Button(buttons_frame, text="- Delete Last Segment", command=self._delete_segment_click)
        delete_segment_button.grid(row=0, column=2, sticky="ew", padx=5)

        results_frame = ttk.LabelFrame(self, text="Award Results", padding=10)
        results_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(results_frame)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.results_listbox = tk.Listbox(results_frame, yscrollcommand=scrollbar.set, height=20, font=("Courier", 10))
        self.results_listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=self.results_listbox.yview)

        self.results_listbox.bind("<MouseWheel>", lambda e: self.results_listbox.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        self.results_listbox.bind("<Button-4>", lambda e: self.results_listbox.yview_scroll(-1, "units"))
        self.results_listbox.bind("<Button-5>", lambda e: self.results_listbox.yview_scroll(1, "units"))

        self.results_listbox.insert(tk.END, "Select origin, destination, carrier, cabin, and distance")
        self.results_listbox.insert(tk.END, "then click 'Search Awards' to see results.")

    # ===== SEGMENT MANAGEMENT (UNCHANGED) =====

    def _add_segment_panel(self):
        """Add a new segment input panel"""
        segment_index = len(self.segments)

        segment_frame = ttk.LabelFrame(self.segments_scrollable_frame, text=f"Segment {segment_index + 1}", padding=10)
        segment_frame.pack(fill="x", padx=5, pady=5)
        segment_frame.grid_columnconfigure(1, weight=1)

        origin_var = tk.StringVar()
        dest_var = tk.StringVar()
        carrier_var = tk.StringVar()
        cabin_var = tk.StringVar(value="economy")
        distance_var = tk.StringVar()

        ttk.Label(segment_frame, text="Origin:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        origin_dropdown = ttk.Combobox(segment_frame, textvariable=origin_var, state="normal", width=35)
        origin_dropdown.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        origin_dropdown.bind("<<ComboboxSelected>>", lambda e, seg_idx=segment_index: self._on_origin_selected(seg_idx))
        origin_dropdown.bind("<KeyRelease>", lambda e, seg_idx=segment_index: self._filter_locations(seg_idx, "origin"))

        ttk.Label(segment_frame, text="Destination:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        dest_dropdown = ttk.Combobox(segment_frame, textvariable=dest_var, state="normal", width=35)
        dest_dropdown.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        dest_dropdown.bind("<<ComboboxSelected>>", lambda e, seg_idx=segment_index: self._on_dest_selected(seg_idx))
        dest_dropdown.bind("<KeyRelease>", lambda e, seg_idx=segment_index: self._filter_locations(seg_idx, "dest"))

        ttk.Label(segment_frame, text="Carrier:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        carrier_dropdown = ttk.Combobox(segment_frame, textvariable=carrier_var, state="normal", width=35)
        carrier_dropdown.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        carrier_dropdown.bind("<KeyRelease>", lambda e, seg_idx=segment_index: self._filter_carriers(seg_idx))

        ttk.Label(segment_frame, text="Cabin:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        cabin_dropdown = ttk.Combobox(segment_frame, textvariable=cabin_var, state="readonly", width=35)
        cabin_dropdown.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)

        ttk.Label(segment_frame, text="Distance (miles):").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        distance_entry = ttk.Entry(segment_frame, textvariable=distance_var, width=35)
        distance_entry.grid(row=4, column=1, sticky=tk.EW, padx=5, pady=5)

        cabin_dropdown["values"] = self._get_available_cabins()
        if cabin_dropdown["values"]:
            cabin_var.set(cabin_dropdown["values"][0])

        origin_dropdown["values"] = self.origin_full_list
        dest_dropdown["values"] = self.dest_full_list
        carrier_dropdown["values"] = self.carrier_full_list

        segment_data = {
            "frame": segment_frame,
            "origin_var": origin_var,
            "dest_var": dest_var,
            "carrier_var": carrier_var,
            "cabin_var": cabin_var,
            "distance_var": distance_var,
            "origin_dropdown": origin_dropdown,
            "dest_dropdown": dest_dropdown,
            "carrier_dropdown": carrier_dropdown,
            "cabin_dropdown": cabin_dropdown,
        }

        self.segments.append(segment_data)

        if segment_index > 0:
            prev_dest = self.segments[segment_index - 1]["dest_var"].get()
            if prev_dest:
                origin_var.set(prev_dest)

    def _add_segment_click(self):
        """Handle + Add Segment button click"""
        self._add_segment_panel()
        self.segments_canvas.yview_moveto(1)

    def _delete_segment_click(self):
        """Handle - Delete Last Segment button click"""
        if len(self.segments) <= 1:
            messagebox.showwarning("Cannot Delete", "Cannot delete the first segment.")
            return

        last_segment = self.segments.pop()
        last_segment["frame"].destroy()

    # ===== HELPER FUNCTIONS (UNCHANGED) =====

    def _populate_origin_destinations(self):
        """Populate origin/dest dropdowns with all locations"""
        destinations = self.app.zone_systems.get("destinations", {})
        all_locations = []
        for region_code, region_data in destinations.items():
            locations = region_data.get("locations", {})
            for loc_code, loc_info in locations.items():
                if isinstance(loc_info, dict):
                    display_str = f"{loc_code} - {loc_info.get('name', loc_code)}"
                else:
                    display_str = f"{loc_code} - {loc_info}"
                all_locations.append(display_str)

        all_locations = sorted(list(set(all_locations)))
        self.origin_full_list = all_locations
        self.dest_full_list = all_locations

    def _populate_cabins(self):
        """Populate cabin dropdown with available cabins"""
        all_cabins = set()
        for chart_data in self.app.award_charts.get("award_charts", {}).values():
            cabins = chart_data.get("cabins", {})
            all_cabins.update(cabins.keys())

        cabin_order = ["economy", "premium_economy", "business", "first"]
        self.available_cabins = [c for c in cabin_order if c in all_cabins]

    def _get_available_cabins(self):
        """Get available cabins for dropdown"""
        if not hasattr(self, "available_cabins"):
            self._populate_cabins()
        return self.available_cabins

    def _populate_carriers(self):
        """Populate carrier dropdown with all carriers (sorted)"""
        carrier_list = [f"{c['code']} - {c['name']}" for c in self.app.carriers.get("carriers", [])]
        self.carrier_full_list = sorted(carrier_list)

    def _get_location_country(self, location_code):
        """Get the country/region for a location code"""
        destinations = self.app.zone_systems.get("destinations", {})
        for region_code, region_data in destinations.items():
            locations = region_data.get("locations", {})
            if location_code in locations:
                return region_code
        return None

    def _sort_carriers(self, segment_index):
        """Sort carriers by origin country first, then destination country, then rest."""
        if segment_index >= len(self.segments):
            return self.carrier_full_list

        origin_str = self.segments[segment_index]["origin_var"].get().strip()
        dest_str = self.segments[segment_index]["dest_var"].get().strip()

        origin_code = origin_str.split(" - ")[0].strip() if origin_str else None
        dest_code = dest_str.split(" - ")[0].strip() if dest_str else None

        origin_country = self._get_location_country(origin_code) if origin_code else None
        dest_country = self._get_location_country(dest_code) if dest_code else None

        carriers_map = {c["code"]: c for c in self.app.carriers.get("carriers", [])}

        origin_carriers = []
        dest_carriers = []
        other_carriers = []

        for carrier_display in self.carrier_full_list:
            code = carrier_display.split(" - ")[0].strip()
            carrier_info = carriers_map.get(code, {})
            carrier_country = carrier_info.get("country")

            if origin_country and carrier_country == origin_country:
                origin_carriers.append(carrier_display)
            elif dest_country and carrier_country == dest_country:
                dest_carriers.append(carrier_display)
            else:
                other_carriers.append(carrier_display)

        sorted_carriers = origin_carriers + dest_carriers + other_carriers
        return sorted_carriers

    def _on_origin_selected(self, segment_index):
        """Called when user SELECTS origin from dropdown"""
        self._filter_carriers(segment_index)

    def _on_dest_selected(self, segment_index):
        """Called when user SELECTS destination from dropdown"""
        self._filter_carriers(segment_index)

    def _filter_carriers(self, segment_index):
        """Filter carriers based on user input and smart sorting"""
        if segment_index >= len(self.segments):
            return

        segment = self.segments[segment_index]
        user_input = segment["carrier_var"].get().strip().lower()

        sorted_carriers = self._sort_carriers(segment_index)

        if not user_input:
            segment["carrier_dropdown"]["values"] = sorted_carriers
            return

        filtered_options = []
        for carrier_display in sorted_carriers:
            parts = carrier_display.split(" - ", 1)
            if len(parts) == 2:
                code, full_name = parts
                if user_input in code.lower() or user_input in full_name.lower():
                    filtered_options.append(carrier_display)
            else:
                if user_input in carrier_display.lower():
                    filtered_options.append(carrier_display)

        segment["carrier_dropdown"]["values"] = filtered_options

    def _filter_locations(self, segment_index, location_type):
        """Generic filter for origin/dest dropdowns"""
        if segment_index >= len(self.segments):
            return

        segment = self.segments[segment_index]

        if location_type == "origin":
            var = segment["origin_var"]
            dropdown = segment["origin_dropdown"]
            full_list = self.origin_full_list
        else:
            var = segment["dest_var"]
            dropdown = segment["dest_dropdown"]
            full_list = self.dest_full_list

        user_input = var.get().strip().lower()

        if not user_input:
            dropdown["values"] = full_list
            return

        filtered_options = []
        for option in full_list:
            parts = option.split(" - ", 1)
            if len(parts) == 2:
                code, full_name = parts
                if user_input in code.lower() or user_input in full_name.lower():
                    filtered_options.append(option)
            else:
                if user_input in option.lower():
                    filtered_options.append(option)

        dropdown["values"] = filtered_options

    def _validate_segment_inputs(self, segment_index):
        """Validate that a segment has been properly filled."""
        if segment_index >= len(self.segments):
            return False, f"Segment {segment_index + 1} not found"

        segment = self.segments[segment_index]
        origin_str = segment["origin_var"].get().strip()
        dest_str = segment["dest_var"].get().strip()
        carrier_str = segment["carrier_var"].get().strip()
        distance_str = segment["distance_var"].get().strip()
        cabin = segment["cabin_var"].get()

        if not all([origin_str, dest_str, carrier_str, distance_str, cabin]):
            return False, f"Segment {segment_index + 1}: Please fill all fields"

        if origin_str not in self.origin_full_list:
            return False, f"Segment {segment_index + 1}: '{origin_str}' is not a valid origin"

        if dest_str not in self.dest_full_list:
            return False, f"Segment {segment_index + 1}: '{dest_str}' is not a valid destination"

        valid_carriers = segment["carrier_dropdown"]["values"]
        if not valid_carriers or carrier_str not in valid_carriers:
            return False, f"Segment {segment_index + 1}: '{carrier_str}' is not a valid carrier"

        try:
            float(distance_str)
        except ValueError:
            return False, f"Segment {segment_index + 1}: Distance must be a number"

        return True, None

    def _validate_all_segments(self):
        """Validate all segments."""
        for i in range(len(self.segments)):
            is_valid, error_msg = self._validate_segment_inputs(i)
            if not is_valid:
                return False, error_msg
        return True, None

    # ===== MAIN SEARCH HANDLER (UNCHANGED) =====

    def _on_search_awards(self, event=None):
        """Main search handler"""
        try:
            # Validate segment count (max 6)
            if len(self.segments) > 6:
                messagebox.showerror("Segment Limit", "Maximum 6 segments allowed. Please remove extra segments.")
                return

            # Validate all segments
            is_valid, error_msg = self._validate_all_segments()
            if not is_valid:
                messagebox.showerror("Input Error", error_msg)
                return

            segment_count = len(self.segments)

            if segment_count == 1:
                self._search_single_segment_route()
            else:
                self._search_multiple_segment_route()

        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {str(e)}")
            import traceback
            traceback.print_exc()

    def _search_single_segment_route(self):
        """Route to single segment search"""
        segment = self.segments[0]
        origin_str = segment["origin_var"].get().strip()
        dest_str = segment["dest_var"].get().strip()
        distance_str = segment["distance_var"].get().strip()
        cabin = segment["cabin_var"].get()
        carrier_str = segment["carrier_var"].get()

        origin = origin_str.split(" - ")[0].strip()
        dest = dest_str.split(" - ")[0].strip()
        carrier_code = carrier_str.split(" - ")[0].strip()

        distance = math.ceil(float(distance_str))

        results = self._search_single_segment(origin, dest, distance, cabin, carrier_code)

        self._display_results(results)

    def _search_multiple_segment_route(self):
        """Route to multiple segment search with subsegment analysis (v4)"""
        try:
            all_carriers = self._extract_all_carriers()

            applicable_ffps = self._find_ffps_for_all_carriers(all_carriers)

            # CHANGE v3: Don't return early on "No ffp" - still do subsegment search
            results = []
            
            if applicable_ffps:
                # Full segment search (if FFP available)
                for ffp_code in applicable_ffps:
                    ffp_name = self.app.ffp.get("ffps", {}).get(ffp_code, {}).get("name", ffp_code)

                    ffp_info = self.app.ffp.get("ffps", {}).get(ffp_code, {})
                    separate_pricing = ffp_info.get("seperate_Segment_pricing", False)

                    if separate_pricing:
                        miles_result = self._calculate_separate_segment_pricing(ffp_code)
                        results.append((ffp_name, miles_result, ffp_code))
                    else:
                        miles_result = self._calculate_multisegment_fixed_pricing(ffp_code, all_carriers)
                        results.append((ffp_name, miles_result, ffp_code))
            else:
                # No FFP for full segment - still show this
                results = [("No FFP", "No ffp stored can issue this entire itinerary.", None)]

            # CHANGE v3: Always execute subsegment search (regardless of full segment result)
            num_segments = len(self.segments)
            if num_segments > 1:
                self.subsegment_results = {}
                self._search_subsegments(num_segments)
                self._display_results(results, has_subsegments=True)
            else:
                self._display_results(results)

        except Exception as e:
            messagebox.showerror("Error", f"Multi-segment search failed: {str(e)}")
            import traceback
            traceback.print_exc()

    # ===== SUBSEGMENT SEARCH FUNCTIONS (v4: FIXED LOGIC) =====

    def _search_subsegments(self, num_segments):
        """Search all contiguous subsegment combinations"""
        subseg_ranges = self._generate_contiguous_subsegments(num_segments)

        for start, end in subseg_ranges:
            # Skip the original full segment (already searched)
            if start == 0 and end == num_segments - 1:
                continue

            miles_results = self._search_subsegment_range_all_programs(start, end)
            key = f"seg_{start}_{end}"
            
            self.subsegment_results[key] = {
                "results": miles_results,  # List of (program_name, miles) tuples
                "range": (start, end)
            }

    def _generate_contiguous_subsegments(self, num_segments):
        """Generate all contiguous subsegment ranges"""
        ranges = []
        for length in range(1, num_segments + 1):
            for start in range(num_segments - length + 1):
                end = start + length - 1
                ranges.append((start, end))
        return ranges

    def _search_subsegment_range_all_programs(self, start_idx, end_idx):
        """
        Search subsegment range using SAME logic as full segment search (v4 FIX).
        This ensures all special cases (AC dynamic partners, etc.) are handled correctly.
        """
        try:
            # Save original segments
            original_segments = self.segments
            
            try:
                # Temporarily set segments to just the subsegment range
                self.segments = original_segments[start_idx:end_idx + 1]
                
                if len(self.segments) == 1:
                    # Single segment: use existing single segment search
                    segment = self.segments[0]
                    origin_str = segment["origin_var"].get().strip()
                    dest_str = segment["dest_var"].get().strip()
                    distance_str = segment["distance_var"].get().strip()
                    cabin = segment["cabin_var"].get()
                    carrier_str = segment["carrier_var"].get()

                    origin = origin_str.split(" - ")[0].strip()
                    dest = dest_str.split(" - ")[0].strip()
                    carrier_code = carrier_str.split(" - ")[0].strip()
                    distance = math.ceil(float(distance_str))

                    # Use existing single-segment search logic
                    results = self._search_single_segment(origin, dest, distance, cabin, carrier_code)
                    # Return: [(program_name, miles), ...]
                    return [(name, miles) for name, miles, _ in results]
                
                else:
                    # Multi-segment: use existing multi-segment search logic
                    carriers_in_range = set()
                    for seg in self.segments:
                        carrier_str = seg["carrier_var"].get().strip()
                        carrier_code = carrier_str.split(" - ")[0].strip()
                        carriers_in_range.add(carrier_code)

                    applicable_ffps = self._find_ffps_for_all_carriers(list(carriers_in_range))

                    if not applicable_ffps:
                        return []

                    results = []
                    for ffp_code in applicable_ffps:
                        ffp_name = self.app.ffp.get("ffps", {}).get(ffp_code, {}).get("name", ffp_code)

                        ffp_info = self.app.ffp.get("ffps", {}).get(ffp_code, {})
                        separate_pricing = ffp_info.get("seperate_Segment_pricing", False)

                        if separate_pricing:
                            # Use existing pricing calculation
                            miles_result = self._calculate_separate_segment_pricing(ffp_code)
                        else:
                            # Use existing multi-segment pricing (includes AC special case!)
                            miles_result = self._calculate_multisegment_fixed_pricing(ffp_code, list(carriers_in_range))

                        results.append((ffp_name, miles_result))

                    return results
                    
            finally:
                # Always restore original segments
                self.segments = original_segments
                
        except Exception as e:
            return []

    # ===== PARTITION ANALYSIS (UNCHANGED) =====

    def _generate_partitions(self, num_segments):
        """Generate all valid partition combinations (breakdown-only, excluding full segment)"""
        def generate_partitions_helper(start, end):
            if start > end:
                return [[]]

            result = []
            for split in range(start, end + 1):
                first_part = (start, split)
                remaining = generate_partitions_helper(split + 1, end)

                for rest in remaining:
                    result.append([first_part] + rest)

            return result

        partitions = generate_partitions_helper(0, num_segments - 1)
        
        # CHANGE v3: Remove full segment partition from comparison
        # Only keep breakdowns (2+ groups)
        breakdown_partitions = [p for p in partitions if len(p) > 1]
        
        return breakdown_partitions

    def _find_cheapest_partition_combo(self):
        """Find cheapest combination from BREAKDOWN ONLY (not including full segment)"""
        if not self.subsegment_results:
            return None

        num_segments = len(self.segments)
        all_partitions = self._generate_partitions(num_segments)

        if not all_partitions:
            return None

        cheapest_combo = None
        cheapest_cost = float('inf')

        for partition in all_partitions:
            total_cost = 0
            partition_valid = True
            combo_details = []

            for start, end in partition:
                key = f"seg_{start}_{end}"

                if key not in self.subsegment_results:
                    partition_valid = False
                    break

                seg_info = self.subsegment_results[key]
                # Find cheapest numeric result for this segment range
                cheapest_for_range = None
                cheapest_miles_for_range = float('inf')

                for program_name, miles in seg_info["results"]:
                    if isinstance(miles, (int, float)) and miles < cheapest_miles_for_range:
                        cheapest_for_range = (program_name, miles)
                        cheapest_miles_for_range = miles

                if cheapest_for_range is None:
                    partition_valid = False
                    break

                program_name, miles = cheapest_for_range
                total_cost += miles
                combo_details.append({
                    "range": (start, end),
                    "program": program_name,
                    "miles": miles
                })

            if partition_valid and total_cost < cheapest_cost:
                cheapest_cost = total_cost
                cheapest_combo = combo_details

        if cheapest_combo is None:
            return None

        return {
            "combo": cheapest_combo,
            "total_miles": cheapest_cost
        }

    def _format_segment_range_display(self, start_idx, end_idx):
        """Format segment range (e.g., 'CHN-JPN')"""
        origin_str = self.segments[start_idx]["origin_var"].get().strip()
        dest_str = self.segments[end_idx]["dest_var"].get().strip()

        origin_code = origin_str.split(" - ")[0].strip()
        dest_code = dest_str.split(" - ")[0].strip()

        return f"{origin_code}-{dest_code}"

    def _get_segment_distance(self, start_idx, end_idx):
        """Get total distance for segment range"""
        total = 0
        for i in range(start_idx, end_idx + 1):
            distance_str = self.segments[i]["distance_var"].get().strip()
            total += math.ceil(float(distance_str))
        return total

    def _format_miles_display(self, miles):
        """Format numeric miles as XX.XXk"""
        if isinstance(miles, (int, float)):
            return f"{miles / 1000:.2f}k"
        else:
            return str(miles)

    def _sort_results(self, results):
        """Sort results: numeric ascending, then Dynamic, then errors (v4 FIX)"""
        def sort_key(item):
            # Item is either (program_name, miles) or (program_name, miles, ffp_code)
            miles = item[1]
            
            if isinstance(miles, (int, float)):
                return (0, miles)  # Numeric: sort first, by value ascending
            elif miles == "Dynamic":
                return (1, 0)  # Dynamic: sort second
            else:
                return (2, 0)  # Errors/text: sort last

        return sorted(results, key=sort_key)

    # ===== EXISTING SEARCH FUNCTIONS (UNCHANGED) =====

    def _extract_all_carriers(self):
        """Extract all unique carrier codes from all segments"""
        carriers = set()
        for segment in self.segments:
            carrier_str = segment["carrier_var"].get().strip()
            carrier_code = carrier_str.split(" - ")[0].strip()
            carriers.add(carrier_code)
        return list(carriers)

    def _find_ffps_for_all_carriers(self, carrier_list):
        """Find all FFPs that can redeem on ALL carriers in the list"""
        if not carrier_list:
            return []

        ffps = self.app.ffp.get("ffps", {})
        partners_data = self.app.partners.get("programs", [])
        alliances_data = self.app.alliance.get("alliances", [])

        ffps_per_carrier = {}

        for carrier_code in carrier_list:
            applicable = set()

            if carrier_code in ffps:
                applicable.add(carrier_code)

            for partner_entry in partners_data:
                if partner_entry.get("relationship") not in ["both", "redeem_only"]:
                    continue

                ffp_code = partner_entry.get("ffp")

                if ffp_code not in ffps:
                    continue

                can_redeem = False

                if partner_entry.get("type") == "alliance":
                    alliance_code = partner_entry.get("alliance")
                    for alliance in alliances_data:
                        if alliance.get("code") == alliance_code:
                            if carrier_code in alliance.get("members", []):
                                can_redeem = True
                            break

                elif partner_entry.get("type") == "individual":
                    if carrier_code in partner_entry.get("carriers", []):
                        can_redeem = True

                if can_redeem:
                    applicable.add(ffp_code)

            ffps_per_carrier[carrier_code] = applicable

        if not ffps_per_carrier:
            return []

        all_ffp_sets = list(ffps_per_carrier.values())
        common_ffps = all_ffp_sets[0]

        for carrier_ffps in all_ffp_sets[1:]:
            common_ffps = common_ffps.intersection(carrier_ffps)

        return sorted(list(common_ffps))

    def _calculate_separate_segment_pricing(self, ffp_code):
        """Calculate total miles for multi-segment with separate pricing"""
        segment_results = []

        for segment in self.segments:
            origin_str = segment["origin_var"].get().strip()
            dest_str = segment["dest_var"].get().strip()
            distance_str = segment["distance_var"].get().strip()
            cabin = segment["cabin_var"].get()
            carrier_str = segment["carrier_var"].get()

            origin = origin_str.split(" - ")[0].strip()
            dest = dest_str.split(" - ")[0].strip()
            carrier_code = carrier_str.split(" - ")[0].strip()
            distance = math.ceil(float(distance_str))

            award_chart = self._get_award_chart(ffp_code, carrier_code, origin, dest)

            if award_chart is None or cabin not in award_chart.get("cabins", {}):
                return "No applicable award chart"

            is_domestic = self._detect_domestic(origin, dest, award_chart)
            miles = self._calculate_award_miles(ffp_code, award_chart, origin, dest, distance, cabin, is_domestic)

            if miles == "Dynamic":
                return "Dynamic"

            if miles is None:
                return "No applicable award chart"

            segment_results.append(miles)

        total_miles = sum(segment_results)
        return total_miles

    def _calculate_multisegment_fixed_pricing(self, ffp_code, carrier_list):
        """Calculate total miles for multi-segment with fixed pricing"""
        try:
            if ffp_code == "AC":
                return self._calculate_ac_multisegment(carrier_list)

            origin_first = self.segments[0]["origin_var"].get().strip().split(" - ")[0].strip()
            dest_last = self.segments[-1]["dest_var"].get().strip().split(" - ")[0].strip()
            cabin = self.segments[0]["cabin_var"].get()

            chart = self._find_applies_to_multiple_chart(ffp_code, carrier_list, origin_first, dest_last)

            if chart is None:
                return "No applicable award chart"

            if cabin not in chart.get("cabins", {}):
                return "No applicable award chart"

            chart_type = chart.get("type")

            if chart_type == "distance_based":
                total_distance = 0
                for segment in self.segments:
                    distance_str = segment["distance_var"].get().strip()
                    total_distance += math.ceil(float(distance_str))

                brackets = chart.get("cabins", {}).get(cabin, [])
                for bracket in brackets:
                    min_miles = bracket.get("min_miles")
                    max_miles = bracket.get("max_miles")
                    award_miles = bracket.get("award_miles")

                    if min_miles <= total_distance <= max_miles:
                        return award_miles

                return "No applicable award chart"

            elif chart_type == "zone_based":
                origin_zone = self._get_zone_for_location(origin_first, chart.get("zone_system"))
                dest_zone = self._get_zone_for_location(dest_last, chart.get("zone_system"))

                if origin_zone is None or dest_zone is None:
                    return "No applicable award chart"

                zone_pairs = chart.get("cabins", {}).get(cabin, [])
                for pair in zone_pairs:
                    if (pair.get("from") == origin_zone and pair.get("to") == dest_zone) or \
                       (pair.get("from") == dest_zone and pair.get("to") == origin_zone):
                        return pair.get("miles")

                return "No applicable award chart"

            return "No applicable award chart"

        except Exception as e:
            return "Error calculating"

    def _calculate_ac_multisegment(self, carrier_list):
        """AC Aeroplan special case"""
        award_charts = self.app.award_charts.get("award_charts", {})
        ac_dynpart = award_charts.get("AC_DynPart")

        if ac_dynpart is None:
            return "Unable to find AC dynamic partner"

        dynamic_partners = set(ac_dynpart.get("specific_partners", []))
        dynamic_partners.add("AC")

        all_dynamic = all(c in dynamic_partners for c in carrier_list)

        if all_dynamic:
            return "Dynamic"

        origin_first = self.segments[0]["origin_var"].get().strip().split(" - ")[0].strip()
        dest_last = self.segments[-1]["dest_var"].get().strip().split(" - ")[0].strip()
        cabin = self.segments[0]["cabin_var"].get()

        chart = self._find_applies_to_multiple_chart("AC", carrier_list, origin_first, dest_last)

        if chart is None:
            return "No applicable award chart"

        if cabin not in chart.get("cabins", {}):
            return "No applicable award chart"

        total_distance = 0
        for segment in self.segments:
            distance_str = segment["distance_var"].get().strip()
            total_distance += math.ceil(float(distance_str))

        brackets = chart.get("cabins", {}).get(cabin, [])
        for bracket in brackets:
            min_miles = bracket.get("min_miles")
            max_miles = bracket.get("max_miles")
            award_miles = bracket.get("award_miles")

            if min_miles <= total_distance <= max_miles:
                return award_miles

        return "No applicable award chart"

    def _find_applies_to_multiple_chart(self, ffp_code, carrier_list, origin, dest):
        """Find the applies_to_multiple chart for the FFP"""
        award_charts = self.app.award_charts.get("award_charts", {})

        applicable_charts = [
            chart for chart in award_charts.values()
            if chart.get("ffp_code") == ffp_code and chart.get("applies_to_multiple") is True
        ]

        if not applicable_charts:
            return None

        if len(applicable_charts) == 1:
            chart = applicable_charts[0]

            if "route_specific" in chart:
                if self._validate_chart_for_route(chart, origin, dest):
                    return chart
                else:
                    return None
            return chart

        for chart in applicable_charts:
            if "route_specific" in chart:
                if self._validate_chart_for_route(chart, origin, dest):
                    return chart
            else:
                return chart

        return None

    def _search_single_segment(self, origin, dest, distance, cabin, carrier_code):
        """Main search logic for single segment"""
        results = []

        applicable_ffps = self._find_programs_for_carrier(carrier_code)

        if not applicable_ffps:
            messagebox.showinfo("No Options", f"No programs found to redeem {carrier_code}")
            return []

        for ffp_code in applicable_ffps:
            ffp_name = self.app.ffp.get("ffps", {}).get(ffp_code, {}).get("name", ffp_code)

            try:
                award_chart = self._get_award_chart(ffp_code, carrier_code, origin, dest)

                if award_chart is None:
                    results.append((ffp_name, "No applicable award chart", ffp_code))
                    continue

                if cabin not in award_chart.get("cabins", {}):
                    results.append((ffp_name, "No applicable award chart", ffp_code))
                    continue

                is_domestic = self._detect_domestic(origin, dest, award_chart)
                miles = self._calculate_award_miles(ffp_code, award_chart, origin, dest, distance, cabin, is_domestic)

                if miles is not None:
                    results.append((ffp_name, miles, ffp_code))
                else:
                    results.append((ffp_name, "No applicable award chart", ffp_code))

            except Exception as e:
                results.append((ffp_name, "Error calculating", ffp_code))

        return results

    def _find_programs_for_carrier(self, carrier_code):
        """Find all FFP programs that can redeem the specified carrier"""
        ffps = self.app.ffp.get("ffps", {})
        partners_data = self.app.partners.get("programs", [])
        alliances_data = self.app.alliance.get("alliances", [])

        results = []

        if carrier_code in ffps:
            results.append(carrier_code)

        for partner_entry in partners_data:
            if partner_entry.get("relationship") not in ["both", "redeem_only"]:
                continue

            ffp_code = partner_entry.get("ffp")

            if ffp_code not in ffps:
                continue

            can_redeem = False

            if partner_entry.get("type") == "alliance":
                alliance_code = partner_entry.get("alliance")
                for alliance in alliances_data:
                    if alliance.get("code") == alliance_code:
                        if carrier_code in alliance.get("members", []):
                            can_redeem = True
                        break

            elif partner_entry.get("type") == "individual":
                if carrier_code in partner_entry.get("carriers", []):
                    can_redeem = True

            if can_redeem and ffp_code not in results:
                results.append(ffp_code)

        return results

    def _get_award_chart(self, ffp_code, carrier_code, origin=None, dest=None):
        """Get the appropriate award chart for an FFP when redeeming on a carrier"""
        award_charts = self.app.award_charts.get("award_charts", {})

        ffp_charts = [
            (chart_id, chart_data)
            for chart_id, chart_data in award_charts.items()
            if chart_data.get("ffp_code") == ffp_code
        ]

        if not ffp_charts:
            return None

        if ffp_code == carrier_code:
            for chart_id, chart in ffp_charts:
                if chart.get("applies_to") == "self":
                    if origin and dest:
                        if self._validate_chart_for_route(chart, origin, dest):
                            return chart
                    else:
                        return chart

        for chart_id, chart in ffp_charts:
            if chart.get("applies_to") == "specific":
                if carrier_code in chart.get("specific_partners", []):
                    if origin and dest:
                        if self._validate_chart_for_route(chart, origin, dest):
                            return chart
                    else:
                        return chart

        for chart_id, chart in ffp_charts:
            if chart.get("applies_to") == "all_partners":
                if origin and dest:
                    if self._validate_chart_for_route(chart, origin, dest):
                        return chart
                else:
                    return chart

        return None

    def _validate_chart_for_route(self, award_chart, origin, dest):
        """Check if a chart's route_specific constraints match this origin-dest pair"""
        if "route_specific" not in award_chart:
            return True

        zone_system_name = award_chart.get("zone_system")

        if zone_system_name is None:
            return False

        origin_zone = self._get_zone_for_location(origin, zone_system_name)
        dest_zone = self._get_zone_for_location(dest, zone_system_name)

        if origin_zone is None or dest_zone is None:
            return False

        route_specific = award_chart.get("route_specific", [])

        for route_pair in route_specific:
            route_from = route_pair.get("from")
            route_to = route_pair.get("to")

            if (route_from == origin_zone and route_to == dest_zone) or \
               (route_from == dest_zone and route_to == origin_zone):
                return True

        return False

    def _detect_domestic(self, origin, dest, award_chart):
        """Detect if route is domestic"""
        destinations = self.app.zone_systems.get("destinations", {})
        origin_destination = None
        dest_destination = None

        for dest_name, dest_info in destinations.items():
            if origin in dest_info.get("locations", []):
                origin_destination = dest_name

            if dest in dest_info.get("locations", []):
                dest_destination = dest_name

        if not origin_destination or not dest_destination:
            return False

        if origin_destination != dest_destination:
            return False

        dest_info = destinations.get(origin_destination, {})
        dest_type = dest_info.get("type", "COUNTRY")

        if dest_type == "COUNTRY" or dest_type is None:
            return True

        elif dest_type == "MULTI_COUNTRY":
            return origin == dest

        return False

    def _calculate_award_miles(self, ffp_code, award_chart, origin, dest, distance, cabin, is_domestic):
        """Calculate award miles based on chart type"""
        if is_domestic:
            override_miles = self._apply_domestic_override(ffp_code, award_chart, origin, dest, cabin)

            if override_miles is not None:
                return override_miles

        chart_type = award_chart.get("type")

        if chart_type == "dynamic":
            return "Dynamic"

        elif chart_type == "zone_based":
            miles = self._lookup_zone_based(award_chart, origin, dest, cabin)
            return miles

        elif chart_type == "distance_based":
            miles = self._lookup_distance_based(award_chart, distance, cabin)
            return miles

        elif chart_type == "hybrid_distance_zone":
            priority = award_chart.get("priority", "distance_first")
            if priority == "distance_first":
                miles = self._hybrid_distance_first(award_chart, origin, dest, distance, cabin)
            else:
                miles = self._hybrid_zone_first(award_chart, origin, dest, distance, cabin)
            return miles

        return None

    def _apply_domestic_override(self, ffp_code, award_chart, origin, dest, cabin):
        """Apply domestic override rules"""
        zone_system_name = award_chart.get("zone_system")

        if zone_system_name is None:
            return None

        zone_definitions = self.app.zone_systems.get("zone_definitions", {})
        zone_system = zone_definitions.get(zone_system_name)

        if zone_system is None:
            return None

        domestic_override = zone_system.get("domestic_override")

        if domestic_override is None:
            return None

        if ffp_code == "TK" and (origin == "HI" or dest == "HI"):
            hawaii_rates = domestic_override.get("hawaii", {})
            if hawaii_rates and cabin in hawaii_rates:
                return hawaii_rates[cabin]

        if ffp_code == "AA":
            exceptions = domestic_override.get("exceptions", {})
            if origin == dest and origin in exceptions:
                rate = exceptions[origin].get(cabin)
                if rate is not None:
                    return rate

        if ffp_code == "TK":
            default_rates = domestic_override.get("default", {})
            if default_rates and cabin in default_rates:
                return default_rates[cabin]

        return None

    def _lookup_zone_based(self, award_chart, origin, dest, cabin):
        """Lookup miles for zone-based award chart"""
        zone_system_name = award_chart.get("zone_system")
        zone_pairs = award_chart.get("cabins", {}).get(cabin, [])

        if not zone_pairs:
            return None

        if zone_system_name is None:
            for pair in zone_pairs:
                pair_from = pair.get("from")
                pair_to = pair.get("to")
                miles = pair.get("miles")

                if (pair_from == origin and pair_to == dest) or \
                   (pair_from == dest and pair_to == origin):
                    return miles

            return None

        origin_zone = self._get_zone_for_location(origin, zone_system_name)
        dest_zone = self._get_zone_for_location(dest, zone_system_name)

        if origin_zone is None or dest_zone is None:
            return None

        for pair in zone_pairs:
            pair_from = pair.get("from")
            pair_to = pair.get("to")
            miles = pair.get("miles")

            if (pair_from == origin_zone and pair_to == dest_zone) or \
               (pair_from == dest_zone and pair_to == origin_zone):
                return miles

        return None

    def _lookup_distance_based(self, award_chart, distance, cabin):
        """Lookup miles for distance-based award chart"""
        brackets = award_chart.get("cabins", {}).get(cabin, [])

        if not brackets:
            return None

        for bracket in brackets:
            min_miles = bracket.get("min_miles")
            max_miles = bracket.get("max_miles")
            award_miles = bracket.get("award_miles")

            if min_miles <= distance <= max_miles:
                return award_miles

        return None

    def _hybrid_distance_first(self, award_chart, origin, dest, distance, cabin):
        """Hybrid: distance priority"""
        threshold = award_chart.get("distance_threshold", 999999)
        cabin_data = award_chart.get("cabins", {}).get(cabin, {})

        if distance <= threshold:
            distance_brackets = cabin_data.get("distance_based", [])
            for bracket in distance_brackets:
                if bracket["min_miles"] <= distance <= bracket["max_miles"]:
                    return bracket["award_miles"]

        zone_pairs = cabin_data.get("zone_based", [])
        if zone_pairs:
            result = self._lookup_zone_based_from_pairs(award_chart, origin, dest, zone_pairs)
            if result is not None:
                return result

        return None

    def _hybrid_zone_first(self, award_chart, origin, dest, distance, cabin):
        """Hybrid: zone priority"""
        cabin_data = award_chart.get("cabins", {}).get(cabin, {})

        zone_pairs = cabin_data.get("zone_based", [])
        if zone_pairs:
            result = self._lookup_zone_based_from_pairs(award_chart, origin, dest, zone_pairs)
            if result is not None:
                return result

        distance_brackets = cabin_data.get("distance_based", [])
        for bracket in distance_brackets:
            if bracket["min_miles"] <= distance <= bracket["max_miles"]:
                return bracket["award_miles"]

        return None

    def _lookup_zone_based_from_pairs(self, award_chart, origin, dest, zone_pairs):
        """Lookup miles from explicit zone pairs"""
        zone_system_name = award_chart.get("zone_system")

        if not zone_system_name:
            return None

        origin_zone = self._get_zone_for_location(origin, zone_system_name)
        dest_zone = self._get_zone_for_location(dest, zone_system_name)

        if origin_zone is None or dest_zone is None:
            return None

        for pair in zone_pairs:
            pair_from = pair.get("from")
            pair_to = pair.get("to")
            miles = pair.get("miles")

            if (pair_from == origin_zone and pair_to == dest_zone) or \
               (pair_from == dest_zone and pair_to == origin_zone):
                return miles

        return None

    def _get_zone_for_location(self, location_code, zone_system_name):
        """Find which zone a location belongs to"""
        zone_definitions = self.app.zone_systems.get("zone_definitions", {})
        zone_system = zone_definitions.get(zone_system_name)

        if zone_system is None:
            return None

        zones = zone_system.get("zones", {})

        for zone_name, zone_data in zones.items():
            locations = zone_data.get("locations", [])

            if location_code in locations:
                return zone_name

        return None

    # ===== DISPLAY FUNCTION (v4: FIXED SORTING) =====

    def _display_results(self, results, has_subsegments=False):
        """Display search results with subsegment breakdown section (v4: sorted)"""
        self.results_listbox.delete(0, tk.END)

        if not results:
            self.results_listbox.insert(tk.END, "No results found")
            return

        # Sort results: numeric ascending, then "Dynamic", then errors (v4 FIX)
        sorted_results = self._sort_results(results)

        # === SECTION 1: FULL SEGMENT RESULTS ===
        header = f"{'Program':<40} {'Miles':<25}"
        self.results_listbox.insert(tk.END, header)
        self.results_listbox.insert(tk.END, "=" * 65)

        for program_name, miles, ffp_code in sorted_results:
            if isinstance(miles, (int, float)):
                miles_str = f"{miles / 1000:.2f}k"
            else:
                miles_str = str(miles)

            display_text = f"{program_name:<40} {miles_str:<25}"
            self.results_listbox.insert(tk.END, display_text)

        # === SECTION 2: SUBSEGMENT RESULTS (v4: SORTED) ===
        if has_subsegments and self.subsegment_results:
            self.results_listbox.insert(tk.END, "")
            self.results_listbox.insert(tk.END, "-" * 65)
            self.results_listbox.insert(tk.END, "Subsegment Search Results:")
            self.results_listbox.insert(tk.END, "")

            # Sort subsegment keys by segment range
            sorted_keys = sorted(self.subsegment_results.keys(), 
                               key=lambda k: (int(k.split("_")[1]), int(k.split("_")[2])))

            for key in sorted_keys:
                seg_info = self.subsegment_results[key]
                start, end = seg_info["range"]
                segment_display = self._format_segment_range_display(start, end)
                distance = self._get_segment_distance(start, end)

                # Header for this segment
                self.results_listbox.insert(tk.END, f"Segment {segment_display} ({distance} miles):")
                
                # Sort subsegment results (v4 FIX)
                sub_header = f"  {'Program':<38} {'Miles':<25}"
                self.results_listbox.insert(tk.END, sub_header)
                self.results_listbox.insert(tk.END, f"  {'-' * 63}")

                results_for_segment = seg_info["results"]
                
                if results_for_segment:
                    # Sort: numeric ascending, Dynamic, errors
                    sorted_sub_results = sorted(results_for_segment, key=lambda x: (
                        (0, x[1]) if isinstance(x[1], (int, float)) else
                        (1, 0) if x[1] == "Dynamic" else
                        (2, 0)
                    ))
                    
                    for program_name, miles in sorted_sub_results:
                        if isinstance(miles, (int, float)):
                            miles_str = f"{miles / 1000:.2f}k"
                        else:
                            miles_str = str(miles)

                        display_text = f"  {program_name:<38} {miles_str:<25}"
                        self.results_listbox.insert(tk.END, display_text)
                else:
                    self.results_listbox.insert(tk.END, f"  (No results)")

                self.results_listbox.insert(tk.END, "")

        # === SECTION 3: CHEAPEST BREAKDOWN COMBO ===
        if has_subsegments:
            cheapest_combo_info = self._find_cheapest_partition_combo()

            if cheapest_combo_info is not None:
                self.results_listbox.insert(tk.END, "-" * 65)
                self.results_listbox.insert(tk.END, "The possible cheapest option (in miles) if you are willing to")
                self.results_listbox.insert(tk.END, "break down the segments:")
                self.results_listbox.insert(tk.END, "")

                combo_details = cheapest_combo_info["combo"]
                total_miles = cheapest_combo_info["total_miles"]

                combo_text_parts = []
                for detail in combo_details:
                    start, end = detail["range"]
                    program = detail["program"]
                    miles = detail["miles"]

                    segment_display = self._format_segment_range_display(start, end)
                    miles_display = self._format_miles_display(miles)

                    combo_text_parts.append(f"Segment {segment_display} from {program} with {miles_display} miles")

                combo_display = ", ".join(combo_text_parts)
                total_display = self._format_miles_display(total_miles)

                self.results_listbox.insert(tk.END, combo_display + ",")
                self.results_listbox.insert(tk.END, f"with a total of {total_display} miles")
                self.results_listbox.insert(tk.END, "-" * 65)
        # === SECTION 4: POPULATE SEARCH_CONTEXT FOR TAB3 ===
        # Extract metadata based on search type
        # This ensures Tab3 receives the correct main results

        segment_count = len(self.segments)

        if segment_count == 1:
            # Single segment search
            segment = self.segments[0]
            origin_str = segment["origin_var"].get().strip()
            dest_str = segment["dest_var"].get().strip()
            distance_str = segment["distance_var"].get().strip()
            cabin = segment["cabin_var"].get()
            carrier_str = segment["carrier_var"].get()

            origin = origin_str.split(" - ")[0].strip()
            dest = dest_str.split(" - ")[0].strip()
            carrier_code = carrier_str.split(" - ")[0].strip()
            distance = math.ceil(float(distance_str))
            route_type = "Single Segment"

        else:
            # Multi-segment search
            first_segment = self.segments[0]
            last_segment = self.segments[-1]

            origin_str = first_segment["origin_var"].get().strip()
            dest_str = last_segment["dest_var"].get().strip()
            cabin = first_segment["cabin_var"].get()
            carrier_str = first_segment["carrier_var"].get()

            origin = origin_str.split(" - ")[0].strip()
            dest = dest_str.split(" - ")[0].strip()
            carrier_code = carrier_str.split(" - ")[0].strip()

            # Calculate total distance
            distance = 0
            for seg in self.segments:
                distance_str = seg["distance_var"].get().strip()
                distance += math.ceil(float(distance_str))

            route_type = "Multi-Segment"

        # CRITICAL: Pass ONLY main results (not subsegments)
        # Results are tuples: (program_name, miles_value, ffp_code)
        # Convert miles to k-miles for Tab3 (divide by 1000)
        # This way Tab3 uses k-miles directly in calculations
        converted_results = []
        for program_name, miles, ffp_code in results:
            if isinstance(miles, (int, float)):
                # Convert to k-miles
                k_miles = miles / 1000
            else:
                # Keep text values like "Dynamic" or "No applicable award chart"
                k_miles = miles
            converted_results.append((program_name, k_miles, ffp_code))

        self.app.search_context = {
            'route_type': route_type,
            'carrier_code': carrier_code,
            'origin': origin,
            'destination': dest,
            'distance': distance,
            'cabin': cabin,
            'results': converted_results  # k-miles format for Tab3
        }

