from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import settings

# Setup the FastMail configuration using Pydantic settings from config.py
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME or "your_email@gmail.com",
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM or settings.MAIL_USERNAME or "your_email@gmail.com",
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

fm = FastMail(conf)

async def send_invoice_email(email_to: str, invoice_data: dict):
    if not settings.MAIL_PASSWORD:
        print("Skipping email: No SMTP password configured.")
        return
    
    if not email_to or email_to == "N/A":
        print("Skipping email: No recipient email provided.")
        return

    # Build the HTML table rows for items
    items_html = ""
    for item in invoice_data.get("items", []):
        name = item.get("name", "Item")
        qty = item.get("quantity", 1)
        price = item.get("price", 0)
        items_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{name}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{qty}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">TZS{price:,.2f}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">TZS{price * qty:,.2f}</td>
            </tr>
        """

    # Get formatting details safely
    amount_data = invoice_data.get('amount', {})
    total = amount_data.get('total', invoice_data.get('payment', {}).get('amount', 0))

    html_content = f"""
   <div style="font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 20px auto; border: 1px solid #edf2f7; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
    
    <div style="background-color: #f97316; padding: 40px 20px; text-align: center; border-radius: 12px 12px 0 0;">
        <div style="background: rgba(255,255,255,0.2); display: inline-block; padding: 8px 16px; border-radius: 20px; color: white; font-size: 12px; font-weight: bold; text-transform: uppercase; margin-bottom: 10px;">
            Payment Successful
        </div>
        <h1 style="margin: 0; font-size: 28px; color: white; letter-spacing: -0.5px;">Feza Shop</h1>
    </div>

    <div style="padding: 30px; background-color: #ffffff;">
        <h2 style="color: #1a202c; margin-top: 0;">Thanks for your order!</h2>
        <p style="font-size: 16px; color: #4a5568; line-height: 1.6;">
            Your payment was processed successfully. **Please keep this email handy**—you'll need to show the Invoice ID below when collecting your items.
        </p>

        <div style="background-color: #f8fafc; border-left: 4px solid #f97316; border-radius: 6px; padding: 20px; margin: 25px 0;">
            <table style="width: 100%; font-size: 14px; color: #64748b;">
                <tr>
                    <td style="padding-bottom: 8px;"><strong>Invoice ID:</strong></td>
                    <td style="padding-bottom: 8px; text-align: right; color: #1a202c;">#{invoice_data.get('invoice_id', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="padding-bottom: 8px;"><strong>Transaction ID:</strong></td>
                    <td style="padding-bottom: 8px; text-align: right; color: #1a202c;">{invoice_data.get('transaction_id', 'N/A')}</td>
                </tr>
                <tr>
                    <td><strong>Date:</strong></td>
                    <td style="text-align: right; color: #1a202c;">{invoice_data.get('date', 'N/A')}</td>
                </tr>
            </table>
        </div>

        <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
            <thead>
                <tr style="text-align: left; border-bottom: 1px solid #e2e8f0;">
                    <th style="padding: 12px 0; color: #1a202c; font-size: 14px;">Item</th>
                    <th style="padding: 12px 0; color: #1a202c; font-size: 14px; text-align: center;">Qty</th>
                    <th style="padding: 12px 0; color: #1a202c; font-size: 14px; text-align: right;">Total</th>
                </tr>
            </thead>
            <tbody style="font-size: 15px; color: #4a5568;">
                {items_html} 
                </tbody>
        </table>

        <div style="border-top: 2px solid #edf2f7; margin-top: 20px; padding-top: 20px; text-align: right;">
            <span style="color: #64748b; font-size: 16px;">Amount Paid:</span>
            <div style="font-size: 24px; color: #1a202c; font-weight: bold; margin-top: 5px;">
                TZS {float(total):,.2f}
            </div>
        </div>

        <div style="text-align: center; margin-top: 40px;">
            <a href="#" style="background-color: #f97316; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Track Your Delivery</a>
        </div>

        <hr style="border: 0; border-top: 1px solid #edf2f7; margin: 40px 0 20px 0;">
        
        <p style="font-size: 13px; color: #94a3b8; text-align: center; line-height: 1.5;">
            Questions about your order? Reply to this email or visit our help center.<br>
            <strong>Feza Shop - Smart Campus Shopping</strong>
        </p>
    </div>
</div>
    """

    message = MessageSchema(
        subject=f"Receipt for your order at Feza Shop (#{invoice_data.get('invoice_id')})",
        recipients=[email_to],
        body=html_content,
        subtype=MessageType.html
    )

    try:
        await fm.send_message(message)
        print(f"✅ Successfully sent automated invoice email to {email_to}")
    except Exception as e:
        print(f"❌ Failed to send automated email: {str(e)}")

async def send_topup_pin_email(email_to: str, pin_code: str):
    if not settings.MAIL_PASSWORD:
        print("Skipping PIN email: No SMTP password configured.")
        return

    html_content = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 500px; margin: 20px auto; border: 1px solid #edf2f7; border-radius: 12px; overflow: hidden;">
        <div style="background-color: #ff6b35; padding: 30px; text-align: center;">
            <h2 style="margin: 0; color: white;">FEZA SHOP Wallet</h2>
            <p style="color: rgba(255,255,255,0.9); margin-top: 5px;">Security Verification Code</p>
        </div>
        <div style="padding: 40px 30px; text-align: center; background: white;">
            <p style="color: #4a5568; font-size: 16px;">Someone requested a top-up for your student wallet. Use the PIN below to authorize this transaction:</p>
            <div style="background: #f8fafc; border: 2px dashed #ff6b35; border-radius: 8px; padding: 20px; margin: 30px 0; font-size: 32px; font-weight: bold; letter-spacing: 12px; color: #1a202c;">
                {pin_code}
            </div>
            <p style="color: #94a3b8; font-size: 13px;">This code will expire in 10 minutes. If you didn't request this, please ignore this email.</p>
        </div>
        <div style="background: #f1f5f9; padding: 20px; text-align: center; font-size: 12px; color: #64748b;">
            Secure Banking for Feza Students
        </div>
    </div>
    """

    message = MessageSchema(
        subject=f"Your Feza Shop Top-Up PIN: {pin_code}",
        recipients=[email_to],
        body=html_content,
        subtype=MessageType.html
    )

    try:
        await fm.send_message(message)
        print(f"✅ Sent Top-Up PIN to {email_to}")
    except Exception as e:
        print(f"❌ Failed to send PIN email: {str(e)}")
        raise e

async def send_restock_order_email(supplier_email: str, order_details: dict):
    if not settings.MAIL_PASSWORD:
        print("Skipping Restock email: No SMTP password configured.")
        return

    product_name = order_details.get("product_name", "Product")
    quantity = order_details.get("quantity", 0)
    current_stock = order_details.get("current_stock", 0)
    image_url = order_details.get("image_url", "")

    # For email visibility, we use the Vercel hosted URL for images if not full URL
    full_image_url = image_url
    if image_url and not (image_url.startswith('http') or image_url.startswith('data')):
        # Map local names to professional CDN-hosted versions if possible, or fallback
        full_image_url = f"https://raw.githubusercontent.com/Saidi-Baraka/Feza-Shop/main/{image_url.replace(' ', '%20')}"
    
    html_content = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 20px auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
        <div style="background-color: #1a1a1a; padding: 30px; text-align: center; border-bottom: 4px solid #ff6b35;">
            <h1 style="margin: 0; color: white; letter-spacing: 1px; font-size: 24px;">FEZA SHOP</h1>
            <p style="color: #ff6b35; margin-top: 5px; font-weight: bold; text-transform: uppercase; font-size: 11px; letter-spacing: 2px;">Official Purchase Order & Catalog Reference</p>
        </div>
        
        <div style="padding: 40px 35px; background: white;">
            <div style="text-align: center; margin-bottom: 30px;">
                <div style="display: inline-block; padding: 8px 16px; background: #fff7ed; border: 1px solid #ffedd5; border-radius: 20px; color: #ea580c; font-size: 13px; font-weight: bold;">
                    Order Status: URGENT RESTOCK
                </div>
            </div>

            <div style="display: flex; gap: 25px; align-items: flex-start; margin-bottom: 35px; border-bottom: 1px solid #f1f5f9; padding-bottom: 35px;">
                <div style="flex: 0 0 120px;">
                    <img src="{full_image_url}" alt="{product_name}" style="width: 120px; height: 120px; object-fit: cover; border-radius: 12px; border: 1px solid #f1f5f9;">
                </div>
                <div style="flex: 1;">
                    <h2 style="color: #1a202c; margin: 0 0 10px 0; font-size: 20px;">{product_name}</h2>
                    <p style="color: #64748b; font-size: 13px; margin: 0 0 20px 0; line-height: 1.5;">Catalog Ref: <strong>#{product_name[:3].upper()}-INVENTORY</strong></p>
                    
                    <div style="background: #1a1a1a; padding: 12px; border-radius: 8px; color: white;">
                        <div style="font-size: 10px; text-transform: uppercase; color: #94a3b8; margin-bottom: 2px;">Order Quantity</div>
                        <div style="font-size: 20px; font-weight: 800; color: #ff6b35;">{quantity} Units</div>
                    </div>
                </div>
            </div>

            <div style="background: #f8fafc; border-radius: 12px; padding: 20px; border: 1px solid #edf2f7;">
                <table style="width: 100%; font-size: 14px; color: #4a5568;">
                    <tr>
                        <td style="padding-bottom: 12px;">Current Stock Level:</td>
                        <td style="padding-bottom: 12px; text-align: right; font-weight: bold; color: #ef4444;">{current_stock} Units remaining</td>
                    </tr>
                    <tr>
                        <td style="padding-bottom: 12px;">Requested By:</td>
                        <td style="padding-bottom: 12px; text-align: right; color: #1a202c;">Procurement Dept.</td>
                    </tr>
                </table>
            </div>

            <p style="color: #718096; font-size: 14px; margin-top: 30px; line-height: 1.6;"> 
                <strong>Supplier Notice:</strong> This request is being sent following an inventory threshold alert. Please confirm receipt and adjust billing accordingly.
            </p>
        </div>
        
        <div style="background: #f1f5f9; padding: 25px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0;">
            <strong>Feza Shop Procurement</strong><br>
            Managed by Baraka Saidi Kiwanga | {settings.PROJECT_NAME}
        </div>
    </div>
    """

    message = MessageSchema(
        subject=f"RESTOCK ORDER: {product_name} ({quantity} Units) - Feza Shop",
        recipients=[supplier_email],
        body=html_content,
        subtype=MessageType.html
    )

    try:
        await fm.send_message(message)
        print(f"✈️ Restock order for {product_name} sent to {supplier_email}")
    except Exception as e:
        print(f"❌ Failed to send restock email: {str(e)}")
        raise e
