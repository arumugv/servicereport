import streamlit as st
from fpdf import FPDF
from datetime import datetime
import pandas as pd
import tempfile
import os


# 1. PDF Class Definition
class ServiceReportPDF(FPDF):
    def __init__(self, logo_path=None):
        super().__init__()
        self.logo_path = logo_path

    def header(self):
        # Use the physical file path of the temporary logo
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                self.image(self.logo_path, x=10, y=8, w=30)
                self.set_x(45)
            except Exception as e:
                st.error(f"Logo placement error: {e}")

        self.set_font('Arial', 'B', 15)
        self.cell(0, 8, 'PIE PTE LTD', ln=True)
        self.set_font('Arial', '', 8)
        if self.logo_path: self.set_x(45)
        self.cell(0, 4, 'UEN: 201634529C', ln=True)
        if self.logo_path: self.set_x(45)
        self.cell(0, 4, 'Address: 1 North Bridge Road, #B1-05A High Street Centre S 179094', ln=True)
        if self.logo_path: self.set_x(45)
        self.cell(0, 4, 'Email: Brian@piesgservice.com | Hp: 92331569', ln=True)
        self.ln(5)
        self.set_draw_color(0, 0, 0)
        self.line(10, 35, 200, 35)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')


# 2. PDF Generation Logic
def generate_report(data, personnel_df, ra_values, logo_file):
    temp_logo_path = None

    # PERMANENT FIX: Save the uploaded logo to a temporary physical file
    if logo_file:
        suffix = "." + logo_file.name.split('.')[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(logo_file.getvalue())
            temp_logo_path = tmp.name

    try:
        pdf = ServiceReportPDF(logo_path=temp_logo_path)
        pdf.add_page()

        # Title
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'SERVICE REPORT / DOCKET', ln=True, align='C')
        pdf.ln(5)

        # Job Details
        pdf.set_font('Arial', 'B', 9)
        fields = [
            ("Report No:", str(data.get('report_no', '')), "Date:", str(data.get('date', ''))),
            ("Customer:", str(data.get('customer', '')), "Requestor:", str(data.get('requestor', ''))),
            ("Location:", str(data.get('location', '')), "Contact:", str(data.get('contact', '')))
        ]
        for l1, v1, l2, v2 in fields:
            pdf.set_font('Arial', 'B', 9);
            pdf.cell(30, 7, l1)
            pdf.set_font('Arial', '', 9);
            pdf.cell(60, 7, v1, border='B')
            pdf.set_font('Arial', 'B', 9);
            pdf.cell(30, 7, l2)
            pdf.set_font('Arial', '', 9);
            pdf.cell(60, 7, v2, border='B', ln=True)
        pdf.ln(5)

        # Work Description
        pdf.set_font('Arial', 'B', 10);
        pdf.cell(0, 8, 'Scope of Work / Description of Tasks', ln=True)
        pdf.set_font('Arial', '', 9);
        pdf.multi_cell(0, 5, str(data.get('work_description', '')), border=1)
        pdf.ln(5)

        # Personnel Table
        pdf.set_font('Arial', 'B', 10);
        pdf.cell(0, 8, 'Personnel / Hours', ln=True)
        headers = ['Date', 'Name', 'From', 'To', 'Hrs', 'Remarks']
        widths = [25, 45, 20, 20, 15, 65]
        pdf.set_fill_color(240, 240, 240)
        for i, h in enumerate(headers):
            pdf.cell(widths[i], 8, h, border=1, fill=True, align='C')
        pdf.ln()

        pdf.set_font('Arial', '', 8)
        total_hrs = 0.0
        for _, row in personnel_df.iterrows():
            pdf.cell(widths[0], 7, str(row['Date']), border=1)
            pdf.cell(widths[1], 7, str(row['Name']), border=1)
            pdf.cell(widths[2], 7, str(row['From']), border=1)
            pdf.cell(widths[3], 7, str(row['To']), border=1)
            pdf.cell(widths[4], 7, str(row['Hrs']), border=1)
            pdf.cell(widths[5], 7, str(row['Remarks']), border=1, ln=True)
            try:
                total_hrs += float(row['Hrs'])
            except:
                pass

        # Total Hours Summary Row
        pdf.set_font('Arial', 'B', 8)
        pdf.cell(sum(widths[:4]), 7, "TOTAL MAN-HOURS", border=1, align='R')
        pdf.cell(widths[4], 7, f"{total_hrs:.1f}", border=1, align='C')
        pdf.cell(widths[5], 7, "", border=1, ln=True)
        pdf.ln(10)

        # --- 3 SIGNATURES SECTION ---
        # 1. Service Personnel
        pdf.set_font('Arial', 'B', 9);
        pdf.cell(0, 5, "Service Personnel", ln=True);
        pdf.ln(12)
        pdf.set_font('Arial', '', 8);
        pdf.cell(95, 5, "____________________________________", ln=True)
        pdf.cell(95, 5, "Name / Designation / Date", ln=True);
        pdf.ln(8)

        # Row 2: Supervisor & Client
        start_y = pdf.get_y()
        pdf.set_font('Arial', 'B', 9);
        pdf.text(10, start_y + 5, "Supervisor / In-charge")
        pdf.line(10, start_y + 25, 90, start_y + 25)
        pdf.set_font('Arial', '', 8);
        pdf.text(10, start_y + 30, "Signature & Date")

        pdf.set_xy(105, start_y)
        pdf.set_font('Arial', 'B', 9);
        pdf.cell(95, 5, "CLIENT'S APPROVAL OF WORK", ln=True)
        pdf.set_font('Arial', 'I', 7);
        pdf.set_x(105)
        pdf.multi_cell(95, 3.5,
                       "This work has been completed to my satisfaction and I agree to accept the resulting charges. We confirm that the above had been carried out to our satisfaction.")
        pdf.line(105, start_y + 25, 195, start_y + 25)
        pdf.set_font('Arial', '', 8);
        pdf.set_xy(105, start_y + 26)
        pdf.cell(95, 5, "Signature & Co Stamp / Date", align='L')

        pdf_out = pdf.output(dest='S')
        return pdf_out if isinstance(pdf_out, bytes) else pdf_out.encode('latin-1')

    finally:
        # Cleanup: Remove the temporary file after PDF is generated
        if temp_logo_path and os.path.exists(temp_logo_path):
            os.remove(temp_logo_path)


# 3. Streamlit UI (Kept the same logic for inputs)
st.set_page_config(page_title="PIE Service Report", layout="wide")
st.title("📋 Service Report & Docket Generator")

with st.sidebar:
    st.header("Settings")
    uploaded_logo = st.file_uploader("Upload Company Logo", type=["png", "jpg", "jpeg"])

with st.expander("📝 1. Job Information", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        report_no = st.text_input("Service Report / Docket No.", "SR-04983")
        customer = st.text_input("Customer", "Concord")
        requestor = st.text_input("Requestor", "Mr. Meyyappan")
    with col2:
        date = st.date_input("Date", datetime.now())
        location = st.text_input("Location / Site Address", "810 22kv / RTS Woodlands Station")
        contact = st.text_input("Contact No.", "9066 5191")
    work_desc = st.text_area("Scope of Work / Work Done", "Attendance for site acceptance test")

with st.expander("🛡️ 2. Site Specific Risk Assessment"):
    ra_items = ["Helmet", "Safety Shoes", "Safety Vest", "Hand Gloves", "Goggles", "Harness", "Face Mask"]
    ra_cols = st.columns(len(ra_items))
    ra_values = {item: ra_cols[i].checkbox(item, key=f"ra_{item}") for i, item in enumerate(ra_items)}

with st.expander("👥 3. Personnel & Attendance"):
    if 'rows' not in st.session_state:
        st.session_state.rows = [
            {"Date": str(date), "Name": "Chua Ju Jin", "From": "1000", "To": "1700", "Hrs": "7.0", "Remarks": ""}]


    def add_row():
        st.session_state.rows.append({"Date": str(date), "Name": "", "From": "", "To": "", "Hrs": "0.0", "Remarks": ""})


    for i, row in enumerate(st.session_state.rows):
        c1, c2, c3, c4, c5, c6 = st.columns([1.5, 3, 1, 1, 1, 3])
        st.session_state.rows[i]['Date'] = c1.text_input("Date", row['Date'], key=f"date_{i}")
        st.session_state.rows[i]['Name'] = c2.text_input("Name", row['Name'], key=f"name_{i}")

        t_from = c3.text_input("From", row['From'], key=f"from_{i}")
        t_to = c4.text_input("To", row['To'], key=f"to_{i}")

        calc_hrs = row['Hrs']
        try:
            if len(t_from) == 4 and len(t_to) == 4:
                dt1 = datetime.strptime(t_from, "%H%M")
                dt2 = datetime.strptime(t_to, "%H%M")
                calc_hrs = str(round((dt2 - dt1).total_seconds() / 3600, 1))
        except:
            pass

        st.session_state.rows[i]['From'] = t_from
        st.session_state.rows[i]['To'] = t_to
        st.session_state.rows[i]['Hrs'] = c5.text_input("Hrs", calc_hrs, key=f"hrs_{i}")
        st.session_state.rows[i]['Remarks'] = c6.text_input("Remarks", row['Remarks'], key=f"rem_{i}")
    st.button("➕ Add Personnel Row", on_click=add_row)

if st.button("🚀 Generate PDF Service Report"):
    try:
        job_data = {"report_no": report_no, "customer": customer, "requestor": requestor, "date": date,
                    "location": location, "contact": contact, "work_description": work_desc}
        pdf_bytes = generate_report(job_data, pd.DataFrame(st.session_state.rows), ra_values, uploaded_logo)
        st.download_button(label="📥 Download PDF", data=pdf_bytes, file_name=f"Report_{report_no}.pdf",
                           mime="application/pdf")
    except Exception as e:
        st.error(f"Error: {e}")