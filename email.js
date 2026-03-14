 (function () {
    // Configure these with your EmailJS credentials
    const EMAILJS_PUBLIC_KEY = 'aZJ3z2hujuttk3-PE';
    const EMAILJS_SERVICE_ID = 'service_5kir6mn';
    const EMAILJS_TEMPLATE_ID = 'template_vtf7oyq';

     // Initialize EmailJS when the script loads
     if (window.emailjs && typeof window.emailjs.init === 'function') {
         try {
             window.emailjs.init(EMAILJS_PUBLIC_KEY);
             console.log('EmailJS initialized');
         } catch (e) {
             console.warn('EmailJS init failed:', e);
         }
     } else {
         console.warn('EmailJS SDK not found. Did you include the CDN script?');
     }

     // Expose a send function globally
     window.sendInvoiceEmail = async function sendInvoiceEmail(params) {
         // params: { to_email, invoice_id, amount, items_json }
         if (!window.emailjs) {
             console.error('EmailJS SDK not loaded.');
             return { ok: false, error: 'sdk_missing' };
         }
         // Use the provided input email from feza-pay.html
         const recipient = params.to_email;
         try {
             const response = await window.emailjs.send(
                 EMAILJS_SERVICE_ID,
                 EMAILJS_TEMPLATE_ID,
                 {
                     to_email: recipient,
                     invoice_id: params.invoice_id,
                     amount_total: params.amount,
                     items_json: params.items_json
                 }
             );
             return { ok: true, response };
         } catch (error) {
             console.error('EmailJS send failed:', error);
             return { ok: false, error };
         }
     };
 })();

