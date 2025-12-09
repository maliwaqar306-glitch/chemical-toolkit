import streamlit as st
import math
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Chemical Engineering Toolkit",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 Chemical Engineering Toolkit")
st.caption("✨ Easy access anytime, on any device")

st.header("📊 Reynolds Number Calculator")

col1, col2 = st.columns(2)

with col1:
    rho = st.number_input("Density (kg/m³)", value=1000.0)
    v = st.number_input("Velocity (m/s)", value=1.0)

with col2:
    D = st.number_input("Diameter (m)", value=0.05)
    mu = st.number_input("Viscosity (Pa·s)", value=0.001)

if st.button("Calculate", use_container_width=True):
    Re = (rho * v * D) / mu
    
    st.markdown(f"""
    <div style="background-color: #313244; padding: 20px; border-radius: 10px; border: 2px solid #89b4fa; margin: 10px 0;">
        <h3 style="color: #a6e3a1;">✅ Result</h3>
        <h2 style="color: #89b4fa;">Reynolds Number = {Re:.2f}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    if Re < 2300:
        st.info("🌊 Flow Regime: **LAMINAR** (Re < 2300)")
    elif Re < 4000:
        st.warning("🔄 Flow Regime: **TRANSITIONAL** (2300 < Re < 4000)")
    else:
        st.error("💨 Flow Regime: **TURBULENT** (Re > 4000)")

st.divider()

st.subheader("📚 More Equations Coming Soon")
st.write("- Darcy-Weisbach Equation")
st.write("- Pump Power Calculation")
st.write("- Antoine Equation")
st.write("- Batch Reactor")
st.write("- CSTR")

st.divider()
st.caption("Made with ❤️ for Chemical Engineers | v1.0")