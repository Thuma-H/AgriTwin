"""
AgriTwin-ZM GUI - Tkinter-based graphical interface

Professional desktop application for running agricultural simulations
with a clean, responsive user interface.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from datetime import datetime

from models.maize import Maize
from models.tomato import Tomato
from engines.supply_demand import SupplyDemandEngine
from engines.storage_loss import StorageLossSimulator
from engines.policy import PolicyEngine
from reports.dashboard import ReportingDashboard


class AgriTwinGUI:
    """Main GUI application for AgriTwin-ZM."""

    def __init__(self, root):
        self.root = root
        self.root.title("AgriTwin-ZM v1.0 - Agricultural Simulation Dashboard")
        self.root.geometry("1200x700")
        self.root.minsize(1000, 600)

        # Zambia-inspired palette: deep green base with warm gold accents.
        self.BG_COLOR = "#0f2a1f"
        self.SURFACE_COLOR = "#1a3b2d"
        self.CARD_COLOR = "#214d3a"
        self.PRIMARY_COLOR = "#2f7d57"
        self.GOLD_COLOR = "#d4af37"
        self.GOLD_HOVER = "#c49b2b"
        self.DANGER_COLOR = "#c94b3d"
        self.WARNING_COLOR = "#f0b74a"
        self.TEXT_LIGHT = "#f5f3e8"
        self.TEXT_MUTED = "#d7dbc9"
        self.TEXT_DARK = "#1b221e"

        self.root.configure(bg=self.BG_COLOR)

        style = ttk.Style()
        style.theme_use("clam")

        style.configure("App.TFrame", background=self.BG_COLOR)
        style.configure("Card.TFrame", background=self.CARD_COLOR)
        style.configure("Title.TLabel", font=("Segoe UI", 24, "bold"), foreground=self.GOLD_COLOR, background=self.BG_COLOR)
        style.configure("Heading.TLabel", font=("Segoe UI", 13, "bold"), foreground=self.TEXT_LIGHT, background=self.BG_COLOR)
        style.configure("Normal.TLabel", font=("Segoe UI", 11), foreground=self.TEXT_LIGHT, background=self.BG_COLOR)
        style.configure("Subtle.TLabel", font=("Segoe UI", 10, "italic"), foreground=self.TEXT_MUTED, background=self.BG_COLOR)

        style.configure("TLabelframe", background=self.CARD_COLOR, borderwidth=2, relief="solid", foreground=self.GOLD_COLOR)
        style.configure("TLabelframe.Label", background=self.CARD_COLOR, foreground=self.GOLD_COLOR, font=("Segoe UI", 11, "bold"))

        style.configure("TNotebook", background=self.BG_COLOR, borderwidth=0)
        style.configure("TNotebook.Tab", font=("Segoe UI", 11, "bold"), background=self.PRIMARY_COLOR, foreground=self.TEXT_LIGHT, padding=(20, 12))
        style.map("TNotebook.Tab", background=[("selected", self.GOLD_COLOR), ("active", self.GOLD_HOVER)], foreground=[("selected", self.TEXT_DARK)])

        style.configure("TEntry", fieldbackground="#f9f7ef", foreground=self.TEXT_DARK)
        style.configure("TCombobox", fieldbackground="#f9f7ef", foreground=self.TEXT_DARK)

        style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), background=self.PRIMARY_COLOR, foreground=self.TEXT_LIGHT, borderwidth=0, padding=(16, 10))
        style.map("Primary.TButton", background=[("active", "#276849")])

        style.configure("Gold.TButton", font=("Segoe UI", 11, "bold"), background=self.GOLD_COLOR, foreground=self.TEXT_DARK, borderwidth=0, padding=(16, 10))
        style.map("Gold.TButton", background=[("active", self.GOLD_HOVER)])

        style.configure("Danger.TButton", font=("Segoe UI", 11, "bold"), background=self.DANGER_COLOR, foreground=self.TEXT_LIGHT, borderwidth=0, padding=(16, 10))
        style.map("Danger.TButton", background=[("active", "#ac3f33")])

        # State
        self.dashboard = ReportingDashboard()
        self.policy_engine = PolicyEngine()
        self.storage_sim = StorageLossSimulator()
        self._quick_start_shown = False

        # Build UI first (creates status_label)
        self.build_ui()

        # Load sample data after UI is built
        self.load_sample_data()

        # Show quick start guide after a short delay
        self.root.after(350, self.show_quick_start)

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        pass

    def build_ui(self):
        """Build the entire UI structure."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, style="App.TFrame", padding="15")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Initialize status_label early (before tabs that may call update_status)
        footer = ttk.Frame(main_frame, style="App.TFrame")
        footer.grid(row=2, column=0, sticky="ew", pady=(15, 0))
        footer.columnconfigure(0, weight=1)
        footer.columnconfigure(1, weight=0)

        self.status_label = tk.Label(
            footer,
            text="Ready",
            bg=self.SURFACE_COLOR,
            fg=self.TEXT_LIGHT,
            font=("Segoe UI", 10),
            anchor="w",
            padx=12,
            pady=8,
            relief="flat",
        )
        self.status_label.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        ttk.Button(footer, text="Quick Guide", style="Gold.TButton", command=self.show_help, width=12).grid(row=0, column=1, sticky="e")

        # Header
        header = ttk.Frame(main_frame, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        header.columnconfigure(1, weight=1)

        title = ttk.Label(header, text="AgriTwin-ZM v1.0", style="Title.TLabel")
        title.grid(row=0, column=0, sticky="w")

        subtitle = ttk.Label(header, text="Agricultural Digital Twin for Zambia", style="Subtle.TLabel")
        subtitle.grid(row=1, column=0, sticky="w")

        # Notebook (tabs) with custom style
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky="nsew", pady=10)
        main_frame.rowconfigure(1, weight=1)

        # Tabs
        self.sim_frame = ttk.Frame(self.notebook, style="App.TFrame")
        self.results_frame_tab = ttk.Frame(self.notebook, style="App.TFrame")
        self.dashboard_frame = ttk.Frame(self.notebook, style="App.TFrame")
        self.policy_frame = ttk.Frame(self.notebook, style="App.TFrame")
        self.data_frame = ttk.Frame(self.notebook, style="App.TFrame")

        self.notebook.add(self.sim_frame, text="Run Simulation")
        self.notebook.add(self.results_frame_tab, text="📊 Results")
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        self.notebook.add(self.policy_frame, text="Policy")
        self.notebook.add(self.data_frame, text="Data & Export")

        self.build_simulation_tab()
        self.build_results_tab()
        self.build_dashboard_tab()
        self.build_policy_tab()
        self.build_data_tab()

    def build_simulation_tab(self):
        """Build the simulation tab with scrolling support."""
        # Create main scrollable frame
        canvas = tk.Canvas(self.sim_frame, bg=self.BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.sim_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style="App.TFrame")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Enable mouse wheel scrolling
        canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.sim_frame.rowconfigure(0, weight=1)
        self.sim_frame.columnconfigure(0, weight=1)

        # Commodity selection with icon-like styling
        commodity_frame = ttk.LabelFrame(scrollable_frame, text="Select Commodity", padding="15")
        commodity_frame.pack(fill="x", padx=8, pady=8)

        self.commodity_var = tk.StringVar(value="Maize")
        maize_btn = ttk.Radiobutton(
            commodity_frame,
            text="🌽 Maize (grain)",
            variable=self.commodity_var,
            value="Maize",
            command=self.on_commodity_change,
        )
        maize_btn.grid(row=0, column=0, padx=25, pady=12)

        tomato_btn = ttk.Radiobutton(
            commodity_frame,
            text="🍅 Tomato (perishable)",
            variable=self.commodity_var,
            value="Tomato",
            command=self.on_commodity_change,
        )
        tomato_btn.grid(row=0, column=1, padx=25, pady=12)

        # Input fields
        input_frame = ttk.LabelFrame(scrollable_frame, text="Simulation Parameters", padding="15")
        input_frame.pack(fill="x", padx=8, pady=8)
        input_frame.columnconfigure(1, weight=1)
        input_frame.columnconfigure(3, weight=1)

        self.input_fields = {}

        # Maize inputs
        self.maize_inputs = {
            "production": ("Production (tons)", "50000"),
            "demand": ("Market Demand (tons)", "45000"),
            "moisture": ("Moisture Level (%)", "13.5"),
            "price": ("Price per Ton (ZMW)", "4500"),
            "loss_pct": ("Loss % per Month", "3.0"),
            "months": ("Storage Months", "6"),
        }

        # Tomato inputs
        self.tomato_inputs = {
            "production": ("Production (tons)", "2000"),
            "demand": ("Market Demand (tons)", "1800"),
            "shelf_life": ("Shelf Life (days)", "14"),
            "storage_type": ("Storage Type", "open"),
            "price_crate": ("Price per Crate (ZMW)", "120"),
        }

        self.display_inputs(input_frame, "Maize")

        # Buttons with colors (sticky at bottom)
        button_frame = ttk.Frame(scrollable_frame, style="App.TFrame")
        button_frame.pack(fill="x", padx=8, pady=15)
        button_frame.columnconfigure(0, weight=1)

        ttk.Button(button_frame, text="▶ Run Simulation", style="Gold.TButton", command=self.run_simulation).pack(fill="x", pady=10)
        ttk.Label(button_frame, text="💡 Tip: Results will appear in the 'Results' tab after running simulation", style="Subtle.TLabel").pack(pady=(5, 0))

    def display_inputs(self, parent, commodity):
        """Display input fields based on commodity type."""
        # Clear existing widgets
        for widget in parent.winfo_children():
            widget.destroy()

        self.input_fields = {}

        if commodity == "Maize":
            inputs = self.maize_inputs
        else:
            inputs = self.tomato_inputs

        for key, (label, default) in inputs.items():
            row_frame = ttk.Frame(parent)
            row_frame.pack(fill="x", padx=5, pady=6)
            row_frame.columnconfigure(1, weight=1)

            ttk.Label(row_frame, text=label, style="Normal.TLabel", width=20).grid(row=0, column=0, sticky="w", padx=8)

            if key == "storage_type":
                var = tk.StringVar(value=default)
                combo = ttk.Combobox(
                    row_frame, textvariable=var, values=["cold", "open"],
                    state="readonly", width=25, font=("Segoe UI", 10)
                )
                combo.grid(row=0, column=1, sticky="ew", padx=8)
                self.input_fields[key] = var
            else:
                var = tk.StringVar(value=default)
                entry = ttk.Entry(row_frame, textvariable=var, width=30, font=("Segoe UI", 10))
                entry.grid(row=0, column=1, sticky="ew", padx=8)
                self.input_fields[key] = var


    def build_results_tab(self):
        """Build the results tab with card-based visualization."""
        self.results_frame_tab.columnconfigure(0, weight=1)
        self.results_frame_tab.rowconfigure(1, weight=1)

        # Store current results
        self.current_results = {}

        # Header with title and export button
        header_frame = ttk.Frame(self.results_frame_tab, style="App.TFrame")
        header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        header_frame.columnconfigure(0, weight=1)

        ttk.Label(header_frame, text="📊 Simulation Results", style="Title.TLabel").grid(row=0, column=0, sticky="w")

        btn_frame = ttk.Frame(header_frame, style="App.TFrame")
        btn_frame.grid(row=0, column=1, sticky="e")
        ttk.Button(btn_frame, text="💾 Export", style="Primary.TButton", command=self.export_current_results).pack(side="right", padx=5)

        # Main scrollable content
        canvas = tk.Canvas(self.results_frame_tab, bg=self.BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.results_frame_tab, orient="vertical", command=canvas.yview)
        self.results_content_frame = ttk.Frame(canvas, style="App.TFrame")

        self.results_content_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.results_content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        scrollbar.grid(row=1, column=1, sticky="ns", pady=(0, 15))

        # Initial "no results" message
        self.show_no_results_message()

    def show_no_results_message(self):
        """Display message when no results are available."""
        for widget in self.results_content_frame.winfo_children():
            widget.destroy()

        empty_frame = tk.Frame(self.results_content_frame, bg=self.SURFACE_COLOR, relief="flat")
        empty_frame.pack(fill="both", expand=True, padx=20, pady=100)

        tk.Label(
            empty_frame,
            text="📊",
            font=("Segoe UI", 48),
            bg=self.SURFACE_COLOR,
            fg=self.TEXT_MUTED
        ).pack(pady=(40, 20))

        tk.Label(
            empty_frame,
            text="No simulation results yet",
            font=("Segoe UI", 16, "bold"),
            bg=self.SURFACE_COLOR,
            fg=self.TEXT_LIGHT
        ).pack(pady=5)

        tk.Label(
            empty_frame,
            text="Run a simulation from the 'Run Simulation' tab to see results here",
            font=("Segoe UI", 11),
            bg=self.SURFACE_COLOR,
            fg=self.TEXT_MUTED
        ).pack(pady=5)

    def display_results_cards(self, data):
        """Display results using card-based layout."""
        for widget in self.results_content_frame.winfo_children():
            widget.destroy()

        # Main container
        container = ttk.Frame(self.results_content_frame, style="App.TFrame")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Commodity title
        commodity_type = data.get('commodity_type', 'Unknown')
        title_frame = tk.Frame(container, bg=self.GOLD_COLOR, height=60)
        title_frame.pack(fill="x", pady=(0, 20))
        title_frame.pack_propagate(False)

        tk.Label(
            title_frame,
            text=f"{'🌽 Maize' if commodity_type == 'Maize' else '🍅 Tomato'} Simulation Results",
            font=("Segoe UI", 18, "bold"),
            bg=self.GOLD_COLOR,
            fg=self.TEXT_DARK
        ).pack(pady=15)

        # Storage Loss Section
        if 'storage' in data:
            self.create_card(container, "📦 Storage Loss Summary", data['storage'], self.PRIMARY_COLOR)

        # Supply & Demand Section
        if 'supply_demand' in data:
            self.create_card(container, "📊 Supply & Demand Analysis", data['supply_demand'], self.PRIMARY_COLOR)

        # Food Security Section
        if 'food_security' in data:
            self.create_card(container, "🛡️ Food Security Status", data['food_security'], self.WARNING_COLOR if data['food_security'].get('status') == 'At Risk' else self.PRIMARY_COLOR)

    def create_card(self, parent, title, data, accent_color):
        """Create a styled card for displaying data."""
        # Card frame
        card = tk.Frame(parent, bg=self.SURFACE_COLOR, relief="flat", bd=0)
        card.pack(fill="x", pady=10)

        # Add subtle border
        card.config(highlightbackground=accent_color, highlightthickness=2)

        # Card header
        header = tk.Frame(card, bg=accent_color, height=45)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text=title,
            font=("Segoe UI", 13, "bold"),
            bg=accent_color,
            fg=self.TEXT_LIGHT if accent_color != self.WARNING_COLOR else self.TEXT_DARK
        ).pack(side="left", padx=15, pady=10)

        # Card content
        content = tk.Frame(card, bg=self.SURFACE_COLOR)
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Display data as rows
        row = 0
        for key, value in data.items():
            if key == 'status':  # Special handling for status
                continue

            # Create label and value pair
            label_text = key.replace('_', ' ').title()

            label_frame = tk.Frame(content, bg=self.SURFACE_COLOR)
            label_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=8)
            label_frame.columnconfigure(1, weight=1)

            tk.Label(
                label_frame,
                text=label_text + ":",
                font=("Segoe UI", 11, "bold"),
                bg=self.SURFACE_COLOR,
                fg=self.TEXT_MUTED,
                anchor="w"
            ).grid(row=0, column=0, sticky="w", padx=(0, 20))

            # Format value
            if isinstance(value, (int, float)):
                if 'percentage' in key.lower() or 'percent' in key.lower():
                    value_text = f"{value:.2f}%"
                elif 'zmw' in key.lower() or 'revenue' in key.lower():
                    value_text = f"ZMW {value:,.2f}"
                else:
                    value_text = f"{value:,.2f}"
            else:
                value_text = str(value)

            tk.Label(
                label_frame,
                text=value_text,
                font=("Segoe UI", 11),
                bg=self.SURFACE_COLOR,
                fg=self.TEXT_LIGHT,
                anchor="e"
            ).grid(row=0, column=1, sticky="e")

            row += 1

    def on_commodity_change(self):
        """Handle commodity selection change."""
        commodity = self.commodity_var.get()
        input_frame = self.sim_frame.winfo_children()[1]
        self.display_inputs(input_frame, commodity)

    def run_simulation(self):
        """Run the selected simulation."""
        try:
            commodity = self.commodity_var.get()

            if commodity == "Maize":
                self.run_maize_sim()
            else:
                self.run_tomato_sim()

            self.update_status(f"Simulation completed at {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            messagebox.showerror("Simulation Error", f"Error: {str(e)}")
            self.update_status("Error running simulation")

    def run_maize_sim(self):
        """Run maize simulation."""
        production = float(self.input_fields["production"].get())
        demand = float(self.input_fields["demand"].get())
        moisture = float(self.input_fields["moisture"].get())
        price = float(self.input_fields["price"].get())
        loss_pct = float(self.input_fields["loss_pct"].get())
        months = int(self.input_fields["months"].get())

        maize = Maize(production, 60_000, moisture, price, loss_pct)

        # Storage simulation
        storage_results = self.storage_sim.simulate_maize_storage(production, loss_pct, months)

        # Supply/demand
        monthly_loss = maize.calculate_monthly_loss()
        engine = SupplyDemandEngine(maize, production, demand)
        result = engine.run_monthly_simulation("Month-1", monthly_loss)
        self.dashboard.add_monthly_result(result)

        # Policy checks
        self.policy_engine.clear_alerts()
        self.policy_engine.check_fra_reserve(production)
        self.policy_engine.check_export_restriction(engine.calculate_surplus(),
                                                    production >= 500_000)
        self.policy_engine.check_max_storage_time("maize", months * 30)

        # Display results
        output = self.storage_sim.generate_loss_summary("maize")
        output += "\n\n" + "="*60 + "\n"
        output += "SUPPLY & DEMAND ANALYSIS\n"
        output += "="*60 + "\n"
        output += f"  Production        : {result['monthly_production']:>15,.2f} tons\n"
        output += f"  Demand            : {result['market_demand']:>15,.2f} tons\n"
        output += f"  Surplus           : {result['surplus']:>15,.2f} tons\n"
        output += f"  Shortage          : {result['shortage']:>15,.2f} tons\n"
        output += f"  Waste %           : {result['waste_percentage']:>15.2f}%\n"
        output += f"  Revenue (ZMW)     : {result['revenue_zmw']:>15,.2f}\n"
        output += f"  Food Security     : {result['food_security_percentage']:>14.1f}% "
        output += f"[{self.dashboard.food_security_label(result['food_security_percentage'])}]\n"
        output += f"  Price Adjustment  : {result['price_adjustment']['adjustment']}\n"

        self.display_results(output)

    def run_tomato_sim(self):
        """Run tomato simulation."""
        production = float(self.input_fields["production"].get())
        demand = float(self.input_fields["demand"].get())
        shelf_life = int(self.input_fields["shelf_life"].get())
        storage_type = self.input_fields["storage_type"].get()
        price_crate = float(self.input_fields["price_crate"].get())

        spoilage_rate = 1.5 if storage_type == "cold" else 4.0
        tomato = Tomato(production, shelf_life, storage_type, spoilage_rate, price_crate)

        # Storage simulation
        storage_results = self.storage_sim.simulate_tomato_storage(
            production, storage_type, shelf_life
        )

        # Supply/demand
        spoilage_info = tomato.calculate_spoilage(shelf_life)
        spoilage_tons = spoilage_info["total_spoilage_tons"]
        engine = SupplyDemandEngine(tomato, production, demand)
        result = engine.run_monthly_simulation("Month-1", spoilage_tons)
        self.dashboard.add_monthly_result(result)

        # Policy checks
        self.policy_engine.clear_alerts()
        self.policy_engine.check_max_storage_time("tomato", shelf_life, shelf_life)

        # Display results
        output = self.storage_sim.generate_loss_summary("tomato")
        output += "\n\n" + "="*60 + "\n"
        output += "SUPPLY & DEMAND ANALYSIS\n"
        output += "="*60 + "\n"
        output += f"  Production        : {result['monthly_production']:>15,.2f} tons\n"
        output += f"  Demand            : {result['market_demand']:>15,.2f} tons\n"
        output += f"  Surplus           : {result['surplus']:>15,.2f} tons\n"
        output += f"  Shortage          : {result['shortage']:>15,.2f} tons\n"
        output += f"  Spoilage (tons)   : {result['spoilage_tons']:>15,.2f}\n"
        output += f"  Waste %           : {result['waste_percentage']:>15.2f}%\n"
        output += f"  Revenue (ZMW)     : {result['revenue_zmw']:>15,.2f}\n"
        output += f"  Food Security     : {result['food_security_percentage']:>14.1f}% "
        output += f"[{self.dashboard.food_security_label(result['food_security_percentage'])}]\n"
        output += f"  Crates Produced   : {tomato.crates_from_production:>15,.0f}\n"

        self.display_results(output)

    def display_results(self, text):
        """Parse results text and display in card format."""
        # Parse the text output into structured data
        data = self.parse_results_text(text)

        # Store results
        self.current_results = data

        # Display in cards
        self.display_results_cards(data)

        # Switch to Results tab
        self.notebook.select(1)  # Index 1 is the Results tab

    def parse_results_text(self, text):
        """Parse the text output into structured data."""
        data = {
            'commodity_type': 'Maize' if 'MAIZE' in text else 'Tomato',
            'storage': {},
            'supply_demand': {},
            'food_security': {}
        }

        lines = text.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()

            if 'STORAGE LOSS SUMMARY' in line:
                current_section = 'storage'
            elif 'SUPPLY & DEMAND ANALYSIS' in line:
                current_section = 'supply_demand'
            elif not line or line.startswith('=') or line.startswith('-'):
                continue
            elif ':' in line and current_section:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()

                    # Clean up the value
                    value = value.replace(',', '')

                    # Try to convert to number
                    try:
                        if '%' in value:
                            data[current_section][key] = float(value.replace('%', '').strip())
                        elif 'tons' in value.lower():
                            data[current_section][key] = float(value.lower().replace('tons', '').strip())
                        elif 'zmw' in value.lower():
                            data[current_section][key] = float(value.lower().replace('zmw', '').strip())
                        elif value.replace('.', '').replace('-', '').isdigit():
                            data[current_section][key] = float(value)
                        else:
                            # Keep special values like [Secure], [At Risk]
                            if '[' in value:
                                status = value[value.find('[')+1:value.find(']')]
                                data['food_security']['status'] = status
                                # Extract percentage before bracket
                                pct_part = value[:value.find('[')].strip()
                                if pct_part:
                                    data[current_section][key] = pct_part
                            else:
                                data[current_section][key] = value
                    except (ValueError, AttributeError):
                        data[current_section][key] = value

        return data

    def show_results_window(self):
        """Deprecated - kept for compatibility."""
        # Just switch to results tab
        self.notebook.select(1)


    def export_current_results(self):
        """Export current results to a text file."""
        if not self.current_results:
            messagebox.showinfo("No Results", "No simulation results to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("JSON Files", "*.json"), ("All Files", "*.*")],
            initialfile=f"simulation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

        if file_path:
            try:
                if file_path.endswith('.json'):
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(self.current_results, f, indent=2)
                else:
                    # Export as formatted text
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(f"{self.current_results['commodity_type']} Simulation Results\n")
                        f.write("=" * 60 + "\n\n")

                        for section_name, section_data in self.current_results.items():
                            if section_name == 'commodity_type' or not section_data:
                                continue
                            f.write(f"{section_name.upper().replace('_', ' ')}\n")
                            f.write("-" * 60 + "\n")
                            for key, value in section_data.items():
                                f.write(f"{key}: {value}\n")
                            f.write("\n")

                messagebox.showinfo("Success", f"Results exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export: {str(e)}")

    def clear_results(self):
        """Clear the results."""
        self.current_results = {}
        self.show_no_results_message()

    def build_dashboard_tab(self):
        """Build the dashboard tab."""
        self.dashboard_frame.columnconfigure(0, weight=1)
        self.dashboard_frame.rowconfigure(0, weight=1)

        # Report display
        report_frame = ttk.LabelFrame(self.dashboard_frame, text="Full Report", padding="15")
        report_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        report_frame.columnconfigure(0, weight=1)
        report_frame.rowconfigure(0, weight=1)

        self.report_text = tk.Text(
            report_frame,
            height=35,
            width=120,
            wrap="word",
            font=("Consolas", 10),
            state="disabled",
            bg=self.SURFACE_COLOR,
            fg=self.TEXT_LIGHT,
            insertbackground=self.TEXT_LIGHT,
            relief="solid",
            bd=2,
            borderwidth=2,
            highlightthickness=1,
            highlightbackground=self.PRIMARY_COLOR,
        )
        self.report_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(report_frame, orient="vertical", command=self.report_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.report_text.config(yscrollcommand=scrollbar.set)

        # Buttons with icons
        button_frame = ttk.Frame(self.dashboard_frame, style="App.TFrame")
        button_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=15)
        button_frame.columnconfigure(5, weight=1)

        ttk.Button(button_frame, text="Refresh Report", style="Primary.TButton", command=self.refresh_dashboard).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Export CSV", style="Gold.TButton", command=lambda: self.export_report("csv")).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Export JSON", style="Gold.TButton", command=lambda: self.export_report("json")).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Export TXT", style="Gold.TButton", command=lambda: self.export_report("txt")).pack(side="left", padx=5)

        # Initial load
        self.refresh_dashboard()

    def refresh_dashboard(self):
        """Refresh and display the dashboard report."""
        if len(self.dashboard.results) == 0:
            text = "No simulation results yet. Run a simulation from the 'Run Simulation' tab."
        else:
            text = self.dashboard.print_full_report()

        self.report_text.config(state="normal")
        self.report_text.delete("1.0", "end")
        self.report_text.insert("1.0", text if isinstance(text, str) else "")
        self.report_text.config(state="disabled")

    def export_report(self, fmt):
        """Export the report in the specified format."""
        if len(self.dashboard.results) == 0:
            messagebox.showwarning("No Data", "No simulations to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=f".{fmt}",
            filetypes=[(f"{fmt.upper()} Files", f"*.{fmt}"), ("All Files", "*.*")]
        )

        if not file_path:
            return

        try:
            if fmt == "csv":
                self.dashboard.export_to_csv(file_path)
            elif fmt == "json":
                self.dashboard.export_to_json(file_path)
            else:
                self.dashboard.export_to_txt(file_path)

            messagebox.showinfo("Success", f"Report exported to {file_path}")
            self.update_status(f"Exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")

    def build_policy_tab(self):
        """Build the policy tab."""
        self.policy_frame.columnconfigure(0, weight=1)
        self.policy_frame.rowconfigure(1, weight=1)

        # Controls
        control_frame = ttk.LabelFrame(self.policy_frame, text="Policy Check Parameters", padding="15")
        control_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        control_frame.columnconfigure(1, weight=1)

        ttk.Label(control_frame, text="FRA Reserve (tons):", style="Normal.TLabel").grid(row=0, column=0, sticky="w", padx=8, pady=8)
        self.fra_var = tk.StringVar(value="500000")
        ttk.Entry(control_frame, textvariable=self.fra_var, width=25, font=("Segoe UI", 10)).grid(row=0, column=1, sticky="w", padx=8, pady=8)

        # Report display
        report_frame = ttk.LabelFrame(self.policy_frame, text="Policy Alerts & Recommendations", padding="15")
        report_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        report_frame.columnconfigure(0, weight=1)
        report_frame.rowconfigure(0, weight=1)

        self.policy_text = tk.Text(
            report_frame,
            height=33,
            width=120,
            wrap="word",
            font=("Consolas", 10),
            state="disabled",
            bg=self.SURFACE_COLOR,
            fg=self.TEXT_LIGHT,
            insertbackground=self.TEXT_LIGHT,
            relief="solid",
            bd=2,
            borderwidth=2,
            highlightthickness=1,
            highlightbackground=self.PRIMARY_COLOR,
        )
        self.policy_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(report_frame, orient="vertical", command=self.policy_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.policy_text.config(yscrollcommand=scrollbar.set)

        # Buttons
        button_frame = ttk.Frame(self.policy_frame, style="App.TFrame")
        button_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=15)

        ttk.Button(button_frame, text="Check FRA Reserve", style="Gold.TButton", command=self.check_fra).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Clear Alerts", style="Danger.TButton", command=self.clear_alerts).pack(side="left", padx=5)

    def check_fra(self):
        """Check FRA reserve."""
        try:
            fra_stock = float(self.fra_var.get())
            self.policy_engine.clear_alerts()
            self.policy_engine.check_fra_reserve(fra_stock)

            alerts = self.policy_engine.generate_policy_report()
            text = "\n".join(alerts)

            self.policy_text.config(state="normal")
            self.policy_text.delete("1.0", "end")
            self.policy_text.insert("1.0", text)
            self.policy_text.config(state="disabled")

            self.update_status(f"FRA check completed")
        except ValueError:
            messagebox.showerror("Input Error", "FRA Reserve must be a valid number.")

    def clear_alerts(self):
        """Clear policy alerts."""
        self.policy_engine.clear_alerts()
        self.policy_text.config(state="normal")
        self.policy_text.delete("1.0", "end")
        self.policy_text.config(state="disabled")
        self.update_status("Alerts cleared")

    def build_data_tab(self):
        """Build the data and export tab."""
        self.data_frame.columnconfigure(0, weight=1)
        self.data_frame.rowconfigure(1, weight=1)

        # Controls
        control_frame = ttk.LabelFrame(self.data_frame, text="Data Management", padding="15")
        control_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        control_frame.columnconfigure(2, weight=1)

        ttk.Button(control_frame, text="Load from JSON", style="Primary.TButton", command=self.load_from_json).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Clear All Data", style="Danger.TButton", command=self.clear_all_data).pack(side="left", padx=5)

        # Data display
        data_frame = ttk.LabelFrame(self.data_frame, text="Current Data (JSON)", padding="15")
        data_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        data_frame.columnconfigure(0, weight=1)
        data_frame.rowconfigure(0, weight=1)

        self.data_text = tk.Text(
            data_frame,
            height=35,
            width=120,
            wrap="word",
            font=("Consolas", 10),
            state="disabled",
            bg=self.SURFACE_COLOR,
            fg=self.TEXT_LIGHT,
            insertbackground=self.TEXT_LIGHT,
            relief="solid",
            bd=2,
            borderwidth=2,
            highlightthickness=1,
            highlightbackground=self.PRIMARY_COLOR,
        )
        self.data_text.grid(row=0, column=0, sticky="nsew")

        self.refresh_data_display()

    def refresh_data_display(self):
        """Refresh the data display."""
        data_json = json.dumps(
            {"simulations": self.dashboard.results},
            indent=2
        )
        self.data_text.config(state="normal")
        self.data_text.delete("1.0", "end")
        self.data_text.insert("1.0", data_json)
        self.data_text.config(state="disabled")

    def load_from_json(self):
        """Load data from a JSON file."""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )

        if not file_path:
            return

        try:
            self.dashboard.load_from_json(file_path)
            messagebox.showinfo("Success", f"Loaded {len(self.dashboard.results)} results from {file_path}")
            self.refresh_data_display()
            self.refresh_dashboard()
            self.update_status(f"Loaded data from {file_path}")
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load: {str(e)}")

    def clear_all_data(self):
        """Clear all simulation data."""
        if messagebox.askyesno("Confirm", "Clear all simulation data?"):
            self.dashboard = ReportingDashboard()
            self.refresh_data_display()
            self.refresh_dashboard()
            self.update_status("All data cleared")

    def load_sample_data(self):
        """Load sample data from data/simulation_data.json."""
        try:
            self.dashboard.load_from_json("data/simulation_data.json")
            self.update_status("Sample data loaded")
        except Exception:
            self.update_status("No sample data available")

    def update_status(self, message):
        """Update the status bar."""
        self.status_label.config(text=message)

    def show_quick_start(self):
        """Show a one-time startup guide."""
        if self._quick_start_shown:
            return
        self._quick_start_shown = True

        quick_text = (
            "Welcome to AgriTwin-ZM.\n\n"
            "1) Open Run Simulation and keep default values for a first run.\n"
            "2) Click Run Simulation to generate outputs.\n"
            "3) Open Dashboard to review totals and food security status.\n"
            "4) Open Policy for FRA reserve alerts.\n"
            "5) Use Data & Export to save CSV, JSON, or TXT reports."
        )
        messagebox.showinfo("Quick Start", quick_text)

    def show_help(self):
        """Show comprehensive help popup."""
        help_text = """
AGRITWIN-ZM v1.0 - USER GUIDE

RUN SIMULATION TAB
- Select Maize or Tomato from radio buttons
- Enter production, demand, and commodity parameters
- Default values are based on Zambian agricultural data
- Click "Run Simulation" to execute
- Results show storage loss, supply/demand, and revenue analysis

DASHBOARD TAB
- View all simulation results in a formatted table
- Food Security Status:
  * Secure (>80%)
  * At Risk (60-80%)
  * Crisis (<60%)
- Export to CSV, JSON, or TXT for further analysis

POLICY TAB
- Check FRA (Food Reserve Agency) reserve levels
- Default threshold: 500,000 tons
- Alerts show:
  * OK: Reserve meets minimum
  * WARNING: Reserve below threshold
  * CRITICAL: Reserve critically low
- Recommendations for export restrictions included

DATA & EXPORT TAB
- Load simulations from JSON file
- View raw simulation data in JSON format
- Clear all data with confirmation dialog
- Persistent storage for analysis

KEYBOARD TIPS
- Tab: Move between fields
- Enter: Run simulation
- Ctrl+A: Select all text (in results area)

SAMPLE DATA
Sample data is pre-loaded. Check Dashboard tab to explore.

QUESTIONS?
All commodities use real Zambian agricultural parameters:
- Maize: Monthly 3% loss typical in storage
- Tomato: 1.5% spoilage/day (cold), 4% (open storage)
- Prices in Zambian Kwacha (ZMW)
"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Help - AgriTwin-ZM")
        help_window.geometry("720x680")
        help_window.resizable(True, True)
        help_window.configure(bg=self.BG_COLOR)

        header = ttk.Label(help_window, text="User Guide", style="Title.TLabel")
        header.pack(pady=15, padx=15)

        text_area = tk.Text(
            help_window,
            wrap="word",
            font=("Consolas", 10),
            height=32,
            bg=self.SURFACE_COLOR,
            fg=self.TEXT_LIGHT,
            insertbackground=self.TEXT_LIGHT,
            relief="flat",
        )
        text_area.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        scrollbar = ttk.Scrollbar(text_area, orient="vertical", command=text_area.yview)
        scrollbar.pack(side="right", fill="y")
        text_area.config(yscrollcommand=scrollbar.set)

        text_area.insert("1.0", help_text)
        text_area.config(state="disabled")

        ttk.Button(help_window, text="Close", style="Gold.TButton", command=help_window.destroy).pack(pady=10)


def main():
    """Launch the GUI application."""
    root = tk.Tk()
    app = AgriTwinGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

