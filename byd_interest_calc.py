import streamlit as st
st.set_page_config(page_title="Car Calculator", page_icon="🚗", layout="wide")

import pandas as pd
import io
import re
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

# --------- App layout ---------
st.title("🚗 Car Down Payment & Installment Calculator")

# --------- Define main layout columns ---------
col_img, col_inputs = st.columns([4, 2])

# --------- Input Column ---------
with col_inputs:
    st.markdown("### Select Car & Options")

    # --- Car Selection ---
    model_options = sorted(car_df["model"].unique())
    if 'selected_model' not in st.session_state or st.session_state.selected_model not in model_options:
         st.session_state.selected_model = model_options[0]

    selected_model = st.selectbox(
        "Select Car Model",
        model_options,
        key="selected_model",
    )

    submodel_options = sorted(car_df[car_df["model"] == selected_model]["sub model"].unique())
    if not submodel_options:
        st.error(f"No submodels found for {selected_model}. Please check the data.")
        st.stop()

    if 'selected_submodel' not in st.session_state or st.session_state.selected_submodel not in submodel_options:
        st.session_state.selected_submodel = submodel_options[0]

    try:
        submodel_index = submodel_options.index(st.session_state.selected_submodel)
    except ValueError:
        st.session_state.selected_submodel = submodel_options[0]
        submodel_index = 0

    selected_submodel = st.selectbox(
        "Select Submodel",
        submodel_options,
        key="selected_submodel",
        index=submodel_index
    )

    # --- Get Data Based on Selections ---
    car_row = car_df[(car_df["model"] == selected_model) & (car_df["sub model"] == selected_submodel)]

    if not car_row.empty:
        price = car_row["price"].values[0]
        image_url_for_display = car_row["image_url"].values[0]
        if pd.notna(image_url_for_display) and isinstance(image_url_for_display, str) and "drive.google.com" in image_url_for_display:
             image_url_for_display = convert_drive_link_to_direct_image_url(image_url_for_display)
    else:
        st.error(f"Could not find data for {selected_model} - {selected_submodel}. Using default price 0.")
        price = 0
        image_url_for_display = None

    # --- Display Price ---
    st.metric(label="💰 Car Price", value=f"฿{price:,.2f}")
    st.markdown("---")

    # --- Down Payment & Installment Options ---
    st.markdown("#### 💸 Down Payment & Installment")

    input_type = st.radio("Down Payment Input Type", ("Amount (THB)", "Percentage (%)"), key="dp_type", horizontal=True)

    down_payment_amount = 0.0
    down_percent = 0.0
    input_valid = False

    if price > 0:
        if input_type == "Amount (THB)":
            raw_input = st.text_input("Enter Down Payment Amount (THB)", value=f"{price*0.1:,.0f}", key="dp_amount_thb")
            try:
                down_payment_amount = float(raw_input.replace(",", ""))
                down_percent = (down_payment_amount / price) * 100
                min_down_required = price * 0.05

                if down_payment_amount < min_down_required:
                    st.warning(f"🚫 Minimum 5% down payment required (฿{min_down_required:,.2f})")
                elif down_payment_amount > price:
                    st.warning(f"🚫 Down payment cannot exceed car price (฿{price:,.2f})")
                else:
                    input_valid = True
            except ValueError:
                st.warning("⚠️ Please enter a valid number for the down payment amount.")
        else:
            if not down_payment_df.empty and 'down_payment' in down_payment_df.columns:
                 options = sorted(down_payment_df['down_payment'].unique())
                 default_ix = options.index(10.0) if 10.0 in options else (options.index(15.0) if 15.0 in options else 0)
                 down_percent = st.selectbox("Select Down Payment Percentage", options, index=default_ix, key="dp_percent", format_func=lambda x: f"{x:.1f}%")
                 down_payment_amount = (down_percent / 100) * price
                 input_valid = True
            else:
                st.warning("⚠️ Down payment percentage options not available.")

        if input_valid:
             st.caption(f"Selected Down Payment: ฿{down_payment_amount:,.2f} ({down_percent:.2f}%)")
        elif not input_valid and input_type == "Amount (THB)":
             st.caption("Enter a valid amount above the minimum required.")
    else:
         st.error("Cannot calculate down payment as car price is invalid.")

    period_options = [48, 60, 72, 84]
    period = st.selectbox("Select Installment Period (months)", period_options, key="period_months")

# --------- Image Column ---------
with col_img:
    st.markdown("#### Selected Car")
    if pd.notna(image_url_for_display) and isinstance(image_url_for_display, str) and image_url_for_display.startswith("http"):
        st.image(image_url_for_display, caption=f"{selected_model} - {selected_submodel}", use_container_width=True)
    elif price > 0:
        st.info("ℹ️ No image available for this model.")

# --------- Calculations & Results ---------
st.markdown("---")

if input_valid and price > 0 and not down_payment_df.empty:
    # If the down payment equals (or exceeds) the car's price, show an info message.
    if down_payment_amount >= price:
         st.info("The down payment is equal to the car's price. No financing is required.")
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
                 st.success(f"✅ With {down_percent:.2f}% down payment, you qualify for these 30% plan options (minimum interest condition met):")
                 st.table(df_30)
             else:
                 st.warning("No periods qualify for the 30% plan because the calculated interest does not exceed the minimum threshold for any period.")
             
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

                         st.markdown("### 📊 Down and Installment Payment Result")
                         res_col1, res_col2, res_col3 = st.columns(3)
                         res_col1.metric("Down Payment", f"฿{down_payment_amount:,.2f} ({down_percent:.2f}%)")
                         res_col2.metric("Interest Rate Applied", f"{interest_rate:.2f}%", help=f"Based on the nearest qualifying tier: {matched_percent:.1f}%")
                         res_col3.metric("Monthly Installment", f"฿{monthly_installment:,.2f}")
                     except (ValueError, TypeError, ZeroDivisionError) as e:
                         st.error(f"⚠️ Error calculating installment for {period} months: {e}")
                 else:
                     st.error(f"⚠️ Interest rate data is missing or invalid for {matched_percent:.1f}% down payment and {period} months period.")
             else:
                 st.error(f"❌ No interest rate data found for the qualifying tier: {matched_percent:.1f}%.")
         else:
             st.error("❌ No financing options available for the provided down payment percentage.")
elif not input_valid:
    st.info("ℹ️ Please provide valid down payment details above to see calculations.")
elif price <= 0:
    st.info("ℹ️ Please select a valid car with a price > 0.")
elif down_payment_df.empty:
    st.error("❌ Cannot perform calculations because the down payment interest rate data is missing or invalid.")
else:
    st.error("An unexpected state occurred. Please check inputs and data sources.")

# PDF Section remains commented out
# ... (rest of the PDF code if needed) ...
