"""
tab2_v2.py: Award Chart Lookup - Simplified with Pre-processed Data

Core logic moved to gui.py startup.
Tab receives pre-processed data structures and handles UI + search logic.
Updated to support multi-segment search functionality.

LOGIC STRICTLY FOLLOWS tab2_example.py structure.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import math


class Tab2Frame(ttk.Frame):
    """Tab 2: Award Chart Lookup"""

    def __init__(self, parent, app, airports_disp, airports_list, carriers_disp,
                 ffp_dict_redeem, award_chart_dict, legal_zone_type, zone_system_dict,
                 alliance_members=None):
        super().__init__(parent)
        self.app = app

        # Store pre-processed data
        self.airports_disp = airports_disp
        self.airports_list = airports_list
        self.carriers_disp = carriers_disp
        self.ffp_dict_redeem = ffp_dict_redeem
        self.award_chart_dict = award_chart_dict
        self.legal_zone_type = legal_zone_type
        self.zone_system_dict = zone_system_dict

        # Alliance members (for multi-segment)
        self.OW_member = alliance_members[0].get('members')
        self.SA_member = alliance_members[1].get('members')
        self.ST_member = alliance_members[2].get('members')

        # Cabin options (hard-coded)
        self.possible_cabins = ['economy', 'premium_economy', 'business', 'first']

        # Segment storage
        self.segments = []

        # Setup UI
        self._setup_ui()

        # Add initial segment
        self._add_segment_panel()

    def _setup_ui(self):
        """Build the user interface"""
        # Configure grid
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=0, minsize=450)
        self.grid_columnconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(self, text="Award Chart Lookup", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, sticky='w', padx=10, pady=10)

        # ==================== LEFT FRAME: Segment Parameters ====================

        left_frame = ttk.LabelFrame(self, text="Flight Segments", padding=10)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        # Segments canvas + scrollbar
        self.segments_canvas = tk.Canvas(left_frame, bg="white", highlightthickness=0)
        segments_scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.segments_canvas.yview)
        self.segments_scrollable_frame = ttk.Frame(self.segments_canvas)

        self.segments_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.segments_canvas.configure(scrollregion=self.segments_canvas.bbox("all"))
        )

        self.segments_canvas.create_window((0, 0), window=self.segments_scrollable_frame, anchor="nw")
        self.segments_canvas.configure(yscrollcommand=segments_scrollbar.set)

        # Mouse wheel scrolling
        self.segments_canvas.bind("<MouseWheel>", lambda e: self.segments_canvas.yview_scroll(int(-1 * e.delta / 120), "units"))
        self.segments_canvas.bind("<Button-4>", lambda e: self.segments_canvas.yview_scroll(-1, "units"))
        self.segments_canvas.bind("<Button-5>", lambda e: self.segments_canvas.yview_scroll(1, "units"))

        self.segments_canvas.grid(row=0, column=0, sticky="nsew")
        segments_scrollbar.grid(row=0, column=1, sticky="ns")

        # Buttons frame
        buttons_frame = ttk.Frame(left_frame)
        buttons_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        buttons_frame.grid_columnconfigure(2, weight=1)

        search_button = ttk.Button(buttons_frame, text="Search Awards", command=self._on_search_awards)
        search_button.grid(row=0, column=0, sticky="ew", padx=2)

        add_segment_button = ttk.Button(buttons_frame, text="+ Add Segment", command=self._add_segment_click)
        add_segment_button.grid(row=0, column=1, sticky="ew", padx=2)

        delete_segment_button = ttk.Button(buttons_frame, text="- Delete Last", command=self._delete_segment_click)
        delete_segment_button.grid(row=0, column=2, sticky="ew", padx=2)

        # ==================== RIGHT FRAME: Results ====================

        results_frame = ttk.LabelFrame(self, text="Award Results", padding=10)
        results_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        # Results display
        results_scrollbar = ttk.Scrollbar(results_frame, orient="vertical")
        results_scrollbar.grid(row=0, column=1, sticky="ns")

        self.results_listbox = tk.Listbox(
            results_frame,
            yscrollcommand=results_scrollbar.set,
            height=25,
            font=("Courier", 10),
            bg="#f5f5f5"
        )

        self.results_listbox.grid(row=0, column=0, sticky="nsew")
        results_scrollbar.config(command=self.results_listbox.yview)

        # Mouse wheel scrolling for results
        self.results_listbox.bind("<MouseWheel>", lambda e: self.results_listbox.yview_scroll(int(-1 * e.delta / 120), "units"))
        self.results_listbox.bind("<Button-4>", lambda e: self.results_listbox.yview_scroll(-1, "units"))
        self.results_listbox.bind("<Button-5>", lambda e: self.results_listbox.yview_scroll(1, "units"))

        # Initial message
        self.results_listbox.insert(tk.END, "Configure segments and click 'Search Awards'")
        self.results_listbox.insert(tk.END, "to see available award options.")

    # ==================== SEGMENT MANAGEMENT ====================

    def _add_segment_panel(self):
        """Add a new segment input panel"""
        if len(self.segments) >= 8:
            messagebox.showwarning("Segment Limit", "Maximum 8 segments allowed.")
            return

        segment_index = len(self.segments)

        # Create segment frame
        segment_frame = ttk.LabelFrame(
            self.segments_scrollable_frame,
            text=f"Segment {segment_index + 1}",
            padding=10
        )

        segment_frame.pack(fill="x", padx=5, pady=5)
        segment_frame.grid_columnconfigure(1, weight=1)

        # Variables
        origin_var = tk.StringVar()
        dest_var = tk.StringVar()
        carrier_var = tk.StringVar()
        cabin_var = tk.StringVar(value=self.possible_cabins[0])
        distance_var = tk.StringVar()

        # Origin
        ttk.Label(segment_frame, text="Origin:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        origin_combo = ttk.Combobox(segment_frame, textvariable=origin_var, state='normal', width=40)
        origin_combo['values'] = self.airports_disp
        origin_combo.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        origin_combo.bind('<<ComboboxSelected>>', lambda e, idx=segment_index: self._on_airport_changed(idx))
        origin_combo.bind('<KeyRelease>', lambda e, idx=segment_index: self._filter_airports(idx, 'origin'))

        # Destination
        ttk.Label(segment_frame, text="Destination:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        dest_combo = ttk.Combobox(segment_frame, textvariable=dest_var, state='normal', width=40)
        dest_combo['values'] = self.airports_disp
        dest_combo.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        dest_combo.bind('<<ComboboxSelected>>', lambda e, idx=segment_index: self._on_airport_changed(idx))
        dest_combo.bind('<KeyRelease>', lambda e, idx=segment_index: self._filter_airports(idx, 'dest'))

        # Carrier
        ttk.Label(segment_frame, text="Carrier:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        carrier_combo = ttk.Combobox(segment_frame, textvariable=carrier_var, state='normal', width=40)
        carrier_combo['values'] = self.carriers_disp
        carrier_combo.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
        carrier_combo.bind('<KeyRelease>', lambda e, idx=segment_index: self._filter_carriers(idx))

        # Cabin
        ttk.Label(segment_frame, text="Cabin:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        cabin_combo = ttk.Combobox(segment_frame, textvariable=cabin_var, state='readonly', width=40)
        cabin_combo['values'] = self.possible_cabins
        cabin_combo.grid(row=3, column=1, sticky='ew', padx=5, pady=5)

        # Distance
        ttk.Label(segment_frame, text="Distance (miles):").grid(row=4, column=0, sticky='w', padx=5, pady=5)
        distance_entry = ttk.Entry(segment_frame, textvariable=distance_var, width=40)
        distance_entry.grid(row=4, column=1, sticky='ew', padx=5, pady=5)

        # Store segment data
        segment_data = {
            'frame': segment_frame,
            'origin_var': origin_var,
            'dest_var': dest_var,
            'carrier_var': carrier_var,
            'cabin_var': cabin_var,
            'distance_var': distance_var,
            'origin_combo': origin_combo,
            'dest_combo': dest_combo,
            'carrier_combo': carrier_combo,
            'cabin_combo': cabin_combo
        }

        self.segments.append(segment_data)

        # Auto-fill origin from previous segment's destination
        if segment_index > 0:
            prev_dest = self.segments[segment_index - 1]['dest_var'].get()
            if prev_dest:
                origin_var.set(prev_dest)

    def _add_segment_click(self):
        """Handle Add Segment button click"""
        self._add_segment_panel()
        self.segments_canvas.yview_moveto(1.0)

    def _delete_segment_click(self):
        """Handle Delete Last Segment button click"""
        if len(self.segments) <= 1:
            messagebox.showwarning("Cannot Delete", "Cannot delete the first segment.")
            return

        last_segment = self.segments.pop()
        last_segment['frame'].destroy()

    # ==================== EVENT HANDLERS ====================

    def _on_airport_changed(self, segment_index):
        """Called when user changes origin or destination"""
        if segment_index >= len(self.segments):
            return

        segment = self.segments[segment_index]
        origin_str = segment['origin_var'].get()
        dest_str = segment['dest_var'].get()

        if origin_str and dest_str:
            # Extract IATA codes
            origin_code = origin_str.split('-')[0].strip()
            dest_code = dest_str.split('-')[0].strip()

            # Calculate and set GC distance
            try:
                distance = self._calculateGcdistance(origin_code, dest_code)
                segment['distance_var'].set(str(distance))
            except Exception as e:
                messagebox.showerror("Distance Calculation Error", str(e))

    def _filter_airports(self, segment_index, location_type):
        """Filter airports based on user input - match IATA code"""
        if segment_index >= len(self.segments):
            return

        segment = self.segments[segment_index]

        if location_type == 'origin':
            var = segment['origin_var']
            combo = segment['origin_combo']
        else:
            var = segment['dest_var']
            combo = segment['dest_combo']

        user_input = var.get().strip().upper()

        if not user_input:
            combo['values'] = self.airports_disp
            return

        # Filter by IATA code (first part before ' - ')
        filtered = [
            airport for airport in self.airports_disp
            if airport.split(' - ')[0].strip().upper().startswith(user_input)
        ]

        combo['values'] = filtered

    def _filter_carriers(self, segment_index):
        """Filter carriers based on user input - match code or name"""
        if segment_index >= len(self.segments):
            return

        segment = self.segments[segment_index]
        user_input = segment['carrier_var'].get().strip().upper()

        if not user_input:
            segment['carrier_combo']['values'] = self.carriers_disp
            return

        # Filter by code or name
        filtered = [
            carrier for carrier in self.carriers_disp
            if user_input in carrier.upper()
        ]

        segment['carrier_combo']['values'] = filtered

    # ==================== HELPER FUNCTIONS ====================

    def _getAirportDetail(self, airport_iata):
        """Get airport details by IATA code"""
        for airport in self.airports_list:
            code = airport.get('iata_code')
            if code == airport_iata:
                continent = airport.get('continent')
                country = airport.get('iso_country')
                region = airport.get('iso_region')
                lat = airport.get('latitude_deg')
                lon = airport.get('longitude_deg')
                full_name = airport.get('name')
                return continent, country, region, lat, lon, full_name

        raise ValueError(f'Airport mismatch: {airport_iata} not found')

    def _calculateGcdistance(self, orig, dest):
        """Calculate great-circle distance between two airports"""
        _, _, _, lat1, lon1, _ = self._getAirportDetail(orig)
        _, _, _, lat2, lon2, _ = self._getAirportDetail(dest)

        lat1 = math.radians(lat1)
        lat2 = math.radians(lat2)
        lon1 = math.radians(lon1)
        lon2 = math.radians(lon2)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        earth_radius_miles = 3959
        distance = round(earth_radius_miles * c)

        return distance

    def _stripZones(self, chartValue, wrappername):
        """Extract zones and from-to pairs in zone-based systems"""
        chartValue = chartValue.get(wrappername)
        origdestpair = []

        for _, value in chartValue.items():
            for iv in range(len(value)):
                datadict = value[iv]
                pair = [datadict.get('from'), datadict.get('to')]
                if pair not in origdestpair:
                    origdestpair.append(pair)

        return origdestpair

    def _stripZones2(self, chartValue, wrappername):
        """Extract zones from route_specific restrictions"""
        chartValue = chartValue.get(wrappername)
        origdestpair = []

        for i in range(len(chartValue)):
            datadict = chartValue[i]
            pair = [datadict.get('from'), datadict.get('to')]
            if pair not in origdestpair:
                origdestpair.append(pair)

        return origdestpair

    def _fitAirportWithZone(self, airport_iata, zonedict):
        """Match airport to zone based on continent/country/region/airport"""
        continent, country, region, _, _, _ = self._getAirportDetail(airport_iata)

        for name, value in zonedict.items():
            isInInclude = False
            isInExclude = False

            I0 = value.get(self.legal_zone_type[0])  # continents
            I1 = value.get(self.legal_zone_type[1])  # countries
            I2 = value.get(self.legal_zone_type[2])  # regions
            I3 = value.get(self.legal_zone_type[3])  # airports
            E0 = value.get(self.legal_zone_type[4])  # countries_exclude
            E1 = value.get(self.legal_zone_type[5])  # regions_exclude
            E2 = value.get(self.legal_zone_type[6])  # airports_exclude

            if I0 and continent in I0:
                isInInclude = True
            if I1 and country in I1:
                isInInclude = True
            if I2 and region in I2:
                isInInclude = True
            if I3 and airport_iata in I3:
                isInInclude = True

            if E0 and country in E0:
                isInExclude = True
            if E1 and region in E1:
                isInExclude = True
            if E2 and airport_iata in E2:
                isInExclude = True

            if isInInclude and not isInExclude:
                return name

        return None

    def _matchItineraryWithZonePairs(self, pairs, awardchartdict, orig_iata, dest_iata):
        """Check if itinerary matches zone-based pairs"""
        zonename = awardchartdict.get('zone_system')
        zone_system = self.zone_system_dict[zonename]['zones']

        orig_zone = self._fitAirportWithZone(orig_iata, zone_system)
        dest_zone = self._fitAirportWithZone(dest_iata, zone_system)

        if orig_zone and dest_zone:
            for pair in pairs:
                pair_to = pair[0]
                pair_from = pair[1]
            
                pair_to = pair_to if isinstance(pair_to, list) else [pair_to]
                pair_from = pair_from if isinstance(pair_from, list) else [pair_from]

                if (orig_zone in pair_to and dest_zone in pair_from) or (orig_zone in pair_from and dest_zone in pair_to):
                    return True

        return False

    # ==================== FIND CHART LOGIC ====================

    def _findChart_attachChart(self, ffpcode, ffpname, chartname, allchartlist):
        """Attach chart to results list"""
        chart = dict(ffp_disp_name=ffpname, ffp=ffpcode, chart_name=chartname)
        allchartlist.append(chart)
        return allchartlist, True

    def _findChart_SingleSeg(self, orig, dest, distance, carrier, ffp_dict=None):
        """Find which award chart each FFP should use for this segment"""
        chart_allffp = []

        # Use provided scope or default to full list
        search_scope = ffp_dict if ffp_dict else self.ffp_dict_redeem

        for ffp_code, value in search_scope.items():
            ffp_name = value.get('name')
            ffp_self_carriers = value.get('carriers')
            ffp_redeem_partner = value.get('redeem_partner')

            award_chart_ffpspecific = {
                name2: value2
                for name2, value2 in self.award_chart_dict.items()
                if value2.get('ffp_code') == ffp_code and not value2.get('applies_to_multiple')
            }

            chart_candidates = {}
            flg = 0

            # Determine if self-redeem or partner-redeem
            if carrier in ffp_self_carriers:
                # Self redeem case
                for chart_name, chart_content in award_chart_ffpspecific.items():
                    if chart_content['ffp_code'] == ffp_code and chart_content['applies_to'] == 'self':
                        chart_candidates[chart_name] = chart_content

            elif ffp_redeem_partner and carrier in ffp_redeem_partner:
                # Partner redeem case
                award_chart_ffpspecific_specpart = {
                    name3: value3
                    for name3, value3 in award_chart_ffpspecific.items()
                    if value3.get('applies_to') == "specific"
                }

                award_chart_ffpspecific_genpart = {
                    name4: value4
                    for name4, value4 in award_chart_ffpspecific.items()
                    if value4.get('applies_to') == "all_partners"
                }

                if award_chart_ffpspecific_specpart:
                    # Program has partner-specific chart
                    for name5, value5 in award_chart_ffpspecific_specpart.items():
                        if carrier in value5.get('specific_partners'):
                            chart_candidates[name5] = value5

                    if not chart_candidates:
                        # Program has special charts, but not for this specific carrier
                        if award_chart_ffpspecific_genpart:
                            for name6, value6 in award_chart_ffpspecific_genpart.items():
                                chart_candidates[name6] = value6

                elif award_chart_ffpspecific_genpart:
                    # Program only has general partner chart
                    for name7, value7 in award_chart_ffpspecific_genpart.items():
                        chart_candidates[name7] = value7

                else:
                    # Program has no defined partner chart despite having partners
                    flg = 1
                    print(f'Program {ffp_name} has no defined partner chart despite having partners.')

            else:
                # Carrier is not a partner with this FFP (normal case)
                flg = 2

            # Process chart candidates if applicable
            if flg == 0:
                if len(chart_candidates) == 0:
                    print(f'No chart found for carrier {carrier} in program {ffp_name}')

                elif len(chart_candidates) == 1:
                    # Only one applicable chart
                    (name, value), = chart_candidates.items()
                    chart = dict(ffp_disp_name=ffp_name, ffp=ffp_code, chart_name=name)
                    chart_allffp.append(chart)

                else:
                    # Multiple charts - need to determine priority
                    num_specialoverwrite = 0
                    num_domoverwrite = 0
                    num_normchart = 0

                    for name, value in chart_candidates.items():
                        if value.get('is_special_overwrite'):
                            num_specialoverwrite += 1
                        elif value.get('is_domestic_overwrite'):
                            num_domoverwrite += 1
                        else:
                            num_normchart += 1

                    if num_specialoverwrite > 1 or num_domoverwrite > 1 or num_normchart < 1:
                        raise ValueError('More than 1 special chart. Unexpected')

                    isFoundChart = False

                    # Priority 1: Special overwrite chart
                    for name, value in chart_candidates.items():
                        if value.get('is_special_overwrite'):
                            if value.get('type') == "zone_based":
                                pairs = self._stripZones(value, 'cabins')
                                isRestrictMatch = self._matchItineraryWithZonePairs(pairs, value, orig, dest)

                                if isRestrictMatch:
                                    chart_allffp, isFoundChart = self._findChart_attachChart(
                                        ffp_code, ffp_name, name, chart_allffp)
                                    break

                            elif value.get('type') == "distance_based":
                                if value.get('route_specific'):
                                    pairs = self._stripZones2(value, 'route_specific')
                                    isRestrictMatch = self._matchItineraryWithZonePairs(pairs, value, orig, dest)

                                    if isRestrictMatch:
                                        chart_allffp, isFoundChart = self._findChart_attachChart(
                                            ffp_code, ffp_name, name, chart_allffp)
                                        break

                    # Priority 2: Domestic overwrite chart
                    if not isFoundChart:
                        for name, value in chart_candidates.items():
                            if value.get('is_domestic_overwrite'):
                                _, orig_country, _, _, _, _ = self._getAirportDetail(orig)
                                _, dest_country, _, _, _, _ = self._getAirportDetail(dest)

                                if orig_country == dest_country:
                                    if value.get('default'):
                                        # Default domestic chart
                                        chart_allffp, isFoundChart = self._findChart_attachChart(
                                            ffp_code, ffp_name, name, chart_allffp)
                                        break

                                    elif value.get('exceptions'):
                                        # Exception-based domestic chart
                                        if orig_country in value.get('exceptions'):
                                            chart_allffp, isFoundChart = self._findChart_attachChart(
                                                ffp_code, ffp_name, name, chart_allffp)
                                            break

                    # Priority 3: Regular charts
                    if not isFoundChart:
                        if num_normchart == 1:
                            for name, value in chart_candidates.items():
                                if not value.get('is_domestic_overwrite') and not value.get('is_special_overwrite'):
                                    chart_allffp, isFoundChart = self._findChart_attachChart(
                                        ffp_code, ffp_name, name, chart_allffp)
                                    break

                        else:
                            # Multiple normal charts with limits
                            for name, value in chart_candidates.items():
                                if value.get('type') == 'distance_based' and value.get('route_specific'):
                                    pairs = self._stripZones2(value, 'route_specific')
                                    isRestrictMatch = self._matchItineraryWithZonePairs(pairs, value, orig, dest)

                                    if isRestrictMatch:
                                        chart_allffp, isFoundChart = self._findChart_attachChart(
                                            ffp_code, ffp_name, name, chart_allffp)
                                        break

                                elif value.get('type') == 'zone_based':
                                    pairs = self._stripZones(value, 'cabins')
                                    isRestrictMatch = self._matchItineraryWithZonePairs(pairs, value, orig, dest)

                                    if isRestrictMatch:
                                        chart_allffp, isFoundChart = self._findChart_attachChart(
                                            ffp_code, ffp_name, name, chart_allffp)
                                        break

                        if not isFoundChart:
                            raise ValueError('Somehow this FFP still has multiple charts for this search')

        return chart_allffp

    # ==================== FIND PRICE LOGIC ====================

    def _findPrice_SingleSeg(self, datadict, orig_iata, dest_iata, cabin, distance):
        """Calculate award miles for a single segment"""
        chartname = datadict['chart_name']
        chart = self.award_chart_dict[chartname]

        def theDistMethod(valuelist, distance):
            """Find price using distance-based method"""
            flg = False
            mile = 0
            for value_entry in valuelist:
                start_milage = value_entry['min_miles']
                end_milage = value_entry['max_miles']
                if start_milage <= distance <= end_milage:
                    flg = True
                    mile = value_entry['miles']
                    break
            return flg, mile

        def theZoneMethod(valuelist, orig_zone, dest_zone):
            """Find price using zone-based method"""
            flg = False
            mile = 0
            for value_entry in valuelist:
                start_zone = value_entry['from']
                end_zone = value_entry['to']

                start_zone = start_zone if isinstance(start_zone,list) else [start_zone]
                end_zone = end_zone if isinstance(end_zone,list) else [end_zone]
                if orig_zone and dest_zone:
                    if (orig_zone in start_zone and dest_zone in end_zone) or (orig_zone in end_zone and dest_zone in start_zone):
                        flg = True
                        mile = value_entry['miles']
                        break
            return flg, mile

        # Process different chart types
        if chart.get('type') == 'distance_based':
            value_wrap = chart['cabins']
            if value_wrap.get(cabin):
                value_cabin = value_wrap.get(cabin)
                isfind, awardMiles = theDistMethod(value_cabin, distance)

                if not isfind:
                    datadict['award_miles'] = 'Distance exceeds award chart maximum.'
                else:
                    datadict['award_miles'] = awardMiles
            else:
                datadict['award_miles'] = 'This cabin is not available on this FFP.'

        elif chart.get('type') == 'dynamic':
            datadict['award_miles'] = 'Dynamic'

        elif chart.get('type') == 'zone_based':
            zonename = chart['zone_system']
            zone_system = self.zone_system_dict[zonename]['zones']

            orig_zone = self._fitAirportWithZone(orig_iata, zone_system)
            dest_zone = self._fitAirportWithZone(dest_iata, zone_system)

            if orig_zone and dest_zone:
                value_wrap = chart['cabins']
                if value_wrap.get(cabin):
                    value_cabin = value_wrap.get(cabin)
                    isfind, awardMiles = theZoneMethod(value_cabin, orig_zone, dest_zone)

                    if not isfind:
                        datadict['award_miles'] = 'Price of such route is not defined'
                    else:
                        datadict['award_miles'] = awardMiles
                else:
                    datadict['award_miles'] = 'This cabin is not available on this FFP.'
            else:
                datadict['award_miles'] = 'Origin or destination not included in the zone-based chart'

        elif chart.get('type') == 'hybrid_distance_zone':
            hybrid_priority = chart['priority']
            zonename = chart['zone_system']
            zone_system = self.zone_system_dict[zonename]['zones']

            orig_zone = self._fitAirportWithZone(orig_iata, zone_system)
            dest_zone = self._fitAirportWithZone(dest_iata, zone_system)

            value_wrap = chart['cabins']
            if value_wrap.get(cabin):
                value_cabin = value_wrap.get(cabin)

                if hybrid_priority == "zone_first":
                    highPriorityList = value_cabin.get('zone_based')
                    lowPriorityList = value_cabin.get('distance_based')

                    if highPriorityList:
                        isfind, awardMiles = theZoneMethod(highPriorityList, orig_zone, dest_zone)

                        if isfind:
                            datadict['award_miles'] = awardMiles
                        elif lowPriorityList:
                            isfind, awardMiles = theDistMethod(lowPriorityList, distance)

                            if isfind:
                                datadict['award_miles'] = awardMiles
                            else:
                                datadict['award_miles'] = 'Hybrid Zone unable to find such route.'
                        else:
                            datadict['award_miles'] = 'Hybrid Zone unable to find such route.'

                    elif lowPriorityList:
                        isfind, awardMiles = theDistMethod(lowPriorityList, distance)

                        if isfind:
                            datadict['award_miles'] = awardMiles
                        else:
                            datadict['award_miles'] = 'Hybrid Zone unable to find such route.'
                    else:
                        datadict['award_miles'] = 'Hybrid Zone unable to find such route.'

                elif hybrid_priority == "distance_first":
                    dist_thresh = chart['distance_threshold']
                    highPriorityList = value_cabin.get('distance_based')
                    lowPriorityList = value_cabin.get('zone_based')

                    if distance <= dist_thresh and highPriorityList:
                        isfind, awardMiles = theDistMethod(highPriorityList, distance)

                        if isfind:
                            datadict['award_miles'] = awardMiles
                        else:
                            datadict['award_miles'] = 'Hybrid Zone unable to find such route.'

                    elif lowPriorityList:
                        isfind, awardMiles = theZoneMethod(lowPriorityList, orig_zone, dest_zone)

                        if isfind:
                            datadict['award_miles'] = awardMiles
                        else:
                            datadict['award_miles'] = 'Hybrid Zone unable to find such route.'
                    else:
                        datadict['award_miles'] = 'Hybrid Zone unable to find such route.'
                else:
                    datadict['award_miles'] = 'Hybrid Zone unable to find such route.'

            else:
                datadict['award_miles'] = 'This cabin is not available on this FFP.'

        elif chart.get("is_domestic_overwrite"):
            _, orig_country, _, _, _, _ = self._getAirportDetail(orig_iata)
            _, dest_country, _, _, _, _ = self._getAirportDetail(dest_iata)

            if orig_country != dest_country:
                datadict['award_miles'] = 'Wrong chart: Domestic chart picked despite not being domestic'
            else:
                value_wrap = chart['cabins']

                if chart.get('default'):
                    if value_wrap.get(cabin):
                        value_cabin = value_wrap.get(cabin)
                        datadict['award_miles'] = value_cabin[0]
                    else:
                        datadict['award_miles'] = 'This cabin is not available on this FFP.'

                elif chart.get('exceptions'):
                    if orig_country not in chart.get('exceptions'):
                        datadict['award_miles'] = 'Wrong chart: Domestic chart picked despite not being special domestic case.'
                    elif value_wrap.get(cabin):
                        value_cabin = value_wrap.get(cabin)
                        datadict['award_miles'] = next(
                            (item[orig_country] for item in value_cabin if orig_country in item), None)
                    else:
                        datadict['award_miles'] = 'This cabin is not available on this FFP.'
                else:
                    datadict['award_miles'] = 'Unknown type of domestic chart.'
        else:
            datadict['award_miles'] = 'Unknown type of chart.'

    # ==================== MULTI-SEGMENT HELPER FUNCTIONS ====================

    def _getMultiPartChart(self, ffpname):
        """Get multi-part chart for FFP"""
        for name, value in self.award_chart_dict.items():
            if value.get('ffp_code') == ffpname and value.get('applies_to_multiple'):
                return name
        return None

    def _cumulativePricing(self, ffpname, origins, destinations, distances, carrier_eff, cabin, subchart):
        """Calculate cumulative pricing for all segments"""
        orig_eff = origins[0]
        dest_eff = destinations[-1]
        distance_eff = sum(distances)

        # Create subchart dict for this FFP
        ffp_subchart = {ffpname: subchart[ffpname]} if ffpname in subchart else {ffpname: self.ffp_dict_redeem.get(ffpname, {})}

        charts = self._findChart_SingleSeg(orig_eff, dest_eff, distance_eff, carrier_eff, ffp_dict=ffp_subchart)

        if charts:
            chart = charts[0]  # since only 1 ffp is involved
            self._findPrice_SingleSeg(chart, orig_eff, dest_eff, cabin, distance_eff)
        else:
            chart = dict(ffp=ffpname,
                        ffp_disp_name=subchart.get(ffpname, {}).get('name', ffpname),
                        chart_name='N/A',
                        award_miles='No chart found.')

        return chart

    def _cumulativePricing_multipartchart(self, ffpname, origins, destinations, distances, cabin, subchart):
        """Calculate cumulative pricing using multi-part chart"""
        multipartchart = self._getMultiPartChart(ffpname)

        chart = dict(ffp=ffpname,
                    ffp_disp_name=subchart.get(ffpname, {}).get('name', ffpname),
                    chart_name=multipartchart)

        orig_eff = origins[0]
        dest_eff = destinations[-1]
        distance_eff = sum(distances)

        self._findPrice_SingleSeg(chart, orig_eff, dest_eff, cabin, distance_eff)

        return chart

    def _persegPricing(self, origins, destinations, distances, carriers, cabin, ffpname, subchart):
        """Calculate per-segment pricing"""
        num_seg = len(origins)
        awardmile_tot = []

        for iseg in range(num_seg):
            orig_eff = origins[iseg]
            dest_eff = destinations[iseg]
            carrier_eff = carriers[iseg]
            distance_eff = distances[iseg]

            ffp_subchart = {ffpname: subchart[ffpname]} if ffpname in subchart else {ffpname: self.ffp_dict_redeem.get(ffpname, {})}

            charts = self._findChart_SingleSeg(orig_eff, dest_eff, distance_eff, carrier_eff, ffp_dict=ffp_subchart)

            if charts:
                chart_seg = charts[0]  # since only 1 ffp is involved
                self._findPrice_SingleSeg(chart_seg, orig_eff, dest_eff, cabin, distance_eff)
                awardmile_seg = chart_seg['award_miles']
                awardmile_tot.append(awardmile_seg)
            else:
                awardmile_tot.append('N/A')

        return awardmile_tot

    def _handlePersegPricingReturn(self, awardmile_tot):
        """Handle per-segment pricing result"""
        if all(isinstance(item, int) for item in awardmile_tot):
            result = sum(awardmile_tot)
        else:
            result = 'Per Segment Pricing: At least price for one segment is non-int type.'

        return result

    # ==================== MULTI-SEGMENT CASES ====================

    def _multiseg_Case1(self, ffpname, origs, dests, distances, carriers, cabin, subchart):
        """Case 1: Transfer involving only self as carrier (follows tab2_example.py)"""
        if ffpname in ['AS', 'AA', 'IB', 'QR', 'CX', 'AV', 'BR', 'SQ', 'TP', 'UA', 'AM', 'VS', 'EK', 'EY', 'B6', 'WN', 'NK']:
            chart = self._cumulativePricing(ffpname, origs, dests, distances, carriers[0], cabin, subchart)

        elif ffpname in ['BA', 'JL', 'TK', 'EI']:
            # Use self chart, per segment pricing
            result = self._persegPricing(origs, dests, distances, carriers, cabin, ffpname, subchart)
            result = self._handlePersegPricingReturn(result)
            chart = dict(ffp=ffpname, ffp_disp_name=subchart[ffpname]['name'], chart_name='Per Segment', award_miles=result)

        elif ffpname in ['AY']:
            # Use self chart, per segment pricing with AY-specific exception logic
            zone_system = self.zone_system_dict['AY_self']['zones']
            num_seg = len(origs)

            flg_existlonghaul = False
            flg_existzone1 = False
            zone1connectionsegment = []

            for i in range(num_seg):
                orig_zone = self._fitAirportWithZone(origs[i], zone_system)
                dest_zone = self._fitAirportWithZone(dests[i], zone_system)

                if orig_zone and dest_zone:
                    if orig_zone in ["FI", "EU_north"] and dest_zone in ["FI", "EU_north"]:
                        flg_existzone1 = True
                        zone1connectionsegment.append(i)
                    elif (orig_zone in ["FI"] and dest_zone not in ["FI", "EU_north"]) or (orig_zone not in ["FI", "EU_north"] and dest_zone in ["FI"]):
                        flg_existlonghaul = True

            result = self._persegPricing(origs, dests, distances, carriers, cabin, ffpname, subchart)

            if all(isinstance(item, int) for item in result):
                if flg_existlonghaul and flg_existzone1:
                    result_tokeep = [item for index, item in enumerate(result) if index not in zone1connectionsegment]
                    result = sum(result_tokeep)
                else:
                    result = sum(result)
            else:
                result = 'Per Segment Pricing: At least price for one segment is non-int type.'

            chart = dict(ffp=ffpname, ffp_disp_name=subchart[ffpname]['name'], chart_name='Per Segment', award_miles=result)

        else:
            # Default fallback
            chart = self._cumulativePricing(ffpname, origs, dests, distances, carriers[0], cabin, subchart)

        return chart

    def _multiseg_Case2(self, ffpname, origs, dests, distances, carriers, cabin, subchart):
        """Case 2: Transfer involving only one partner as carrier"""
        if ffpname in ['AS', 'AA', 'IB', 'AY', 'CX', 'AV', 'BR', 'SQ', 'TP', 'UA', 'AM', 'FB', 'DL', 'VS', 'EY', 'B6']:
            chart = self._cumulativePricing(ffpname, origs, dests, distances, carriers[0], cabin, subchart)

        elif ffpname in ['BA', 'QR', 'TK', 'EK']:
            # Use partner chart, per segment pricing
            result = self._persegPricing(origs, dests, distances, carriers, cabin, ffpname, subchart)
            result = self._handlePersegPricingReturn(result)
            chart = dict(ffp=ffpname, ffp_disp_name=subchart[ffpname]['name'], chart_name='Per Segment', award_miles=result)

        elif ffpname in ['JL']:
            if carriers[0] == 'GK':
                result = self._persegPricing(origs, dests, distances, carriers, cabin, ffpname, subchart)
                result = self._handlePersegPricingReturn(result)
                chart = dict(ffp=ffpname, ffp_disp_name=subchart[ffpname]['name'], chart_name='Per Segment', award_miles=result)
            else:
                chart = self._cumulativePricing(ffpname, origs, dests, distances, carriers[0], cabin, subchart)

        else:
            # Default fallback
            chart = self._cumulativePricing(ffpname, origs, dests, distances, carriers[0], cabin, subchart)

        return chart

    def _multiseg_Case3(self, ffpname, origs, dests, distances, selfcarriers, carriers, cabin, subchart):
        """Case 3: Transfer involving self and one partner as carrier"""
        unique_carriers = list(set(carriers))
        if unique_carriers[0] in selfcarriers:
            part_carrier = unique_carriers[1]
        else:
            part_carrier = unique_carriers[0]

        if ffpname in ['AS', 'AA', 'AY', 'CX', 'UA', 'AM', 'FB', 'DL']:
            # Use the partner's chart, cumulative pricing
            chart = self._cumulativePricing(ffpname, origs, dests, distances, part_carrier, cabin, subchart)

        elif ffpname in ['BA', 'TK']:
            # Use each chart, per segment pricing
            result = self._persegPricing(origs, dests, distances, carriers, cabin, ffpname, subchart)
            result = self._handlePersegPricingReturn(result)
            chart = dict(ffp=ffpname, ffp_disp_name=subchart[ffpname]['name'], chart_name='Per Segment', award_miles=result)

        elif ffpname in ['IB', 'JL']:
            # Multipartner chart, distance based cumulative pricing. Only allow alliance partner mixing
            if part_carrier in self.OW_member:
                chart = self._cumulativePricing_multipartchart(ffpname, origs, dests, distances, cabin, subchart)
            else:
                msg = f"{subchart[ffpname]['name']} only allows itinerary carrier mixing with alliance partners."
                chart = dict(ffp=ffpname, ffp_disp_name=subchart[ffpname]['name'], chart_name='N/A', award_miles=msg)

        elif ffpname in ['AV', 'BR', 'SQ', 'TP']:
            if part_carrier in self.SA_member:
                chart = self._cumulativePricing(ffpname, origs, dests, distances, part_carrier, cabin, subchart)
            else:
                msg = f"{subchart[ffpname]['name']} only allows itinerary carrier mixing with alliance partners."
                chart = dict(ffp=ffpname, ffp_disp_name=subchart[ffpname]['name'], chart_name='N/A', award_miles=msg)

        elif ffpname in ['QR', 'VS', 'EK', 'EY', 'B6']:
            msg = f"{subchart[ffpname]['name']} does not allow Self + Partner."
            chart = dict(ffp=ffpname, ffp_disp_name=subchart[ffpname]['name'], chart_name='N/A', award_miles=msg)

        else:
            # Default fallback
            chart = self._cumulativePricing(ffpname, origs, dests, distances, part_carrier, cabin, subchart)

        return chart

    def _multiseg_Case4(self, ffpname, origs, dests, distances, carriers, cabin, subchart):
        """Case 4: Transfer involving more than one partner as carrier"""
        if ffpname in ['AS']:
            allowedCombo = ["AA", "BA", "AY"]
            unique_carriers = list(set(carriers))
            if all(item in allowedCombo for item in unique_carriers):
                chart = self._cumulativePricing(ffpname, origs, dests, distances, carriers[0], cabin, subchart)
            else:
                msg = 'This itinerary is not allowed. (AS multi-partner limited to AA/BA/AY)'
                chart = dict(ffp=ffpname, ffp_disp_name=subchart[ffpname]['name'], chart_name='N/A', award_miles=msg)

        elif ffpname in ['AA', 'UA', 'AM', 'FB', 'DL']:
            # Use the partner's chart, cumulative pricing
            chart = self._cumulativePricing(ffpname, origs, dests, distances, carriers[0], cabin, subchart)

        elif ffpname in ['BA']:
            # Multipartner chart, distance based cumulative pricing
            chart = self._cumulativePricing_multipartchart(ffpname, origs, dests, distances, cabin, subchart)

        elif ffpname in ['IB', 'CX', 'JL']:
            unique_carriers = list(set(carriers))
            if all(item in self.OW_member for item in unique_carriers):
                chart = self._cumulativePricing_multipartchart(ffpname, origs, dests, distances, cabin, subchart)
            else:
                msg = f"{subchart[ffpname]['name']} only allows itinerary carrier mixing with alliance partners."
                chart = dict(ffp=ffpname, ffp_disp_name=subchart[ffpname]['name'], chart_name='N/A', award_miles=msg)

        elif ffpname in ['AV', 'BR', 'SQ', 'TP']:
            unique_carriers = list(set(carriers))
            if all(item in self.SA_member for item in unique_carriers):
                chart = self._cumulativePricing(ffpname, origs, dests, distances, carriers[0], cabin, subchart)
            else:
                msg = f"{subchart[ffpname]['name']} only allows itinerary carrier mixing with alliance partners."
                chart = dict(ffp=ffpname, ffp_disp_name=subchart[ffpname]['name'], chart_name='N/A', award_miles=msg)

        elif ffpname in ['AY', 'QR', 'VS', 'EK', 'EY', 'B6']:
            msg = f"{subchart[ffpname]['name']} does not allow mixed partners"
            chart = dict(ffp=ffpname, ffp_disp_name=subchart[ffpname]['name'], chart_name='N/A', award_miles=msg)

        elif ffpname in ['TK']:
            result = self._persegPricing(origs, dests, distances, carriers, cabin, ffpname, subchart)
            result = self._handlePersegPricingReturn(result)
            chart = dict(ffp=ffpname, ffp_disp_name=subchart[ffpname]['name'], chart_name='Per Segment', award_miles=result)

        else:
            # Default fallback
            chart = self._cumulativePricing(ffpname, origs, dests, distances, carriers[0], cabin, subchart)

        return chart

    # ==================== MULTI-SEGMENT PRICE LOGIC ====================

    def _multiseg_price(self, carriers, origs, dests, cabin, distances):
        """Calculate award miles for multi-segment itinerary (follows tab2_example.py)"""
        unique_carriers = list(set(carriers))

        # First, find which programs take all carriers as redeem partners
        ffp2keep = {}

        for ffpname, ffpcontent in self.ffp_dict_redeem.items():
            ffp_self_carriers = ffpcontent['carriers']
            ffp_redeempartners = ffpcontent.get('redeem_partner')

            if ffp_redeempartners:
                ffp_redeem = ffp_redeempartners + ffp_self_carriers
            else:
                ffp_redeem = ffp_self_carriers

            if all(item in ffp_redeem for item in unique_carriers):
                ffp2keep[ffpname] = ffpcontent

        result_list = []

        if ffp2keep:
            for ffpname, ffpcontent in ffp2keep.items():
                subchart = {ffpname: ffpcontent}
                ffp_self_carriers = ffpcontent['carriers']
                ffp_redeempartners = ffpcontent.get('redeem_partner', [])

                # ===== SPECIAL CASES: QF and AC =====
                if ffpname == 'QF':
                    chart = dict(ffp=ffpname, ffp_disp_name=subchart[ffpname]['name'])

                    type1part_a = self.award_chart_dict['QF_AA']['specific_partners']
                    type1part_b = self.award_chart_dict['QF_GK']['specific_partners']
                    type1part = type1part_a + type1part_b
                    type2part = list(set(ffp_redeempartners) - set(type1part))
                    type1part += ["QF"]

                    if all(item in type1part_b for item in unique_carriers):
                        chart['chart_name'] = 'QF_GK'
                        self._findPrice_SingleSeg(chart, origs[0], dests[-1], cabin, sum(distances))

                    elif all(item in self.OW_member for item in unique_carriers) and ((len(unique_carriers) >= 3 and 'QF' in unique_carriers) or (len(unique_carriers) >= 2 and 'QF' not in unique_carriers)):
                        chart['chart_name'] = 'QF_mulpart'
                        self._findPrice_SingleSeg(chart, origs[0], dests[-1], cabin, sum(distances))

                    elif all(item in type1part for item in unique_carriers):
                        chart['chart_name'] = 'QF_AA'
                        self._findPrice_SingleSeg(chart, origs[0], dests[-1], cabin, sum(distances))

                    elif all(item in type2part for item in unique_carriers):
                        chart['chart_name'] = 'QF_partners'
                        self._findPrice_SingleSeg(chart, origs[0], dests[-1], cabin, sum(distances))

                    else:
                        chart['chart_name'] = 'N/A'
                        chart['award_miles'] = 'This itinerary is not allowed. QF charts rules.'

                    result_list.append(chart)

                elif ffpname == 'AC':
                    chart = dict(ffp=ffpname, ffp_disp_name=subchart[ffpname]['name'])

                    dynpart = self.award_chart_dict['AC_DynPart']['specific_partners']
                    dynpart = dynpart + ['AC']

                    if all(item in dynpart for item in unique_carriers):
                        chart['chart_name'] = 'N/A'
                        chart['award_miles'] = 'Dynamic.'
                    else:
                        carrier_eff = next(item for item in unique_carriers if item not in dynpart)
                        chart = self._cumulativePricing(ffpname, origs, dests, distances, carrier_eff, cabin, subchart)

                    result_list.append(chart)

                else:
                    # ===== GENERAL CASES: Case1-4 classification =====
                    is_self_involved = any(c in ffp_self_carriers for c in unique_carriers)
                    is_partner_involved = any(c in ffp_redeempartners for c in unique_carriers)

                    case1 = all(c in ffp_self_carriers for c in unique_carriers)
                    case2 = (not case1) and (len(unique_carriers) == 1)
                    case3 = (len(unique_carriers) > 1) and is_self_involved
                    case4 = (len(unique_carriers) > 1) and (not is_self_involved)

                    if case1:
                        chart = self._multiseg_Case1(ffpname, origs, dests, distances, carriers, cabin, subchart)
                        result_list.append(chart)

                    elif case2:
                        chart = self._multiseg_Case2(ffpname, origs, dests, distances, carriers, cabin, subchart)
                        result_list.append(chart)

                    elif case3:
                        chart = self._multiseg_Case3(ffpname, origs, dests, distances, ffp_self_carriers, carriers, cabin, subchart)
                        result_list.append(chart)

                    elif case4:
                        chart = self._multiseg_Case4(ffpname, origs, dests, distances, carriers, cabin, subchart)
                        result_list.append(chart)

        else:
            # No FFP can redeem those carriers together
            result_list = 'No FFP can be used for this carriers combination.'

        return result_list

    # ==================== SEARCH HANDLER ====================

    def _on_search_awards(self):
        """Main search handler"""
        try:
            # Validate inputs
            if not self._validate_all_segments():
                return

            # Check segment count
            if len(self.segments) > 1:
                # Multi-segment search
                self._search_multi_segment()
            else:
                # Single segment search
                self._search_single_segment()

        except Exception as e:
            messagebox.showerror("Search Error", str(e))

    def _validate_all_segments(self):
        """Validate all segment inputs"""
        for idx, segment in enumerate(self.segments):
            origin_str = segment['origin_var'].get().strip()
            dest_str = segment['dest_var'].get().strip()
            carrier_str = segment['carrier_var'].get().strip()
            distance_str = segment['distance_var'].get().strip()
            cabin = segment['cabin_var'].get()

            if not all([origin_str, dest_str, carrier_str, distance_str, cabin]):
                messagebox.showerror("Input Error", f"Segment {idx + 1}: Please fill all fields")
                return False

            # Validate distance is positive number
            try:
                dist = float(distance_str)
                if dist <= 0:
                    messagebox.showerror("Input Error", f"Segment {idx + 1}: Distance must be positive")
                    return False
            except ValueError:
                messagebox.showerror("Input Error", f"Segment {idx + 1}: Distance must be a number")
                return False

        return True

    def _search_single_segment(self):
        """Execute single segment search"""
        segment = self.segments[0]

        # Extract data
        origin_str = segment['origin_var'].get().strip()
        dest_str = segment['dest_var'].get().strip()
        carrier_str = segment['carrier_var'].get().strip()
        distance_str = segment['distance_var'].get().strip()
        cabin = segment['cabin_var'].get()

        # Parse codes
        origin = origin_str.split('-')[0].strip()
        dest = dest_str.split('-')[0].strip()
        carrier = carrier_str.split('-')[0].strip()
        distance = round(float(distance_str))

        # Find charts
        charts = self._findChart_SingleSeg(origin, dest, distance, carrier)

        # Find prices
        for chart in charts:
            self._findPrice_SingleSeg(chart, origin, dest, cabin, distance)

        # Display results
        self._display_results(charts)

        self._pass_results_to_tab3(charts)    
        
    def _search_multi_segment(self):
        """Execute multi-segment search with sub-segment breakdown"""
        # Collect data from all segments
        origs = []
        dests = []
        carriers = []
        distances = []
        cabins = []

        for segment in self.segments:
            origin_str = segment['origin_var'].get().strip()
            dest_str = segment['dest_var'].get().strip()
            carrier_str = segment['carrier_var'].get().strip()
            distance_str = segment['distance_var'].get().strip()
            cabin = segment['cabin_var'].get()

            origs.append(origin_str.split('-')[0].strip())
            dests.append(dest_str.split('-')[0].strip())
            carriers.append(carrier_str.split('-')[0].strip())
            distances.append(round(float(distance_str)))
            cabins.append(cabin)

        # Figure out the highest cabin chosen in this itinerary
        cabin_hierarchy = {'economy': 0, 'premium_economy': 1, 'business': 2, 'first': 3}
        cabin = max(cabins, key=lambda c: cabin_hierarchy.get(c, -1))

        num_seg = len(origs)

        # Store all results with metadata for display
        all_results = []

        # ===== 1. FULL SEGMENT SEARCH =====
        result_list_full = self._multiseg_price(carriers, origs, dests, cabin, distances)

        self._pass_results_to_tab3(result_list_full)

        all_results.append({
            'type': 'full',
            'seg_range': f"Segments 1-{num_seg} (Full Route)",
            'route': f"{origs[0]} → {dests[-1]}",
            'results': result_list_full,
            'start_idx': 0,
            'end_idx': num_seg
        })

        # ===== 2. SUB-SEGMENT SEARCHES (from longest to shortest, length >= 2) =====
        # Loop through sub-segment lengths from (num_seg-1) down to 2
        for seg_length in range(num_seg - 1, 1, -1):
            # Generate all possible consecutive sub-segments of this length
            for start_idx in range(num_seg - seg_length + 1):
                end_idx = start_idx + seg_length

                # Extract sub-segment data
                origs_sub = origs[start_idx:end_idx]
                dests_sub = dests[start_idx:end_idx]
                carriers_sub = carriers[start_idx:end_idx]
                distances_sub = distances[start_idx:end_idx]
                cabins_sub = cabins[start_idx:end_idx]

                # Use highest cabin in sub-segment
                cabin_sub = max(cabins_sub, key=lambda c: cabin_hierarchy.get(c, -1))

                # Call multi-segment search logic for this sub-segment
                result_list_sub = self._multiseg_price(carriers_sub, origs_sub, dests_sub, cabin_sub, distances_sub)

                # Store results
                all_results.append({
                    'type': 'subseg',
                    'seg_range': f"Segments {start_idx+1}-{end_idx}",
                    'route': f"{origs_sub[0]} → {dests_sub[-1]}",
                    'results': result_list_sub,
                    'start_idx': start_idx,
                    'end_idx': end_idx
                })

        # ===== 3. INDIVIDUAL SEGMENT SEARCHES =====
        for i in range(num_seg):
            orig_eff = origs[i]
            dest_eff = dests[i]
            distance_eff = distances[i]
            carrier_eff = carriers[i]
            cabin_eff = cabins[i]

            # Call single segment search logic
            charts = self._findChart_SingleSeg(orig_eff, dest_eff, distance_eff, carrier_eff)

            # Find prices
            for chart in charts:
                self._findPrice_SingleSeg(chart, orig_eff, dest_eff, cabin_eff, distance_eff)

            # Store results
            all_results.append({
                'type': 'single',
                'seg_range': f"Segment {i+1}",
                'route': f"{orig_eff} → {dest_eff}",
                'results': charts,
                'start_idx': i,
                'end_idx': i + 1
            })

        # Display all results
        self._display_multi_results(all_results, num_seg)

    def _pass_results_to_tab3(self, results):
        """
        Pass search results to Tab 3.
        Expects a list of result dictionaries.
        """
        # Specific check to ensure we only pass valid lists, not error strings
        if not isinstance(results, list):
            return

        # Use stored app reference to call the update method
        if self.app and hasattr(self.app, "update_tab3_data"):
            self.app.update_tab3_data(results)
        else:
            print("DEBUG: Sending data to Tab 3 (implement 'update_tab3_data' in main app)")


    def _calculate_cheapest_combination(self, num_seg, all_results):
        """
        Find the cheapest combination of tickets to cover the entire trip.
        Returns a formatted string summary.
        """
        # 1. Build Cost Map: (start_idx, end_idx) -> (min_cost, program_name)
        segment_costs = {}
        segment_routes = {}  # Store origin-destination pairs

        for group in all_results:
            results = group['results']
            start = group.get('start_idx')
            end = group.get('end_idx')

            if start is None or end is None:
                continue

            if isinstance(results, str) or not results:
                continue

            # Extract origin and destination from route string (e.g., "JFK → LAX")
            route = group.get('route', '')
            segment_routes[(start, end)] = route

            # Find lowest cost in this group
            min_cost = float('inf')
            best_program = None

            for res in results:
                miles = res.get('award_miles')
                if isinstance(miles, (int, float)):
                    if miles < min_cost:
                        min_cost = miles
                        best_program = res.get('ffp_disp_name')

            if best_program is not None:
                # If we have multiple entries for the same segment (unlikely in this logic but possible), take best
                if (start, end) not in segment_costs or min_cost < segment_costs[(start, end)][0]:
                    segment_costs[(start, end)] = (min_cost, best_program)

        # 2. DP to find min cost
        # dp[i] = min cost to finish segments from index i to num_seg
        # dp[num_seg] = 0
        dp = [float('inf')] * (num_seg + 1)
        dp[num_seg] = 0
        path = {}  # path[i] = (next_node, cost, program)

        for i in range(num_seg - 1, -1, -1):
            for j in range(i + 1, num_seg + 1):
                if (i, j) in segment_costs:
                    cost, program = segment_costs[(i, j)]
                    if cost + dp[j] < dp[i]:
                        dp[i] = cost + dp[j]
                        path[i] = (j, cost, program)

        # 3. Reconstruct Path
        if dp[0] == float('inf'):
            return "Could not find a valid combination for the entire trip."

        summary_parts = []
        curr = 0
        total_cost = dp[0]

        while curr < num_seg:
            if curr not in path:
                break
            next_node, cost, program = path[curr]
            
            # Get the route (origin → destination) for this segment combination
            route = segment_routes.get((curr, next_node), "Unknown")
            
            # Format miles
            miles_str = f"{cost/1000:.1f}k" if cost >= 1000 else str(int(cost))
            
            summary_parts.append(f"issue {route} with {program} ({miles_str})")
            curr = next_node

        total_cost_str = f"{total_cost/1000:.1f}k" if total_cost >= 1000 else str(int(total_cost))

        summary_text = "Summary of broken down segment: \n\n"
        summary_text += f"The cheapest way to finish the entire trip (allowing multiple tickets) will be: "
        summary_text += f"{', '.join(summary_parts)}, with a total cost of {total_cost_str} miles."
        
        return summary_text


    def _display_results(self, charts):
        """Display search results with proper formatting (Single Segment)"""
        self.results_listbox.delete(0, tk.END)

        if not charts:
            self.results_listbox.insert(tk.END, "No results found")
            return

        if isinstance(charts, str):
            self.results_listbox.insert(tk.END, charts)
            return

        # Extract columns (NO CHART NAME)
        disp_leftcol = [tp['ffp_disp_name'] for tp in charts]
        disp_rightcol = [tp['award_miles'] for tp in charts]

        combined = list(zip(disp_leftcol, disp_rightcol))

        def sort_key(item):
            miles = item[1]
            if isinstance(miles, (int, float)):
                return (0, miles)
            else:
                return (1, str(miles))

        sorted_results = sorted(combined, key=sort_key)

        # Display header
        header = f"{'Program':<35}{'Award Miles':<15}"
        self.results_listbox.insert(tk.END, header)
        self.results_listbox.insert(tk.END, "=" * 50)

        for program_name, miles in sorted_results:
            if isinstance(miles, (int, float)):
                miles_str = f"{miles / 1000:.1f}k" if miles >= 1000 else str(int(miles))
            else:
                miles_str = str(miles)

            display_line = f"{program_name:<35}{miles_str:<15}"
            self.results_listbox.insert(tk.END, display_line)


    def _display_multi_results(self, all_results, num_seg):
        """Display multi-segment search results with sub-segment breakdown"""
        self.results_listbox.delete(0, tk.END)

        if not all_results:
            self.results_listbox.insert(tk.END, "No results found")
            return

        # 1. Display Full Trip Result (First element)
        first_group = all_results[0]
        self._display_single_group(first_group)

        # 2. Display Optimization Summary
        self.results_listbox.insert(tk.END, "")
        summary_text = self._calculate_cheapest_combination(num_seg, all_results)
        
        # Split long lines for listbox
        import textwrap
        wrapped_summary = textwrap.wrap(summary_text, width=80)
        for line in wrapped_summary:
            self.results_listbox.insert(tk.END, line)
        
        # 3. Display Sub-segments (Rest of the elements)
        for idx, result_group in enumerate(all_results[1:], start=1):
            self.results_listbox.insert(tk.END, "")
            self._display_single_group(result_group)

    def _display_single_group(self, result_group):
        """Helper to display one group of results"""
        seg_range = result_group['seg_range']
        route = result_group['route']
        results = result_group['results']

        # Header
        header_line = f"{'=' * 60}"
        self.results_listbox.insert(tk.END, header_line)
        self.results_listbox.insert(tk.END, f"{seg_range}, {route}")
        self.results_listbox.insert(tk.END, header_line)

        if isinstance(results, str):
            self.results_listbox.insert(tk.END, results)
        elif results:
            # Extract and format results (NO CHART NAME)
            disp_leftcol = [tp['ffp_disp_name'] for tp in results]
            disp_rightcol = [tp['award_miles'] for tp in results]

            combined = list(zip(disp_leftcol, disp_rightcol))

            def sort_key(item):
                miles = item[1]
                if isinstance(miles, (int, float)):
                    return (0, miles)
                else:
                    return (1, str(miles))

            sorted_results = sorted(combined, key=sort_key)

            # Display column header
            col_header = f"{'Program':<35}{'Award Miles':<15}"
            self.results_listbox.insert(tk.END, col_header)
            self.results_listbox.insert(tk.END, "-" * 50)

            for program_name, miles in sorted_results:
                if isinstance(miles, (int, float)):
                    miles_str = f"{miles / 1000:.1f}k" if miles >= 1000 else str(int(miles))
                else:
                    miles_str = str(miles)

                display_line = f"{program_name:<35}{miles_str:<15}"
                self.results_listbox.insert(tk.END, display_line)
        else:
            self.results_listbox.insert(tk.END, "No results for this segment")


