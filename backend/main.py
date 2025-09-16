import os
import stripe
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase import create_client

# Cargar variables de entorno
load_dotenv()

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not all([STRIPE_SECRET_KEY, STRIPE_PRICE_ID, SUPABASE_URL, SUPABASE_SERVICE_KEY]):
    raise Exception("Faltan variables de entorno necesarias")

stripe.api_key = STRIPE_SECRET_KEY
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

app = FastAPI(title="Fitness AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PredictInput(BaseModel):
    age: int
    sex: str
    weight: float
    height: float

@app.post("/predict")
def predict_free(data: PredictInput):
    tmb = 10 * data.weight + 6.25 * data.height - 5 * data.age + (5 if data.sex.upper().startswith("M") else -161)
    mantenimiento = round(tmb * 1.55)
    return {
        "calorias_mantenimiento": mantenimiento,
        "rutina_demo": "Fullbody 3x semana (demo gratuita)"
    }

@app.post("/create-checkout-session")
def create_checkout_session(payload: dict):
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="email required")
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        customer_email=email,
        line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
        mode="subscription",
        success_url=f"{FRONTEND_URL}/dashboard",
        cancel_url=f"{FRONTEND_URL}/premium"
    )
    return {"checkout_url": session.url}

@app.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_email = session.get("customer_email")
        if customer_email:
            supabase.table("profiles").upsert({"email": customer_email, "is_premium": True}).execute()

    return {"status": "ok"}

@app.post("/plan-premium")
def plan_premium(payload: dict):
    email = payload.get("email")
    if not email:
        raise HTTPException(400, "email required")
    res = supabase.table("profiles").select("*").eq("email", email).single().execute()
    row = res.data
    if not row or not row.get("is_premium"):
        raise HTTPException(403, "Requiere suscripción premium")
    kcal = 2200
    protein = 2.0 * (row.get("weight") or 75)
    carbs = 3 * (row.get("weight") or 75)
    fat = round((kcal - protein * 4 - carbs * 4) / 9)
    return {
        "macros": {"calorias": kcal, "proteina_g": int(protein), "carbohidratos_g": int(carbs), "grasas_g": int(fat)},
        "rutina": {
            "Lunes": ["Sentadillas 4x8", "Press Banca 4x6"],
            "Miercoles": ["Remo 4x8", "Peso muerto 3x5"],
            "Viernes": ["Press militar 4x8", "Curl bíceps 3x10"]
        }
    }
