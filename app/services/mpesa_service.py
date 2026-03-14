import time
import uuid

# In a real environment, you'd integrate with Safaricom Daraja API here
# using requests or httpx to get OAuth tokens and send the STK push.
# Since we are doing "Option B" (Local Simulation), we will simulate
# the API response and the background webhook callback.

async def initiate_stk_push(phone_number: str, amount: float, account_reference: str):
    """
    Simulates sending an STK Push to a user's phone.
    """
    print(f"📡 [M-Pesa Simulation] Initiating STK Push to {phone_number} for {amount} TZS")
    
    # Simulate API network delay
    time.sleep(1.5)
    
    # Generate a fake CheckoutRequestID
    checkout_request_id = f"ws_CO_{int(time.time())}_{str(uuid.uuid4())[:8]}"
    
    # Simulate a successful Daraja API accepted response
    response = {
        "MerchantRequestID": f"req_{int(time.time())}",
        "CheckoutRequestID": checkout_request_id,
        "ResponseCode": "0",
        "ResponseDescription": "Success. Request accepted for processing",
        "CustomerMessage": "Success. Request accepted for processing"
    }
    
    return response

async def simulate_mpesa_webhook_callback(checkout_request_id: str, phone_number: str, amount: float, success: bool = True):
    """
    Simulates the asynchronous webhook callback from M-Pesa that occurs
    after the user enters (or fails to enter) their PIN.
    """
    # Wait for the user to "enter their PIN"
    print(f"⏳ [M-Pesa Simulation] Waiting for user {phone_number} to enter PIN on their phone...")
    time.sleep(5) 
    
    print(f"🔔 [M-Pesa Simulation] Webhook received for {checkout_request_id}")
    
    if success:
        return {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "req_123",
                    "CheckoutRequestID": checkout_request_id,
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": amount},
                            {"Name": "MpesaReceiptNumber", "Value": f"R{str(uuid.uuid4())[:8].upper()}"},
                            {"Name": "PhoneNumber", "Value": phone_number}
                        ]
                    }
                }
            }
        }
    else:
        return {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "req_123",
                    "CheckoutRequestID": checkout_request_id,
                    "ResultCode": 1032,
                    "ResultDesc": "Request cancelled by user",
                }
            }
        }
