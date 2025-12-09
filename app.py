import streamlit as st
import math
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os

# Use Plotly for plotting (works better on Streamlit Cloud)
import plotly.graph_objects as go
import plotly.express as px

# Page config
st.set_page_config(
    page_title="Chemical Engineering Toolkit",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background-color:  #1e1e2e;
        color: #cdd6f4;
    }
    .stButton>button {
        background-color: #89b4fa;
        color:   #1e1e2e;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px 24px;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #74c7ec;
    }
    . result-box {
        background-color: #313244;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #89b4fa;
        margin: 10px 0;
    }
    .equation-card {
        background-color: #313244;
        padding: 15px;
        border-radius:  8px;
        border-left: 4px solid #89b4fa;
        margin:  10px 0;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        color: #89b4fa;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'calculation_history' not in st.session_state:
    st.session_state.calculation_history = []
if 'templates' not in st.session_state:
    st.session_state.templates = {}

# Add to history
def add_to_history(equation_name, inputs, result):
    entry = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'equation': equation_name,
        'inputs': inputs,
        'result': result
    }
    st.session_state.calculation_history.insert(0, entry)
    if len(st.session_state. calculation_history) > 50: 
        st.session_state.calculation_history = st.session_state.calculation_history[: 50]

# Complete equation definitions (ALL 20)
def get_equations():
    return {
        'Reynolds Number': {
            'desc': 'Determines flow regime (laminar, transitional, turbulent)',
            'formula': 'Re = ρvD/μ',
            'params': {
                'rho': ('Fluid Density', 'kg/m³', 1000.0),
                'v': ('Fluid Velocity', 'm/s', 1.0),
                'D':  ('Pipe Diameter', 'm', 0.05),
                'mu': ('Dynamic Viscosity', 'Pa·s', 0.001)
            },
            'calc': lambda p:  p['rho'] * p['v'] * p['D'] / p['mu'],
            'result_label': 'Reynolds Number',
            'result_unit': ''
        },
        'Darcy-Weisbach':  {
            'desc': 'Calculates pressure drop due to friction in a pipe',
            'formula': 'ΔP = f(L/D)(ρv²/2)',
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
            'desc': 'Calculates pump power needed for fluid transport',
            'formula': 'P = ρgQH/η',
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
            'formula': 'log₁₀(P) = A - B/(C+T)',
            'params':  {
                'A': ('Coefficient A', '', 8.07131),
                'B': ('Coefficient B', '', 1730.63),
                'C': ('Coefficient C', '', 233.426),
                'T': ('Temperature', '°C', 25.0)
            },
            'calc': lambda p: 10**(p['A'] - p['B']/(p['T'] + p['C'])),
            'result_label': 'Vapor Pressure',
            'result_unit': 'mmHg'
        },
        'Batch Reactor (1st Order)': {
            'desc': '1st-order batch reactor concentration over time',
            'formula': 'C = C₀e^(-kt)',
            'params':  {
                'C0': ('Initial Concentration', 'mol/L', 1.0),
                'k':  ('Rate Constant', '1/s', 0.1),
                't': ('Time', 's', 10.0)
            },
            'calc': lambda p: p['C0'] * math.exp(-p['k'] * p['t']),
            'result_label': 'Concentration',
            'result_unit': 'mol/L'
        },
        'CSTR (1st Order)': {
            'desc': 'Steady-state CSTR for 1st order reaction',
            'formula': 'C = C₀/(1+kτ)',
            'params': {
                'C0': ('Feed Concentration', 'mol/L', 1.0),
                'k': ('Rate Constant', '1/s', 0.1),
                'tau': ('Residence Time', 's', 10.0)
            },
            'calc': lambda p: p['C0'] / (1 + p['k'] * p['tau']),
            'result_label': 'Outlet Concentration',
            'result_unit': 'mol/L'
        },
        'LMTD':  {
            'desc': 'Log-Mean Temperature Difference for heat exchangers',
            'formula': 'LMTD = (ΔT₁-ΔT₂)/ln(ΔT₁/ΔT₂)',
            'params': {
                'dT1': ('ΔT₁ (Hot in - Cold out)', 'K', 30.0),
                'dT2': ('ΔT₂ (Hot out - Cold in)', 'K', 10.0)
            },
            'calc':  lambda p: (p['dT1'] - p['dT2']) / math.log(p['dT1']/p['dT2']) if p['dT1'] > 0 and p['dT2'] > 0 else 0,
            'result_label': 'LMTD',
            'result_unit': 'K'
        },
        'Arrhenius Equation': {
            'desc': 'Temperature dependence of rate constant',
            'formula': 'k = Ae^(-Ea/RT)',
            'params': {
                'A': ('Frequency Factor', '1/s', 1e10),
                'Ea': ('Activation Energy', 'J/mol', 50000.0),
                'T': ('Temperature', 'K', 298.0)
            },
            'calc': lambda p: p['A'] * math.exp(-p['Ea'] / (8.314 * p['T'])),
            'result_label':  'Rate Constant',
            'result_unit': '1/s'
        },
        'Hagen-Poiseuille': {
            'desc': 'Laminar flow pressure drop in circular pipe',
            'formula': 'ΔP = 32μLv/D²',
            'params': {
                'mu': ('Dynamic Viscosity', 'Pa·s', 0.001),
                'L': ('Pipe Length', 'm', 100.0),
                'v': ('Average Velocity', 'm/s', 1.0),
                'D': ('Pipe Diameter', 'm', 0.05)
            },
            'calc':  lambda p: 32 * p['mu'] * p['L'] * p['v'] / (p['D']**2),
            'result_label': 'Pressure Drop',
            'result_unit': 'Pa'
        },
        'Bernoulli Equation': {
            'desc':  'Energy conservation in fluid flow',
            'formula': 'P₁/ρg + v₁²/2g + z₁ = P₂/ρg + v₂²/2g + z₂',
            'params': {
                'P1':  ('Pressure 1', 'Pa', 200000.0),
                'v1': ('Velocity 1', 'm/s', 2.0),
                'z1': ('Height 1', 'm', 10.0),
                'rho':  ('Density', 'kg/m³', 1000.0),
                'v2': ('Velocity 2', 'm/s', 5.0),
                'z2': ('Height 2', 'm', 5.0)
            },
            'calc': lambda p: p['P1']/(p['rho']*9.81) + p['v1']**2/(2*9.81) + p['z1'] - p['v2']**2/(2*9.81) - p['z2'],
            'result_label':  'Pressure Head 2',
            'result_unit':  'm'
        },
        'Ideal Gas Law': {
            'desc': 'Equation of state for ideal gases',
            'formula': 'PV = nRT',
            'params': {
                'P': ('Pressure', 'Pa', 101325.0),
                'V': ('Volume', 'm³', 0.0224),
                'n': ('Moles', 'mol', 1.0),
                'T': ('Temperature', 'K', 273.15)
            },
            'calc': lambda p: p['P'] * p['V'] / (p['n'] * p['T']),
            'result_label': 'Gas Constant R',
            'result_unit':  'J/(mol·K)'
        },
        'Ergun Equation': {
            'desc': 'Pressure drop in packed bed',
            'formula': 'ΔP/L = 150μv(1-ε)²/(ε³Dp²) + 1.75ρv²(1-ε)/(ε³Dp)',
            'params': {
                'mu': ('Viscosity', 'Pa·s', 0.001),
                'v': ('Superficial Velocity', 'm/s', 0.1),
                'epsilon': ('Void Fraction', '', 0.4),
                'Dp': ('Particle Diameter', 'm', 0.001),
                'rho': ('Density', 'kg/m³', 1000.0),
                'L': ('Bed Length', 'm', 1.0)
            },
            'calc': lambda p: p['L'] * (150*p['mu']*p['v']*(1-p['epsilon'])**2/(p['epsilon']**3*p['Dp']**2) + 1.75*p['rho']*p['v']**2*(1-p['epsilon'])/(p['epsilon']**3*p['Dp'])),
            'result_label': 'Pressure Drop',
            'result_unit': 'Pa'
        },
        'Heat Exchanger (NTU)': {
            'desc': 'Number of Transfer Units method',
            'formula': 'NTU = UA/(mCp)min',
            'params': {
                'U': ('Overall Heat Transfer Coeff', 'W/(m²·K)', 500.0),
                'A':  ('Heat Transfer Area', 'm²', 10.0),
                'm': ('Mass Flow Rate (min)', 'kg/s', 1.0),
                'Cp': ('Specific Heat (min)', 'J/(kg·K)', 4180.0)
            },
            'calc': lambda p: p['U'] * p['A'] / (p['m'] * p['Cp']),
            'result_label': 'NTU',
            'result_unit': ''
        },
        'Fanning Equation': {
            'desc': 'Pressure drop using Fanning friction factor',
            'formula': 'ΔP = 4f(L/D)(ρv²/2)',
            'params': {
                'f':  ('Fanning Friction Factor', '', 0.005),
                'L': ('Pipe Length', 'm', 100.0),
                'D':  ('Diameter', 'm', 0.05),
                'rho': ('Density', 'kg/m³', 1000.0),
                'v': ('Velocity', 'm/s', 2.0)
            },
            'calc': lambda p: 4 * p['f'] * (p['L']/p['D']) * (p['rho'] * p['v']**2 / 2),
            'result_label': 'Pressure Drop',
            'result_unit': 'Pa'
        },
        'Continuity Equation': {
            'desc': 'Mass conservation in pipe flow',
            'formula': 'A₁v₁ = A₂v₂',
            'params':  {
                'D1': ('Diameter 1', 'm', 0.1),
                'v1': ('Velocity 1', 'm/s', 2.0),
                'D2': ('Diameter 2', 'm', 0.05)
            },
            'calc':  lambda p: (math.pi * p['D1']**2 / 4) * p['v1'] / (math.pi * p['D2']**2 / 4),
            'result_label': 'Velocity 2',
            'result_unit': 'm/s'
        },
        'Clausius-Clapeyron':  {
            'desc': 'Vapor pressure vs temperature relationship',
            'formula':  'ln(P₂/P₁) = -ΔHvap/R(1/T₂ - 1/T₁)',
            'params': {
                'P1': ('Pressure 1', 'Pa', 101325.0),
                'T1': ('Temperature 1', 'K', 373.15),
                'T2': ('Temperature 2', 'K', 298.15),
                'dHvap': ('Heat of Vaporization', 'J/mol', 40660.0)
            },
            'calc': lambda p: p['P1'] * math.exp(-p['dHvap']/8.314 * (1/p['T2'] - 1/p['T1'])),
            'result_label': 'Pressure 2',
            'result_unit': 'Pa'
        },
        'Raoult\'s Law': {
            'desc': 'Vapor pressure of ideal solution',
            'formula': 'P = x₁P₁° + x₂P₂°',
            'params': {
                'x1': ('Mole Fraction 1', '', 0.5),
                'P1': ('Vapor Pressure 1', 'Pa', 3000.0),
                'x2': ('Mole Fraction 2', '', 0.5),
                'P2': ('Vapor Pressure 2', 'Pa', 2000.0)
            },
            'calc':  lambda p: p['x1'] * p['P1'] + p['x2'] * p['P2'],
            'result_label': 'Total Vapor Pressure',
            'result_unit': 'Pa'
        },
        'Graham\'s Law': {
            'desc': 'Effusion and diffusion rates of gases',
            'formula': 'r₁/r₂ = √(M₂/M₁)',
            'params': {
                'M1': ('Molar Mass 1', 'g/mol', 2.0),
                'M2': ('Molar Mass 2', 'g/mol', 32.0),
                'r1': ('Rate 1', 'mol/s', 1.0)
            },
            'calc':  lambda p: p['r1'] * math.sqrt(p['M2']/p['M1']),
            'result_label': 'Rate 1 (relative)',
            'result_unit':  'relative to rate 2'
        },
        'Fick\'s First Law': {
            'desc':  'Diffusion flux in steady state',
            'formula': 'J = -D(dC/dx)',
            'params':  {
                'D': ('Diffusion Coefficient', 'm²/s', 1e-9),
                'C1': ('Concentration 1', 'mol/m³', 100.0),
                'C2': ('Concentration 2', 'mol/m³', 0.0),
                'dx': ('Distance', 'm', 0.001)
            },
            'calc': lambda p: -p['D'] * (p['C2'] - p['C1']) / p['dx'],
            'result_label': 'Diffusion Flux',
            'result_unit': 'mol/(m²·s)'
        },
        'Packed Bed Height': {
            'desc': 'Height of packed column for separation',
            'formula': 'Z = HTU × NTU',
            'params': {
                'HTU': ('Height of Transfer Unit', 'm', 0.5),
                'NTU':  ('Number of Transfer Units', '', 5.0)
            },
            'calc': lambda p: p['HTU'] * p['NTU'],
            'result_label': 'Column Height',
            'result_unit': 'm'
        }
    }

# Unit converter
def unit_converter_page():
    st.header("🔄 Unit Converter")
    
    conversions = {
        'Temperature': {
            'units': ['°C', 'K', '°F', 'R'],
            'to_base': {
                '°C': lambda x: x + 273.15,
                'K': lambda x: x,
                '°F': lambda x:  (x + 459.67) * 5/9,
                'R': lambda x: x * 5/9
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
                'Pa': lambda x: x,
                'kPa': lambda x: x * 1000,
                'bar': lambda x: x * 100000,
                'psi':  lambda x: x * 6894.76,
                'atm': lambda x: x * 101325,
                'mmHg': lambda x: x * 133.322
            },
            'from_base': {
                'Pa': lambda x: x,
                'kPa': lambda x: x / 1000,
                'bar': lambda x: x / 100000,
                'psi':  lambda x: x / 6894.76,
                'atm': lambda x: x / 101325,
                'mmHg': lambda x: x / 133.322
            }
        },
        'Length': {
            'units': ['m', 'cm', 'mm', 'ft', 'in', 'km'],
            'to_base':  {
                'm': lambda x:  x,
                'cm': lambda x: x / 100,
                'mm':  lambda x: x / 1000,
                'ft': lambda x: x * 0.3048,
                'in': lambda x: x * 0.0254,
                'km': lambda x: x * 1000
            },
            'from_base': {
                'm':  lambda x: x,
                'cm': lambda x: x * 100,
                'mm': lambda x: x * 1000,
                'ft': lambda x: x / 0.3048,
                'in': lambda x: x / 0.0254,
                'km': lambda x: x / 1000
            }
        },
        'Flow Rate': {
            'units':  ['m³/s', 'm³/h', 'L/min', 'L/s', 'gpm', 'ft³/min'],
            'to_base': {
                'm³/s': lambda x: x,
                'm³/h': lambda x: x / 3600,
                'L/min': lambda x: x / 60000,
                'L/s':  lambda x: x / 1000,
                'gpm': lambda x: x * 0.00006309,
                'ft³/min': lambda x: x * 0.000471947
            },
            'from_base': {
                'm³/s': lambda x: x,
                'm³/h': lambda x: x * 3600,
                'L/min': lambda x: x * 60000,
                'L/s': lambda x: x * 1000,
                'gpm': lambda x: x / 0.00006309,
                'ft³/min': lambda x: x / 0.000471947
            }
        },
        'Mass':  {
            'units': ['kg', 'g', 'mg', 'lb', 'oz', 'ton'],
            'to_base':  {
                'kg': lambda x: x,
                'g':  lambda x: x / 1000,
                'mg': lambda x: x / 1000000,
                'lb':  lambda x: x * 0.453592,
                'oz':  lambda x: x * 0.0283495,
                'ton': lambda x: x * 1000
            },
            'from_base': {
                'kg': lambda x: x,
                'g': lambda x: x * 1000,
                'mg': lambda x: x * 1000000,
                'lb':  lambda x: x / 0.453592,
                'oz':  lambda x: x / 0.0283495,
                'ton': lambda x: x / 1000
            }
        },
        'Energy': {
            'units': ['J', 'kJ', 'cal', 'kcal', 'BTU', 'kWh'],
            'to_base': {
                'J':  lambda x: x,
                'kJ': lambda x: x * 1000,
                'cal': lambda x: x * 4.184,
                'kcal': lambda x: x * 4184,
                'BTU': lambda x: x * 1055.06,
                'kWh': lambda x: x * 3600000
            },
            'from_base': {
                'J': lambda x: x,
                'kJ': lambda x: x / 1000,
                'cal': lambda x: x / 4.184,
                'kcal': lambda x: x / 4184,
                'BTU': lambda x: x / 1055.06,
                'kWh': lambda x: x / 3600000
            }
        }
    }
    
    col1, col2 = st. columns(2)
    
    with col1:
        category = st.selectbox("Category", list(conversions.keys()))
        from_unit = st.selectbox("From Unit", conversions[category]['units'], key='from')
        from_value = st.number_input("Value", value=0.0, format="%.6f")
    
    with col2:
        st.write("")
        st.write("")
        to_unit = st.selectbox("To Unit", conversions[category]['units'], key='to')
        
        if from_value: 
            base = conversions[category]['to_base'][from_unit](from_value)
            result = conversions[category]['from_base'][to_unit](base)
            
            st.markdown(f"""
            <div class="result-box">
                <h3>Result</h3>
                <h2 style="color: #89b4fa;">{result:. 6f} {to_unit}</h2>
            </div>
            """, unsafe_allow_html=True)

# Main calculator
def calculator_page():
    st.header("📊 Calculator")
    
    equations = get_equations()
    
    # Search equations
    search = st.text_input("🔍 Search equations", "")
    
    # Filter equations
    if search:
        filtered_eqs = {k: v for k, v in equations.items() if search.lower() in k.lower() or search.lower() in v['desc'].lower()}
    else:
        filtered_eqs = equations
    
    # Equation selection
    equation_name = st.selectbox(
        f"Select Equation ({len(filtered_eqs)} available)",
        list(filtered_eqs.keys()),
        help="Choose the equation you want to calculate"
    )
    
    equation = filtered_eqs[equation_name]
    
    # Display equation info
    st.markdown(f"""
    <div class="equation-card">
        <h4>📐 {equation_name}</h4>
        <p>{equation['desc']}</p>
        <p><strong>Formula:</strong> <code>{equation['formula']}</code></p>
    </div>
    """, unsafe_allow_html=True)
    
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
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
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
    
    with col2:
        if st.button("💾 Save as Template", use_container_width=True):
            st.session_state['show_save_template'] = True
    
    with col3:
        if st. button("🔄 Reset", use_container_width=True):
            st.rerun()
    
    # Template saving dialog
    if st.session_state.get('show_save_template', False):
        with st.form("save_template_form"):
            template_name = st.text_input("Template name:")
            submit = st.form_submit_button("Save Template")
            
            if submit and template_name:
                st.session_state. templates[template_name] = {
                    'equation': equation_name,
                    'inputs':  inputs,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.success(f"✅ Saved as '{template_name}'!")
                st.session_state['show_save_template'] = False

# Parametric study
def parametric_study_page():
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
    cols = st.columns(2)
    
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
            
            # Create interactive Plotly plot
            var_label = equation['params'][var_param][0]
            var_unit = equation['params'][var_param][1]
            xlabel = f"{var_label} ({var_unit})" if var_unit else var_label
            
            result_unit = equation['result_unit']
            ylabel = f"{equation['result_label']} ({result_unit})" if result_unit else equation['result_label']
            
            fig = go.Figure()
            fig.add_trace(go. Scatter(
                x=x_values,
                y=y_values,
                mode='lines+markers',
                line=dict(color='#89b4fa', width=2),
                marker=dict(size=6, color='#89b4fa'),
                name=equation_name
            ))
            
            fig.update_layout(
                title=f"{equation_name} vs {var_label}",
                xaxis_title=xlabel,
                yaxis_title=ylabel,
                plot_bgcolor='#313244',
                paper_bgcolor='#1e1e2e',
                font=dict(color='#cdd6f4', size=12),
                xaxis=dict(gridcolor='#45475a', showgrid=True),
                yaxis=dict(gridcolor='#45475a', showgrid=True),
                height=500,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
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

# Templates page
def templates_page():
    st.header("📋 Templates")
    
    if st.session_state.templates:
        # Search
        search = st.text_input("🔍 Search templates", "")
        
        # Filter templates
        filtered = {k: v for k, v in st.session_state. templates.items() 
                   if search.lower() in k.lower()}
        
        st.write(f"**{len(filtered)} templates found**")
        
        # Display templates
        for name, template in filtered.items():
            with st.expander(f"📌 {name}"):
                st.write(f"**Equation:** {template['equation']}")
                st.write(f"**Created:** {template. get('timestamp', 'Unknown')}")
                st.write("**Parameters:**")
                
                for key, value in template['inputs'].items():
                    st.write(f"  • {key} = {value}")
                
                col1, col2 = st. columns(2)
                with col1:
                    if st.button(f"🔄 Load", key=f"load_{name}"):
                        st.info(f"Template '{name}' loaded!  Go to Calculator tab.")
                
                with col2:
                    if st.button(f"🗑️ Delete", key=f"del_{name}"):
                        del st.session_state.templates[name]
                        st.rerun()
    else:
        st.info("📭 No templates saved yet. Create one in the Calculator tab!")

# History page
def history_page():
    st.header("📜 Calculation History")
    
    if st.session_state.calculation_history:
        col1, col2 = st. columns([3, 1])
        
        with col1:
            st.write(f"**Total Calculations:** {len(st. session_state.calculation_history)}")
        
        with col2:
            if st.button("🗑️ Clear All"):
                st.session_state. calculation_history = []
                st.rerun()
        
        # Export history
        if st.button("📥 Export History (CSV)"):
            history_data = []
            for entry in st.session_state.calculation_history:
                row = {
                    'Timestamp': entry['timestamp'],
                    'Equation': entry['equation'],
                    'Result': entry['result']
                }
                for key, value in entry['inputs'].items():
                    row[key] = value
                history_data.append(row)
            
            df = pd.DataFrame(history_data)
            csv = df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                "calculation_history.csv",
                "text/csv"
            )
        
        st.divider()
        
        # Display history
        for i, entry in enumerate(st. session_state.calculation_history):
            with st.expander(f"🔢 {entry['timestamp']} - {entry['equation']}"):
                col1, col2 = st. columns(2)
                
                with col1:
                    st.write("**Inputs:**")
                    for key, value in entry['inputs'].items():
                        st.write(f"  • {key} = {value}")
                
                with col2:
                    st.write("**Result:**")
                    st.markdown(f"### {entry['result']:.6f}")
    else:
        st.info("📭 No calculations yet. Start calculating in the Calculator tab!")

# Main app
def main():
    # Header
    st.title("🧪 Chemical Engineering Toolkit")
    st.caption("✨ 20 Equations | Unit Converter | Parametric Studies | Access Anywhere")
    
    # Sidebar navigation
    with st.sidebar:
        st. image("https://img.icons8.com/fluency/96/000000/test-tube. png", width=80)
        st.title("Navigation")
        
        page = st.radio(
            "Select a page:",
            ["📊 Calculator", "🔄 Unit Converter", "📈 Parametric Study", 
             "📋 Templates", "📜 History"],
            label_visibility="visible"
        )
        
        st.divider()
        
        # Stats
        col1, col2 = st. columns(2)
        with col1:
            st.metric("Equations", "20")
        with col2:
            st.metric("Calculations", len(st.session_state.calculation_history))
        
        st.divider()
        st.caption("Made with ❤️ for Chemical Engineers")
        st.caption(f"v2.0 | {datetime.now().year}")
    
    # Page routing
    if page == "📊 Calculator":
        calculator_page()
    elif page == "🔄 Unit Converter": 
        unit_converter_page()
    elif page == "📈 Parametric Study":
        parametric_study_page()
    elif page == "📋 Templates":
        templates_page()
    elif page == "📜 History":
        history_page()

if __name__ == "__main__":
    main()