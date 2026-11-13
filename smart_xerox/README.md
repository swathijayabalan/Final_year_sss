# Smart Xerox - Django starter project

A local-development MVP for a QR-based PDF printing workflow.

## Included
- PDF upload and server-side page counting
- Pricing for B&W/colour and single/double-sided printing
- Order saved in the database
- Local demo payment mode (no money is charged)
- QR code created only after the demo payment is confirmed
- Optional Razorpay Checkout integration using test keys
- Staff-only operator dashboard and status updates
- PDF receipt download (staff login required)
- Responsive colourful CSS interface

## 1. Create and activate a virtual environment (Windows PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

## 2. Install packages
```powershell
pip install -r requirements.txt
```

If `mysqlclient` is unavailable on Windows, install a compatible MySQL driver for your Python version or keep SQLite for the first run. The default configuration uses SQLite and works without MySQL setup.

## 3. Environment settings
Copy `.env.example` to `.env`.
Keep `DB_ENGINE=sqlite` and `DEMO_PAYMENT=True` for the first run.

## 4. Create database tables and admin account
```powershell
python manage.py makemigrations orders
python manage.py migrate
python manage.py createsuperuser
```

## 5. Run
```powershell
python manage.py runserver
```
Open http://127.0.0.1:8000/

## Operator dashboard
Log in with the superuser account at http://127.0.0.1:8000/admin/ first.
Then open http://127.0.0.1:8000/operator/

## Demo payment
The default demo payment mode simulates payment locally. It is ONLY for development and does not charge money or prove that money was received. Never deploy with `DEMO_PAYMENT=True`.

## Optional MySQL Workbench
1. In MySQL Workbench, run:
   `CREATE DATABASE smart_xerox CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`
2. In `.env`, set `DB_ENGINE=mysql` and fill in DB_NAME, DB_USER, DB_PASSWORD, DB_HOST and DB_PORT.
3. Ensure your environment has a MySQL driver compatible with your Python installation.
4. Run `python manage.py migrate`.

If you switch databases after migrating, Django creates tables separately in the newly selected database. It does not automatically copy data from SQLite to MySQL.

## Optional Razorpay test mode
Set in `.env`:
```env
DEMO_PAYMENT=False
RAZORPAY_KEY_ID=your_razorpay_test_key_id
RAZORPAY_KEY_SECRET=your_razorpay_test_key_secret
```
Restart the development server. Use Razorpay TEST keys only while testing. The server verifies the checkout signature before marking the order paid and creating its QR code.

## Pricing used (sample rates)
- B&W single: ₹2 per page
- B&W double: ₹3 per physical sheet
- Colour single: ₹5 per page
- Colour double: ₹8 per physical sheet

Edit `calculate_amount()` in `orders/views.py` and the rate list in `templates/orders/home.html` together if you change prices.

## Important limitations before real deployment
This is a learning/demo MVP, not a production-ready printing service. Configure production hosting, HTTPS, secure secret management, private file storage, file scanning, upload quotas, backups, payment webhooks/reconciliation, access controls, and privacy/retention policies before accepting real customers. The operator currently downloads/opens the PDF and prints it manually; a website cannot silently print to an arbitrary local printer.
