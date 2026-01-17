"""

Frequent Flyer Planner - Main Application V2

Data preparation moved to startup for easy sharing across tabs


"""

import os

import json

import tkinter as tk

from tkinter import ttk, messagebox

from tab1 import Tab1Frame

from tab2 import Tab2Frame

from tab3 import Tab3Frame

from tab4_simp import Tab4Frame

BASEDIR = os.path.dirname(__file__)

ASSETSDIR = os.path.join(BASEDIR, 'assets')

JSONDIR = os.path.join(ASSETSDIR, 'data')

class App(tk.Tk):

	"""Main application class with centralized data loading"""

	def __init__(self):

		super().__init__()

		self.title('Frequent Flyer Planner')

		self.geometry('1400x750')

		# Store directory paths for reference

		self.BASEDIR = BASEDIR

		self.JSONDIR = JSONDIR

		# Initialize search context for tab communication

		self.search_context = {

			'carrier_code': None,

			'origin': None,

			'destination': None,

			'distance': None,

			'cabin': None,

			'results': None

		}

		print('=' * 70)

		print('FREQUENT FLYER PLANNER - STARTUP')

		print('=' * 70)

		print(f'Data directory: {JSONDIR}')

		try:

			self.load_all_data()

			self.validate_data()

			self.prepare_tab1_data()

			self.prepare_tab2_data()

			self.prepare_tab4_data()

			self.setup_ui()

		except Exception as e:

			messagebox.showerror('Startup Error', f'Failed to start application: {str(e)}')

			print(f'ERROR: {str(e)}')

			self.destroy()

			return

		print('=' * 70)

		print('STARTUP COMPLETE')

		print('=' * 70)

	def load_all_data(self):

		"""Load all required JSON files once at startup"""

		print('\nLoading data files...')

		# Define all required JSON files

		json_files = {

			'carriers': 'carriers.json',

			'ffp': 'ffp.json',

			'alliance': 'alliance.json',

			'partners': 'partners.json',

			'award_charts': 'award_charts.json',

			'zonesystems': 'zone_systems.json',

			'valuations': 'valuations.json',

			'airports': 'airports_filtered.json',

			'countries': 'countries.json',

		}

		# Load each file

		for attr_name, filename in json_files.items():

			filepath = os.path.join(self.JSONDIR, filename)

			try:

				with open(filepath, 'r', encoding='utf-8') as f:

					data = json.load(f)

					setattr(self, attr_name, data)

					print(f'✓ Loaded {filename}')

			except FileNotFoundError:

				raise FileNotFoundError(f'Missing required file: {filepath}')

			except json.JSONDecodeError as e:

				raise ValueError(f'Invalid JSON in {filename}: {str(e)}')

	def validate_data(self):

		"""Validate loaded data for consistency and structure"""

		print('\nValidating data...')

		try:

			# Check basic structure

			if 'carriers' not in self.carriers:

				raise ValueError('carriers.json must contain "carriers" key')

			if 'alliances' not in self.alliance:

				raise ValueError('alliance.json must contain "alliances" key')

			if 'ffps' not in self.ffp:

				raise ValueError('ffp.json must contain "ffps" key')

			if 'programs' not in self.partners:

				raise ValueError('partners.json must contain "programs" key')

			if 'award_charts' not in self.award_charts:

				raise ValueError('awardcharts.json must contain "award_charts" key')

			if 'zone_definitions' not in self.zonesystems:

				raise ValueError('zone_systems.json must contain "zone_definitions" key')

			if 'shared_groups' not in self.zonesystems:

				raise ValueError('zone_systems.json must contain "shared_groups" key')

			if not isinstance(self.countries, list):

				raise ValueError('countries.json must be a list of {code,name} objects')

			# Validate airports structure

			if not isinstance(self.airports, list):

				raise ValueError('airports_filtered.json must be an array of airport objects')

			# Build airport lookup by IATA code

			self.airport_lookup = {}

			for airport in self.airports:

				iata_code = airport.get('iata_code', '').upper()

				if iata_code and len(iata_code) == 3:

					self.airport_lookup[iata_code] = {

						'name': airport.get('name', ''),

						'continent': airport.get('continent', ''),

						'iso_country': airport.get('iso_country', ''),

						'iso_region': airport.get('iso_region', ''),

						'latitude': airport.get('latitude_deg', 0),

						'longitude': airport.get('longitude_deg', 0),

					}

			carrier_codes = [c for c in self.carriers['carriers']]

			print(f'✓ Loaded {len(carrier_codes)} carriers')

			alliance_codes = set()

			for alliance in self.alliance['alliances']:

				alliance_code = alliance.get('code')

				alliance_codes.add(alliance_code)

			print(f'✓ Validated {len(alliance_codes)} alliances')

			ffp_data = self.ffp['ffps']

			if not isinstance(ffp_data, dict):

				raise ValueError('ffp.json: "ffps" must be a dictionary')

			ffp_codes = set(ffp_data.keys())

			print(f'✓ Validated {len(ffp_codes)} FFPs')

			zone_definitions = self.zonesystems['zone_definitions']

			zone_def_count = len(zone_definitions)

			print(f'✓ Loaded {zone_def_count} zone definitions')

			valuation_count = len(self.valuations)

			print(f'✓ Loaded {valuation_count} valuations')

			airport_count = len(self.airport_lookup)

			print(f'✓ Loaded {airport_count} airports')

			print('\n✓ All data validation passed')

		except Exception as e:

			raise ValueError(f'Data validation failed: {str(e)}')

	def prepare_tab1_data(self):

		"""Prepare Tab1-specific data structures at startup"""

		print('\nPreparing Tab1 data...')

		try:

			carriers_list = self.carriers['carriers']

			ffp_dict = self.ffp['ffps']

			alliance_list = self.alliance['alliances']

			partners_list = self.partners['programs']

			countries_list = self.countries

			# Extract alliance members

			OW_member = alliance_list[0].get('members')

			SA_member = alliance_list[1].get('members')

			ST_member = alliance_list[2].get('members')

			carriers_alliance = ['StarAlliance', 'OneWorld', 'SkyTeam', 'None']

			# Build carrierlist_tab1 and carriers_country_tab1

			carrierlist_tab1 = []

			carriers_country_tab1 = []

			for carrier in carriers_list:

				carrier_code = carrier['code']

				carrier_name = carrier['name']

				carrier_displayName = carrier_code + ' - ' + carrier_name

				carrier_country = carrier['country']

				matched_country = [c for c in countries_list if c['code'] == carrier_country]

				if not matched_country:

					raise ValueError(f'Unknown country code "{carrier_country}" in carriers.json')

				carrier_displayCountry = matched_country[0]['code'] + ' - ' + matched_country[0]['name']

				if carrier_displayCountry not in carriers_country_tab1:

					carriers_country_tab1.append(carrier_displayCountry)

				# Determine alliance

				if carrier_code in SA_member:

					carrier_alliance = carriers_alliance[0]

				elif carrier_code in OW_member:

					carrier_alliance = carriers_alliance[1]

				elif carrier_code in ST_member:

					carrier_alliance = carriers_alliance[2]

				else:

					carrier_alliance = carriers_alliance[3]

				carrier_dict = {

					'name': carrier_displayName,

					'country': carrier_displayCountry,

					'alliance': carrier_alliance

				}

				carrierlist_tab1.append(carrier_dict)

			carriers_country_tab1 = sorted(carriers_country_tab1)

			# Build ffp_dict_redeem

			keep = {'name', 'carriers'}

			ffp_dict_redeem = {

				name: {k: v for k, v in value.items() if k in keep}

				for name, value in ffp_dict.items()

			}

			for ffp_name, ffp_value in ffp_dict_redeem.items():

				ffp_self_carriers = ffp_value['carriers']

				partner_carrier = []

				for partnership in partners_list:

					if partnership['ffp'] == ffp_name and partnership.get('relationship') in ['both', 'redeem_only']:

						if partnership.get('type') == 'alliance':

							alliance_name = partnership.get('alliance')

							if alliance_name == "OW":

								partner_carrier += OW_member

							elif alliance_name == "SA":

								partner_carrier += SA_member

							elif alliance_name == "ST":

								partner_carrier += ST_member

							else:

								raise ValueError(f'Unrecognized alliance "{alliance_name}" in partnership definition')

						elif partnership.get('type') == 'individual':

							partner_carrier += partnership.get('carriers')

						else:

							raise ValueError(f'Unknown partnership relationship in partnership definition')

				# Remove duplicates and self carriers

				partner_carrier = list(dict.fromkeys(partner_carrier))

				partner_carrier = [item for item in partner_carrier if item not in ffp_self_carriers]

				if partner_carrier:

					ffp_value['redeem_partner'] = partner_carrier

			# Store prepared data as app attributes

			self.carrierlist_tab1 = carrierlist_tab1

			self.carriers_country_tab1 = carriers_country_tab1

			self.ffp_dict_redeem = ffp_dict_redeem

			print(f'✓ Prepared {len(carrierlist_tab1)} carriers for Tab1')

			print(f'✓ Prepared {len(carriers_country_tab1)} countries for Tab1')

			print(f'✓ Prepared {len(ffp_dict_redeem)} FFPs with redeem partners')

		except Exception as e:

			raise ValueError(f'Tab1 data preparation failed: {str(e)}')

	def prepare_tab2_data(self):

		"""Prepare Tab2-specific data structures at startup"""

		print('\nPreparing Tab2 data...')

		try:

			carriers_list = self.carriers['carriers']

			airports_list = self.airports

			zone_system_dict = self.zonesystems['zone_definitions']

			zone_system_ref = self.zonesystems['shared_groups']

			award_chart_dict = self.award_charts['award_charts']

			alliance_list = self.alliance['alliances']

			# Define legal zone types

			legal_zone_type = [

				"continents", "countries", "regions", "airports",

				"countries_exclude", "regions_exclude", "airports_exclude"

			]

			# Expand zone system references

			def handleZoneSystemReference(datalist, glb_shared_dict, zone_group_dict):

				overall_list = []

				for element_str in datalist:

					if element_str.startswith('$lcl_shared.'):

						referred_group = element_str.split('.')[1]

						collected_local_refer = zone_group_dict.get('local_shared_groups')

						if collected_local_refer:

							for name, value in collected_local_refer.items():

								if name == referred_group:

									overall_list += value

					elif element_str.startswith('$glb_shared.'):

						referred_group = element_str.split('.')[1]

						for name, value in glb_shared_dict.items():

							if name == referred_group:

								overall_list += value

					else:

						overall_list.append(element_str)

				return list(set(overall_list))

			# Process zone system to expand all references

			for name, value in zone_system_dict.items():

				group_zones = value.get('zones')

				if group_zones:

					for name2, value2 in group_zones.items():

						for name3, value3 in value2.items():

							if name3 in legal_zone_type and any(item.startswith('$') for item in value3):

								temp = handleZoneSystemReference(value3, zone_system_ref, value)

								value2[name3] = temp

			# Build airports display list

			airports_disp = []

			for airport in airports_list:

				tempstring = airport['iata_code'] + ' - ' + airport['name']

				airports_disp.append(tempstring)

			# Build carriers display list

			carriers_disp = []

			for carrier in carriers_list:

				carrier_code = carrier['code']

				carrier_name = carrier['name']

				carrier_displayName = carrier_code + ' - ' + carrier_name

				carriers_disp.append(carrier_displayName)

			# Store prepared data as app attributes

			self.airports_disp = airports_disp

			self.airports_list = airports_list

			self.carriers_disp = carriers_disp

			self.award_chart_dict = award_chart_dict

			self.legal_zone_type = legal_zone_type

			self.zone_system_dict = zone_system_dict

			self.alliance_list = alliance_list

			print(f'✓ Prepared {len(airports_disp)} airports for Tab2')

			print(f'✓ Prepared {len(carriers_disp)} carriers for Tab2')

			print('✓ Expanded zone system references')

			print(f'✓ Prepared {len(award_chart_dict)} award charts')

		except Exception as e:

			raise ValueError(f'Tab2 data preparation failed: {str(e)}')

	def prepare_tab4_data(self):

		"""Prepare Tab4-specific data structures at startup (Earning partners)"""

		print('\nPreparing Tab4 data...')

		try:

			ffp_dict = self.ffp['ffps']

			alliance_list = self.alliance['alliances']

			partners_list = self.partners['programs']

			# Extract alliance members

			OW_member = alliance_list[0].get('members')

			SA_member = alliance_list[1].get('members')

			ST_member = alliance_list[2].get('members')

			# Build ffp_dict_earn (similar to ffp_dict_redeem but for earning)

			keep = {'name', 'carriers'}

			ffp_dict_earn = {

				name: {k: v for k, v in value.items() if k in keep}

				for name, value in ffp_dict.items()

			}

			for ffp_name, ffp_value in ffp_dict_earn.items():

				ffp_self_carriers = ffp_value['carriers']

				partner_carrier = []

				for partnership in partners_list:

					if partnership['ffp'] == ffp_name and partnership.get('relationship') in ['both', 'earn_only']:

						if partnership.get('type') == 'alliance':

							alliance_name = partnership.get('alliance')

							if alliance_name == "OW":

								partner_carrier += OW_member

							elif alliance_name == "SA":

								partner_carrier += SA_member

							elif alliance_name == "ST":

								partner_carrier += ST_member

							else:

								raise ValueError(f'Unrecognized alliance "{alliance_name}" in partnership definition')

						elif partnership.get('type') == 'individual':

							partner_carrier += partnership.get('carriers')

						else:

							raise ValueError(f'Unknown partnership relationship in partnership definition')

				# Remove duplicates and self carriers

				partner_carrier = list(dict.fromkeys(partner_carrier))

				partner_carrier = [item for item in partner_carrier if item not in ffp_self_carriers]

				if partner_carrier:

					ffp_value['earn_partner'] = partner_carrier

			# Store prepared data as app attributes

			self.ffp_dict_earn = ffp_dict_earn

			print(f'✓ Prepared {len(ffp_dict_earn)} FFPs with earning partners')

		except Exception as e:

			raise ValueError(f'Tab4 data preparation failed: {str(e)}')

	def update_tab3_data(self, results):

		"""

		Receive search results from Tab 2 and pass them to Tab 3.

		`results` should be a list of result dictionaries from Tab 2.

		"""

		# Optionally store to app-wide context too

		self.search_context['results'] = results

		# Forward to Tab 3 if it exists and supports load_data()

		if hasattr(self, 'tab3') and hasattr(self.tab3, 'load_data'):

			self.tab3.load_data(results)

		else:

			print("DEBUG: Tab 3 not available or does not implement load_data().")

	def setup_ui(self):

		"""Setup main UI with tabs"""

		print('\nSetting up UI...')

		notebook = ttk.Notebook(self)

		notebook.pack(fill='both', expand=True, padx=5, pady=5)

		# Tab 1: Eligibility Finder (Redeem)

		try:

			tab1 = Tab1Frame(

				notebook,

				carriers_country_tab1=self.carriers_country_tab1,

				carrierlist_tab1=self.carrierlist_tab1,

				ffp_dict_redeem=self.ffp_dict_redeem

			)

			notebook.add(tab1, text='Tab 1 - Redeem Eligibility')

			print('✓ Created Tab 1 - Redeem Eligibility')

		except Exception as e:

			messagebox.showerror('Tab 1 Error', f'Failed to create Tab 1: {str(e)}')

			print(f'Tab 1 Error: {str(e)}')

		# Tab 2: Award Chart Lookup

		try:

			tab2 = Tab2Frame(

				notebook,

				app = self,

				airports_disp=self.airports_disp,

				airports_list=self.airports_list,

				carriers_disp=self.carriers_disp,

				ffp_dict_redeem=self.ffp_dict_redeem,

				award_chart_dict=self.award_chart_dict,

				legal_zone_type=self.legal_zone_type,

				zone_system_dict=self.zone_system_dict,

				alliance_members = self.alliance_list

			)

			notebook.add(tab2, text='Tab 2 - Award Chart Lookup')

			print('✓ Created Tab 2 - Award Chart Lookup')

		except Exception as e:

			messagebox.showerror('Tab 2 Error', f'Failed to create Tab 2: {str(e)}')

			print(f'Tab 2 Error: {str(e)}')

		# Tab 3: (e.g. Cash or Mile.)

		try:

			self.tab3 = Tab3Frame(

				notebook,

				app=self

			)

			notebook.add(self.tab3, text='Tab 3 - Cash vs Miles')

			print('✓ Created Tab 3')

		except Exception as e:

			messagebox.showerror('Tab 3 Error', f'Failed to create Tab 3: {str(e)}')

			print(f'Tab 3 Error: {str(e)}')

		# Tab 4: Earning Partner Finder

		try:

			tab4 = Tab4Frame(

				notebook,

				carriers_country_tab1=self.carriers_country_tab1,

				carrierlist_tab1=self.carrierlist_tab1,

				ffp_dict_earn=self.ffp_dict_earn,

				ffp_dict=self.ffp['ffps']

			)

			notebook.add(tab4, text='Tab 4 - Earning Partner')

			print('✓ Created Tab 4 - Earning Partner Finder')

		except Exception as e:

			messagebox.showerror('Tab 4 Error', f'Failed to create Tab 4: {str(e)}')

			print(f'Tab 4 Error: {str(e)}')

		print('✓ UI setup completed')

	def reload_data(self):

		"""Reload all data (useful for development/testing)"""

		try:

			self.load_all_data()

			self.validate_data()

			self.prepare_tab1_data()

			self.prepare_tab2_data()

			self.prepare_tab4_data()

			messagebox.showinfo('Success', 'Data reloaded successfully')

			print('Data reloaded successfully')

		except Exception as e:

			messagebox.showerror('Reload Error', f'Failed to reload data: {str(e)}')

			print(f'Reload Error: {str(e)}')

if __name__ == '__main__':

	app = App()

	app.mainloop()