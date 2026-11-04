# Feza Shop: Step-by-Step Deployment Guide

Follow these steps to move Feza Shop from your local flash drive to the live internet.

---

## 🏗️ Step 1: Push Code to GitHub
You need a GitHub account for this. GitHub will store your code and tell Render/Vercel to update whenever you make changes.

1.  **Create a Repo**: Go to [github.com/new](https://github.com/new) and create a private repository named `feza-shop`.
2.  **Initialize Git** (Run these in your terminal in `f:\Feza_shop - Copy (using python)`):
    ```powershell
    --
    git init
    git add .
    git commit -m "Initialize Feza Shop deployment"
    ```
3.  **Connect to GitHub**:
    ```powershell
    git remote add origin https://github.com/YOUR_USERNAME/Feza-shop.git
    git branch -M main
    git push -u origin main
    ```

---

## ⚙️ Step 2: Deploy Backend to Render.com
Render will host your Python server and your Database.

1.  **Sign Up**: Go to [Render.com](https://render.com) and sign up (connect your GitHub).
2.  **Create a PostgreSQL Database**:
    - Click **New +** -> **PostgreSQL**.
    - Name it `feza_db`.
    - Choose the **Free** tier.
    - Click **Create Database**.
    - **Important**: **Internal Database URL**[dpg-d6qjnljuibrs739bpaq0-a].<now obtained from render>
3.  **Create a Web Service**:
    - Click **New +** -> **Web Service**.
    - Connect your `feza-shop` GitHub repo.
    - **Settings**:
        - **Name**: `feza-shop-backend`
        - **Runtime**: `Python`
        - **Build Command**: `pip install -r requirements.txt`
        - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
    - **Environment Variables** (Click "Advanced"):
        - `DATABASE_URL`: (Paste your Internal Database URL)
        - `STRIPE_SECRET_KEY`: (Your Stripe Secret Key)
        - `MAIL_USERNAME`: (Set your SMTP username in the hosting environment)
        - `MAIL_PASSWORD`: (Set your SMTP app password in the hosting environment)
        - `SECRET_KEY`: (Generate a random string)
    - Click **Create Web Service**.
4.  **Wait**: Render will build your app. Once it says "Live",THE URL:`https://feza-shop-backend.onrender.com`.

---

## 🎨 Step 3: Deploy Frontend to Vercel
Vercel will host your HTML/CSS/JS files.

1.  **Sign Up**: Go to [Vercel.com](https://vercel.com) and sign up with GitHub.
2.  **Import Project**:
    - Click **Add New** -> **Project**.
    - Import your `feza-shop` GitHub repo.
3.  **Configure**:
    - Vercel should auto-detect that it is a static site.
    - Click **Deploy**.
4.  **Connect to Backend**:
    - Once deployed, copy your Vercel URL (e.g., `https://feza-shop.vercel.app`).
    - **Crucial**: Go back to your **Render Web Service Settings** and add another Environment Variable:
        - `CORS_ORIGINS`: `https://feza-shop.vercel.app` (This allows your frontend to talk to your backend).

---

## 📱 Step 4: Real M-Pesa STK Setup
Now that the server is live, the "Success!" callbacks from Safaricom can find your website.

1.  Go to [Safaricom Daraja Portal](https://developer.safaricom.co.ke/).
2.  Create an App and get your **Consumer Key** and **Consumer Secret**.
3.  Add these as Environment Variables in **Render**:
    - `MPESA_CONSUMER_KEY`
    - `MPESA_CONSUMER_SECRET`
    - `MPESA_PASSKEY`
    - `MPESA_BUSINESS_SHORTCODE`

---

## ✅ Final Check
1. Open your Vercel link on your phone.
2. Click the "Install" icon (it should pop up because we made it a PWA).
3. Try a payment—it will now hit your live Render backend and trigger a **Real PIN Prompt**!

**Need help with a specific step? Just let me know!**
