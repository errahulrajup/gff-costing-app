import streamlit as st
import pandas as pd
from datetime import datetime
import io

# ---------------- CONFIGURATION ----------------
st.set_page_config(page_title="GFF Costing Pro", layout="wide")

# Hide Streamlit Style (Optional)
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Data Structures
INGREDIENTS_CONFIG = [
    {"name":"Palm Oil","default_pct":43.0,"default_rate":120.0,"gst":5.0,"auto":False},
    {"name":"MDP","default_pct":1.0,"default_rate":50.0,"gst":5.0,"auto":False},
    {"name":"Water","default_pct":50.0,"default_rate":0.01,"gst":0.0,"auto":True},
    {"name":"Salt","default_pct":3.7,"default_rate":5.0,"gst":0.0,"auto":False},
    {"name":"DMG","default_pct":0.3,"default_rate":155.0,"gst":18.0,"auto":False},
    {"name":"Soya Leci","default_pct":0.3,"default_rate":85.0,"gst":18.0,"auto":False},
    {"name":"PGPR","default_pct":0.3,"default_rate":290.0,"gst":18.0,"auto":False},
    {"name":"CA","default_pct":0.15,"default_rate":65.0,"gst":18.0,"auto":False},
    {"name":"SC","default_pct":0.1,"default_rate":83.0,"gst":18.0,"auto":False},
    {"name":"PS","default_pct":0.1,"default_rate":230.0,"gst":18.0,"auto":False},
    {"name":"SB","default_pct":0.1,"default_rate":95.0,"gst":18.0,"auto":False},
    {"name":"EDTA","default_pct":0.02,"default_rate":270.0,"gst":18.0,"auto":False},
    {"name":"Starch","default_pct":0.001,"default_rate":50.0,"gst":18.0,"auto":False},
    {"name":"Flav","default_pct":0.01,"default_rate":600.0,"gst":18.0,"auto":False},
    {"name":"B-Carotin","default_pct":0.001,"default_rate":4800.0,"gst":18.0,"auto":False},
]

PACKING_ITEMS = [
    {"name":"Butter Paper (₹/kg)", "cost":148.0, "gst":18.0, "key":"but"},
    {"name":"Mono Carton (₹/pc)",  "cost":1.50,  "gst":5.0,  "key":"mono"},
    {"name":"Outer Carton (₹/box)","cost":25.0,  "gst":5.0,  "key":"out"},
    {"name":"Tape (₹/box)",        "cost":2.0,   "gst":18.0, "key":"tape"},
]

# ---------------- UI LAYOUT ----------------
st.title("🏭 GFF Costing Dashboard")

# Initialize Session State for Ingredients if not exists
if 'ing_data' not in st.session_state:
    st.session_state['ing_data'] = INGREDIENTS_CONFIG

# --- SIDEBAR (Batch Info) ---
with st.sidebar:
    st.header("Batch Details")
    batch_no = st.text_input("Batch No", value="GFF-B-001")
    batch_size = st.number_input("Batch Size (kg)", value=2700.0, step=100.0)
    
    st.header("Overhead & Misc")
    overhead_pct = st.number_input("Overhead %", value=1.0)
    misc_labour = st.number_input("Labour (₹/box)", value=40.0)
    misc_elec = st.number_input("Electricity (₹/box)", value=30.0)
    misc_trans = st.number_input("Transport (₹/box)", value=80.0)
    misc_total = misc_labour + misc_elec + misc_trans
    st.info(f"Total Misc: ₹{misc_total}/box")

# --- MAIN FORM ---
with st.form("calc_form"):
    
    # 1. INGREDIENTS SECTION
    st.subheader("1. Ingredients Mixer")
    
    # Create columns for header
    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
    c1.markdown("**Item**")
    c2.markdown("**% (Percentage)**")
    c3.markdown("**Rate (₹/kg)**")
    c4.markdown("**GST %**")
    
    user_inputs = []
    
    # Loop through ingredients
    for i, ing in enumerate(INGREDIENTS_CONFIG):
        c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
        with c1:
            st.write(f"{ing['name']}")
        with c2:
            if ing['auto']:
                # Water calculation placeholder
                st.write("🌊 Auto (Bal)")
                val_pct = 0.0 # Will calc later
            else:
                val_pct = st.number_input(f"pct_{i}", value=ing['default_pct'], label_visibility="collapsed", step=0.1)
        with c3:
            val_rate = st.number_input(f"rate_{i}", value=ing['default_rate'], label_visibility="collapsed")
        with c4:
            val_gst = st.number_input(f"gst_{i}", value=ing['gst'], label_visibility="collapsed")
            
        user_inputs.append({"name":ing['name'], "pct":val_pct, "rate":val_rate, "gst":val_gst, "auto":ing['auto']})

    # 2. PACKAGING SECTION
    st.subheader("2. Packaging Rates")
    
    pack_inputs = {}
    cols = st.columns(2)
    for i, p in enumerate(PACKING_ITEMS):
        with cols[i % 2]:
            c_cost = st.number_input(f"{p['name']}", value=p['cost'])
            c_gst = st.number_input(f"GST% ({p['name']})", value=p['gst'])
            # Rate with GST
            rate_final = c_cost * (1 + c_gst/100)
            pack_inputs[p['name']] = rate_final
            st.caption(f"Rate incl GST: ₹{rate_final:.2f}")

    submitted = st.form_submit_button("🚀 CALCULATE COST", type="primary")

# ---------------- CALCULATION LOGIC ----------------
if submitted:
    # 1. Calculate Water %
    fixed_sum = sum(i['pct'] for i in user_inputs if not i['auto'])
    water_pct = max(0.0, 100.0 - fixed_sum)
    
    # Update Water in list
    for i in user_inputs:
        if i['auto']:
            i['pct'] = water_pct
            
    # 2. Calculate Ingredient Costs
    g_basic = 0.0
    g_total = 0.0
    
    oil_phase = 0.0
    water_phase = 0.0
    oil_phase_names = ["palm", "dmg", "pgpr", "soya", "mdp", "flav", "b-carotin"]
    
    calc_data = []
    
    for item in user_inputs:
        kg = (item['pct'] / 100.0) * batch_size
        basic_amt = kg * item['rate']
        gst_amt = basic_amt * (item['gst'] / 100.0)
        total_amt = basic_amt + gst_amt
        
        g_basic += basic_amt
        g_total += total_amt
        
        # Phase Calc
        if any(x in item['name'].lower() for x in oil_phase_names):
            oil_phase += total_amt
        else:
            water_phase += total_amt
            
        calc_data.append([item['name'], item['pct'], kg, item['rate'], total_amt])

    ing_cost_per_kg = g_total / batch_size
    
    # 3. Packaging Scenarios
    # Rate Fetching
    r_butter = pack_inputs.get("Butter Paper (₹/kg)", 0)
    r_mono = pack_inputs.get("Mono Carton (₹/pc)", 0)
    r_outer = pack_inputs.get("Outer Carton (₹/box)", 0)
    r_tape = pack_inputs.get("Tape (₹/box)", 0)
    
    # Function to calc box
    def calc_box(box_kg, butter_w_kg, mono_pcs):
        prod_cost = ing_cost_per_kg * box_kg
        pack_cost = (butter_w_kg * r_butter) + (mono_pcs * r_mono) + r_outer + r_tape + misc_total
        oh_cost = prod_cost * (overhead_pct / 100.0)
        final_box = prod_cost + pack_cost + oh_cost
        return final_box, final_box/mono_pcs, pack_cost
        
    # Scenario A (15kg)
    boxA_tot, boxA_pc, boxA_pack = calc_box(15.0, 0.075, 30)
    # Scenario B (16kg)
    boxB_tot, boxB_pc, boxB_pack = calc_box(16.0, 0.250, 32)
    
    # Final Batch Projection (Based on A)
    boxes_needed = batch_size / 15.0
    total_pack_batch = boxes_needed * boxA_pack
    grand_total = g_total + total_pack_batch + (g_total * overhead_pct/100)
    final_cpk = grand_total / batch_size
    
    # ---------------- DISPLAY RESULTS ----------------
    st.divider()
    st.subheader("📊 Result Report")
    
    # Key Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Final Cost / Kg", f"₹ {final_cpk:.2f}")
    m2.metric("Batch Total", f"₹ {grand_total:,.0f}")
    m3.metric("Ing Cost / Kg", f"₹ {ing_cost_per_kg:.2f}")
    
    # Phase Analysis
    st.success(f"🛢️ Oil Phase: ₹{oil_phase:,.0f} | 💧 Water Phase: ₹{water_phase:,.0f}")
    
    # Packaging Table
    st.write("📦 **Packaging Scenarios**")
    pack_df = pd.DataFrame([
        {"Type": "15kg Box (30pc)", "Rules": "75g Paper", "Box Cost": f"₹{boxA_tot:.2f}", "Per Pc": f"₹{boxA_pc:.2f}"},
        {"Type": "16kg Box (32pc)", "Rules": "250g Paper", "Box Cost": f"₹{boxB_tot:.2f}", "Per Pc": f"₹{boxB_pc:.2f}"},
    ])
    st.table(pack_df)
    
    # Detailed Ingredient Table (Expander)
    with st.expander("View Detailed Ingredient List"):
        df_ing = pd.DataFrame(calc_data, columns=["Item", "%", "Kg", "Rate", "Total Amount"])
        st.dataframe(df_ing)
        
    # ---------------- DOWNLOAD REPORT ----------------
    # Create text report for download
    report_text = f"""
    GFF COSTING REPORT
    Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
    Batch: {batch_no} | Size: {batch_size} kg
    -------------------------------------------
    INGREDIENTS TOTAL: ₹ {g_total:,.2f}
    (Oil: ₹{oil_phase:,.0f} | Water: ₹{water_phase:,.0f})
    
    PACKAGING (15kg Box Scenario):
    - 75g Butter Paper, 30 Mono, 1 Outer, 1 Tape + Misc
    - Packaging Cost per Batch: ₹ {total_pack_batch:,.2f}
    
    FINAL TOTALS:
    -------------------------------------------
    GRAND TOTAL:     ₹ {grand_total:,.2f}
    FINAL COST / KG: ₹ {final_cpk:.2f}
    -------------------------------------------
    Generated via GFF Mobile App
    """
    
    st.download_button(
        label="📥 Download Report (Text)",
        data=report_text,
        file_name=f"{batch_no}_report.txt",
        mime="text/plain"
    )