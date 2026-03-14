// server.js
const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const app = express();
const port = 3000;

// In-memory store for simulated transactions and invoices
const transactions = {};
const invoices = {};

// Use CORS to allow the frontend (feza-pay.html) to call the API
app.use(cors());

// Use body-parser middleware to parse JSON requests
app.use(bodyParser.json());

// --- Utility Functions ---

function generateInvoice(transactionData) {
    const invoiceId = 'INV-' + Date.now() + Math.random().toString(36).substr(2, 6).toUpperCase();
    
    // Extract payment details (simulated based on frontend data structure)
    const subtotal = transactionData.items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    // Note: Shipping and Tax are usually stored in the transaction but are simplified here.
    const shipping = 0.00; 
    const tax = 0.00; 
    const total = transactionData.amount;
    
    const invoice = {
        invoice_id: invoiceId,
        date: new Date().toISOString(),
        merchant: {
            name: 'Feza Shop',
            id: transactionData.merchant
        },
        customer: {
            phone_number: transactionData.phone,
            email: transactionData.customer_email,
        },
        items: transactionData.items,
        transaction_id: transactionData.id,
        payment: {
            method: transactionData.payment_method,
            network: transactionData.network,
            status: 'completed',
            timestamp: new Date().toISOString(),
            subtotal: subtotal,
            shipping: shipping,
            tax: tax,
            amount: total
        }
    };
    
    invoices[invoiceId] = invoice;
    return invoiceId;
}

// --- Stripe Endpoint ---

/**
 * 1. POST /create-payment-intent
 * Simulates the backend creating a Stripe PaymentIntent and returning the client_secret.
 */
app.post('/create-payment-intent', (req, res) => {
    const { amount, currency, customerEmail } = req.body;
    
    if (!amount || !currency || !customerEmail) {
        return res.status(400).json({ status: 'failed', message: 'Missing amount, currency, or customer email.' });
    }

    // In a real app, you call stripe.paymentIntents.create() here.
    // We generate a mock client secret in the correct format for the frontend to render the Element.
    const mockIntentId = 'pi_' + Date.now() + Math.random().toString(36).substr(2, 10);
    // This format must match the one the frontend is expecting, including the '_secret_' part.
    const mockClientSecret = `${mockIntentId}_secret_abcdef1234567890abcdef1234567890`;

    console.log(`[STRIPE MOCK] Payment Intent created. ID: ${mockIntentId}, Amount: $${(amount/100).toFixed(2)}, Email: ${customerEmail}`);
    
    res.status(200).json({ 
        status: 'success', 
        clientSecret: mockClientSecret,
        paymentIntentId: mockIntentId
    });
});


// --- Simulated NMB & Unified API Endpoints ---

/**
 * 2. POST /api/v1/mobile_payment
 * Simulates initiating a payment (Mobile Money, Bank, or recording a Stripe success for invoicing).
 */
app.post('/api/v1/mobile_payment', (req, res) => {
    const { merchant_id, phone_number, amount, network, items, customer_email, external_transaction_id } = req.body;
    
    if (!merchant_id || !req.headers.authorization) {
        return res.status(401).json({ status: 'failed', message: 'Authentication required (Missing Merchant ID or API Key).' });
    }

    if (!amount || !customer_email || !items) {
        return res.status(400).json({ status: 'failed', message: 'Missing required payment/order details.' });
    }
    
    // Use external_transaction_id (e.g., Stripe's pi_ ID) or generate a new one for NMB/Bank
    const transaction_id = external_transaction_id || ('TXN-' + Date.now() + Math.random().toString(36).substr(2, 9));
    const payment_method = external_transaction_id ? 'STRIPE_CARD' : network;

    // Store the transaction
    transactions[transaction_id] = {
        id: transaction_id,
        merchant: merchant_id,
        phone: phone_number || 'N/A',
        amount: amount,
        network: network,
        payment_method: payment_method,
        items: items,
        customer_email: customer_email,
        status: external_transaction_id ? 'completed' : 'pending', // Stripe payments are immediately 'completed' here
        invoice_id: null,
        time: new Date().toISOString()
    };
    
    console.log(`[API LOG] Payment initiated. ID: ${transaction_id}, Method: ${payment_method}, Amount: $${amount}, Status: ${transactions[transaction_id].status}`);

    if (external_transaction_id) {
        // For external payments (Stripe), immediately finalize the invoice
        const invoiceId = generateInvoice(transactions[transaction_id]);
        transactions[transaction_id].invoice_id = invoiceId;
        console.log(`[API LOG] External transaction ${transaction_id} immediately COMPLETED. Invoice ID: ${invoiceId}`);
        return res.status(200).json({ 
            status: 'success', 
            message: `External payment recorded and completed.`,
            transaction_id: transaction_id,
            invoice_id: invoiceId
        });
    }

    // Response for Mobile/Bank payments (PULL)
    res.status(200).json({ 
        status: 'success', 
        message: `Payment request successfully sent to phone number ${phone_number}. Awaiting confirmation.`,
        transaction_id: transaction_id 
    });

    // --- Background Simulation of Mobile/Bank Payment Confirmation ---
    setTimeout(() => {
        if (transactions[transaction_id] && transactions[transaction_id].status === 'pending') {
            transactions[transaction_id].status = 'completed';
            const invoiceId = generateInvoice(transactions[transaction_id]);
            transactions[transaction_id].invoice_id = invoiceId;
            console.log(`[API LOG] Transaction ${transaction_id} successfully COMPLETED after user confirmation simulation. Invoice ID: ${invoiceId}`);
        }
    }, 4000); // 4 second delay for simulation confirmation
});

/**
 * 3. GET /api/v1/transaction_status/:transactionId
 * Simulates checking the transaction status using the polling method.
 */
app.get('/api/v1/transaction_status/:transactionId', (req, res) => {
    const transaction_id = req.params.transactionId;
    
    if (!transactions[transaction_id]) {
        return res.status(404).json({ status: 'not_found', message: 'Transaction ID not found.' });
    }
    
    const status = transactions[transaction_id].status;
    const invoice_id = transactions[transaction_id].invoice_id;
    
    // Log current status
    console.log(`[API LOG] Status check for ${transaction_id}: ${status}`);

    res.status(200).json({
        status: status,
        message: `Transaction is currently ${status}.`,
        transaction_id: transaction_id,
        invoice_id: invoice_id // Return the invoice ID if completed
    });
});

/**
 * 4. GET /api/v1/invoice/:invoiceId
 * Endpoint to retrieve the generated invoice.
 */
app.get('/api/v1/invoice/:invoiceId', (req, res) => {
    const invoiceId = req.params.invoiceId;

    if (!invoices[invoiceId]) {
        return res.status(404).json({ status: 'failed', message: 'Invoice ID not found.' });
    }
    
    console.log(`[API LOG] Invoice retrieved: ${invoiceId}`);
    
    res.status(200).json({
        status: 'success',
        invoice: invoices[invoiceId]
    });
});

// Alias for invoice generation from transaction ID (used in old frontend logic)
app.get('/api/v1/generate_invoice/:transactionId', (req, res) => {
    const transaction_id = req.params.transactionId;
    
    if (!transactions[transaction_id] || transactions[transaction_id].status !== 'completed' || !transactions[transaction_id].invoice_id) {
        return res.status(404).json({ status: 'failed', message: 'Transaction not found or not yet completed for invoice generation.' });
    }
    
    const invoiceId = transactions[transaction_id].invoice_id;
    
    res.status(200).json({
        status: 'success',
        invoice_id: invoiceId,
        invoice: invoices[invoiceId]
    });
});

app.get('/', (req, res) => {
    res.send('Feza Pay Backend Simulator is running.');
});

app.listen(port, () => {
    console.log(`Feza Pay Backend Simulator listening at http://localhost:${port}`);
});