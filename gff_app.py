import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ---------------- PAGE CONFIG (Mobile Friendly) ----------------
st.set_page_config(page_title="GFF Pro Calc", layout="wide", page_icon="🏭")

# Custom CSS for Better Mobile UI
st.markdown("""
    <style>
    .stApp {background-color: #f8f9fa;}
    div.stButton > button:first-child {
        background-color: #0d6efd; color: white; border-radius: 10px; 
        height: 3em; width: 100%; font-weight: bold; font-size: 18px;
    }
    div[data-testid="stMetricValue"] {font-size: 24px; color: #1f77b4;}
    .big-font {font-size:20px !important; font-weight: bold;}
    .success-box {padding:15px; background-color:#d1e7dd; color:#0f5132; border-radius:10px; margin-bottom:10px;}
    </style>
""", unsafe_allow_html=True)

# ---------------- DEFAULT DATA ----------------
if 'ing_df' not in st.session_state:
    # Initialize Data only once
    data = [
        {"Item": "Palm Oil", "%": 43.0, "Rate": 120.0, "GST": 5.0, "Type": "Oil"},
        {"Item": "Water", "%": 0.0, "Rate": 0.01, "GST": 0.0, "Type": "Water"}, # Auto calc
        {"Item": "MDP", "%": 1.0, "Rate": 50.0, "GST": 5.0, "Type": "Oil"},
        {"Item": "Salt", "%": 3.7, "Rate": 5.0, "GST": 0.0, "Type": "Water"},
        {"Item": "DMG", "%": 0.3, "Rate": 155.0, "GST": 18.0, "Type": "Oil"},
        {"Item": "Soya Leci", "%": 0.3, "Rate": 85.0, "GST": 18.0, "Type": "Oil"},
        {"Item": "PGPR", "%": 0.3, "Rate": 290.0, "GST": 18.0, "Type": "Oil"},
        {"Item": "CA", "%": 0.15, "Rate": 65.0, "GST": 18.0, "Type": "Water"},
        {"Item": "SC", "%": 0.1, "Rate": 83.0, "GST": 18.0, "Type": "Water"},
        {"Item": "PS", "%": 0.1, "Rate": 230.0, "GST": 18.0, "Type": "Water"},
        {"Item": "SB", "%": 0.1, "Rate": 95.0, "GST": 18.0, "Type": "Water"},
        {"Item": "EDTA", "%": 0.02, "Rate": 270.0, "GST": 18.0, "Type": "Water"},
        {"Item": "Starch", "%": 0.001, "Rate": 50.0, "GST": 18.0, "Type": "Water"},
        {"Item": "Flav", "%": 0.01, "Rate": 600.0, "GST": 18.0, "Type": "Oil"},
        {"Item": "B-Carotin", "%": 0.001, "Rate": 4800.0, "GST": 18.0, "Type": "Oil"},
    ]
    st.session_state.ing_df = pd.DataFrame(data)

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("⚙️ Batch Settings")
    batch_no = st.text_input("Batch No", "GFF-B-001")
    batch_size = st.number_input("Batch Size (kg)", value=2700.0, step=100.0)
    st.divider()
    overhead_pct = st.slider("Overhead %", 0.0, 5.0, 1.0, 0.1)
    misc_total = st.number_input("Misc (Labour+Elec) / Box", value=150.0)

# ---------------- MAIN APP (TABS) ----------------
st.title("🏭 GFF Pro Costing")
tab1, tab2, tab3 = st.tabs(["🧪 Mixer (Ingredients)", "📦 Packaging", "📊 Final Report"])

# --- TAB 1: INGREDIENTS (Excel Style) ---
with tab1:
    st.caption("Edit Percentage (%) and Rates below. Water is calculated automatically.")
    
    # Logic to balance Water
    df = st.session_state.ing_df
    current_sum = df.loc[df["Item"] != "Water", "%"].sum()
    water_bal = max(0.0, 100.0 - current_sum)
    
    # Update Water row in display
    df.loc[df["Item"] == "Water", "%"] = water_bal
    
    # Display Editable Table
    edited_df = st.data_editor(
        df,
        column_config={
            "%": st.column_config.NumberColumn(format="%.3f %%"),
            "Rate": st.column_config.NumberColumn(format="₹ %.2f"),
            "GST": st.column_config.NumberColumn(format="%.1f %%"),
        },
        disabled=["Item", "Type"], # Prevent changing names
        hide_index=True,
        use_container_width=True,
        height=500
    )
    
    # Store changes back to session state so they persist across tabs
    if not edited_df.equals(st.session_state.ing_df):
        st.session_state.ing_df = edited_df
        st.rerun()

    # Show Balance
    col1, col2 = st.columns(2)
    col1.metric("Total Solids", f"{current_sum:.2f}%")
    col2.metric("Water Balance", f"{water_bal:.2f}%")
    if current_sum > 100:
        st.error("⚠️ Total Percentage > 100%! Please reduce ingredients.")

# --- TAB 2: PACKAGING ---
with tab2:
    st.caption("Enter Rates (Basic Rate). GST is added automatically.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🧈 Wrapper")
        cost_butter = st.number_input("Butter Paper (₹/kg)", value=148.0)
        gst_butter = 18.0
        
        st.markdown("### 📦 Inner Box")
        cost_mono = st.number_input("Mono Carton (₹/pc)", value=1.50)
        gst_mono = 5.0
        
    with col2:
        st.markdown("### 📦 Outer Box")
        cost_outer = st.number_input("Outer Carton (₹/box)", value=25.0)
        gst_outer = 5.0
        
        st.markdown("### 🎗️ Tape")
        cost_tape = st.number_input("Tape (₹/box)", value=2.0)
        gst_tape = 18.0

# --- TAB 3: REPORT ---
with tab3:
    if st.button("🚀 CALCULATE FINAL COST"):
        
        # 1. Calc Ingredients
        final_df = st.session_state.ing_df.copy()
        
        # Ensure water is updated
        c_sum = final_df.loc[final_df["Item"] != "Water", "%"].sum()
        final_df.loc[final_df["Item"] == "Water", "%"] = max(0.0, 100.0 - c_sum)
        
        # Math
        final_df["Kg"] = (final_df["%"] / 100) * batch_size
        final_df["Basic"] = final_df["Kg"] * final_df["Rate"]
        final_df["Tax"] = final_df["Basic"] * (final_df["GST"] / 100)
        final_df["Total"] = final_df["Basic"] + final_df["Tax"]
        
        total_ing_cost = final_df["Total"].sum()
        ing_cpk = total_ing_cost / batch_size
        
        # Phase Splits
        oil_cost = final_df[final_df["Type"]=="Oil"]["Total"].sum()
        water_cost = final_df[final_df["Type"]=="Water"]["Total"].sum()

        # 2. Calc Packaging
        # Rates with GST
        r_butter = cost_butter * (1 + gst_butter/100)
        r_mono = cost_mono * (1 + gst_mono/100)
        r_outer = cost_outer * (1 + gst_outer/100)
        r_tape = cost_tape * (1 + gst_tape/100)
        
        # Scenario A (15kg)
        prod_val = ing_cpk * 15.0
        pack_val_A = (0.075 * r_butter) + (30 * r_mono) + r_outer + r_tape + misc_total
        oh_val = prod_val * (overhead_pct/100)
        box_A_total = prod_val + pack_val_A + oh_val
        
        # Scenario B (16kg)
        prod_val_B = ing_cpk * 16.0
        pack_val_B = (0.250 * r_butter) + (32 * r_mono) + r_outer + r_tape + misc_total
        oh_val_B = prod_val_B * (overhead_pct/100)
        box_B_total = prod_val_B + pack_val_B + oh_val_B
        
        # Batch Totals
        total_boxes = batch_size / 15.0
        total_pack_exp = total_boxes * pack_val_A
        grand_total = total_ing_cost + total_pack_exp + (total_ing_cost * overhead_pct/100)
        final_cpk = grand_total / batch_size
        
        # --- DISPLAY UI ---
        
        # 1. Main Highlights
        st.markdown(f"""
        <div class="success-box">
            <h2 style="margin:0; text-align:center;">Final Cost: ₹ {final_cpk:.2f} / kg</h2>
            <p style="margin:0; text-align:center;">Grand Total: ₹ {grand_total:,.0f}</p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Ingredients", f"₹ {ing_cpk:.2f}/kg")
        c2.metric("15kg Box", f"₹ {box_A_total:.2f}")
        c3.metric("16kg Box", f"₹ {box_B_total:.2f}")
        
        # 2. Charts (Visual Appeal)
        st.divider()
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("#### Cost Breakup")
            # Donut Chart
            cost_data = pd.DataFrame({
                "Category": ["Oil Phase", "Water Phase", "Packaging", "Overhead"],
                "Amount": [oil_cost, water_cost, total_pack_exp, (total_ing_cost * overhead_pct/100)]
            })
            fig = px.pie(cost_data, values='Amount', names='Category', hole=0.4)
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250)
            st.plotly_chart(fig, use_container_width=True)
            
        with col_chart2:
            st.markdown("#### Phase Analysis")
            st.info(f"🛢️ Oil Phase: ₹ {oil_cost:,.0f}")
            st.success(f"💧 Water Phase: ₹ {water_cost:,.0f}")
        
        # 3. Detailed Data
        with st.expander("📄 See Detailed Breakdown"):
            st.dataframe(final_df[["Item", "Kg", "Total"]], use_container_width=True)
            
            report_txt = f"""
            BATCH: {batch_no} ({batch_size} kg)
            --------------------------
            Ing Cost: {total_ing_cost:,.2f}
            Pack Cost: {total_pack_exp:,.2f}
            Final Total: {grand_total:,.2f}
            FINAL CPK: {final_cpk:.2f}
            """
            st.download_button("Download Text Report", report_txt, file_name="report.txt")

    else:
        st.info("👈 Go to tabs and click Calculate")
