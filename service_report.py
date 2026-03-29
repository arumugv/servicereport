import streamlit as st
from fpdf import FPDF
from datetime import datetime
import pandas as pd
import tempfile
import os
import sqlite3
import json


# --- DATABASE FUNCTIONS ---
def init_db():
    conn = sqlite3.connect('pie_reports.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reports
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     report_no
                     TEXT,
                     customer
                     TEXT,
                     date
                     TEXT,
                     location
                     TEXT,
                     requestor
                     TEXT,
                     contact
                     TEXT,
                     work_desc
                     TEXT,
                     ra_json
                     TEXT,
                     personnel_json
                     TEXT
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS drafts
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     report_no
                     TEXT,
                     customer
                     TEXT,
                     date
                     TEXT,
                     location
                     TEXT,
                     requestor
                     TEXT,
                     contact
                     TEXT,
                     work_desc
                     TEXT,
                     ra_json
                     TEXT,
                     personnel_json
                     TEXT,
                     last_saved
                     TEXT
                 )''')
    conn.commit()
    conn.close()


def delete_report_from_db(report_id):
    conn = sqlite3.connect('pie_reports.db')
    c = conn.cursor()
    c.execute("DELETE FROM reports WHERE id = ?", (report_id,))
    conn.commit()
    conn.close()


def save_draft(report_no, customer, date, location, requestor, contact, work_desc, ra_values, personnel_list):
    conn = sqlite3.connect('pie_reports.db')
    c = conn.cursor()
    c.execute("SELECT id FROM drafts WHERE report_no = ?", (report_no,))
    exists = c.fetchone()
    ra_json = json.dumps(ra_values)
    p_json = json.dumps(personnel_list)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if exists:
        c.execute('''UPDATE drafts
                     SET customer=?,
                         date=?,
                         location=?,
                         requestor=?,
                         contact=?,
                         work_desc=?,
                         ra_json=?,
                         personnel_json=?,
                         last_saved=?
                     WHERE report_no = ?''',
                  (customer, str(date), location, requestor, contact, work_desc, ra_json, p_json, now, report_no))
    else:
        c.execute('''INSERT INTO drafts (report_no, customer, date, location, requestor, contact, work_desc, ra_json,
                                         personnel_json, last_saved)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (report_no, customer, str(date), location, requestor, contact, work_desc, ra_json, p_json, now))
    conn.commit()
    conn.close()


def save_report_to_db(report_no, customer, date, location, requestor, contact, work_desc, ra_values, personnel_list):
    conn = sqlite3.connect('pie_reports.db')
    c = conn.cursor()
    ra_json = json.dumps(ra_values)
    p_json = json.dumps(personnel_list)
    c.execute('''INSERT INTO reports (report_no, customer, date, location, requestor, contact, work_desc, ra_json,
                                      personnel_json)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (report_no, customer, str(date), location, requestor, contact, work_desc, ra_json, p_json))
    c.execute("DELETE FROM drafts WHERE report_no = ?", (report_no,))
    conn.commit()
    conn.close()


init_db()


# --- PDF CLASS & GENERATOR ---
class ServiceReportPDF(FPDF):
    def __init__(self, logo_path="logo.jpeg"):  # Set permanent logo path here
        super().__init__()
        self.logo_path = logo_path

    def header(self):
        # Check for permanent logo file
        if os.path.exists(self.logo_path):
            try:
                self.image(self.logo_path, x=10, y=8, w=30)
                self.set_x(45)
            except:
                pass
        else:
            self.set_x(10)  # Fallback if logo file is missing

        self.set_font('Arial', 'B', 15)
        self.cell(0, 8, 'PIE PTE LTD', ln=True)
        self.set_font('Arial', '', 8)
        self.set_x(45)
        self.cell(0, 4, 'UEN: 201634529C', ln=True)  # Permanent UEN inclusion
        self.set_x(45)
        self.cell(0, 4, 'Address: 1 North Bridge Road, #B1-05A High Street Centre S 179094', ln=True)
        self.set_x(45)
        self.cell(0, 4, 'Email: Brian@piesgservice.com | Hp: 92331569', ln=True)
        self.ln(5)
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.2)
        self.line(10, 35, 200, 35)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')


def generate_report(data, personnel_df, ra_values):
    # Logo is now handled permanently within the Class
    pdf = ServiceReportPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'SERVICE REPORT / DOCKET', ln=True, align='C')
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 9)
    fields = [("Report No:", str(data.get('report_no', '')), "Date:", str(data.get('date', ''))),
              ("Customer:", str(data.get('customer', '')), "Requestor:", str(data.get('requestor', ''))),
              ("Location:", str(data.get('location', '')), "Contact:", str(data.get('contact', '')))]
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
    pdf.set_font('Arial', 'B', 10);
    pdf.cell(0, 8, 'SITE SPECIFIC RISK ASSESSMENT', ln=True)
    pdf.set_font('Arial', '', 8)
    ra_items_list = list(ra_values.items())
    for i in range(0, len(ra_items_list), 4):
        chunk = ra_items_list[i:i + 4]
        for key, val in chunk:
            status = "[X]" if val else "[ ]"
            pdf.cell(45, 6, f"{status} {key}")
        pdf.ln()
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 10);
    pdf.cell(0, 8, 'Scope of Work / Description of Tasks', ln=True)
    pdf.set_font('Arial', '', 9);
    pdf.multi_cell(0, 5, str(data.get('work_description', '')), border=1)
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 10);
    pdf.cell(0, 8, 'Personnel / Hours', ln=True)
    headers, widths = ['Date', 'Name', 'From', 'To', 'Hrs', 'Remarks'], [25, 45, 20, 20, 15, 65]
    pdf.set_fill_color(240, 240, 240)
    for i, h in enumerate(headers): pdf.cell(widths[i], 8, h, border=1, fill=True, align='C')
    pdf.ln()
    pdf.set_font('Arial', '', 8)
    for _, row in personnel_df.iterrows():
        pdf.cell(widths[0], 7, str(row['Date']), border=1)
        pdf.cell(widths[1], 7, str(row['Name']), border=1)
        pdf.cell(widths[2], 7, str(row['From']), border=1)
        pdf.cell(widths[3], 7, str(row['To']), border=1)
        pdf.cell(widths[4], 7, str(row['Hrs']), border=1, align='C')
        pdf.cell(widths[5], 7, str(row['Remarks']), border=1, ln=True)

    pdf.ln(10)
    start_y = pdf.get_y()
    pdf.set_font('Arial', 'B', 9);
    pdf.cell(95, 5, "Service Personnel", ln=True)
    pdf.set_font('Arial', '', 8);
    pdf.cell(95, 5, "____________________________________", ln=True);
    pdf.cell(95, 5, "Name / Designation / Date", ln=True)
    pdf.set_xy(105, start_y);
    pdf.set_font('Arial', 'B', 9);
    pdf.cell(95, 5, "CLIENT'S APPROVAL OF WORK", ln=True)
    pdf.set_x(105);
    pdf.set_font('Arial', 'I', 7);
    pdf.multi_cell(95, 3.5, "Work completed to satisfaction. Charges accepted.", align='L');
    pdf.ln(10)
    pdf.set_x(105);
    pdf.set_font('Arial', '', 8);
    pdf.cell(95, 5, "____________________________________", ln=True);
    pdf.set_x(105);
    pdf.cell(95, 5, "Signature & Co Stamp / Date", align='L')
    return pdf.output(dest='S').encode('latin-1')


# --- STREAMLIT UI ---
st.set_page_config(page_title="PIE Service Report", layout="wide")
st.title("📋 Service Report & Generator")


def reset_widget_states():
    """Wipes specific widget keys so they pull fresh data from session_state."""
    for key in list(st.session_state.keys()):
        if any(key.startswith(prefix) for prefix in ['d_', 'n_', 'f_', 't_', 'h_', 'r_', 'ra_ui_', 'job_']):
            del st.session_state[key]


# Initialize Session State
if 'form_data' not in st.session_state:
    st.session_state.form_data = {
        "report_no": "", "customer": "", "requestor": "", "date": datetime.now().date(),
        "location": "", "contact": "", "work_description": "",
        "ra_values": {item: False for item in
                      ["Helmet", "Safety Shoes", "Safety Vest", "Hand Gloves", "Goggles", "Harness", "Face Mask"]}
    }
if 'rows' not in st.session_state:
    st.session_state.rows = [
        {"Date": str(datetime.now().date()), "Name": "", "From": "", "To": "", "Hrs": "0.0", "Remarks": ""}]

with st.sidebar:
    st.header("Settings")
    # File uploader removed as requested for permanent logo use
    st.info("Company Logo is loaded automatically from system files.")

    if st.button("🆕 Clear Form / New Report", type="primary", use_container_width=True):
        reset_widget_states()
        st.session_state.form_data = {
            "report_no": "", "customer": "", "requestor": "", "date": datetime.now().date(),
            "location": "", "contact": "", "work_description": "",
            "ra_values": {item: False for item in
                          ["Helmet", "Safety Shoes", "Safety Vest", "Hand Gloves", "Goggles", "Harness", "Face Mask"]}
        }
        st.session_state.rows = [
            {"Date": str(datetime.now().date()), "Name": "", "From": "", "To": "", "Hrs": "0.0", "Remarks": ""}]
        st.rerun()

    st.markdown("---")
    st.header("💾 Drafts")
    conn = sqlite3.connect('pie_reports.db')
    drafts_df = pd.read_sql_query("SELECT report_no, customer FROM drafts", conn)
    conn.close()
    if not drafts_df.empty:
        selected_draft = st.selectbox("Load a Draft", options=drafts_df['report_no'].tolist())
        if st.button("📂 Load Draft"):
            conn = sqlite3.connect('pie_reports.db')
            d = pd.read_sql_query(f"SELECT * FROM drafts WHERE report_no='{selected_draft}'", conn).iloc[0]
            conn.close()
            reset_widget_states()
            st.session_state.form_data = {
                "report_no": str(d["report_no"]), "customer": str(d["customer"]),
                "requestor": str(d.get("requestor", "")), "date": datetime.strptime(d["date"], "%Y-%m-%d").date(),
                "location": str(d["location"]), "contact": str(d.get("contact", "")),
                "work_description": str(d["work_desc"]), "ra_values": json.loads(d["ra_json"])
            }
            st.session_state.rows = json.loads(d["personnel_json"])
            st.rerun()

with st.expander("📝 1. Job Information", expanded=True):
    col1, col2 = st.columns(2)
    current_rep = st.session_state.form_data["report_no"]
    with col1:
        report_no = st.text_input("Report No.", value=st.session_state.form_data["report_no"],
                                  key=f"job_rep_{current_rep}")
        customer = st.text_input("Customer", value=st.session_state.form_data["customer"],
                                 key=f"job_cust_{current_rep}")
        requestor = st.text_input("Requestor", value=st.session_state.form_data["requestor"],
                                  key=f"job_req_{current_rep}")
    with col2:
        date_input = st.date_input("Date", value=st.session_state.form_data["date"], key=f"job_date_{current_rep}")
        location = st.text_input("Location", value=st.session_state.form_data["location"], key=f"job_loc_{current_rep}")
        contact = st.text_input("Contact No.", value=st.session_state.form_data["contact"],
                                key=f"job_con_{current_rep}")
    work_desc = st.text_area("Scope of Work", value=st.session_state.form_data["work_description"],
                             key=f"job_work_{current_rep}")

with st.expander("🛡️ 2. Site Specific Risk Assessment"):
    ra_items = ["Helmet", "Safety Shoes", "Safety Vest", "Hand Gloves", "Goggles", "Harness", "Face Mask"]
    ra_cols = st.columns(len(ra_items))
    ra_values = {item: ra_cols[i].checkbox(item, value=st.session_state.form_data["ra_values"].get(item, False),
                                           key=f"ra_ui_{item}_{current_rep}") for i, item in enumerate(ra_items)}

with st.expander("👥 3. Personnel & Attendance", expanded=True):
    updated_rows = []
    for i, row in enumerate(st.session_state.rows):
        c1, c2, c3, c4, c5, c6, c7 = st.columns([1.5, 3, 1, 1, 1, 3, 0.5])
        r_date = c1.text_input("Date", value=row.get('Date', ''), key=f"d_{i}_{current_rep}")
        r_name = c2.text_input("Name", value=row.get('Name', ''), key=f"n_{i}_{current_rep}")
        r_from = c3.text_input("From", value=row.get('From', ''), key=f"f_{i}_{current_rep}")
        r_to = c4.text_input("To", value=row.get('To', ''), key=f"t_{i}_{current_rep}")
        current_hrs = row.get('Hrs', '0.0')
        if r_from != row.get('From') or r_to != row.get('To'):
            try:
                if len(r_from) == 4 and len(r_to) == 4:
                    dt1, dt2 = datetime.strptime(r_from, "%H%M"), datetime.strptime(r_to, "%H%M")
                    current_hrs = str(round((dt2 - dt1).total_seconds() / 3600, 1))
            except:
                pass
        r_hrs = c5.text_input("Hrs", value=current_hrs, key=f"h_{i}_{current_rep}")
        r_remarks = c6.text_input("Remarks", value=row.get('Remarks', ''), key=f"r_{i}_{current_rep}")
        updated_rows.append(
            {"Date": r_date, "Name": r_name, "From": r_from, "To": r_to, "Hrs": r_hrs, "Remarks": r_remarks})
        if c7.button("🗑️", key=f"del_row_{i}_{current_rep}"):
            st.session_state.rows.pop(i);
            reset_widget_states();
            st.rerun()
    st.session_state.rows = updated_rows
    if st.button("➕ Add Personnel Row"):
        st.session_state.rows.append(
            {"Date": str(date_input), "Name": "", "From": "", "To": "", "Hrs": "0.0", "Remarks": ""});
        st.rerun()

col_save, col_draft = st.columns([1, 1])
if col_save.button("🚀 Finalize: Generate PDF & Save", use_container_width=True):
    if not report_no:
        st.error("Report No required.")
    else:
        save_report_to_db(report_no, customer, date_input, location, requestor, contact, work_desc, ra_values,
                          st.session_state.rows)
        pdf_bytes = generate_report(
            {"report_no": report_no, "customer": customer, "requestor": requestor, "date": date_input,
             "location": location, "contact": contact, "work_description": work_desc},
            pd.DataFrame(st.session_state.rows), ra_values)
        st.success("Finalized!")
        st.download_button("📥 Download PDF", data=pdf_bytes, file_name=f"Report_{report_no}.pdf",
                           mime="application/pdf")

if col_draft.button("💾 Save as Draft", use_container_width=True):
    if not report_no:
        st.error("Report No required.")
    else:
        save_draft(report_no, customer, date_input, location, requestor, contact, work_desc, ra_values,
                   st.session_state.rows); st.info("Draft saved.")

st.markdown("---")
st.header("📂 Search Finalized History")
search_term = st.text_input("Search by Report No or Customer Name")
conn = sqlite3.connect('pie_reports.db');
sql = "SELECT * FROM reports"
if search_term: sql += f" WHERE report_no LIKE '%{search_term}%' OR customer LIKE '%{search_term}%'"
history_df = pd.read_sql_query(sql + " ORDER BY id DESC", conn);
conn.close()

if not history_df.empty:
    event = st.dataframe(history_df[["id", "report_no", "customer", "date", "location"]], use_container_width=True,
                         on_select="rerun", selection_mode="single-row", key="history_table")
    selected_rows = event.selection.rows
    if selected_rows:
        data = history_df.iloc[selected_rows[0]]
        col_load, col_del = st.columns([1, 1])
        if col_load.button("📂 Load Selected Report", use_container_width=True):
            reset_widget_states()
            st.session_state.form_data = {
                "report_no": str(data["report_no"]), "customer": str(data["customer"]),
                "requestor": str(data.get("requestor", "")), "date": datetime.strptime(data["date"], "%Y-%m-%d").date(),
                "location": str(data["location"]), "contact": str(data.get("contact", "")),
                "work_description": str(data["work_desc"]), "ra_values": json.loads(data["ra_json"])
            }
            st.session_state.rows = json.loads(data["personnel_json"]);
            st.rerun()
        confirm_del = st.checkbox("Confirm Deletion", key="confirm_del_box")
        if col_del.button("🗑️ Delete Permanently") and confirm_del:
            delete_report_from_db(data['id']);
            st.success("Deleted!");
            st.rerun()