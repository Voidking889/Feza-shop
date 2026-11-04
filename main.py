import os
import json
import uuid
import time
import asyncio
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, Request, BackgroundTasks, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
import stripe
from dotenv import load_dotenv
from app.services.email_service import send_invoice_email, send_topup_pin_email

# In-memory storage for transaction verification pins
verification_pins = {}

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
if not stripe.api_key:
    print("[WARN] Stripe is disabled. Set STRIPE_SECRET_KEY in .env to enable payments.")

NMB_API_KEY = os.getenv('NMB_API_KEY')
NMB_CONSUMER_SECRET = os.getenv('NMB_CONSUMER_SECRET')
NMB_CONSUMER_ID = os.getenv('NMB_CONSUMER_ID')

transactions = {}
invoices = {}

@app.middleware("http")
async def protect_private_files(request, call_next):
    if any(part.startswith(".") for part in request.url.path.strip("/").split("/")):
        return Response(status_code=404)
    return await call_next(request)

@app.get("/payment")
async def get_payment():
    return FileResponse(BASE_DIR / "feza-pay.html")

@app.get("/test-page")
async def get_test_page():
    return FileResponse(BASE_DIR / "test.html")

@app.post("/create-payment-intent")
async def create_payment_intent(request: Request):
    if not stripe.api_key:
        return JSONResponse(status_code=503, content={
            "status": "failed",
            "message": "Stripe is not configured on the server."
        })

    try:
        data = await request.json()
        amount = data.get('amount')
        currency = data.get('currency')
        customer_email = data.get('customerEmail')

        if not amount or not currency:
            return JSONResponse(status_code=400, content={
                "status": "failed",
                "message": "A positive amount and currency are required."
            })
            
        payment_intent = stripe.PaymentIntent.create(
            amount=round(float(amount)),
            currency=currency,
            automatic_payment_methods={"enabled": True}
        )
        
        return JSONResponse(content={
            "status": "success",
            "clientSecret": payment_intent.client_secret,
            "paymentIntentId": payment_intent.id
        })
    except Exception as e:
        error_msg = str(e)
        print('Stripe Error:', error_msg)
        # Return the error message to the frontend so it's easier to debug
        return JSONResponse(status_code=400, content={
            "status": "error",
            "message": error_msg,
            "note": "Verify your STRIPE_SECRET_KEY in the backend."
        })

async def simulate_payment_completion(transaction_id: str):
    await asyncio.sleep(2)
    if transaction_id in transactions and transactions[transaction_id]['status'] == 'pending':
        transactions[transaction_id]['payment_stages'].append({
            'stage': 'request_received',
            'time': datetime.utcnow().isoformat() + "Z",
            'status': 'success',
            'message': 'Payment request received by mobile network'
        })
        print(f"[API LOG] Transaction {transaction_id} - Payment request received by mobile network")
        
    await asyncio.sleep(2)
    if transaction_id in transactions and transactions[transaction_id]['status'] == 'pending':
        transactions[transaction_id]['payment_stages'].append({
            'stage': 'prompt_sent',
            'time': datetime.utcnow().isoformat() + "Z",
            'status': 'success',
            'message': 'Payment prompt sent to user phone'
        })
        print(f"[API LOG] Transaction {transaction_id} - Payment prompt sent to user phone")

    await asyncio.sleep(2)
    if transaction_id in transactions and transactions[transaction_id]['status'] == 'pending':
        transactions[transaction_id]['payment_stages'].append({
            'stage': 'user_confirmed',
            'time': datetime.utcnow().isoformat() + "Z",
            'status': 'success',
            'message': 'User confirmed payment on mobile device'
        })
        print(f"[API LOG] Transaction {transaction_id} - User confirmed payment on mobile device")

    await asyncio.sleep(2)
    if transaction_id in transactions and transactions[transaction_id]['status'] == 'pending':
        transactions[transaction_id]['status'] = 'completed'
        transactions[transaction_id]['payment_stages'].append({
            'stage': 'payment_completed',
            'time': datetime.utcnow().isoformat() + "Z",
            'status': 'success',
            'message': 'Payment successfully processed and completed'
        })
        
        invoice_id = 'INV-' + str(int(time.time() * 1000)) + str(uuid.uuid4())[:5]
        transactions[transaction_id]['invoice_id'] = invoice_id
        
        transaction = transactions[transaction_id]
        amount_val = float(transaction['amount'])
        
        invoice = {
            'invoice_id': invoice_id,
            'transaction_id': transaction_id,
            'merchant_id': transaction.get('merchant'),
            'customer_phone': transaction.get('phone'),
            'customer_email': transaction.get('customer_email'),
            'date': datetime.utcnow().isoformat() + "Z",
            'items': transaction.get('items', []),
            'payment_method': {
                'type': 'mobile_money',
                'network': transaction.get('network')
            },
            'amount': {
                'subtotal': amount_val - 5.99 - (amount_val * 0.1),
                'shipping': 5.99,
                'tax': amount_val * 0.1,
                'total': amount_val
            },
            'status': 'paid'
        }
        
        invoices[invoice_id] = invoice
        print(f"[API LOG] Transaction {transaction_id} successfully COMPLETED.")
        print(f"[API LOG] Invoice {invoice_id} generated.")
        
        # Send automated invoice email via Gmail SMTP
        customer_email_addr = transaction.get('customer_email')
        if customer_email_addr and customer_email_addr != 'N/A':
            print(f"[EMAIL] Sending invoice email to {customer_email_addr}...")
            await send_invoice_email(customer_email_addr, invoice)
        else:
            print("[EMAIL] No customer email provided — skipping invoice email.")

@app.post("/api/v1/mobile_payment")
async def mobile_payment(request: Request, background_tasks: BackgroundTasks, authorization: str = Header(None)):
    data = await request.json()
    merchant_id = data.get('merchant_id')
    phone_number = data.get('phone_number')
    amount = data.get('amount')
    network = data.get('network')
    items = data.get('items', [])
    customer_email = data.get('customer_email')
    
    if not merchant_id or not authorization:
        return JSONResponse(status_code=401, content={'status': 'failed', 'message': 'Authentication required (Missing Merchant ID or API Key).'})
        
    provided_api_key = authorization.replace('Bearer ', '')
    if NMB_API_KEY and provided_api_key != NMB_API_KEY:
        return JSONResponse(status_code=401, content={'status': 'failed', 'message': 'Invalid API credentials.'})
        
    if not phone_number or not amount or network == 'Select Network':
        return JSONResponse(status_code=400, content={'status': 'failed', 'message': 'Missing required payment details.'})
        
    transaction_id = 'TXN-' + str(int(time.time() * 1000)) + str(uuid.uuid4())[:9]
    
    transactions[transaction_id] = {
        'id': transaction_id,
        'merchant': merchant_id,
        'phone': phone_number,
        'amount': amount,
        'network': network,
        'status': 'pending',
        'time': datetime.utcnow().isoformat() + "Z",
        'items': items,
        'customer_email': customer_email,
        'payment_stages': [
            {'stage': 'initiated', 'time': datetime.utcnow().isoformat() + "Z", 'status': 'success'}
        ]
    }
    
    print(f"[API LOG] Payment initiated. ID: {transaction_id}, Amount: ${amount}, Status: pending")
    
    background_tasks.add_task(simulate_payment_completion, transaction_id)
    
    return JSONResponse(content={
        'status': 'success',
        'message': f'Payment request successfully sent to phone number {phone_number}. Awaiting confirmation.',
        'transaction_id': transaction_id
    })
    
@app.get("/api/v1/transaction_status/{transactionId}")
async def transaction_status(transactionId: str):
    if transactionId not in transactions:
        return JSONResponse(status_code=404, content={'status': 'not_found', 'message': 'Transaction ID not found.'})
        
    transaction = transactions[transactionId]
    status_val = transaction['status']
    
    return JSONResponse(content={
        'status': status_val,
        'message': f"Transaction is currently {status_val}.",
        'transaction_id': transactionId,
        'invoice_id': transaction.get('invoice_id'),
        'details': {
            'amount': transaction.get('amount'),
            'network': transaction.get('network'),
            'phone': transaction.get('phone'),
            'time': transaction.get('time'),
            'payment_stages': transaction.get('payment_stages', [])
        }
    })

@app.get("/api/v1/generate_invoice/{transactionId}")
async def generate_invoice_endpoint(transactionId: str):
    if transactionId not in transactions:
        return JSONResponse(status_code=404, content={'status': 'not_found', 'message': 'Transaction ID not found.'})
        
    transaction = transactions[transactionId]
    
    if transaction['status'] != 'completed' or not transaction.get('invoice_id'):
        return JSONResponse(status_code=400, content={
            'status': 'failed',
            'message': 'Invoice not yet generated. Transaction status: ' + transaction['status']
        })
        
    invoice_id = transaction['invoice_id']
    invoice = invoices.get(invoice_id)
    
    if not invoice:
        return JSONResponse(status_code=500, content={'status': 'failed', 'message': 'Internal error: Invoice ID found, but invoice data is missing.'})
        
    return JSONResponse(content={
        'status': 'success',
        'message': 'Invoice retrieved successfully',
        'invoice_id': invoice_id,
        'invoice': invoice
    })
    
@app.post("/api/v1/send-receipt")
async def send_receipt(request: Request):
    """
    Called by the frontend after a successful Stripe payment to trigger
    the automated invoice email.
    """
    try:
        data = await request.json()
        customer_email = data.get('email')
        invoice_id = data.get('invoice_id', 'N/A')
        transaction_id = data.get('transaction_id', 'N/A')
        items = data.get('items', [])
        total = data.get('total', 0)
        campus = data.get('campus', 'N/A')
        date = data.get('date', datetime.utcnow().isoformat() + "Z")

        if not customer_email or customer_email == 'N/A':
            print("[EMAIL] No customer email provided in send-receipt request — skipping.")
            return JSONResponse(content={'status': 'skipped', 'message': 'No email provided.'})

        # Build an invoice dict compatible with send_invoice_email
        invoice = {
            'invoice_id': invoice_id,
            'transaction_id': transaction_id,
            'customer_email': customer_email,
            'date': date,
            'items': items,
            'amount': {
                'subtotal': float(total),
                'shipping': 0.0,
                'tax': 0.0,
                'total': float(total)
            },
            'payment_method': {'type': 'Stripe Card', 'network': 'Stripe'},
            'status': 'paid',
            'campus': campus
        }

        print(f"[EMAIL] Sending Stripe invoice email to {customer_email}...")
        await send_invoice_email(customer_email, invoice)
        return JSONResponse(content={'status': 'success', 'message': f'Invoice email sent to {customer_email}'})
    except Exception as e:
        print(f"❌ Failed to send automated email: {str(e)}")



@app.get("/api/v1/invoice/{invoiceId}")
async def get_invoice(invoiceId: str):
    if invoiceId not in invoices:
        return JSONResponse(status_code=404, content={'status': 'not_found', 'message': 'Invoice ID not found.'})
        
    invoice = invoices[invoiceId]
    
    return JSONResponse(content={
        'status': 'success',
        'invoice': {
            'invoice_id': invoice['invoice_id'],
            'transaction_id': invoice['transaction_id'],
            'merchant': {
                'name': 'Feza Shop',
                'id': invoice['merchant_id']
            },
            'customer': {
                'phone_number': invoice['customer_phone'],
                'email': invoice.get('customer_email', 'N/A')
            },
            'date': invoice['date'],
            'items': invoice['items'],
            'payment': {
                'method': 'Mobile Money',
                'network': invoice['payment_method']['network'],
                'status': invoice['status'],
                'timestamp': invoice['date'],
                'subtotal': invoice['amount']['subtotal'],
                'shipping': invoice['amount']['shipping'],
                'tax': invoice['amount']['tax'],
                'amount': invoice['amount']['total']
            }
        }
    })

@app.post("/api/v1/request-topup-pin")
async def request_topup_pin(request: Request):
    try:
        data = await request.json()
        email = data.get('email')
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        # Generate a 6-digit PIN
        import random
        pin = f"{random.randint(100000, 999999)}"
        
        # Store PIN in memory (linked to email for demo)
        verification_pins[email] = {
            "pin": pin,
            "expiry": time.time() + 600 # 10 minutes
        }
        
        # Send PIN via email service
        try:
            await send_topup_pin_email(email, pin)
        except Exception as e:
            # If email fails, we might still want to return success in development
            # but for production we should probably let the user know.
            print(f"❌ Critical Email Error: {str(e)}")
            return JSONResponse(status_code=500, content={"status": "error", "message": "Failed to send verification email."})
        
        return JSONResponse(content={"status": "success", "message": "PIN sent successfully"})
    except Exception as e:
        print(f"PIN Error: {str(e)}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.post("/api/v1/verify-topup-pin")
async def verify_topup_pin(request: Request):
    data = await request.json()
    email = data.get('email')
    pin = data.get('pin')
    
    saved_data = verification_pins.get(email)
    if not saved_data:
        return JSONResponse(status_code=400, content={"status": "failed", "message": "No PIN requested for this email."})
    
    if time.time() > saved_data["expiry"]:
        return JSONResponse(status_code=400, content={"status": "failed", "message": "PIN has expired."})
    
    if saved_data["pin"] == pin:
        # Clear pin after use
        del verification_pins[email]
        return JSONResponse(content={"status": "success", "message": "PIN verified"})
    else:
        return JSONResponse(status_code=400, content={"status": "failed", "message": "Invalid PIN code."})

# Mount the static files at the end to act as a catch-all route, serving from root
app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="static")
