import streamlit as st
import math
import pandas as pd
import numpy as np

# Configure matplotlib for Streamlit
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Page configuration
st.set_page_config(
    page_title="Chemical Engineering Toolkit",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
<style>
    .stApp {
        background-color:  #1e1e2e;
        color: #cdd6f4;
    }
    .stButton>button {
        background-color:  #89b4fa;
        color: #1e1e2e;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px 24px;
    }
    .stButton>button:hover {
        background-color: #74c7ec;
    }
    . result-box {
        background-color: #313244;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #89b4fa;
        margin:  10px 0;
    }
    .sidebar .sidebar-content {
        background-color: #181825;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'calculation_history' not in st.session_state:
    st.session_state.calculation_history = []

# Helper functions
def add_to_history(equation_name, inputs, result):
    """Add calculation to history"""
    entry = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'equation': equation_name,
        'inputs': inputs,
        'result': result
    }
    st.session_state.calculation_history.insert(0, entry)
    if len(st.session_state. calculation_history) > 50:
        st.session_state.calculation_history = st.session_state.calculation_history[: 50]

# Equation definitions
def get_equations():
    return {
        'Reynolds Number': {
            'desc': 'Determines flow regime (laminar, transitional, turbulent)',
            'params': {
                'rho': ('Fluid Density', 'kg/m³', 1000.0),
                'v': ('Fluid Velocity', 'm/s', 1.0),
                'D': ('Pipe Diameter', 'm', 0.05),
                'mu': ('Dynamic Viscosity', 'Pa·s', 0.001)
            },
            'calc': lambda p: p['rho'] * p['v'] * p['D'] / p['mu'],
            'result_label': 'Reynolds Number',
            'result_unit': ''
        },
        'Darcy-Weisbach': {
            'desc': 'Calculates pressure drop due to friction in a pipe',
            'params': {
                'f': ('Friction Factor', '', 0.02),
                'L': ('Pipe Length', 'm', 100.0),
                'D':  ('Pipe Diameter', 'm', 0.05),
                'rho': ('Fluid Density', 'kg/m³', 1000.0),
                'v': ('Velocity', 'm/s', 2.0)
            },
            'calc': lambda p: p['f'] * (p['L']/p['D']) * (p['rho'] * p['v']**2 / 2),
            'result_label': 'Pressure Drop',
            'result_unit': 'Pa'
        },
        'Pump Power': {
            'desc':  'Calculates pump power needed for fluid transport',
            'params': {
                'rho': ('Density', 'kg/m³', 1000.0),
                'Q': ('Flow Rate', 'm³/s', 0.01),
                'H': ('Head', 'm', 10.0),
                'eff': ('Pump Efficiency', '0-1', 0.8)
            },
            'calc': lambda p: p['rho'] * 9.81 * p['Q'] * p['H'] / p['eff'],
            'result_label': 'Pump Power',
            'result_unit':  'W'
        },
        'Antoine Equation': {
            'desc': 'Gives vapor pressure of a pure component',
            'params': {
                'A': ('Coefficient A', '', 8.07131),
                'B': ('Coefficient B', '', 1730.63),
                'C': ('Coefficient C', '', 233.426),
                'T': ('Temperature', '°C', 25.0)
            },
            'calc': lambda p: 10**(p['A'] - p['B']/(p['T'] + p['C'])),
            'result_label': 'Vapor Pressure',
            'result_unit': 'mmHg'
        },
        'Batch Reactor': {
            'desc': '1st-order batch reactor concentration',
            'params': {
                'k': ('Rate Constant k', '1/s', 0.1),
                't': ('Time', 's', 10.0),
                'C0': ('Initial Concentration', 'mol/L', 1.0)
            },
            'calc':  lambda p: p['C0'] * math.exp(-p['k'] * p['t']),
            'result_label': 'Concentration',
            'result_unit':  'mol/L'
        },
        'CSTR': {
            'desc': 'Steady-state CSTR for 1st order reaction',
            'params': {
                'k': ('Rate Constant k', '1/s', 0.1),
                'tau': ('Residence Time', 's', 10.0),
                'C0': ('Feed Concentration', 'mol/L', 1.0)
            },
            'calc': lambda p: p['C0'] / (1 + p['k'] * p['tau']),
            'result_label': 'Outlet Concentration',
            'result_unit': 'mol/L'
        },
        'LMTD': {
            'desc': 'Log-Mean Temperature Difference for heat exchangers',
            'params': {
                'dT1': ('ΔT₁', 'K', 30.0),
                'dT2': ('ΔT₂', 'K', 10.0)
            },
            'calc':  lambda p: (p['dT1'] - p['dT2']) / math.log(p['dT1']/p['dT2']),
            'result_label': 'LMTD',
            'result_unit': 'K'
        },
        'Arrhenius Equation': {
            'desc':  'Temperature dependence of rate constant',
            'params': {
                'A': ('Frequency Factor A', '', 1e10),
                'Ea': ('Activation Energy', 'J/mol', 50000.0),
                'T':  ('Temperature', 'K', 298.0)
            },
            'calc': lambda p: p['A'] * math.exp(-p['Ea'] / (8.314 * p['T'])),
            'result_label':  'Rate Constant k',
            'result_unit':  ''
        }
    }

# Unit converter
def convert_units():
    st.header("🔄 Unit Converter")
    
    conversions = {
        'Temperature': {
            'units': ['°C', 'K', '°F', 'R'],
            'to_base': {
                '°C': lambda x: x + 273.15,
                'K': lambda x: x,
                '°F': lambda x: (x + 459.67) * 5/9,
                'R':  lambda x: x * 5/9
            },
            'from_base': {
                '°C': lambda x: x - 273.15,
                'K': lambda x: x,
                '°F': lambda x:  x * 9/5 - 459.67,
                'R': lambda x: x * 9/5
            }
        },
        'Pressure': {
            'units': ['Pa', 'kPa', 'bar', 'psi', 'atm', 'mmHg'],
            'to_base': {
                'Pa':  lambda x: x,
                'kPa': lambda x: x * 1000,
                'bar': lambda x: x * 100000,
                'psi': lambda x: x * 6894.76,
                'atm':  lambda x: x * 101325,
                'mmHg':  lambda x: x * 133.322
            },
            'from_base': {
                'Pa':  lambda x: x,
                'kPa': lambda x: x / 1000,
                'bar': lambda x:  x / 100000,
                'psi': lambda x: x / 6894.76,
                'atm': lambda x:  x / 101325,
                'mmHg': lambda x:  x / 133.322
            }
        },
        'Length': {
            'units': ['m', 'cm', 'mm', 'ft', 'in'],
            'to_base': {
                'm': lambda x: x,
                'cm': lambda x: x / 100,
                'mm':  lambda x: x / 1000,
                'ft': lambda x: x * 0.3048,
                'in': lambda x: x * 0.0254
            },
            'from_base': {
                'm': lambda x: x,
                'cm': lambda x: x * 100,
                'mm': lambda x: x * 1000,
                'ft': lambda x: x / 0.3048,
                'in': lambda x: x / 0.0254
            }
        },
        'Flow Rate': {
            'units':  ['m³/s', 'm³/h', 'L/min', 'L/s', 'gpm'],
            'to_base': {
                'm³/s': lambda x: x,
                'm³/h': lambda x: x / 3600,
                'L/min': lambda x: x / 60000,
                'L/s':  lambda x: x / 1000,
                'gpm': lambda x: x * 0.00006309
            },
            'from_base': {
                'm³/s': lambda x: x,
                'm³/h': lambda x: x * 3600,
                'L/min': lambda x: x * 60000,
                'L/s': lambda x: x * 1000,
                'gpm': lambda x: x / 0.00006309
            }
        }
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        category = st.selectbox("Category", list(conversions.keys()))
        from_unit = st.selectbox("From Unit", conversions[category]['units'], key='from')
        from_value = st.number_input("Value", value=0.0, format="%.6f")
    
    with col2:
        st.write("")  # Spacing
        st.write("")
        to_unit = st.selectbox("To Unit", conversions[category]['units'], key='to')
        
        if from_value: 
            base = conversions[category]['to_base'][from_unit](from_value)
            result = conversions[category]['from_base'][to_unit](base)
            
            st.markdown(f"""
            <div class="result-box">
                <h3>Result</h3>
                <h2 style="color: #89b4fa;">{result:.6f} {to_unit}</h2>
            </div>
            """, unsafe_allow_html=True)

# Main calculator
def main_calculator():
    st.header("📊 Calculator")
    
    equations = get_equations()
    
    # Equation selection
    equation_name = st.selectbox(
        "Select Equation",
        list(equations. keys()),
        help="Choose the equation you want to calculate"
    )
    
    equation = equations[equation_name]
    st.info(f"ℹ️ {equation['desc']}")
    
    # Input section
    st.subheader("Input Parameters")
    
    inputs = {}
    cols = st.columns(2)
    
    for i, (key, (label, unit, default)) in enumerate(equation['params']. items()):
        with cols[i % 2]:
            unit_str = f" ({unit})" if unit else ""
            inputs[key] = st.number_input(
                f"{label}{unit_str}",
                value=default,
                format="%.6f",
                key=f"{equation_name}_{key}"
            )
    
    # Calculate button
    if st.button("🔍 Calculate", use_container_width=True):
        try:
            result = equation['calc'](inputs)
            
            # Display result
            result_unit = f" {equation['result_unit']}" if equation['result_unit'] else ""
            
            st.markdown(f"""
            <div class="result-box">
                <h3 style="color: #a6e3a1;">✅ Result</h3>
                <h2 style="color: #89b4fa;">{equation['result_label']}:  {result:.6f}{result_unit}</h2>
            </div>
            """, unsafe_allow_html=True)
            
            # Add to history
            add_to_history(equation_name, inputs, result)
            
            st.success("✅ Calculation saved to history!")
            
        except Exception as e:
            st.error(f"❌ Calculation Error: {str(e)}")

# Parametric study
def parametric_study():
    st.header("📈 Parametric Study")
    
    equations = get_equations()
    
    # Equation selection
    equation_name = st.selectbox("Select Equation", list(equations. keys()))
    equation = equations[equation_name]
    
    st.info(f"ℹ️ {equation['desc']}")
    
    # Variable parameter
    var_param = st.selectbox(
        "Variable Parameter",
        list(equation['params'].keys()),
        format_func=lambda x: equation['params'][x][0]
    )
    
    # Range settings
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start = st.number_input("Start Value", value=0.1, format="%.6f")
    with col2:
        end = st.number_input("End Value", value=10.0, format="%.6f")
    with col3:
        steps = st.number_input("Steps", value=50, min_value=10, max_value=500)
    
    # Constant parameters
    st.subheader("Constant Parameters")
    
    const_inputs = {}
    cols = st. columns(2)
    
    for i, (key, (label, unit, default)) in enumerate(equation['params'].items()):
        if key != var_param:
            with cols[i % 2]:
                unit_str = f" ({unit})" if unit else ""
                const_inputs[key] = st. number_input(
                    f"{label}{unit_str}",
                    value=default,
                    format="%.6f",
                    key=f"param_{key}"
                )
    
    # Generate plot
    if st.button("🔍 Generate Plot", use_container_width=True):
        try:
            x_values = np.linspace(start, end, int(steps))
            y_values = []
            
            for x in x_values:
                inputs = const_inputs.copy()
                inputs[var_param] = x
                try:
                    result = equation['calc'](inputs)
                    y_values.append(result)
                except: 
                    y_values.append(np.nan)
            
            # Create plot with dark theme
            fig, ax = plt.subplots(figsize=(10, 6), facecolor='#1e1e2e')
            ax.set_facecolor('#313244')
            ax.plot(x_values, y_values, 'o-', color='#89b4fa', linewidth=2, markersize=4)
            
            var_label = equation['params'][var_param][0]
            var_unit = equation['params'][var_param][1]
            xlabel = f"{var_label} ({var_unit})" if var_unit else var_label
            
            result_unit = equation['result_unit']
            ylabel = f"{equation['result_label']} ({result_unit})" if result_unit else equation['result_label']
            
            ax. set_xlabel(xlabel, fontsize=12, color='#cdd6f4')
            ax.set_ylabel(ylabel, fontsize=12, color='#cdd6f4')
            ax.set_title(f"{equation_name} vs {var_label}", fontsize=14, color='#89b4fa')
            ax.grid(True, alpha=0.3, color='#cdd6f4')
            ax.tick_params(colors='#cdd6f4')
            
            for spine in ax.spines.values():
                spine.set_color('#cdd6f4')
            
            st.pyplot(fig)
            
            # Download data
            df = pd.DataFrame({
                var_label: x_values,
                equation['result_label']: y_values
            })
            
            csv = df.to_csv(index=False)
            st.download_button(
                "📊 Download Data (CSV)",
                csv,
                f"{equation_name}_parametric_study.csv",
                "text/csv",
                use_container_width=True
            )
            
        except Exception as e:
            st.error(f"❌ Error:  {str(e)}")

# History
def calculation_history():
    st.header("📜 Calculation History")
    
    if st.session_state.calculation_history:
        if st.button("🗑️ Clear All History"):
            st.session_state.calculation_history = []
            st.rerun()
        
        st.write(f"**Total Calculations:** {len(st.session_state.calculation_history)}")
        
        for i, entry in enumerate(st.session_state.calculation_history):
            with st.expander(f"🔢 {entry['timestamp']} - {entry['equation']}"):
                col1, col2 = st. columns(2)
                
                with col1:
                    st.write("**Inputs:**")
                    for key, value in entry['inputs'].items():
                        st.write(f"- {key}: {value}")
                
                with col2:
                    st.write("**Result:**")
                    st. markdown(f"### {entry['result']:.6f}")
    else:
        st.info("📭 No calculations yet. Start calculating in the Calculator tab!")

# Main app
def main():
    # Header
    st.title("🧪 Chemical Engineering Toolkit")
    st.caption("✨ Easy access anytime, on any device")
    
    # Sidebar navigation
    with st. sidebar:
        st.image("https://img.icons8.com/fluency/96/000000/test-tube.png", width=80)
        st.title("Navigation")
        
        page = st.radio(
            "Select a page:",
            ["📊 Calculator", "🔄 Unit Converter", "📈 Parametric Study", "📜 History"],
            label_visibility="visible"
        )
        
        st.divider()
        
        # Stats
        if st.session_state.calculation_history:
            st.metric("Total Calculations", len(st.session_state.calculation_history))
        
        st.divider()
        st.caption("Made with ❤️ for Chemical Engineers")
        st.caption(f"v1.0 | {datetime.now().year}")
    
    # Page routing
    if page == "📊 Calculator":
        main_calculator()
    elif page == "🔄 Unit Converter":
        convert_units()
    elif page == "📈 Parametric Study":
        parametric_study()
    elif page == "📜 History":
        calculation_history()

if __name__ == "__main__":
    main()