from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import date
import uuid

app = Flask(__name__)
CORS(app)

USERS = [
    {"id": 1, "name": "Aarav Admin", "email": "admin@furnivo.demo", "password": "admin123", "role": "admin"},
    {"id": 2, "name": "Meera Sales", "email": "sales@furnivo.demo", "password": "sales123", "role": "sales"},
    {"id": 3, "name": "Kabir Designer", "email": "designer@furnivo.demo", "password": "design123", "role": "designer"},
    {"id": 4, "name": "Riya Client", "email": "client@furnivo.demo", "password": "client123", "role": "client"},
]

PRODUCTS = [
    {
        "id": 1,
        "sku": "FUR-SOF-101",
        "name": "Aster Modular Sofa",
        "category": "Furniture",
        "price": 78500,
        "unit": "set",
        "material": "Oak frame, performance fabric",
        "image": "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&w=900&q=80",
    },
    {
        "id": 2,
        "sku": "INT-LGT-204",
        "name": "Halo Pendant Light",
        "category": "Interiors",
        "price": 12400,
        "unit": "piece",
        "material": "Powder-coated metal, frosted glass",
        "image": "https://images.unsplash.com/photo-1540932239986-30128078f3c5?auto=format&fit=crop&w=900&q=80",
    },
    {
        "id": 3,
        "sku": "BLD-PNL-310",
        "name": "Terra Fluted Wall Panel",
        "category": "Building Material",
        "price": 920,
        "unit": "sq.ft",
        "material": "WPC acoustic panel",
        "image": "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=900&q=80",
    },
]

QUOTES = [
    {"id": "Q-1042", "customer": "Northline Studio", "amount": 186400, "status": "Sent", "date": "2026-09-18"},
    {"id": "Q-1041", "customer": "The Green House", "amount": 94200, "status": "Draft", "date": "2026-09-17"},
    {"id": "Q-1038", "customer": "Avenue Architects", "amount": 328500, "status": "Approved", "date": "2026-09-12"},
]

LEADS = [
    {"id": 1, "name": "Sana Kapoor", "company": "SK Atelier", "phone": "+91 98111 22334", "source": "Website", "stage": "New", "value": 240000},
    {"id": 2, "name": "Arjun Mehta", "company": "Mehta Homes", "phone": "+91 98770 11228", "source": "Referral", "stage": "Qualified", "value": 510000},
    {"id": 3, "name": "Devika Rao", "company": "Form & Field", "phone": "+91 98990 33001", "source": "Instagram", "stage": "Proposal", "value": 175000},
    {"id": 4, "name": "Neil Thomas", "company": "NTH Build", "phone": "+91 97110 81020", "source": "Exhibition", "stage": "Won", "value": 690000},
]

TOKENS = {}

def public_user(user):
    return {key: user[key] for key in ("id", "name", "email", "role")}

def current_user():
    header = request.headers.get("Authorization", "")
    token = header.replace("Bearer ", "", 1) if header.startswith("Bearer ") else ""
    return TOKENS.get(token)

def require_roles(*roles):
    user = current_user()
    if not user:
        return None, (jsonify({"message": "Unauthorized"}), 401)
    if roles and user["role"] not in roles:
        return None, (jsonify({"message": "Forbidden"}), 403)
    return user, None

@app.get("/api/health")
def health():
    return jsonify({"ok": True, "service": "furnivo-api"})

@app.post("/api/auth/register")
def register():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))

    if not name or not email or len(password) < 6:
        return jsonify({"message": "name, email and a 6+ character password are required"}), 400

    if any(user["email"].lower() == email for user in USERS):
        return jsonify({"message": "An account with this email already exists."}), 409

    user = {
        "id": max(user["id"] for user in USERS) + 1,
        "name": name,
        "email": email,
        "password": password,
        "role": "client",
    }
    USERS.append(user)

    token = str(uuid.uuid4())
    TOKENS[token] = user
    return jsonify({"token": token, "user": public_user(user), "mode": "api"}), 201

@app.post("/api/auth/login")
def login():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).lower()
    password = str(payload.get("password", ""))

    user = next(
        (u for u in USERS if u["email"].lower() == email and u["password"] == password),
        None,
    )
    if not user:
        return jsonify({"message": "Invalid email or password"}), 401

    token = str(uuid.uuid4())
    TOKENS[token] = user
    return jsonify({"token": token, "user": public_user(user), "mode": "api"})

@app.get("/api/products")
def products():
    _, error = require_roles("admin", "sales", "designer", "client")
    if error:
        return error
    return jsonify({"items": PRODUCTS, "mode": "api"})

@app.get("/api/quotes")
def quotes():
    _, error = require_roles("admin", "sales", "designer")
    if error:
        return error
    return jsonify({"items": QUOTES, "mode": "api"})

@app.post("/api/quotes")
def create_quote():
    _, error = require_roles("admin", "sales", "designer")
    if error:
        return error

    payload = request.get_json(silent=True) or {}
    if not payload.get("customer") or not payload.get("amount"):
        return jsonify({"message": "customer and amount are required"}), 400

    quote = {
        "id": f"Q-{1043 + len(QUOTES)}",
        "customer": payload["customer"],
        "amount": float(payload["amount"]),
        "status": "Draft",
        "date": date.today().isoformat(),
    }
    QUOTES.insert(0, quote)
    return jsonify({"item": quote, "mode": "api"}), 201

@app.get("/api/leads")
def leads():
    _, error = require_roles("admin", "sales")
    if error:
        return error
    return jsonify({"items": LEADS, "mode": "api"})

@app.patch("/api/leads/<int:lead_id>")
def update_lead(lead_id):
    _, error = require_roles("admin", "sales")
    if error:
        return error

    payload = request.get_json(silent=True) or {}
    stage = payload.get("stage")
    allowed_stages = {"New", "Qualified", "Proposal", "Won"}

    if stage not in allowed_stages:
        return jsonify({"message": "Invalid stage"}), 400

    lead = next((lead for lead in LEADS if lead["id"] == lead_id), None)
    if not lead:
        return jsonify({"message": "Lead not found"}), 404

    lead["stage"] = stage
    return jsonify({"item": lead, "mode": "api"})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
