import streamlit as st
import pandas as pd
import xmlrpc.client
from xmlrpc.client import Fault
import io
import os
from dotenv import load_dotenv
from datetime import datetime
 
# Load environment variables
load_dotenv()
 
# ==========================================
# PAGE CONFIG & STYLING
# ==========================================
st.set_page_config(
    page_title="Odoo Automation Portal", 
    layout="wide",
    page_icon="⚙️",
    initial_sidebar_state="expanded"
)
 
# Professional Light Theme CSS
st.markdown("""
<style>
        /* Main container styling */
        .main {
            background-color: #f8f9fa;
        }
        /* Headers */
        h1 {
            color: #1e3c72;
            font-weight: 700;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        h2, h3 {
            color: #2c3e50;
            font-weight: 600;
        }
        /* Sidebar styling */
        .css-1d391kg, .css-12oz5g7 {
            background-color: #ffffff;
            border-right: 1px solid #e0e4e8;
        }
        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            border: none;
            padding: 0.5rem 2rem;
            font-weight: 600;
            border-radius: 8px;
            transition: all 0.3s ease;
            width: 100%;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(30,60,114,0.3);
        }
        /* Card styling */
        .css-1r6slb0 {
            background-color: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            border: 1px solid #e0e4e8;
        }
        /* Expander styling */
        .streamlit-expanderHeader {
            background-color: #f8f9fa;
            border-radius: 8px;
            font-weight: 600;
            color: #1e3c72;
        }
        /* Success/Error/Warning messages */
        .stAlert {
            border-radius: 8px;
            border-left: 4px solid;
        }
        /* Dataframe styling */
        .dataframe {
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        /* Log container */
        .log-box {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 0.85rem;
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #e0e4e8;
        }
        /* Status indicators */
        .status-success {
            color: #28a745;
            font-weight: 600;
        }
        .status-error {
            color: #dc3545;
            font-weight: 600;
        }
        .status-warning {
            color: #ffc107;
            font-weight: 600;
        }
        /* Metric cards */
        .metric-card {
            background: white;
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            border: 1px solid #e0e4e8;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #1e3c72;
        }
        .metric-label {
            font-size: 0.85rem;
            color: #6c757d;
            margin-top: 0.5rem;
        }
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
            background-color: white;
            padding: 0.5rem;
            border-radius: 12px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 600;
        }
        /* Footer */
        .footer {
            text-align: center;
            padding: 2rem;
            color: #6c757d;
            font-size: 0.8rem;
            border-top: 1px solid #e0e4e8;
            margin-top: 2rem;
        }
</style>
""", unsafe_allow_html=True)
 
# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
 
# ==========================================
# AUTHENTICATION FUNCTION
# ==========================================
def authenticate_user(username, password):
    admin_user = os.getenv('ADMIN_USER')
    admin_password = os.getenv('ADMIN_PASSWORD')
    return username == admin_user and password == admin_password
 
# ==========================================
# LOGIN CONTAINER
# ==========================================
def login_sidebar():
    with st.sidebar:
        st.markdown("### 🔐 Authentication")
        if not st.session_state.logged_in:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submit = st.form_submit_button("Login", use_container_width=True)
                if submit:
                    if authenticate_user(username, password):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.success(f"Welcome back, {username}! 🎉")
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials. Please try again.")
        else:
            st.success(f"✅ Logged in as: **{st.session_state.username}**")
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.rerun()
 
# ==========================================
# ODOO CONNECTION HELPER
# ==========================================
@st.cache_resource
def connect_to_odoo():
    try:
        url = os.getenv('ODOO_URL')
        db = os.getenv('ODOO_DB')
        username = os.getenv('ODOO_USERNAME')
        password = os.getenv('ODOO_PASSWORD')
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
        uid = common.authenticate(db, username, password, {})
        if not uid:
            return None, None, "Authentication Failed. Check Odoo credentials."
        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
        return uid, models, "Success"
    except Exception as e:
        return None, None, str(e)
 
# ==========================================
# PROCESS LOGIC FUNCTIONS
# ==========================================
def process_product_creation(df, models, db, uid, password, log_container):
    RESUPPLY_ROUTE_ID = 12
    results = []
    def execute_button(product_id, method_name):
        try:
            models.execute_kw(db, uid, password, "product.template", method_name, [[product_id]])
        except Fault as e:
            if "allow_none" not in str(e):
                raise Exception(f"{method_name} failed: {e}")
    for index, row in df.iterrows():
        sku, product_name = "Unknown", "Unknown"
        try:
            product_name = str(row.get("Product Name", "")).strip()
            sku = str(row.get("SKU", "")).strip()
            category_name = str(row.get("Category", "")).strip()
            sales_price = float(row.get("Sales Price", 0.0))
            cost_price = float(row.get("Cost Price", 0.0))
            log_container.write(f"**Processing SKU:** {sku} | {product_name}")
            category_ids = models.execute_kw(db, uid, password, "product.category", "search", [[("name", "=", category_name)]], {"limit": 1})
            if not category_ids:
                raise Exception(f"Category Not Found: {category_name}")
            category_id = category_ids[0]
            product_ids = models.execute_kw(db, uid, password, "product.template", "search", [[("sku", "=", sku)]])
            if not product_ids:
                product_ids = models.execute_kw(db, uid, password, "product.template", "search", [[("default_code", "=", sku)]])
            if product_ids:
                product_id = product_ids[0]
                execute_button(product_id, "reset_to_draft")
                models.execute_kw(db, uid, password, "product.template", "write", [
                    [product_id],
                    {"name": product_name, "list_price": sales_price, "standard_price": cost_price, "categ_id": category_id, "tracking": "serial", "route_ids": [(4, RESUPPLY_ROUTE_ID)]}
                ])
                log_container.success(f"✓ Product Updated: {product_id}")
                execute_button(product_id, "action_submit")
                execute_button(product_id, "action_approve")
                results.append({"SKU": sku, "Product Name": product_name, "Status": "Success", "Action": "Updated", "Message": f"Updated ID {product_id}"})
            else:
                product_vals = {
                    "name": product_name, "sku": sku, "list_price": sales_price, "standard_price": cost_price,
                    "categ_id": category_id, "tracking": "serial", "route_ids": [(4, RESUPPLY_ROUTE_ID)]
                }
                product_id = models.execute_kw(db, uid, password, "product.template", "create", [product_vals])
                log_container.success(f"✓ Product Created: {product_id}")
                execute_button(product_id, "action_submit")
                execute_button(product_id, "action_approve")
                results.append({"SKU": sku, "Product Name": product_name, "Status": "Success", "Action": "Created", "Message": f"Created ID {product_id}"})
        except Exception as e:
            log_container.error(f"Error on row {index + 1}: {str(e)}")
            results.append({"SKU": sku, "Product Name": product_name, "Status": "Error", "Action": "Failed", "Message": str(e)})
    return results
 
def process_manufacturing(df, models, db, uid, password, log_container):
    results = []
    for index, row in df.iterrows():
        finished_sku, component_sku = "Unknown", "Unknown"
        try:
            finished_sku = str(row.get("Finished_SKU", "")).strip()
            component_sku = str(row.get("Component_SKU", "")).strip()
            component_qty = float(row.get("Component_Qty", 0.0))
            subcontractor_name = str(row.get("Subcontractor", "")).strip()
            log_container.write(f"**Processing BOM:** {finished_sku} (Component: {component_sku})")
            finished_product = models.execute_kw(db, uid, password, 'product.template', 'search_read', [[('sku', '=', finished_sku)]], {'fields': ['id'], 'limit': 1})
            if not finished_product:
                raise Exception(f"Finished Product not found: {finished_sku}")
            finished_product_tmpl_id = finished_product[0]['id']
            component_template = models.execute_kw(db, uid, password, 'product.template', 'search_read', [[('sku', '=', component_sku)]], {'fields': ['id'], 'limit': 1})
            if not component_template:
                raise Exception(f"Component Product not found: {component_sku}")
            component_variant = models.execute_kw(db, uid, password, 'product.product', 'search_read', [[('product_tmpl_id', '=', component_template[0]['id'])]], {'fields': ['id'], 'limit': 1})
            if not component_variant:
                raise Exception(f"No variant found for {component_sku}")
            component_product_id = component_variant[0]['id']
            subcontractor = models.execute_kw(db, uid, password, 'res.partner', 'search_read', [[('name', '=', subcontractor_name)]], {'fields': ['id'], 'limit': 1})
            if not subcontractor:
                raise Exception(f"Subcontractor not found: {subcontractor_name}")
            subcontractor_id = subcontractor[0]['id']
            existing_bom = models.execute_kw(db, uid, password, 'mrp.bom', 'search', [[('product_tmpl_id', '=', finished_product_tmpl_id)]], {'limit': 1})
            if existing_bom:
                log_container.info(f"⚠️ BOM already exists for {finished_sku}. ID: {existing_bom[0]}")
                results.append({"Finished SKU": finished_sku, "Component SKU": component_sku, "Status": "Skipped", "Message": f"BOM already exists (ID: {existing_bom[0]})"})
                continue
            bom_vals = {
                'product_tmpl_id': finished_product_tmpl_id, 'product_qty': 1, 'type': 'subcontract',
                'subcontractor_ids': [(6, 0, [subcontractor_id])],
                'bom_line_ids': [(0, 0, {'product_id': component_product_id, 'product_qty': component_qty})]
            }
            bom_id = models.execute_kw(db, uid, password, 'mrp.bom', 'create', [bom_vals])
            log_container.success(f"✅ BOM Created Successfully for {finished_sku}. BOM ID: {bom_id}")
            results.append({"Finished SKU": finished_sku, "Component SKU": component_sku, "Status": "Success", "Message": f"Created BOM ID {bom_id}"})
        except Exception as e:
            log_container.error(f"Error on row {index + 1}: {str(e)}")
            results.append({"Finished SKU": finished_sku, "Component SKU": component_sku, "Status": "Error", "Message": str(e)})
    return results
 
def process_purchase_order(df, models, db, uid, password, log_container):
    results = []
    for index, row in df.iterrows():
        vendor_name, product_name = "Unknown", "Unknown"
        try:
            vendor_name = str(row.get("Vendor_Name", "")).strip()
            purchase_team_name = str(row.get("Purchase_Team", "")).strip()
            product_name = str(row.get("Product_Name", "")).strip()
            qty = float(row.get("Qty", 0.0))
            price_unit = float(row.get("Price_Unit", 0.0))
            discount = float(row.get("Discount", 0.0))
            partner_ref = str(row.get("Partner_Ref", "")).strip()
            log_container.write(f"**Processing PO:** {vendor_name} | {product_name}")
            partner = models.execute_kw(db, uid, password, 'res.partner', 'search_read', [[('name', '=', vendor_name)]], {'fields': ['id'], 'limit': 1})
            if not partner:
                raise Exception(f"Vendor not found: {vendor_name}")
            team = models.execute_kw(db, uid, password, 'purchase.team', 'search_read', [[('name', '=', purchase_team_name)]], {'fields': ['id'], 'limit': 1})
            if not team:
                raise Exception(f"Purchase Team not found: {purchase_team_name}")
            product_template = models.execute_kw(db, uid, password, 'product.template', 'search_read', [[('name', '=', product_name)]], {'fields': ['id', 'name'], 'limit': 1})
            if not product_template:
                raise Exception(f"Product not found: {product_name}")
            product_variant = models.execute_kw(db, uid, password, 'product.product', 'search_read', [[('product_tmpl_id', '=', product_template[0]['id'])]], {'fields': ['id'], 'limit': 1})
            if not product_variant:
                raise Exception(f"Product Variant not found: {product_name}")
            po_vals = {
                'partner_id': partner[0]['id'], 'team_id': team[0]['id'], 'partner_ref': partner_ref,
                'order_line': [(0, 0, {
                    'name': product_template[0]['name'], 'product_id': product_variant[0]['id'],
                    'product_template_id': product_template[0]['id'], 'product_qty': qty,
                    'price_unit': price_unit, 'discount': discount
                })]
            }
            po_id = models.execute_kw(db, uid, password, 'purchase.order', 'create', [po_vals])
            models.execute_kw(db, uid, password, 'purchase.order', 'button_confirm', [[po_id]])
            models.execute_kw(db, uid, password, 'purchase.order', 'button_approve', [[po_id]])
            po = models.execute_kw(db, uid, password, 'purchase.order', 'read', [[po_id]], {'fields': ['name']})
            log_container.success(f"✅ PO Approved: {po[0]['name']}")
            results.append({"Vendor": vendor_name, "Product": product_name, "Status": "Success", "Message": f"PO Approved: {po[0]['name']}"})
        except Exception as e:
            log_container.error(f"Error on row {index + 1}: {str(e)}")
            results.append({"Vendor": vendor_name, "Product": product_name, "Status": "Error", "Message": str(e)})
    return results
 
def process_resupply(df, models, db, uid, password, log_container):
    results = []
    for index, row in df.iterrows():
        po_number, lot_number = "Unknown", "Unknown"
        try:
            po_number = str(row.get("PO_NUMBER", "")).strip()
            lot_number = str(row.get("LOT_NUMBER", "")).strip()
            demand_qty = float(row.get("DEMAND_QTY", 0.0))
            source_location_name = str(row.get("SOURCE_LOCATION_NAME", "")).strip()
            log_container.write(f"**Processing Resupply:** PO {po_number} | Lot {lot_number}")
            location = models.execute_kw(db, uid, password, 'stock.location', 'search_read', [[('complete_name', '=', source_location_name)]], {'fields': ['id'], 'limit': 1})
            if not location:
                raise Exception(f"Location Not Found: {source_location_name}")
            new_source_location_id = location[0]['id']
            po = models.execute_kw(db, uid, password, 'purchase.order', 'search_read', [[('name', '=', po_number)]], {'fields': ['picking_ids'], 'limit': 1})
            if not po or not po[0]['picking_ids']:
                raise Exception(f"PO/Receipt Not Found: {po_number}")
            receipt_picking_id = po[0]['picking_ids'][0]
            receipt = models.execute_kw(db, uid, password, 'stock.picking', 'read', [[receipt_picking_id]], {'fields': ['name']})
            resupply = models.execute_kw(db, uid, password, 'stock.picking', 'search_read', [[('origin', '=', receipt[0]['name'])]], {'fields': ['id', 'name'], 'limit': 1})
            if not resupply:
                raise Exception("Resupply Picking Not Found")
            picking_id = resupply[0]['id']
            models.execute_kw(db, uid, password, 'stock.picking', 'write', [[picking_id], {'location_id': new_source_location_id}])
            moves = models.execute_kw(db, uid, password, 'stock.move', 'search_read', [[('picking_id', '=', picking_id)]], {'fields': ['id', 'product_id', 'location_dest_id']})
            if not moves:
                raise Exception("No Move Found")
            move = moves[0]
            models.execute_kw(db, uid, password, 'stock.move', 'write', [[move['id']], {'location_id': new_source_location_id}])
            lot = models.execute_kw(db, uid, password, 'stock.lot', 'search_read', [[('name', '=', lot_number)]], {'fields': ['id'], 'limit': 1})
            if not lot:
                raise Exception(f"Lot Not Found: {lot_number}")
            existing_lines = models.execute_kw(db, uid, password, 'stock.move.line', 'search_read', [[('move_id', '=', move['id'])]], {'fields': ['id']})
            for line in existing_lines:
                models.execute_kw(db, uid, password, 'stock.move.line', 'unlink', [[line['id']]])
            models.execute_kw(db, uid, password, 'stock.move.line', 'create', [{
                'move_id': move['id'], 'product_id': move['product_id'][0], 'lot_id': lot[0]['id'],
                'lot_name': lot_number, 'quantity': demand_qty, 'manual_qty_done': demand_qty,
                'picked': True, 'location_id': new_source_location_id, 'location_dest_id': move['location_dest_id'][0]
            }])
            models.execute_kw(db, uid, password, 'stock.picking', 'button_validate', [[picking_id]])
            models.execute_kw(db, uid, password, 'stock.picking', 'button_validate', [[receipt_picking_id]])
            log_container.success(f"✅ Resupply Validated Successfully for PO {po_number}")
            results.append({"PO Number": po_number, "Lot Number": lot_number, "Status": "Success", "Message": "Resupply validated"})
        except Exception as e:
            log_container.error(f"Error on row {index + 1}: {str(e)}")
            results.append({"PO Number": po_number, "Lot Number": lot_number, "Status": "Error", "Message": str(e)})
    return results
 
# ==========================================
# EXCEL GENERATOR HELPER
# ==========================================
def generate_excel_download(results_df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        results_df.to_excel(writer, index=False, sheet_name='Execution Results')
    processed_data = output.getvalue()
    return processed_data
 
# ==========================================
# DASHBOARD METRICS
# ==========================================
def display_metrics(results):
    if results:
        total = len(results)
        success = sum(1 for r in results if r.get('Status') == 'Success')
        errors = sum(1 for r in results if r.get('Status') == 'Error')
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
<div class="metric-card">
<div class="metric-value">{total}</div>
<div class="metric-label">Total Records</div>
</div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
<div class="metric-card">
<div class="metric-value" style="color: #28a745;">{success}</div>
<div class="metric-label">Successful</div>
</div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
<div class="metric-card">
<div class="metric-value" style="color: #dc3545;">{errors}</div>
<div class="metric-label">Errors</div>
</div>
            """, unsafe_allow_html=True)
        with col4:
            success_rate = (success / total * 100) if total > 0 else 0
            st.markdown(f"""
<div class="metric-card">
<div class="metric-value">{success_rate:.1f}%</div>
<div class="metric-label">Success Rate</div>
</div>
            """, unsafe_allow_html=True)
 
# ==========================================
# MAIN UI APPLICATION
# ==========================================
def main():
    # Sidebar for Login
    login_sidebar()
    # Main content area
    if not st.session_state.logged_in:
        st.markdown("""
<div style="text-align: center; padding: 3rem;">
<h1>⚙️ Odoo Automation Portal</h1>
<p style="font-size: 1.2rem; color: #6c757d; margin-top: 1rem;">
                    Please log in using the sidebar to access the automation features.
</p>
<div style="margin-top: 2rem;">
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                border-radius: 12px; padding: 2rem; color: white;">
<h3 style="color: white;">Features</h3>
<ul style="list-style: none; padding: 0;">
<li>📦 Product Creation & Management</li>
<li>🏭 Manufacturing & BOM Management</li>
<li>📄 Purchase Order Automation</li>
<li>🔄 Resupply Process Automation</li>
</ul>
</div>
</div>
</div>
        """, unsafe_allow_html=True)
        return
    # Display welcome banner
    st.markdown(f"""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem; color: white;">
<div style="display: flex; justify-content: space-between; align-items: center;">
<div>
<h2 style="color: white; margin: 0;">Welcome back, {st.session_state.username}! 👋</h2>
<p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Ready to automate your Odoo workflows?</p>
</div>
<div style="font-size: 3rem;">
                    ⚙️
</div>
</div>
</div>
    """, unsafe_allow_html=True)
    # Main title
    st.title("Odoo Automation Portal")
    st.markdown("<p style='text-align: center; color: #6c757d; margin-bottom: 2rem;'>Streamline your operations with intelligent automation</p>", unsafe_allow_html=True)
    # Create tabs for different operations
    tab1, tab2, tab3, tab4 = st.tabs(["📦 Product Creation", "🏭 Manufacturing", "📄 Purchase Orders", "🔄 Resupply"])
    process_configs = {
        tab1: {
            "name": "Product Creation",
            "cols": ["Product Name", "SKU", "Category", "Sales Price", "Cost Price"],
            "msg": "Upload Excel with columns: Product Name, SKU, Category, Sales Price, Cost Price"
        },
        tab2: {
            "name": "Manufacturing",
            "cols": ["Finished_SKU", "Component_SKU", "Component_Qty", "Subcontractor"],
            "msg": "Upload Excel with columns: Finished_SKU, Component_SKU, Component_Qty, Subcontractor"
        },
        tab3: {
            "name": "Purchaseorder",
            "cols": ["Vendor_Name", "Purchase_Team", "Product_Name", "Qty", "Price_Unit", "Discount", "Partner_Ref"],
            "msg": "Upload Excel with columns: Vendor_Name, Purchase_Team, Product_Name, Qty, Price_Unit, Discount, Partner_Ref"
        },
        tab4: {
            "name": "Resupply",
            "cols": ["PO_NUMBER", "LOT_NUMBER", "DEMAND_QTY", "SOURCE_LOCATION_NAME"],
            "msg": "Upload Excel with columns: PO_NUMBER, LOT_NUMBER, DEMAND_QTY, SOURCE_LOCATION_NAME"
        }
    }
    for tab, config in process_configs.items():
        with tab:
            st.header(config['name'])
            st.info(config['msg'])
            uploaded_file = st.file_uploader(f"Upload Excel for {config['name']}", type=["xlsx"], key=config['name'])
            if uploaded_file is not None:
                try:
                    df = pd.read_excel(uploaded_file)
                    # Column validation
                    missing_cols = [col for col in config['cols'] if col not in df.columns]
                    if missing_cols:
                        st.error(f"❌ Missing columns: {', '.join(missing_cols)}")
                        continue
                    with st.expander("📊 Preview Uploaded Data", expanded=True):
                        st.dataframe(df.head(10), use_container_width=True)
                        st.caption(f"Total rows: {len(df)}")
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        if st.button("🚀 Start Processing", key=f"btn_{config['name']}", use_container_width=True):
                            uid, models, conn_status = connect_to_odoo()
                            if not uid:
                                st.error(f"❌ Failed to connect to Odoo: {conn_status}")
                                return
                            st.success("✅ Connected to Odoo successfully!")
                            # Container for live logs
                            st.subheader("📋 Process Logs")
                            log_container = st.container()
                            results = []
                            with st.spinner("🔄 Processing records..."):
                                if config['name'] == "Product Creation":
                                    results = process_product_creation(df, models, os.getenv('ODOO_DB'), uid, os.getenv('ODOO_PASSWORD'), log_container)
                                elif config['name'] == "Manufacturing":
                                    results = process_manufacturing(df, models, os.getenv('ODOO_DB'), uid, os.getenv('ODOO_PASSWORD'), log_container)
                                elif config['name'] == "Purchaseorder":
                                    results = process_purchase_order(df, models, os.getenv('ODOO_DB'), uid, os.getenv('ODOO_PASSWORD'), log_container)
                                elif config['name'] == "Resupply":
                                    results = process_resupply(df, models, os.getenv('ODOO_DB'), uid, os.getenv('ODOO_PASSWORD'), log_container)
                            st.success(f"✅ Execution complete! Processed {len(df)} records.")
                            # Display metrics
                            display_metrics(results)
                            # Render Results DataFrame and Download Button
                            if results:
                                st.subheader("📊 Execution Summary")
                                results_df = pd.DataFrame(results)
                                st.dataframe(results_df, use_container_width=True)
                                excel_data = generate_excel_download(results_df)
                                st.download_button(
                                    label="📥 Download Results as Excel",
                                    data=excel_data,
                                    file_name=f"{config['name'].replace(' ', '_')}_Results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                except Exception as e:
                    st.error(f"❌ Failed to read the Excel file: {str(e)}")
    # Footer
    st.markdown("""
<div class="footer">
<p>© 2024 Odoo Automation Portal | Powered by Streamlit</p>
<p style="margin-top: 0.5rem;">Version 2.0 | Enterprise Automation Solution</p>
</div>
    """, unsafe_allow_html=True)
 
if __name__ == "__main__":
    main()
