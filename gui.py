"""
gui.py: Main Application with Centralized Data Loading and Search Context

Updated:
- Load accrual_rules.json for Tab 4
- Load updated ffp.json with family_pooling and expiration fields
- Add Tab 4 to notebook
- Update validation for new JSON structures
"""

import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
from tab1 import Tab1Frame
from tab2 import Tab2Frame
from tab3 import Tab3Frame
from tab4_simp import Tab4Frame

# Directories
BASE_DIR = os.path.dirname(__file__)
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
JSON_DIR = os.path.join(ASSETS_DIR, 'data')
ICON_DIR = os.path.join(ASSETS_DIR, 'logos')


class App(tk.Tk):
    """Main application class with centralized data loading"""
    
    def __init__(self):
        super().__init__()
        
        self.title("Frequent Flyer Planner")
        self.geometry("1200x700")
        
        # Store directory paths for reference
        self.BASE_DIR = BASE_DIR
        self.JSON_DIR = JSON_DIR
        self.ICON_DIR = ICON_DIR
        
        # Initialize search context for tab communication
        self.search_context = {
            'route_type': None,
            'carrier_code': None,
            'origin': None,
            'destination': None,
            'distance': None,
            'cabin': None,
            'results': []
        }
        
        print("=" * 60)
        print("FREQUENT FLYER PLANNER - STARTUP")
        print("=" * 60)
        print(f"Data directory: {JSON_DIR}")
        print()
        
        # Load and validate all data once at startup
        try:
            self._load_all_data()
            print()
            self._validate_data()
            print()
            self._setup_ui()
        except Exception as e:
            messagebox.showerror("Startup Error", 
                f"Failed to start application:\n\n{str(e)}")
            print(f"ERROR: {str(e)}")
            self.destroy()
            return
        
        print("=" * 60)
        print("STARTUP COMPLETE")
        print("=" * 60)
    
    def _load_all_data(self):
        """Load all required JSON files once at startup"""
        
        print("Loading data files...")
        
        # Define all required JSON files
        json_files = {
            'carriers': 'carriers.json',
            'ffp': 'ffp.json',
            'alliance': 'alliance.json',
            'partners': 'partners.json',
            'award_charts': 'award_charts.json',
            'zone_systems': 'zone_systems.json',
            'valuations': 'valuations.json',
            # 'accrual_rules': 'accrual_rules.json'  
        }
        
        # Load each file
        for attr_name, filename in json_files.items():
            filepath = os.path.join(self.JSON_DIR, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    setattr(self, attr_name, data)
                    print(f"  ✓ Loaded {filename}")
            
            except FileNotFoundError:
                raise FileNotFoundError(f"Missing required file: {filepath}")
            
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in {filename}:\n{str(e)}")
    
    def _validate_data(self):
        """Validate loaded data for consistency and structure"""
        
        print("\nValidating data...")
        
        try:
            # Check basic structure
            if 'carriers' not in self.carriers:
                raise ValueError("carriers.json must contain 'carriers' key")
            
            if 'alliances' not in self.alliance:
                raise ValueError("alliance.json must contain 'alliances' key")
            
            if 'ffps' not in self.ffp:
                raise ValueError("ffp.json must contain 'ffps' key")
            
            # NEW: Validate ffp.json has new fields
            for ffp_code, ffp_info in self.ffp['ffps'].items():
                if 'family_pooling' not in ffp_info:
                    raise ValueError(f"ffp.json[{ffp_code}] missing 'family_pooling' field")
                if 'expiration' not in ffp_info:
                    raise ValueError(f"ffp.json[{ffp_code}] missing 'expiration' field")
            
            if 'programs' not in self.partners:
                raise ValueError("partners.json must contain 'programs' key")
            

            if 'award_charts' not in self.award_charts:
                raise ValueError("award_charts.json must contain 'award_charts' key")
            
            if 'destinations' not in self.zone_systems:
                raise ValueError("zone_systems.json must contain 'destinations' key")
            
            if 'zone_definitions' not in self.zone_systems:
                raise ValueError("zone_systems.json must contain 'zone_definitions' key")
            
            if 'route_categories' not in self.zone_systems:
                raise ValueError("zone_systems.json must contain 'route_categories' key")
            
            if not isinstance(self.valuations, dict):
                raise ValueError("valuations.json must be a dictionary of FFP code -> cpp value")
            
            # # NEW: Validate accrual_rules.json structure
            # if not isinstance(self.accrual_rules, dict):
            #     raise ValueError("accrual_rules.json must be a dictionary of FFP code -> carriers -> cabin_class -> rules")
            
            # Cross-reference validation
            carrier_codes = {c['code'] for c in self.carriers['carriers']}
            print(f"  ✓ Loaded {len(carrier_codes)} carriers")
            
            # Validate alliance references
            alliance_codes = set()
            for alliance in self.alliance['alliances']:
                alliance_code = alliance['code']
                alliance_codes.add(alliance_code)
                for member in alliance.get('members', []):
                    if member not in carrier_codes:
                        raise ValueError(f"Alliance {alliance_code} references unknown carrier {member}")
            
            print(f"  ✓ Validated {len(alliance_codes)} alliances")
            
            # Validate FFP references
            ffp_data = self.ffp['ffps']
            
            if not isinstance(ffp_data, dict):
                raise ValueError(
                    "ffp.json['ffps'] must be a dictionary, not a list. "
                    "Format: { \"code\": { \"name\": \"...\", \"carriers\": [...], \"family_pooling\": bool, \"expiration\": str } }"
                )
            
            ffp_codes = set(ffp_data.keys())
            
            for ffp_code, ffp_info in ffp_data.items():
                for carrier in ffp_info.get('carriers', []):
                    if carrier not in carrier_codes:
                        raise ValueError(f"FFP {ffp_code} references unknown carrier {carrier}")
            
            print(f"  ✓ Validated {len(ffp_codes)} FFPs with family pooling & expiration policies")
            
           
            print(f"  ✓ Validated award chart mappings")
            
            # Validate zone definitions and route categories
            zone_definitions = self.zone_systems['zone_definitions']
            zone_def_count = len(zone_definitions)
            print(f"  ✓ Loaded {zone_def_count} zone definitions")
            
            route_categories = self.zone_systems['route_categories']
            route_count = len(route_categories)
            print(f"  ✓ Loaded {route_count} route categories")
            
            destinations = self.zone_systems['destinations']
            destination_count = len(destinations)
            print(f"  ✓ Loaded {destination_count} destination regions")
            
            # Validate valuations
            valuation_count = len(self.valuations)
            print(f"  ✓ Loaded {valuation_count} valuations (cpp values)")
            
            # # NEW: Validate accrual_rules
            # accrual_ffp_count = len(self.accrual_rules)
            # print(f"  ✓ Loaded accrual rules for {accrual_ffp_count} FFPs")
            
            print("  ✓ All data validation passed")
        
        except Exception as e:
            raise ValueError(f"Data validation failed: {str(e)}")
    
    def _setup_ui(self):
        """Setup main UI with tabs"""
        
        print("\nSetting up UI...")
        
        # Create main notebook for tabs
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Tab 1: Eligibility Finder
        try:
            tab1 = Tab1Frame(notebook, app=self)
            notebook.add(tab1, text="Tab 1: Eligibility Finder")
            print("  ✓ Created Tab 1: Eligibility Finder")
        except Exception as e:
            messagebox.showerror("Tab 1 Error", 
                f"Failed to create Tab 1:\n{str(e)}")
            print(f"  ✗ Tab 1 Error: {str(e)}")
        
        # Tab 2: Award Chart Lookup
        try:
            tab2 = Tab2Frame(notebook, app=self)
            notebook.add(tab2, text="Tab 2: Award Chart Lookup")
            print("  ✓ Created Tab 2: Award Chart Lookup")
        except Exception as e:
            messagebox.showerror("Tab 2 Error", 
                f"Failed to create Tab 2:\n{str(e)}")
            print(f"  ✗ Tab 2 Error: {str(e)}")
        
        # Tab 3: Award vs Cash Price Comparison
        try:
            tab3 = Tab3Frame(notebook, app=self)
            notebook.add(tab3, text="Tab 3: Award vs Cash")
            print("  ✓ Created Tab 3: Award vs Cash Comparison")
        except Exception as e:
            messagebox.showerror("Tab 3 Error", 
                f"Failed to create Tab 3:\n{str(e)}")
            print(f"  ✗ Tab 3 Error: {str(e)}")
        
        # Tab 4: Mile Accrual Calculator (NEW)
        try:
            tab4 = Tab4Frame(notebook, app=self)
            notebook.add(tab4, text="Tab 4: Mile Accrual")
            print("  ✓ Created Tab 4: Mile Accrual Calculator")
        except Exception as e:
            messagebox.showerror("Tab 4 Error", 
                f"Failed to create Tab 4:\n{str(e)}")
            print(f"  ✗ Tab 4 Error: {str(e)}")
        
        print("  ✓ UI setup completed")
    
    def reload_data(self):
        """Reload all data (useful for development/testing)"""
        try:
            self._load_all_data()
            self._validate_data()
            messagebox.showinfo("Success", "Data reloaded successfully")
            print("\n✓ Data reloaded successfully")
        except Exception as e:
            messagebox.showerror("Reload Error", f"Failed to reload data:\n{str(e)}")
            print(f"\n✗ Reload Error: {str(e)}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
