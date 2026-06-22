import streamlit as st
import pandas as pd
import xmlrpc.client
from xmlrpc.client import Fault
import io
import os
from dotenv import load_dotenv
from datetime import datetime
from collections import defaultdict
import re

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
        /* Branch selector styling */
        .branch-selector {
            background: white;
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid #e0e4e8;
            margin-bottom: 1rem;
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
if 'selected_branch' not in st.session_state:
    st.session_state.selected_branch = "All"

# ==========================================
# BRANCH CONFIGURATION
# ==========================================
BRANCH_KEYWORDS = {
    "CBE": ["CB", "CBE"],
    "TN": ["TN"],
    "MLM": ["MLM"],
    "HYD": ["HYD"],
    "JYR": ["JYR"],
    "Vizag": ["Vizag", "VZG"],
    "Saree Trails": ["PUNE", "Local Expo"]
}

BRANCH_OPTIONS = ["All"] + list(BRANCH_KEYWORDS.keys())

# ==========================================
# ROUTE CONFIGURATION (Backend Team Modifications)
# ==========================================
RESUPPLY_ROUTE_ID = 12  # Resupply route for internal transfers
BUY_ROUTE_ID = 5        # Buy route for purchase orders (NEW - Added by backend team)

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
# BRANCH FILTERING HELPER
# ==========================================
def filter_data_by_branch(df, branch_name, branch_column="Branch"):
    """
    Filter DataFrame rows based on branch selection
    Supports multiple columns that might contain branch information
    """
    if branch_name == "All" or not branch_name:
        return df
    
    # Define all possible branch columns
    possible_columns = [
        "Branch", "Location", "Store", "Warehouse", 
        "Branch_Code", "Store_Code", "Location_Code"
    ]
    
    # Find which columns exist in the dataframe
    existing_columns = [col for col in possible_columns if col in df.columns]
    
    if not existing_columns:
        # If no branch columns found, try to find any column that might contain branch info
        for col in df.columns:
            if any(kw.lower() in col.lower() for kw in ["branch", "location", "store", "warehouse"]):
                existing_columns.append(col)
                break
    
    if not existing_columns:
        # No branch-related columns found, return original data with warning
        st.warning(f"No branch-related columns found. Available columns: {', '.join(df.columns)}")
        return df
    
    # Get branch keywords
    keywords = BRANCH_KEYWORDS.get(branch_name, [branch_name])
    
    # Create filter mask
    mask = pd.Series([False] * len(df))
    
    for col in existing_columns:
        for kw in keywords:
            mask = mask | df[col].astype(str).str.contains(kw, case=False, na=False)
    
    filtered_df = df[mask]
    
    if len(filtered_df) == 0:
        st.warning(f"No records found for branch: {branch_name} in columns: {', '.join(existing_columns)}")
    
    return filtered_df

# ==========================================
# COMPANY HELPER FUNCTION
# ==========================================
def get_company_id(company_name, models, db, uid, password):
    """Get company ID by name"""
    if not company_name or pd.isna(company_name):
        return None
    
    company = models.execute_kw(
        db, uid, password,
        'res.company',
        'search_read',
        [[('name', '=', company_name)]],
        {'fields': ['id', 'name'], 'limit': 1}
    )
    
    if company:
        return company[0]['id']
    return None

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def normalize_product_name(name):
    return str(name).upper().replace("-", "").replace(" ", "").strip()

def get_branch_filter_domain(branch_name):
    """Generate search domain for branch filtering"""
    if branch_name == "All" or not branch_name:
        return []
    
    keywords = BRANCH_KEYWORDS.get(branch_name, [branch_name])
    search_domains = []
    for kw in keywords:
        search_domains.append(['name', 'ilike', kw])
    
    if not search_domains:
        return []
    
    # Build OR domain
    domain = ['|'] * (len(search_domains) - 1) + search_domains
    return domain

def get_category_id(category_name, models, db, uid, password):
    """Get category ID by complete_name"""
    category_ids = models.execute_kw(
        db, uid, password,
        "product.category",
        "search",
        [[("complete_name", "=", category_name)]],
        {"limit": 1}
    )
    if not category_ids:
        return None
    return category_ids[0]

def find_product(sku, models, db, uid, password):
    """Find product by SKU or default_code"""
    product_ids = models.execute_kw(
        db, uid, password,
        "product.template",
        "search",
        [[("sku", "=", sku)]]
    )
    if not product_ids:
        product_ids = models.execute_kw(
            db, uid, password,
            "product.template",
            "search",
            [[("default_code", "=", sku)]]
        )
    return product_ids

def execute_button(product_id, method_name, models, db, uid, password):
    """Execute button action on product template"""
    try:
        models.execute_kw(
            db, uid, password,
            "product.template",
            method_name,
            [[product_id]]
        )
        return True, f"✓ {method_name} executed"
    except Fault as e:
        if "allow_none" in str(e):
            return True, f"✓ {method_name} executed"
        return False, f"✗ {method_name}: {e}"
    except Exception as e:
        return False, f"✗ {method_name}: {e}"

def get_routes_list():
    """Get the list of route IDs for product configuration"""
    # Backend team added BUY_ROUTE_ID along with RESUPPLY_ROUTE_ID
    return [RESUPPLY_ROUTE_ID, BUY_ROUTE_ID]

# ==========================================
# PROCESS LOGIC FUNCTIONS
# ==========================================
def process_product_creation(df, models, db, uid, password, log_container, branch_filter=None):
    # Apply branch filter
    df = filter_data_by_branch(df, branch_filter)
    
    if df.empty:
        log_container.warning(f"No products to process for branch: {branch_filter}")
        return []
    
    results = []
    route_ids = get_routes_list()  # Get both Resupply and Buy routes
    
    for index, row in df.iterrows():
        sku, product_name = "Unknown", "Unknown"
        try:
            product_name = str(row.get("Product Name", "")).strip()
            sku = str(row.get("SKU", "")).strip()
            category_name = str(row.get("Category", "")).strip()
            sales_price = float(row.get("Sales Price", 0.0))
            cost_price = float(row.get("Cost Price", 0.0))
            company_name = str(row.get("Company", "")).strip() if "Company" in df.columns else None
            
            log_container.write(f"**Processing SKU:** {sku} | {product_name}")
            
            category_id = get_category_id(category_name, models, db, uid, password)
            if not category_id:
                raise Exception(f"Category Not Found: {category_name}")
            
            # Get company ID if provided
            company_id = None
            if company_name:
                company_id = get_company_id(company_name, models, db, uid, password)
                if company_id:
                    log_container.write(f"Company: {company_name} (ID: {company_id})")
            
            product_ids = find_product(sku, models, db, uid, password)
            
            if product_ids:
                product_id = product_ids[0]
                success, msg = execute_button(product_id, "reset_to_draft", models, db, uid, password)
                if not success:
                    log_container.warning(msg)
                
                # Prepare update values with BOTH routes
                update_vals = {
                    "name": product_name, 
                    "list_price": sales_price, 
                    "standard_price": cost_price, 
                    "categ_id": category_id, 
                    "tracking": "serial",
                    "route_ids": [(6, 0, route_ids)]  # Now includes both Resupply and Buy routes
                }
                if company_id:
                    update_vals["company_id"] = company_id
                
                models.execute_kw(db, uid, password, "product.template", "write", [
                    [product_id],
                    update_vals
                ])
                log_container.success(f"✓ Product Updated: {product_id}")
                
                execute_button(product_id, "action_submit", models, db, uid, password)
                execute_button(product_id, "action_approve", models, db, uid, password)
                results.append({"SKU": sku, "Product Name": product_name, "Status": "Success", 
                               "Action": "Updated", "Message": f"Updated ID {product_id} with routes: Resupply({RESUPPLY_ROUTE_ID}), Buy({BUY_ROUTE_ID})"})
            else:
                product_vals = {
                    "name": product_name, 
                    "sku": sku, 
                    "list_price": sales_price, 
                    "standard_price": cost_price,
                    "categ_id": category_id, 
                    "tracking": "serial",
                    "route_ids": [(6, 0, route_ids)]  # Now includes both Resupply and Buy routes
                }
                if company_id:
                    product_vals["company_id"] = company_id
                
                product_id = models.execute_kw(db, uid, password, "product.template", "create", [product_vals])
                log_container.success(f"✓ Product Created: {product_id}")
                
                execute_button(product_id, "action_submit", models, db, uid, password)
                execute_button(product_id, "action_approve", models, db, uid, password)
                results.append({"SKU": sku, "Product Name": product_name, "Status": "Success", 
                               "Action": "Created", "Message": f"Created ID {product_id} with routes: Resupply({RESUPPLY_ROUTE_ID}), Buy({BUY_ROUTE_ID})"})
        except Exception as e:
            log_container.error(f"Error on row {index + 1}: {str(e)}")
            results.append({"SKU": sku, "Product Name": product_name, "Status": "Error", 
                           "Action": "Failed", "Message": str(e)})
    
    return results

def process_bom(df, models, db, uid, password, log_container, branch_filter=None):
    # Apply branch filter
    df = filter_data_by_branch(df, branch_filter)
    
    if df.empty:
        log_container.warning(f"No BOMs to process for branch: {branch_filter}")
        return []
    
    results = []
    
    for index, row in df.iterrows():
        finished_sku, component_sku = "Unknown", "Unknown"
        try:
            finished_sku = str(row.get("Finished_SKU", "")).strip()
            component_sku = str(row.get("Component_SKU", "")).strip()
            component_qty = float(row.get("Component_Qty", 0.0))
            subcontractor_name = str(row.get("Subcontractor", "")).strip()
            company_name = str(row.get("Company", "")).strip() if "Company" in df.columns else None
            
            log_container.write(f"**Processing BOM:** {finished_sku} (Component: {component_sku})")
            
            # Get Finished Product Template
            finished_product = models.execute_kw(
                db, uid, password,
                'product.template',
                'search_read',
                [[('sku', '=', finished_sku)]],
                {'fields': ['id', 'name', 'sku'], 'limit': 1}
            )
            if not finished_product:
                raise Exception(f"Finished Product not found: {finished_sku}")
            finished_product_tmpl_id = finished_product[0]['id']
            
            # Get Component Product Template
            component_template = models.execute_kw(
                db, uid, password,
                'product.template',
                'search_read',
                [[('sku', '=', component_sku)]],
                {'fields': ['id', 'name', 'sku'], 'limit': 1}
            )
            if not component_template:
                raise Exception(f"Component Product not found: {component_sku}")
            component_template_id = component_template[0]['id']
            
            # Get Component Variant
            component_variant = models.execute_kw(
                db, uid, password,
                'product.product',
                'search_read',
                [[('product_tmpl_id', '=', component_template_id)]],
                {'fields': ['id', 'display_name'], 'limit': 1}
            )
            if not component_variant:
                raise Exception(f"No variant found for {component_sku}")
            component_product_id = component_variant[0]['id']
            
            # Get Subcontractor
            subcontractor = models.execute_kw(
                db, uid, password,
                'res.partner',
                'search_read',
                [[('name', '=', subcontractor_name)]],
                {'fields': ['id', 'name'], 'limit': 1}
            )
            if not subcontractor:
                raise Exception(f"Subcontractor not found: {subcontractor_name}")
            subcontractor_id = subcontractor[0]['id']
            
            # Get company ID if provided
            company_id = None
            if company_name:
                company_id = get_company_id(company_name, models, db, uid, password)
                if company_id:
                    log_container.write(f"Company: {company_name} (ID: {company_id})")
            
            # Check Existing BOM
            existing_bom = models.execute_kw(
                db, uid, password,
                'mrp.bom',
                'search',
                [[('product_tmpl_id', '=', finished_product_tmpl_id)]],
                {'limit': 1}
            )
            if existing_bom:
                log_container.info(f"⚠️ BOM already exists for {finished_sku}. ID: {existing_bom[0]}")
                results.append({"Finished SKU": finished_sku, "Component SKU": component_sku, 
                               "Status": "Skipped", "Message": f"BOM already exists (ID: {existing_bom[0]})"})
                continue
            
            # Create BOM
            bom_vals = {
                'product_tmpl_id': finished_product_tmpl_id,
                'product_qty': component_qty,
                'type': 'subcontract',
                'subcontractor_ids': [(6, 0, [subcontractor_id])],
                'bom_line_ids': [(0, 0, {
                    'product_id': component_product_id,
                    'product_qty': component_qty
                })]
            }
            if company_id:
                bom_vals['company_id'] = company_id
            
            bom_id = models.execute_kw(db, uid, password, 'mrp.bom', 'create', [bom_vals])
            log_container.success(f"✅ BOM Created Successfully for {finished_sku}. BOM ID: {bom_id}")
            results.append({"Finished SKU": finished_sku, "Component SKU": component_sku, 
                           "Status": "Success", "Message": f"Created BOM ID {bom_id}"})
        except Exception as e:
            log_container.error(f"Error on row {index + 1}: {str(e)}")
            results.append({"Finished SKU": finished_sku, "Component SKU": component_sku, 
                           "Status": "Error", "Message": str(e)})
    
    return results

def process_purchase_order(df, models, db, uid, password, log_container, branch_filter=None):
    # Apply branch filter
    df = filter_data_by_branch(df, branch_filter)
    
    if df.empty:
        log_container.warning(f"No purchase orders to process for branch: {branch_filter}")
        return []
    
    results = []
    
    try:
        # Validate required columns
        required_cols = ["Vendor_Name", "Purchase_Team", "Product_Name", "Qty", "Price_Unit", "Discount", "Partner_Ref"]
        for col in required_cols:
            if col not in df.columns:
                raise Exception(f"Missing column: {col}")
        
        # Get PO header details from first row
        vendor_name = str(df.iloc[0]["Vendor_Name"]).strip()
        purchase_team_name = str(df.iloc[0]["Purchase_Team"]).strip()
        partner_ref = str(df.iloc[0]["Partner_Ref"]).strip()
        company_name = str(df.iloc[0].get("Company", "")).strip() if "Company" in df.columns else None
        
        log_container.write("=" * 80)
        log_container.write("CREATING SINGLE PURCHASE ORDER")
        log_container.write("=" * 80)
        log_container.write(f"Vendor       : {vendor_name}")
        log_container.write(f"Purchase Team: {purchase_team_name}")
        log_container.write(f"Partner Ref  : {partner_ref}")
        log_container.write(f"Company      : {company_name if company_name else 'Default'}")
        log_container.write("=" * 80)
        
        # Get Vendor
        partner = models.execute_kw(
            db, uid, password,
            'res.partner',
            'search_read',
            [[('name', '=', vendor_name)]],
            {'fields': ['id', 'name'], 'limit': 1}
        )
        if not partner:
            raise Exception(f"Vendor not found: {vendor_name}")
        partner_id = partner[0]['id']
        
        # Get Purchase Team
        team = models.execute_kw(
            db, uid, password,
            'purchase.team',
            'search_read',
            [[('name', '=', purchase_team_name)]],
            {'fields': ['id', 'name'], 'limit': 1}
        )
        if not team:
            raise Exception(f"Purchase Team not found: {purchase_team_name}")
        team_id = team[0]['id']
        
        # Get Company
        company_id = None
        if company_name:
            company_id = get_company_id(company_name, models, db, uid, password)
            if company_id:
                log_container.write(f"Company Found: {company_name} (ID: {company_id})")
            else:
                log_container.warning(f"Company not found: {company_name}. Using default company.")
        
        # Build PO Lines
        order_lines = []
        skipped_products = []
        
        for index, row in df.iterrows():
            try:
                product_name = str(row["Product_Name"]).strip()
                qty = float(row["Qty"])
                price_unit = float(row["Price_Unit"])
                discount = float(row["Discount"])
                
                log_container.write(f"Processing Product {index + 1} -> {product_name}")
                
                # Get Product Template
                product_template = models.execute_kw(
                    db, uid, password,
                    'product.template',
                    'search_read',
                    [[('name', '=', product_name)]],
                    {'fields': ['id', 'name'], 'limit': 1}
                )
                if not product_template:
                    skipped_products.append(product_name)
                    log_container.warning(f"Product not found: {product_name}")
                    continue
                
                product_template_id = product_template[0]['id']
                product_description = product_template[0]['name']
                
                # Get Product Variant
                product_variant = models.execute_kw(
                    db, uid, password,
                    'product.product',
                    'search_read',
                    [[('product_tmpl_id', '=', product_template_id)]],
                    {'fields': ['id', 'display_name'], 'limit': 1}
                )
                if not product_variant:
                    skipped_products.append(product_name)
                    log_container.warning(f"Product Variant not found: {product_name}")
                    continue
                
                product_id = product_variant[0]['id']
                
                # Add Order Line
                order_lines.append(
                    (0, 0, {
                        'name': product_description,
                        'product_id': product_id,
                        'product_template_id': product_template_id,
                        'product_qty': qty,
                        'price_unit': price_unit,
                        'discount': discount
                    })
                )
                log_container.write(f"Added -> {product_name} | Qty={qty}")
                
            except Exception as e:
                log_container.error(f"Error in row {index + 1}: {str(e)}")
                results.append({
                    "Vendor": vendor_name, 
                    "Product": row.get("Product_Name", "Unknown"), 
                    "Status": "Error", 
                    "Message": str(e)
                })
        
        if not order_lines:
            raise Exception("No valid products found in Excel")
        
        if skipped_products:
            log_container.warning(f"Skipped {len(skipped_products)} products: {', '.join(skipped_products)}")
        
        # Create Purchase Order
        po_vals = {
            'partner_id': partner_id,
            'team_id': team_id,
            'partner_ref': partner_ref,
            'order_line': order_lines
        }
        if company_id:
            po_vals['company_id'] = company_id
        
        po_id = models.execute_kw(db, uid, password, 'purchase.order', 'create', [po_vals])
        log_container.write(f"\nPurchase Order Created. PO ID: {po_id}")
        
        # Confirm PO
        models.execute_kw(db, uid, password, 'purchase.order', 'button_confirm', [[po_id]])
        log_container.write("Purchase Order Confirmed")
        
        # Approve PO
        models.execute_kw(db, uid, password, 'purchase.order', 'button_approve', [[po_id]])
        log_container.write("Purchase Order Approved")
        
        # Get PO Number
        po = models.execute_kw(db, uid, password, 'purchase.order', 'read', [[po_id]], {'fields': ['name']})
        po_number = po[0]['name']
        
        log_container.success(f"\n✅ PO Number: {po_number}")
        
        # Add success result for each row
        for index, row in df.iterrows():
            results.append({
                "Vendor": vendor_name, 
                "Product": row.get("Product_Name", "Unknown"), 
                "Status": "Success", 
                "Message": f"PO Created: {po_number}"
            })
        
    except Exception as e:
        log_container.error(f"Error creating Purchase Order: {str(e)}")
        for index, row in df.iterrows():
            results.append({
                "Vendor": row.get("Vendor_Name", "Unknown"), 
                "Product": row.get("Product_Name", "Unknown"), 
                "Status": "Error", 
                "Message": str(e)
            })
    
    return results

def process_resupply(df, models, db, uid, password, log_container, branch_filter=None):
    # Apply branch filter
    df = filter_data_by_branch(df, branch_filter)
    
    if df.empty:
        log_container.warning(f"No resupplies to process for branch: {branch_filter}")
        return []
    
    results = []
    
    try:
        # Validate required columns
        required_cols = ["Purchase_order", "Product_Name", "Lot_Number", "Source_Location"]
        for col in required_cols:
            if col not in df.columns:
                raise Exception(f"Missing column: {col}")
        
        # Build Mapping: (PO, Product) -> Lots + Source Location
        mapping = {}
        
        for _, row in df.iterrows():
            po = str(row["Purchase_order"]).strip()
            product = str(row["Product_Name"]).strip()
            lot = str(row["Lot_Number"]).strip()
            source_location = str(row["Source_Location"]).strip()
            
            key = (po, normalize_product_name(product))
            
            if key not in mapping:
                mapping[key] = {
                    "lots": [],
                    "source_location": source_location
                }
            
            mapping[key]["lots"].append(lot)
        
        log_container.write(f"Built mapping with {len(mapping)} unique (PO, Product) combinations")
        
        # Process each PO
        for po_number in df["Purchase_order"].dropna().unique():
            po_number = str(po_number).strip()
            
            log_container.write("=" * 80)
            log_container.write(f"PO : {po_number}")
            log_container.write("=" * 80)
            
            # Get PO
            po = models.execute_kw(
                db, uid, password,
                'purchase.order',
                'search_read',
                [[('name', '=', po_number)]],
                {'fields': ['id', 'picking_ids'], 'limit': 1}
            )
            
            if not po:
                log_container.warning(f"PO Not Found: {po_number}")
                results.append({"PO Number": po_number, "Status": "Error", "Message": "PO Not Found"})
                continue
            
            if not po[0]["picking_ids"]:
                log_container.warning(f"No Receipt Picking Found for PO: {po_number}")
                results.append({"PO Number": po_number, "Status": "Error", "Message": "No Receipt Picking Found"})
                continue
            
            receipt_picking_id = po[0]["picking_ids"][0]
            
            # Get Receipt
            receipt = models.execute_kw(
                db, uid, password,
                'stock.picking',
                'read',
                [[receipt_picking_id]],
                {'fields': ['name']}
            )
            
            receipt_name = receipt[0]["name"]
            log_container.write(f"Receipt: {receipt_name}")
            
            # Get Resupply Pickings
            resupplies = models.execute_kw(
                db, uid, password,
                'stock.picking',
                'search_read',
                [[('origin', '=', receipt_name)]],
                {'fields': ['id', 'name', 'location_id', 'state']}
            )
            
            if not resupplies:
                log_container.warning(f"No Resupply Pickings found for Receipt: {receipt_name}")
                results.append({"PO Number": po_number, "Status": "Error", "Message": "No Resupply Pickings Found"})
                continue
            
            for resupply in resupplies:
                picking_id = resupply["id"]
                resupply_name = resupply["name"]
                
                log_container.write(f"\nResupply: {resupply_name} (State: {resupply['state']})")
                
                if resupply["state"] == "done":
                    log_container.info(f"Skipping {resupply_name} because it is already validated.")
                    results.append({"PO Number": po_number, "Resupply": resupply_name, 
                                   "Status": "Skipped", "Message": "Already validated"})
                    continue
                
                processed_move_found = False
                
                # Get Moves
                moves = models.execute_kw(
                    db, uid, password,
                    'stock.move',
                    'search_read',
                    [[('picking_id', '=', picking_id)]],
                    {'fields': ['id', 'product_id', 'product_uom_qty', 'location_id', 'location_dest_id']}
                )
                
                for move in moves:
                    move_id = move["id"]
                    product_id = move["product_id"][0]
                    product_name = move["product_id"][1]
                    
                    normalized_product_name = normalize_product_name(product_name)
                    key = (po_number, normalized_product_name)
                    
                    if key not in mapping:
                        log_container.warning(f"No mapping found for {product_name} (Normalized: {normalized_product_name})")
                        continue
                    
                    processed_move_found = True
                    
                    lots = mapping[key]["lots"]
                    source_location_name = mapping[key]["source_location"]
                    
                    log_container.write(f"\n✅ MATCH FOUND")
                    log_container.write(f"Product : {product_name}")
                    log_container.write(f"Lots : {lots}")
                    log_container.write(f"Move ID : {move_id}")
                    
                    demand_qty = int(move["product_uom_qty"])
                    
                    if len(lots) != demand_qty:
                        raise Exception(
                            f"Lot Count Mismatch for {product_name}. "
                            f"Demand={demand_qty}, Lots={len(lots)}"
                        )
                    
                    # Get Source Location
                    location = models.execute_kw(
                        db, uid, password,
                        'stock.location',
                        'search_read',
                        [[('complete_name', '=', source_location_name)]],
                        {'fields': ['id'], 'limit': 1}
                    )
                    
                    if not location:
                        raise Exception(f"Location Not Found: {source_location_name}")
                    
                    source_location_id = location[0]["id"]
                    destination_location_id = move["location_dest_id"][0]
                    
                    # Update Picking Location
                    models.execute_kw(
                        db, uid, password,
                        'stock.picking',
                        'write',
                        [[picking_id], {'location_id': source_location_id}]
                    )
                    
                    # Update Move Location
                    models.execute_kw(
                        db, uid, password,
                        'stock.move',
                        'write',
                        [[move_id], {'location_id': source_location_id}]
                    )
                    
                    # Delete existing move lines
                    existing_lines = models.execute_kw(
                        db, uid, password,
                        'stock.move.line',
                        'search_read',
                        [[('move_id', '=', move_id)]],
                        {'fields': ['id']}
                    )
                    
                    for line in existing_lines:
                        models.execute_kw(
                            db, uid, password,
                            'stock.move.line',
                            'unlink',
                            [[line["id"]]]
                        )
                    
                    log_container.write(f"Deleted {len(existing_lines)} existing move lines")
                    
                    # Create new move lines for each lot
                    for lot_number in lots:
                        lot = models.execute_kw(
                            db, uid, password,
                            'stock.lot',
                            'search_read',
                            [[('name', '=', lot_number)]],
                            {'fields': ['id'], 'limit': 1}
                        )
                        
                        if not lot:
                            raise Exception(f"Lot Not Found: {lot_number}")
                        
                        lot_id = lot[0]["id"]
                        
                        move_line_id = models.execute_kw(
                            db, uid, password,
                            'stock.move.line',
                            'create',
                            [{
                                'move_id': move_id,
                                'product_id': product_id,
                                'lot_id': lot_id,
                                'lot_name': lot_number,
                                'quantity': 1,
                                'manual_qty_done': 1,
                                'picked': True,
                                'location_id': source_location_id,
                                'location_dest_id': destination_location_id
                            }]
                        )
                        
                        log_container.write(f"Created Move Line -> {lot_number} ({move_line_id})")
                
                if processed_move_found:
                    log_container.write("\n" + "=" * 80)
                    log_container.write(f"VALIDATING : {resupply_name}")
                    log_container.write("=" * 80)
                    
                    models.execute_kw(
                        db, uid, password,
                        'stock.picking',
                        'button_validate',
                        [[picking_id]]
                    )
                    
                    log_container.success(f"✅ Resupply Validated: {resupply_name}")
                    
                    results.append({
                        "PO Number": po_number, 
                        "Resupply": resupply_name, 
                        "Status": "Success", 
                        "Message": "Resupply validated"
                    })
                else:
                    log_container.warning(
                        f"Skipping validation for {resupply_name} "
                        f"because no matching product was found in Excel."
                    )
                    results.append({
                        "PO Number": po_number, 
                        "Resupply": resupply_name, 
                        "Status": "Skipped", 
                        "Message": "No matching product found"
                    })
            
            # Validate Receipt if not already done
            receipt_state = models.execute_kw(
                db, uid, password,
                'stock.picking',
                'read',
                [[receipt_picking_id]],
                {'fields': ['state']}
            )[0]['state']
            
            if receipt_state != 'done':
                models.execute_kw(
                    db, uid, password,
                    'stock.picking',
                    'button_validate',
                    [[receipt_picking_id]]
                )
                log_container.success(f"✅ Receipt Validated: {receipt_name}")
            else:
                log_container.info(f"Receipt already validated: {receipt_name}")
        
        log_container.write("\nCompleted Successfully")
        
    except Exception as e:
        log_container.error(f"Error processing Resupply: {str(e)}")
        for index, row in df.iterrows():
            results.append({
                "PO Number": row.get("Purchase_order", "Unknown"), 
                "Status": "Error", 
                "Message": str(e)
            })
    
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
        skipped = sum(1 for r in results if r.get('Status') == 'Skipped')
        
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
            st.markdown(f"""
<div class="metric-card">
<div class="metric-value" style="color: #ffc107;">{skipped}</div>
<div class="metric-label">Skipped</div>
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
<li>🏭 Bill Of Materials (BOM) Management</li>
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
    
    # ==========================================
    # BRANCH SELECTOR
    # ==========================================
    st.markdown("""
    <div class="branch-selector">
        <h3 style="margin-top: 0;">🏢 Branch Filter</h3>
        <p style="color: #6c757d; font-size: 0.9rem;">Select a branch to filter operations. This affects all automation processes.</p>
    </div>
    """, unsafe_allow_html=True)
    
    branch = st.selectbox(
        "Select Branch:",
        options=BRANCH_OPTIONS,
        index=0,
        help="Select the branch to filter operations. 'All' will process without branch filtering."
    )
    st.session_state.selected_branch = branch
    
    # Create tabs for different operations
    tab1, tab2, tab3, tab4 = st.tabs(["📦 Product Creation", "🏭 Bill Of Materials", "📄 Purchase Orders", "🔄 Resupply"])
    
    process_configs = {
        tab1: {
            "name": "Product Creation",
            "cols": ["Product Name", "SKU", "Category", "Sales Price", "Cost Price"],
            "msg": "Upload Excel with columns: Product Name, SKU, Category, Sales Price, Cost Price\nOptional: Branch, Company columns for filtering"
        },
        tab2: {
            "name": "Bill Of Materials",
            "cols": ["Finished_SKU", "Component_SKU", "Component_Qty", "Subcontractor"],
            "msg": "Upload Excel with columns: Finished_SKU, Component_SKU, Component_Qty, Subcontractor\nOptional: Branch, Company columns for filtering"
        },
        tab3: {
            "name": "Purchaseorder",
            "cols": ["Vendor_Name", "Purchase_Team", "Product_Name", "Qty", "Price_Unit", "Discount", "Partner_Ref"],
            "msg": "Upload Excel with columns: Vendor_Name, Purchase_Team, Product_Name, Qty, Price_Unit, Discount, Partner_Ref\nOptional: Branch, Company columns for filtering"
        },
        tab4: {
            "name": "Resupply",
            "cols": ["Purchase_order", "Product_Name", "Lot_Number", "Source_Location"],
            "msg": "Upload Excel with columns: Purchase_order, Product_Name, Lot_Number, Source_Location\nOptional: Branch column for filtering"
        }
    }
    
    for tab, config in process_configs.items():
        with tab:
            st.header(config['name'])
            
            # Show active branch filter
            if branch != "All":
                st.info(f"🔍 Active Branch Filter: **{branch}**")
            else:
                st.info("🔍 No branch filter applied. Processing all branches.")
            
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
                    
                    # Preview data with branch filter applied
                    filtered_df = filter_data_by_branch(df, branch)
                    
                    with st.expander("📊 Preview Data", expanded=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Total Records", len(df))
                        with col2:
                            st.metric("Filtered Records", len(filtered_df))
                        
                        st.dataframe(filtered_df.head(10), use_container_width=True)
                        
                        if len(filtered_df) < len(df):
                            st.caption(f"Showing {len(filtered_df)} of {len(df)} records (filtered by branch: {branch})")
                        else:
                            st.caption(f"Total rows: {len(filtered_df)}")
                    
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
                                    results = process_product_creation(df, models, os.getenv('ODOO_DB'), 
                                                                      uid, os.getenv('ODOO_PASSWORD'), 
                                                                      log_container, branch)
                                elif config['name'] == "Bill Of Materials":
                                    results = process_bom(df, models, os.getenv('ODOO_DB'), 
                                                         uid, os.getenv('ODOO_PASSWORD'), 
                                                         log_container, branch)
                                elif config['name'] == "Purchaseorder":
                                    results = process_purchase_order(df, models, os.getenv('ODOO_DB'), 
                                                                    uid, os.getenv('ODOO_PASSWORD'), 
                                                                    log_container, branch)
                                elif config['name'] == "Resupply":
                                    results = process_resupply(df, models, os.getenv('ODOO_DB'), 
                                                              uid, os.getenv('ODOO_PASSWORD'), 
                                                              log_container, branch)
                            
                            st.success(f"✅ Execution complete! Processed {len(results)} records.")
                            
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
<p style="margin-top: 0.5rem;">Enterprise Automation Solution</p>
</div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
