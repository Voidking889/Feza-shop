# Upgrade Documentation - March 11, 2026

## Invoice Email System Fix

### Overview
This update resolves the issue where payment invoice emails were not being received after successful Stripe payments. The root cause was a mismatch between the frontend's expected API endpoints (pointing to port 3000) and the new Python FastAPI backend (running on port 8000), as well as a missing receipt endpoint in the Python migration.

### Changes

#### 1. Backend: Python FastAPI (`main.py`)
- **Added `/api/v1/send-receipt` Endpoint**: 
  - Created a new POST route that the frontend calls immediately after a successful Stripe payment.
  - This route accepts order details (customer email, items, total, campus) and triggers the `send_invoice_email` service.
  - Bridge the gap between the Stripe payment flow and the automated email system.

#### 2. Frontend: Payment Page (`feza-pay.html`)
- **Port Migration (3000 -> 8000)**: 
  - Updated all `fetch` calls to point to the correct Python backend port.
  - Impacted endpoints:
    - `/create-payment-intent`
    - `/api/v1/send-receipt`
    - `/api/v1/generate_invoice/`
    - `/api/v1/invoice/`
- **Email Trigger Fix**: 
  - Ensured the `simulateInvoiceGeneration` function correctly calls the backend to queue the automated email.

### Verification
- SMTP Credentials (Gmail App Password) verified via test script.
- Backend now correctly handles receipt requests for both Mobile Money and Stripe Card flows.
- Frontend now successfully communicates with the Python API for all payment stages.

---
**Note:** Ensure the Python server is running on port 8000 for these changes to take effect.

## UI/UX Reversion & Payment Fixes - March 11, 2026

### Overview
A premium UI/UX overhaul was attempted for the storefront, but as requested, the design has been **reverted** to the original layout. Critical functional updates for payment reliability and delivery features have been **preserved**.

### Retained Functional Updates
- **Stripe Reliability**: Fixed card loading by implementing relative path fetching and TZS currency support to match store pricing. Added better error diagnostics in the UI.
- **Account Centre & Personalization**: Launched a dedicated `Account_centre.html` with dynamic typing greetings, custom profile editing, and full Dark Mode support.
- **Polished Order History**: Redesigned `cart_history.html` with a state-of-the-art glassmorphism UI, real-time statistics (total spent/orders), and localized PDF invoice generation.
- **Delivery Destination Selector**: Added custom destination selection in `feza-pay.html`.
- **Live Delivery Features**: The new chat and driver rating functionality remains active in the tracking system.

---
**Status:** Storefront design reverted to previous version. Functional fixes remained deployed.
