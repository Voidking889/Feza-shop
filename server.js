// server.js
const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
require('dotenv').config();
const path = require('path');
const Stripe = require('stripe');
const app = express();
const port = process.env.PORT || 3000;

// Stripe payments are disabled until a server-side key is configured.
const stripe = process.env.STRIPE_SECRET_KEY
    ? new Stripe(process.env.STRIPE_SECRET_KEY)
    : null;
if (!stripe) {
    console.warn('[WARN] Stripe is disabled. Set STRIPE_SECRET_KEY in .env to enable payments.');
}

// NMB API credentials (moved to env)
const NMB_API_KEY = process.env.NMB_API_KEY;
const NMB_CONSUMER_SECRET = process.env.NMB_CONSUMER_SECRET;
const NMB_CONSUMER_ID = process.env.NMB_CONSUMER_ID;

// In-memory store for simulated transactions
const transactions = {};

// In-memory store for generated invoices
const invoices = {};

// Use CORS to allow the frontend (feza-pay.html) to call the API
app.use(cors());

// Use body-parser middleware to parse JSON requests
app.use(bodyParser.json());

app.use((req, res, next) => {
    if (req.path.split('/').some(part => part.startsWith('.'))) {
        return res.sendStatus(404);
    }
    next();
});

// Serve static files from the root directory
app.use(express.static(__dirname));

// Direct routes to HTML files
app.get('/payment', (req, res) => {
    res.sendFile(path.join(__dirname, 'feza-pay.html'));
});

app.get('/test-page', (req, res) => {
    res.sendFile(path.join(__dirname, 'test.html'));
});

// --- Stripe: Create PaymentIntent (real) ---

app.post('/create-payment-intent', async (req, res) => {
    if (!stripe) {
        return res.status(503).json({ status: 'failed', message: 'Stripe is not configured on the server.' });
    }

    try {
        const { amount, currency, customerEmail } = req.body;
        if (!Number.isSafeInteger(Number(amount)) || Number(amount) <= 0 ||
            typeof currency !== 'string' || !currency.trim()) {
            return res.status(400).json({ status: 'failed', message: 'A positive integer amount and currency are required.' });
        }

        const paymentIntent = await stripe.paymentIntents.create({
            amount: Number(amount),
            currency: currency.trim().toLowerCase(),
            // Do not send receipt_email to avoid Stripe email validation errors
            automatic_payment_methods: { enabled: true }
        });

        return res.status(200).json({
            status: 'success',
            clientSecret: paymentIntent.client_secret,
            paymentIntentId: paymentIntent.id
        });
    } catch (err) {
        console.error('Stripe error:', err?.message || err);
        return res.status(502).json({ status: 'failed', message: 'Stripe could not create the payment intent.' });
    }
});

// --- Simulated NMB API Endpoints ---

/**
 * 1. POST /api/v1/mobile_payment
 * Simulates initiating a payment and sending a prompt to the user's phone.
 */
app.post('/api/v1/mobile_payment', (req, res) => {
    const { merchant_id, phone_number, amount, network, items, customer_email } = req.body;
    
    // Check for API credentials - now using stored NMB API key
    const authHeader = req.headers.authorization;
    if (!merchant_id || !authHeader) {
        return res.status(401).json({ status: 'failed', message: 'Authentication required (Missing Merchant ID or API Key).' });
    }
    
    // Validate API key (in a real scenario, this would be more secure)
    const providedApiKey = authHeader.replace('Bearer ', '');
    if (!!NMB_API_KEY && providedApiKey !== NMB_API_KEY) {
        return res.status(401).json({ status: 'failed', message: 'Invalid API credentials.' });
    }

    if (!phone_number || !amount || network === 'Select Network') {
        return res.status(400).json({ status: 'failed', message: 'Missing required payment details.' });
    }
    
    // Generate a unique transaction ID
    const transaction_id = 'TXN-' + Date.now() + Math.random().toString(36).substr(2, 9);

    // Store the transaction with a 'pending' status
    transactions[transaction_id] = {
        id: transaction_id,
        merchant: merchant_id,
        phone: phone_number,
        amount: amount,
        network: network,
        status: 'pending',
        time: new Date().toISOString(),
        items: items || [], // Store order items for invoice generation
        customer_email: customer_email, // Store customer email
        payment_stages: [
            { stage: 'initiated', time: new Date().toISOString(), status: 'success' }
        ]
    };
    
    console.log(`[API LOG] Payment initiated. ID: ${transaction_id}, Amount: $${amount}, Status: pending`);

    // The API immediately responds that the request was successfully sent.
    res.status(200).json({ 
        status: 'success', 
        message: `Payment request successfully sent to phone number ${phone_number}. Awaiting confirmation.`,
        transaction_id: transaction_id 
    });

    // --- Enhanced Background Simulation of Payment Confirmation ---
    // Stage 1: After 2 seconds, simulate the payment request being received by the mobile network
    setTimeout(() => {
        if (transactions[transaction_id] && transactions[transaction_id].status === 'pending') {
            transactions[transaction_id].payment_stages.push({
                stage: 'request_received',
                time: new Date().toISOString(),
                status: 'success',
                message: 'Payment request received by mobile network'
            });
            console.log(`[API LOG] Transaction ${transaction_id} - Payment request received by mobile network`);
        }
    }, 2000);
    
    // Stage 2: After 4 seconds, simulate the payment prompt being sent to user's phone
    setTimeout(() => {
        if (transactions[transaction_id] && transactions[transaction_id].status === 'pending') {
            transactions[transaction_id].payment_stages.push({
                stage: 'prompt_sent',
                time: new Date().toISOString(),
                status: 'success',
                message: 'Payment prompt sent to user phone'
            });
            console.log(`[API LOG] Transaction ${transaction_id} - Payment prompt sent to user phone`);
        }
    }, 4000);
    
    // Stage 3: After 6 seconds, simulate the user confirming the payment
    setTimeout(() => {
        if (transactions[transaction_id] && transactions[transaction_id].status === 'pending') {
            transactions[transaction_id].payment_stages.push({
                stage: 'user_confirmed',
                time: new Date().toISOString(),
                status: 'success',
                message: 'User confirmed payment on mobile device'
            });
            console.log(`[API LOG] Transaction ${transaction_id} - User confirmed payment on mobile device`);
        }
    }, 6000);
    
    // Stage 4: After 8 seconds, simulate the payment being processed and completed
    setTimeout(() => {
        if (transactions[transaction_id] && transactions[transaction_id].status === 'pending') {
            transactions[transaction_id].status = 'completed';
            transactions[transaction_id].payment_stages.push({
                stage: 'payment_completed',
                time: new Date().toISOString(),
                status: 'success',
                message: 'Payment successfully processed and completed'
            });
            
            // Generate an invoice ID for this transaction
            const invoice_id = 'INV-' + Date.now() + Math.random().toString(36).substr(2, 5);
            transactions[transaction_id].invoice_id = invoice_id;
            
            // Immediately generate the invoice in memory upon completion
            const transaction = transactions[transaction_id];
            
            // Create invoice data
            const invoice = {
                invoice_id: invoice_id,
                transaction_id: transaction_id,
                merchant_id: transaction.merchant,
                customer_phone: transaction.phone,
                customer_email: transaction.customer_email, // Added customer email
                date: new Date().toISOString(),
                items: transaction.items || [],
                payment_method: {
                    type: 'mobile_money',
                    network: transaction.network
                },
                amount: {
                    // Calculation logic derived from the original generate_invoice route
                    // subtotal = total - shipping - tax
                    subtotal: parseFloat(transaction.amount) - 5.99 - (parseFloat(transaction.amount) * 0.1), 
                    shipping: 5.99,
                    tax: parseFloat(transaction.amount) * 0.1,
                    total: parseFloat(transaction.amount)
                },
                status: 'paid'
            };
            
            // Store the invoice
            invoices[invoice_id] = invoice;
            
            // TODO: Real-World Implementation - Email Invoice
            // The following would be the point where you call Postmark or Firebase functions
            // to send the generated invoice (e.g., as a PDF attachment or HTML) 
            // to transactions[transaction_id].customer_email
            console.log(`[EMAIL TODO] Simulating sending invoice ${invoice_id} to ${transaction.customer_email} using Postmark/Firebase.`);
            // End TODO
            
            console.log(`[API LOG] Transaction ${transaction_id} successfully COMPLETED after user confirmation simulation.`);
            console.log(`[API LOG] Invoice ${invoice_id} generated and ready for retrieval.`);
        }
    }, 8000); // 8 second delay for simulation confirmation
});

/**
 * 2. GET /api/v1/transaction_status/:transactionId
 * Enhanced version that simulates checking the transaction status with more detailed information.
 */
app.get('/api/v1/transaction_status/:transactionId', (req, res) => {
    const transaction_id = req.params.transactionId;
    
    if (!transactions[transaction_id]) {
        return res.status(404).json({ status: 'not_found', message: 'Transaction ID not found.' });
    }
    
    const transaction = transactions[transaction_id];
    const status = transaction.status;
    
    // Log current status
    console.log(`[API LOG] Status check for ${transaction_id}: ${status}`);

    // Return enhanced transaction details
    res.status(200).json({
        status: status,
        message: `Transaction is currently ${status}.`,
        transaction_id: transaction_id,
        invoice_id: transaction.invoice_id || null, // Include invoice_id in status check
        details: {
            amount: transaction.amount,
            network: transaction.network,
            phone: transaction.phone,
            time: transaction.time,
            payment_stages: transaction.payment_stages || []
        }
    });
});

/**
 * 3. GET /api/v1/generate_invoice/:transactionId
 * Retrieves an invoice by looking up the pre-generated one.
 * NOTE: The logic for calculating and storing the invoice is now in the 
 * /api/v1/mobile_payment completion simulation to ensure it's generated 
 * when the payment completes. This endpoint now just retrieves it.
 */
app.get('/api/v1/generate_invoice/:transactionId', (req, res) => {
    const transaction_id = req.params.transactionId;
    
    if (!transactions[transaction_id]) {
        return res.status(404).json({ status: 'not_found', message: 'Transaction ID not found.' });
    }
    
    const transaction = transactions[transaction_id];
    
    if (transaction.status !== 'completed' || !transaction.invoice_id) {
        return res.status(400).json({ 
            status: 'failed', 
            message: 'Invoice not yet generated. Transaction status: ' + transaction.status
        });
    }
    
    const invoice_id = transaction.invoice_id;
    const invoice = invoices[invoice_id];
    
    if (!invoice) {
         return res.status(500).json({ 
            status: 'failed', 
            message: 'Internal error: Invoice ID found, but invoice data is missing.'
        });
    }
    
    console.log(`[API LOG] Invoice ${invoice_id} retrieved for transaction ${transaction_id}`);
    
    res.status(200).json({
        status: 'success',
        message: 'Invoice retrieved successfully',
        invoice_id: invoice_id,
        invoice: invoice
    });
});

/**
 * 4. GET /api/v1/invoice/:invoiceId
 * Retrieves an invoice by ID.
 */
app.get('/api/v1/invoice/:invoiceId', (req, res) => {
    const invoice_id = req.params.invoiceId;
    
    if (!invoices[invoice_id]) {
        return res.status(404).json({ status: 'not_found', message: 'Invoice ID not found.' });
    }
    
    const invoice = invoices[invoice_id];
    
    res.status(200).json({
        status: 'success',
        invoice: {
            // Reformat to match the client-side's expected structure for the simulator
            invoice_id: invoice.invoice_id,
            transaction_id: invoice.transaction_id,
            merchant: {
                name: 'Feza Shop', // Hardcoded for simplicity
                id: invoice.merchant_id
            },
            customer: {
                phone_number: invoice.customer_phone,
                email: invoice.customer_email || 'N/A' // Include email
            },
            date: invoice.date,
            items: invoice.items,
            payment: {
                method: 'Mobile Money', // Hardcoded for this flow
                network: invoice.payment_method.network,
                status: invoice.status,
                timestamp: invoice.date, // Use creation date as timestamp for simplicity
                subtotal: invoice.amount.subtotal,
                shipping: invoice.amount.shipping,
                tax: invoice.amount.tax,
                amount: invoice.amount.total
            }
        }
    });
});

app.get('/', (req, res) => {
    res.send('Feza Pay Backend Simulator is running.');
});

app.get('/test', (req, res) => {
    res.send('Test route is working!');
});

app.listen(port, () => {
    console.log(`Feza Pay Backend Simulator listening at http://localhost:${port}`);
});