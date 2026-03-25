import streamlit as st
from fpdf import FPDF
from datetime import datetime
import pandas as pd
import io


# 1. PDF Class Definition
class ServiceReportPDF(FPDF):
    def __init__(self, logo_data=None):
        super().__init__()
        self.logo_data = logo_data

    def header(self):
        if self.logo_data:
            try:
                # Reset the file pointer to the beginning of the file
                self.logo_data.seek(0)

                # Read the bytes from the UploadedFile object
                img_bytes = self.logo_data.read()

                # Get the file extension (e.g., 'jpg', 'png')
                file_ext = self.logo_data.name.split('.')[-1].lower()
                if file_ext == 'jpeg': file_ext = 'jpg'

                # Use io.BytesIO to wrap the bytes for FPDF
                img_stream = io.BytesIO(img_bytes)

                # Specify the 'type' so FPDF knows how to process the stream
                self.image(img_stream, x=10, y=8, w=30, type=file_ext)
                self.set_x(45)
            except Exception as e:
                # If logo fails, we print error to console but let the PDF continue
                print(f"Logo error: {e}")

        self.set_font('Arial', 'B', 15)
        self.cell(0, 8, 'PIE PTE LTD', ln=True)
        self.set_font('Arial', '', 8)
        if self.logo_data: self.set_x(45)
        self.cell(0, 4, 'UEN: 201634529C', ln=True)
        if self.logo_data: self.set_x(45)
        self.cell(0, 4, 'Address: 1 North Bridge Road, #B1-05A High Street Centre S 179094', ln=True)
        if self.logo_data: self.set_x(45)
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
    pdf = ServiceReportPDF(logo_data=logo_file)
    pdf.add_page()

    # Title
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'SERVICE REPORT / DOCKET', ln=True, align='C')
    pdf.ln(5)

    # Job Details Section
    pdf.set_font('Arial', 'B', 9)
    fields = [
        ("Report No:", str(data.get('report_no', '')), "Date:", str(data.get('date', ''))),
        ("Customer:", str(data.get('customer', '')), "Requestor:", str(data.get('requestor', ''))),
        ("Location:", str(data.get('location', '')), "Contact:", str(data.get('contact', '')))
    ]

    for label1, val1, label2, val2 in fields:
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(30, 7, label1)
        pdf.set_font('Arial', '', 9)
        pdf.cell(60, 7, val1, border='B')
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(30, 7, label2)
        pdf.set_font('Arial', '', 9)
        pdf.cell(60, 7, val2, border='B', ln=True)
    pdf.ln(5)

    # Risk Assessment
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 8, 'SITE SPECIFIC RISK ASSESSMENT', ln=True)
    pdf.set_font('Arial', '', 8)
    items = list(ra_values.items())
    for i in range(0, len(items), 4):
        chunk = items[i:i + 4]
        for key, val in chunk:
            status = "[X]" if val else "[ ]"
            pdf.cell(45, 6, f"{status} {key}")
        pdf.ln()
    pdf.ln(5)

    # Scope of Work
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 8, 'Scope of Work / Description of Tasks', ln=True)
    pdf.set_font('Arial', '', 9)
    pdf.multi_cell(0, 5, str(data.get('work_description', '')), border=1)
    pdf.ln(5)

    # Personnel Attendance Table
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 8, 'Personnel / Hours', ln=True)

    pdf.set_font('Arial', 'B', 9)
    pdf.set_fill_color(240, 240, 240)
    headers = ['Date', 'Name of Personnel', 'From', 'To', 'Hrs', 'Remarks']
    widths = [20, 50, 20, 20, 15, 65]
    for i, h in enumerate(headers):
        pdf.cell(widths[i], 8, h, border=1, fill=True, align='C')
    pdf.ln()

    pdf.set_font('Arial', '', 8)
    for _, row in personnel_df.iterrows():
        pdf.cell(widths[0], 7, str(row.get('Date', '')), border=1)
        pdf.cell(widths[1], 7, str(row.get('Name', '')), border=1)
        pdf.cell(widths[2], 7, str(row.get('From', '')), border=1)
        pdf.cell(widths[3], 7, str(row.get('To', '')), border=1)
        pdf.cell(widths[4], 7, str(row.get('Hrs', '')), border=1)
        pdf.cell(widths[5], 7, str(row.get('Remarks', '')), border=1, ln=True)
    pdf.ln(8)

    # --- UPDATED SIGNATURE AREA (3-PERSON LAYOUT) ---
    curr_y = pdf.get_y()

    # 1. Service Personnel
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 5, "Service Personnel", ln=True)
    pdf.ln(10)
    pdf.set_font('Arial', '', 8)
    pdf.cell(95, 5, "____________________________________", ln=True)
    pdf.cell(95, 5, "Name / Designation / Date", ln=True)
    pdf.ln(5)

    # 2. Supervisor & 3. Client (Side by Side)
    start_y_row2 = pdf.get_y()

    # Left: Supervisor
    pdf.set_font('Arial', 'B', 9)
    pdf.text(10, start_y_row2 + 5, "ELECTRICIAN / TECHNICIAN")
    pdf.line(10, start_y_row2 + 25, 90, start_y_row2 + 25)
    pdf.set_font('Arial', '', 8)
    pdf.text(10, start_y_row2 + 30, "Signature & Date")

    # Right: Client Approval
    pdf.set_font('Arial', 'B', 9)
    pdf.set_xy(105, start_y_row2)
    pdf.cell(95, 5, "CLIENT'S APPROVAL OF WORK", ln=True)
    pdf.set_font('Arial', 'I', 7)
    pdf.set_x(105)
    disclaimer = "This work has been completed to my satisfaction and I agree to accept the resulting charges. We confirm that the above had been carried out to our satisfaction."
    pdf.multi_cell(95, 3.5, disclaimer)

    pdf.line(105, start_y_row2 + 25, 195, start_y_row2 + 25)
    pdf.set_font('Arial', '', 8)
    pdf.set_xy(105, start_y_row2 + 26)
    pdf.cell(95, 5, "Signature & Co Stamp / Date", align='L')

    output = pdf.output(dest='S')
    return bytes(output) if isinstance(output, (bytearray, bytes)) else output.encode('latin-1')


# 3. Streamlit UI
st.set_page_config(page_title="Service Report Generator", layout="wide")
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

        # Auto-calc hours
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