from fastapi import APIRouter, Header, HTTPException, Depends, BackgroundTasks
from app.schemas.transaction import PaymentRequest, PaymentResponse, TransactionStatus
from app.services.payment_service import process_payment, transactions, invoices, simulate_payment_completion
from app.core.config import settings
import stripe
import time
import uuid

router = APIRouter()

stripe.api_key = settings.STRIPE_SECRET_KEY

from app.services.mpesa_service import initiate_stk_push

@router.post("/mobile_payment", response_model=PaymentResponse)
async def mobile_payment(
    payload: PaymentRequest, 
    background_tasks: BackgroundTasks, 
    authorization: str = Header(None)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required (Missing API Key).")
        
    provided_api_key = authorization.replace('Bearer ', '')
    if settings.NMB_API_KEY and provided_api_key != settings.NMB_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API credentials.")
        
    # Check if this is an M-Pesa STK Push request
    if payload.network.lower() == "m-pesa":
        # Simulate STK Push
        stk_response = await initiate_stk_push(payload.phone_number, payload.amount, "Feza Shop")
        
        # Register the initial pending transaction
        result = await process_payment(payload) 
        
        # The transaction is initially explicitly 'pending' waiting for PIN
        transactions[result["transaction_id"]]["status"] = "pending_pin"
        
        # The callback is delayed intentionally to simulate typing the PIN
        background_tasks.add_task(simulate_payment_completion, result["transaction_id"], delay=6)
        
        result["message"] = "STK Push sent. Please check your phone and enter your PIN."
        return result
    else:
        # Standard generic flow for other networks (e.g., Tigo, Airtel)
        result = await process_payment(payload)
        background_tasks.add_task(simulate_payment_completion, result["transaction_id"])
        return result

@router.get("/transaction_status/{transaction_id}", response_model=TransactionStatus)
async def transaction_status(transaction_id: str):
    if transaction_id not in transactions:
        raise HTTPException(status_code=404, detail="Transaction ID not found.")
        
    transaction = transactions[transaction_id]
    
    return {
        'status': transaction['status'],
        'message': f"Transaction is currently {transaction['status']}.",
        'transaction_id': transaction_id,
        'invoice_id': transaction.get('invoice_id'),
        'details': {
            'amount': transaction.get('amount'),
            'network': transaction.get('network'),
            'phone': transaction.get('phone'),
            'time': transaction.get('time'),
            'payment_stages': transaction.get('payment_stages', [])
        }
    }

@router.post("/create-payment-intent")
async def create_payment_intent(payload: dict):
    amount = payload.get('amount')
    currency = payload.get('currency')

    if not amount or not currency:
        return {
            "status": "success",
            "clientSecret": f"pi_{int(time.time() * 1000)}_secret_abcdef1234567890abcdef1234567890",
            "paymentIntentId": f"pi_{int(time.time() * 1000)}"
        }
        
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=round(float(amount)),
            currency=currency,
            automatic_payment_methods={"enabled": True}
        )
        return {
            "status": "success",
            "clientSecret": payment_intent.client_secret,
            "paymentIntentId": payment_intent.id
        }
    except Exception as e:
        mock_intent_id = f"pi_{int(time.time() * 1000)}{str(uuid.uuid4())[:10]}"
        return {
            "status": "success",
            "clientSecret": f"{mock_intent_id}_secret_abcdef1234567890abcdef1234567890",
            "paymentIntentId": mock_intent_id,
            "note": "Mock client_secret returned due to Stripe error."
        }
        
@router.get("/generate_invoice/{transaction_id}")
async def generate_invoice_endpoint(transaction_id: str):
    if transaction_id not in transactions:
        raise HTTPException(status_code=404, detail="Transaction ID not found.")
        
    transaction = transactions[transaction_id]
    
    if transaction['status'] != 'completed' or not transaction.get('invoice_id'):
        raise HTTPException(status_code=400, detail="Invoice not yet generated. Transaction status: " + transaction['status'])
        
    invoice_id = transaction['invoice_id']
    invoice = invoices.get(invoice_id)
    
    if not invoice:
        raise HTTPException(status_code=500, detail="Internal error: Invoice ID found, but invoice data is missing.")
        
    return {
        'status': 'success',
        'message': 'Invoice retrieved successfully',
        'invoice_id': invoice_id,
        'invoice': invoice
    }
    
@router.get("/invoice/{invoice_id}")
async def get_invoice(invoice_id: str):
    if invoice_id not in invoices:
        raise HTTPException(status_code=404, detail="Invoice ID not found.")
        
    invoice = invoices[invoice_id]
    
    return {
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
    }

from app.services.email_service import send_invoice_email

@router.post("/send-receipt")
async def send_receipt(payload: dict, background_tasks: BackgroundTasks):
    email_to = payload.get("email")
    if not email_to:
        raise HTTPException(status_code=400, detail="Email is required")
        
    # Queue the email to send in the background safely
    background_tasks.add_task(send_invoice_email, email_to, payload)
    
    return {"status": "success", "message": "Receipt queued for sending."}

import urllib.request
import json

@router.post("/verify-flutterwave")
async def verify_flutterwave(payload: dict):
    transaction_id = payload.get('transaction_id')
    if not transaction_id:
        raise HTTPException(status_code=400, detail="Transaction ID is required")

    # Verify with Flutterwave API
    url = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"
    req = urllib.request.Request(url)
    req.add_header('Authorization', f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}")
    req.add_header('Content-Type', 'application/json')
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data.get('status') == 'success' and data['data']['status'] == 'successful':
                # Payment was successful, you would normally generate an invoice here
                return {
                    "status": "success", 
                    "message": "Payment verified successfully",
                    "data": data['data']
                }
            else:
                raise HTTPException(status_code=400, detail="Payment verification failed")
    except Exception as e:
        print(f"Flutterwave verification error: {str(e)}")
        # In test mode, if it fails due to network/mock, we can still fallback to success for testing 
        # But we'll raise an error if it's a real failure
        if "404" in str(e):
             raise HTTPException(status_code=404, detail="Transaction not found on Flutterwave")
        raise HTTPException(status_code=500, detail=f"Verification server error: {str(e)}")

# --- Wallet/Top-Up Verification PINs ---
from app.services.email_service import send_topup_pin_email
from app.services.payment_service import verification_pins
import random
from fastapi import Request

@router.post("/request-topup-pin")
async def request_topup_pin(request: Request):
    try:
        data = await request.json()
        email = data.get('email')
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        # Generate a 6-digit PIN
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
            print(f"❌ Critical Email Error: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to send verification email.")
        
        return {"status": "success", "message": "PIN sent successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"PIN Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-topup-pin")
async def verify_topup_pin(request: Request):
    try:
        data = await request.json()
        email = data.get('email')
        pin = data.get('pin')
        
        saved_data = verification_pins.get(email)
        if not saved_data:
            raise HTTPException(status_code=400, detail="No PIN requested for this email.")
        
        if time.time() > saved_data["expiry"]:
            raise HTTPException(status_code=400, detail="PIN has expired.")
        
        if saved_data["pin"] == pin:
            # Clear pin after use
            del verification_pins[email]
            return {"status": "success", "message": "PIN verified"}
        else:
            raise HTTPException(status_code=400, detail="Invalid PIN code.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from app.services.email_service import send_restock_order_email

@router.post("/restock-order")
async def restock_order(payload: dict, background_tasks: BackgroundTasks):
    supplier_email = payload.get("supplier_email")
    product_name = payload.get("product_name")
    quantity = payload.get("quantity")
    current_stock = payload.get("current_stock")

    if not all([supplier_email, product_name, quantity]):
        raise HTTPException(status_code=400, detail="Missing required order fields.")

    # Queue the supplier email
    background_tasks.add_task(
        send_restock_order_email, 
        supplier_email, 
        {
            "product_name": product_name,
            "quantity": quantity,
            "current_stock": current_stock,
            "image_url": payload.get("image_url")
        }
    )

    return {"status": "success", "message": f"Restock order for {product_name} queued for {supplier_email}"}
