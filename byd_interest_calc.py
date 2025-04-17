import streamlit as st
st.set_page_config(page_title="คำนวณค่างวดรถ BYD | BYD ชลบุรี ออโตโมทีฟ", page_icon="🚗", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@300;400;700&display=swap');

    * {
        font-family: 'Noto Sans Thai', sans-serif !important;
    }

    html, body, div, span, input, select, button, label, textarea,
    .css-1d391kg, .css-ffhzg2, .css-1cpxqw2, .css-1offfwp, .stButton button {
        font-family: 'Noto Sans Thai', sans-serif !important;
    }
    .custom-button-wrapper {
        display: flex;
        justify-content: center;

    }
    .stButton > button.custom-button {
        background-color: #e63946;
        color: white;
        border: none;
        padding: 12px 20px;
        border-radius: 10px;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
        width: 100%;
        max-width: 320px;
        line-height: 1.3;
        transition: background-color 0.3s ease, transform 0.1s ease;
        font-family: 'Noto Sans Thai', sans-serif;
        box-shadow: 0 2px 5px rgba(0,0,0,0.08);
        white-space: pre-line;
    }
    .stButton > button.custom-button:hover {
        background-color: #d62839;
        transform: scale(1.02);
    }
    @media only screen and (max-width: 768px) {
        .stButton > button.custom-button {
            font-size: 15px;
            padding: 12px 16px;
        }
    }
    </style>
""", unsafe_allow_html=True)

import pandas as pd
import io
import re
import math
from io import StringIO
import requests

# --------- Functions ---------
def convert_google_sheet_link_to_csv(shared_link: str) -> str:
    # Converts a Google Sheet share link to a direct CSV export link
    sheet_id_match = re.search(r"/d/([a-zA-Z0-9-_]+)", shared_link)
    gid_match = re.search(r"gid=([0-9]+)", shared_link)
    if sheet_id_match:
        sheet_id = sheet_id_match.group(1)
        gid = gid_match.group(1) if gid_match else "0"  # Default to first sheet if gid not specified
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    st.warning("⚠️ Could not parse Google Sheet ID from link. Using original link.")
    return shared_link

def convert_drive_link_to_direct_image_url(shared_link: str) -> str:
    # Converts a Google Drive file share link to a direct view link
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", shared_link)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=view&id={file_id}"
    return shared_link

def read_google_sheet_csv(csv_url):
    # Reads a CSV from a URL (designed for Google Sheet export links)
    try:
        response = requests.get(csv_url)
        response.raise_for_status()  # Raise an exception for bad status codes
        csv_content = response.content.decode('utf-8')
        return pd.read_csv(StringIO(csv_content))
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Network error fetching spreadsheet: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Failed to read or parse spreadsheet: {e}")
        return pd.DataFrame()

# --------- Load data ---------
# Convert share links to direct CSV export links
car_url = convert_google_sheet_link_to_csv("https://docs.google.com/spreadsheets/d/1rypFrBiLNemhOy3Gn5_0UiC7o4zP9wDrVXafvd7TxNc/edit?gid=442434100")
car_df = read_google_sheet_csv(car_url)

down_payment_url = convert_google_sheet_link_to_csv("https://docs.google.com/spreadsheets/d/13bc_Vk1G-CDZVkCswlwYakQM-HuQMXi_K0HLG6tdVEY/edit?gid=569887943")
down_payment_df = read_google_sheet_csv(down_payment_url)

# --- Data Cleaning and Preparation ---

# Car Data
if not car_df.empty:
    if not all(col in car_df.columns for col in ["model", "sub model", "price", "image_url"]):
        st.error("❌ Car data sheet is missing required columns ('model', 'sub model', 'price', 'image_url').")
        st.stop()
    car_df['price'] = pd.to_numeric(car_df['price'], errors='coerce')
    car_df.dropna(subset=['price'], inplace=True)  # Remove rows where price isn't valid
    car_df = car_df[car_df['price'] > 0]  # Ensure price is positive
    if car_df.empty:
        st.error("❌ No valid car data found after cleaning (check prices).")
        st.stop()
else:
    st.error("❌ Failed to load car data. Cannot proceed.")
    st.stop()

# Down Payment Data
if not down_payment_df.empty:
    if not all(col in down_payment_df.columns for col in ['ดาวน์', '48', '60', '72', '84']):
         st.error("❌ Down payment data sheet is missing required columns ('ดาวน์', '48', '60', '72', '84'). Calculation might fail.")
         down_payment_df = pd.DataFrame(columns=['down_payment', '48', '60', '72', '84'])
    else:
        down_payment_df = down_payment_df[['ดาวน์', '48', '60', '72', '84']].drop_duplicates()
        down_payment_df = down_payment_df.rename(columns={'ดาวน์': 'down_payment'})
        down_payment_df['down_payment'] = down_payment_df['down_payment'].astype(str).str.replace('%', '').str.strip()
        down_payment_df['down_payment'] = pd.to_numeric(down_payment_df['down_payment'], errors='coerce')
        down_payment_df.dropna(subset=['down_payment'], inplace=True)

        for col in ['48', '60', '72', '84']:
             if col in down_payment_df.columns:
                down_payment_df[col] = down_payment_df[col].astype(str).str.replace('%', '').str.strip()
                down_payment_df[col] = pd.to_numeric(down_payment_df[col], errors='coerce')
        if down_payment_df.empty:
             st.warning("⚠️ No valid down payment percentage tiers found after cleaning.")
else:
    st.error("❌ Failed to load down payment data. Calculations will not be possible.")
    down_payment_df = pd.DataFrame(columns=['down_payment', '48', '60', '72', '84'])
    
# ✅ Session state setup
if "show_result" not in st.session_state:
    st.session_state.show_result = False

# ✅ Initialize variables before form logic
image_url_for_display = None
price = 0
input_valid = False

# ✅ Percent slider data - always defined
percent_options_raw = sorted(down_payment_df['down_payment'].unique())
percent_options = [int(x) for x in percent_options_raw if not pd.isna(x)]
default_percent = 10 if 10 in percent_options else percent_options[0]

# ✅ Image render helper
def render_image():
    global image_url_for_display
    if pd.notna(image_url_for_display) and isinstance(image_url_for_display, str) and image_url_for_display.startswith("http"):
        st.image(image_url_for_display, caption=f"{selected_model} - {selected_submodel}", use_container_width=True)
    elif price > 0:
        st.info("ℹ️ No image available for this model.")


# --------- App layout ---------
st.title("🚗 โปรแกรมคํานวณค่างวดรถ BYD (BYD Car Installment Calculator)")

# --------- Define main layout columns ---------
col_img, col_inputs = st.columns([4, 2])

# --------- Input Column ---------

with col_inputs:
    st.markdown("### 🚗 เลือกรถที่คุณสนใจ (Select Car & Options)")
    
    model_options = sorted(car_df["model"].unique())
    if 'selected_model' not in st.session_state or st.session_state.selected_model not in model_options:
         st.session_state.selected_model = model_options[0]
        
    selected_model = st.selectbox("เลือกรุ่นรถที่ต้องการ (Select Car Model)", model_options, key="selected_model")

    submodel_df = car_df[car_df["model"] == selected_model].sort_values(by="price")
    submodel_options = submodel_df["sub model"].tolist()
    selected_submodel = st.selectbox("เลือกรุ่นย่อย (Select Submodel)", submodel_options, key="selected_submodel")

    car_row = car_df[(car_df["model"] == selected_model) & (car_df["sub model"] == selected_submodel)]
    price = car_row["price"].values[0] if not car_row.empty else 0
    image_url_for_display = convert_drive_link_to_direct_image_url(car_row["image_url"].values[0]) if not car_row.empty else None

    st.metric(label="💰 ราคาจำหน่าย (Car Price)", value=f"฿{price:,.2f}")
    st.markdown("#### 💵 คำนวณค่างวด (Estimate Your Monthly Payment)")

    input_type = st.radio("เลือกรูปแบบการวางเงินดาวน์ (Select Down Payment Method)", ["จำนวนเงิน (Amount - THB)", "เปอร์เซ็นต์ (%) (Percentage)"], key="dp_type", horizontal=True)

    down_payment_amount = 0.0
    down_percent = 0.0
    input_valid = False

    if input_type == "จำนวนเงิน (Amount - THB)":
        raw_input = st.text_input("ระบุจำนวนเงินดาวน์ (Enter Your Down Payment Amount)", value=f"{price*0.1:,.0f}", key="dp_amount_thb")
        try:
            down_payment_amount = float(raw_input.replace(",", ""))
            down_percent = (down_payment_amount / price) * 100
            input_valid = 5 <= down_percent <= 100
        except ValueError:
            st.warning("⚠️ โปรดใส่เงินดาวน์ขั้นต่ำที่ 5% ของราคารถ (Please enter a down payment of at least 5% of the car price)")
    else:
        percent_options = [int(x) for x in sorted(down_payment_df['down_payment'].dropna().unique())]
        default_percent = 10 if 10 in percent_options else percent_options[0]
        selected_percent = st.select_slider("เลือกเปอร์เซ็นต์เงินดาวน์ (Select Down Payment Percentage)", options=percent_options, value=default_percent, format_func=lambda x: f"{x}%", key="dp_percent_slider")
        down_percent = float(selected_percent)
        down_payment_amount = (down_percent / 100) * price
        input_valid = True

    st.caption(f"💸 เงินดาวน์ที่เลือก : ฿{down_payment_amount:,.0f} ({int(down_percent)}%)")
    period = st.selectbox("เลือกระยะเวลาการผ่อน (เดือน) (Select your monthly payment plan)", [48, 60, 72, 84], key="period_months")
    col_center = st.columns([1, 2, 1])[1]
    with col_center:
        st.markdown("""
        <style>
        .custom-button {
            background-color: #e63946;
            color: white;
            font-weight: bold;
            border: none;
            padding: 12px 20px;
            font-size: 18px;
            border-radius: 12px;
            cursor: pointer;
            width: 100%;
            max-width: none !important;
            text-align: center;
            transition: all 0.2s ease;
            font-family: 'Noto Sans Thai', sans-serif;
            line-height: 1.4;
            display: block;
        }
        .custom-button:hover {
            background-color: #d62839;
            transform: scale(1.02);
        }
        </style>
        """, unsafe_allow_html=True)
    
        # HTML-style button inside form
        st.markdown("""
        <form method="get">
            <button type="submit" name="calculate" value="1" class="custom-button">
                🧮 คำนวณค่างวดของคุณ <br><small>(Calculate Your Payment)</small>
            </button>
        </form>
        """, unsafe_allow_html=True)
    
    # Use st.query_params correctly (no deprecated function)
    params = st.query_params
    if "calculate" in params and params["calculate"] == "1":
        st.session_state.show_result = True

    
with col_img:
    st.markdown("#### รถที่คุณเลือก (Your Selected Model)")
    if pd.notna(image_url_for_display) and isinstance(image_url_for_display, str) and image_url_for_display.startswith("http"):
        st.image(image_url_for_display, caption=f"{selected_model} - {selected_submodel}", use_container_width=True)
    elif price > 0:
        st.info("ℹ️ No image available for this model.")
    

# --------- Calculations & Results ---------
period_options = [48, 60, 72, 84]
st.markdown("---")

if st.session_state.show_result and input_valid and price > 0 and not down_payment_df.empty:

    # If the down payment equals (or exceeds) the car's price, show an info message.
    if down_payment_amount >= price:
         st.info("เงินดาวน์เท่ากับราคารถ ไม่สามารถจัดไฟแนนซ์ได้ (The down payment is equal to the car's price. No financing is required.)")
    else:
         available_percents = sorted(down_payment_df['down_payment'].unique())
         matched_percent = max([p for p in available_percents if p <= down_percent], default=None)

         # Initialize variables for the 30% plan branch
         qualified_periods_30_plan = []
         is_using_30_plan = False

         # 30% plan logic: if down payment is above 30% and a 30% tier exists
         if down_percent > 30 and 30.0 in down_payment_df['down_payment'].values:
             thirty_plan_row = down_payment_df[down_payment_df["down_payment"] == 30.0].iloc[0]
             loan_amount = price - down_payment_amount

             for p in period_options:
                 period_col = str(p)
                 if period_col in thirty_plan_row.index and pd.notna(thirty_plan_row[period_col]):
                     try:
                         interest_30 = float(thirty_plan_row[period_col])
                         interest_amount = loan_amount * (interest_30 / 100) * (p / 12)
                         if interest_amount > 25000:
                             monthly_30 = (loan_amount + interest_amount) / p
                             qualified_periods_30_plan.append({
                                "Period": f"{p} months",
                                "Interest (30% Plan Rate)": f"{interest_30:.2f}%",
                                "Monthly Installment": f"฿{monthly_30:,.2f}",
                             })
                     except (ValueError, TypeError, KeyError, ZeroDivisionError):
                         continue

             if qualified_periods_30_plan:
                is_using_30_plan = True
                df_30 = pd.DataFrame(qualified_periods_30_plan)
                df_30.insert(0, "Option", range(1, len(df_30) + 1))
                df_30.set_index("Option", inplace=True)
                st.markdown(f"""
                <div style="background-color: #e6f4ea; padding: 1rem; border-radius: 10px; border-left: 6px solid #34a853;">
                ✅ <strong>ด้วยเงินดาวน์ {down_payment_amount:,.0f} บาท ({down_percent:.2f}%)</strong> 
                แผนที่คุณเลือกไม่เข้าเงื่อนไขการจัดไฟแนนซ์ แต่ยังมีแผนผ่อนชำระระยะยาวอื่น ๆ ที่คุณสามารถเลือกได้ตามรายละเอียดด้านล่าง<br>
                <small><em>(The selected plan is not eligible for special financing rates, but alternative longer-term plans are available below.)</em></small>
                </div>
                """, unsafe_allow_html=True)
                 
                 # 🧩 Mobile-friendly style for vertical layout
                st.markdown("""
                <style>
                .financing-card {
                    border: 1px solid #e0e0e0;
                    border-radius: 10px;
                    padding: 16px;
                    margin-bottom: 12px;
                    background-color: #ffffff;
                    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
                    font-family: 'Noto Sans Thai', sans-serif;
                }
                .financing-card h4 {
                    margin: 0 0 10px;
                    font-size: 16px;
                    font-weight: 600;
                }
                .financing-card .item {
                    margin: 6px 0;
                    font-size: 14.5px;
                }
                .financing-card .item strong {
                    color: #333;
                }
                .financing-card .price {
                    font-size: 16px;
                    font-weight: bold;
                    color: #e63946;
                }
                </style>
                """, unsafe_allow_html=True)
            
                # 🪄 Render each option as a vertical card
                for i, row in df_30.reset_index().iterrows():
                    st.markdown(f"""
                    <div class="financing-card">
                        <h4>📌 Option {i + 1}</h4>
                        <div class="item">📅 <strong>ระยะเวลาผ่อน:</strong> {row['Period']}</div>
                        <div class="item">📈 <strong>อัตราดอกเบี้ย:</strong> {row['Interest (30% Plan Rate)']}</div>
                        <div class="item price">💳 ยอดผ่อนรายเดือน: {row['Monthly Installment']} / เดือน</div>
                    </div>
                    """, unsafe_allow_html=True)
             else:
                st.markdown("""
                <div style="background-color:#fff3cd; padding: 16px; border-left: 6px solid #ffeeba; border-radius: 4px;">
                😕 <strong>ไม่มีแผนผ่อนชำระที่เข้าเงื่อนไข</strong> เนื่องจากดอกเบี้ยที่คำนวณไม่ถึงเกณฑ์ขั้นต่ำที่กำหนด  
                โปรดลองลดจำนวนเงินดาวน์ลง เพื่อดูตัวเลือกแผนผ่อนชำระอื่น ๆ  
                <br><br><small>(There are no qualifying installment plans because the calculated interest does not meet the minimum required threshold.  
                Please try lowering your down payment to view other available financing options.)</small>
                </div>
                """, unsafe_allow_html=True)


             # Since the 30% branch applies, skip showing the regular financing result.
             st.stop()

         # Regular (under 30%) scheme (only if 30% branch is not taken)
         if matched_percent is not None:
             interest_row = down_payment_df[down_payment_df['down_payment'] == matched_percent]
             if not interest_row.empty:
                 period_col = str(period)
                 if period_col in interest_row.columns and pd.notna(interest_row[period_col].values[0]):
                     try:
                         interest_rate = float(interest_row[period_col].values[0])
                         loan_amount = price - down_payment_amount
                         total_interest = loan_amount * (interest_rate / 100) * (period / 12)
                         monthly_installment = (loan_amount + total_interest) / period

                         st.markdown("### 📊 สรุปการผ่อนชำระ (Installment Summary)")
                         res_col1, res_col2, res_col3 = st.columns(3)
                         rounded_down_payment = math.ceil(down_payment_amount)
                         res_col1.metric("เงินดาวน์ที่เลือก (Your Down Payment)", f"฿{rounded_down_payment:,.0f} ({int(down_percent)}%)")
                         res_col2.metric("อัตราดอกเบี้ย (Interest Rate Applied)", f"{interest_rate:.2f}%", help=f"Based on the nearest qualifying tier: {int(matched_percent)}%")
                         rounded_monthly = math.ceil(monthly_installment)
                         res_col3.metric("ยอดผ่อนรายเดือน (Monthly Installment)", f"฿{rounded_monthly:,.0f} /เดือน")

                     except (ValueError, TypeError, ZeroDivisionError) as e:
                         st.error(f"⚠️ Error calculating installment for {period} months: {e}")
                 else:
                     st.error(f"⚠️ Interest rate data is missing or invalid for {matched_percent:.1f}% down payment and {period} months period.")
             else:
                 st.error(f"❌ No interest rate data found for the qualifying tier: {matched_percent:.1f}%.")
         else:
             st.error("❌ No financing options available for the provided down payment percentage.")
elif not input_valid:
    st.markdown("""
    <div style="background-color:#f8d7da; padding: 16px; border-left: 6px solid #f5c6cb; border-radius: 4px;">
    ❌ <strong>โปรดใส่เงินดาวน์ขั้นต่ำที่ 5% ของราคารถ</strong><br>
    <small>(Please enter a down payment of at least 5% of the car price)</small>
    </div>
    """, unsafe_allow_html=True)
elif price <= 0:
    st.info("ℹ️ Please select a valid car with a price > 0.")
elif down_payment_df.empty:
    st.error("❌ Cannot perform calculations because the down payment interest rate data is missing or invalid.")

# PDF Section remains commented out
# ... (rest of the PDF code if needed) ...
