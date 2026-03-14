import uuid
import time
import asyncio
from datetime import datetime
from app.schemas.transaction import PaymentRequest

# In-memory store (temporary until DB ORM is fully adopted into routes)
transactions = {}
invoices = {}
verification_pins = {}

async def process_payment(payload: PaymentRequest) -> dict:
    transaction_id = 'TXN-' + str(int(time.time() * 1000)) + str(uuid.uuid4())[:9]
    
    transactions[transaction_id] = {
        'id': transaction_id,
        'merchant': payload.merchant_id,
        'phone': payload.phone_number,
        'amount': payload.amount,
        'network': payload.network,
        'status': 'pending',
        'time': datetime.utcnow().isoformat() + "Z",
        'items': payload.items,
        'customer_email': payload.customer_email,
        'payment_stages': [
            {'stage': 'initiated', 'time': datetime.utcnow().isoformat() + "Z", 'status': 'success'}
        ]
    }
    
    return {
        'status': 'success',
        'message': f'Payment request successfully sent to phone number {payload.phone_number}. Awaiting confirmation.',
        'transaction_id': transaction_id
    }

async def simulate_payment_completion(transaction_id: str):
    await asyncio.sleep(2)
    if transaction_id in transactions and transactions[transaction_id]['status'] == 'pending':
        transactions[transaction_id]['payment_stages'].append({
            'stage': 'request_received',
            'time': datetime.utcnow().isoformat() + "Z",
            'status': 'success',
            'message': 'Payment request received by mobile network'
        })
        
    await asyncio.sleep(2)
    if transaction_id in transactions and transactions[transaction_id]['status'] == 'pending':
        transactions[transaction_id]['payment_stages'].append({
            'stage': 'prompt_sent',
            'time': datetime.utcnow().isoformat() + "Z",
            'status': 'success',
            'message': 'Payment prompt sent to user phone'
        })

    await asyncio.sleep(2)
    if transaction_id in transactions and transactions[transaction_id]['status'] == 'pending':
        transactions[transaction_id]['payment_stages'].append({
            'stage': 'user_confirmed',
            'time': datetime.utcnow().isoformat() + "Z",
            'status': 'success',
            'message': 'User confirmed payment on mobile device'
        })

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
