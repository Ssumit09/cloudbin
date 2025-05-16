from flask import Flask, render_template, redirect, url_for, flash
from models import db, EwasteRequest, Voucher
from config import Config
from flask_cognito_auth import CognitoAuth

app = Flask(__name__)
app.config.from_object(Config)

# === Initialize Cognito & Database ===
cognito = CognitoAuth(app)
db.init_app(app)

# === Create tables ===
with app.app_context():
    db.create_all()
    if not Voucher.query.first():
        vouchers = [
            Voucher(name="Amazon ₹100", description="₹100 Amazon Gift Card", coins_required=100, code="AMAZON100"),
            Voucher(name="Amazon ₹250", description="₹250 Amazon Gift Card", coins_required=250, code="AMAZON250"),
            Voucher(name="Amazon ₹500", description="₹500 Amazon Gift Card", coins_required=500, code="AMAZON500"),
        ]
        db.session.add_all(vouchers)
        db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return redirect(cognito.get_sign_in_url())

@app.route('/callback')
@cognito.callback
def callback():
    return redirect(url_for('user_dashboard'))

@app.route('/user/dashboard')
@cognito.auth_required
def user_dashboard():
    user_email = cognito.claims.get("email")
    user_id = cognito.claims.get("sub")  # Use this as unique ID

    # Try fetching by email (adapt based on your DB structure)
    user = db.session.query(Voucher).first()  # Dummy usage, adapt
    requests = EwasteRequest.query.filter_by(user_id=user_id).all()

    return render_template('user_dashboard.html', user_email=user_email, requests=requests)

@app.route('/admin/dashboard')
@cognito.auth_required
def admin_dashboard():
    user_email = cognito.claims.get("email")
    if user_email != "admin@cloudbin.com":
        flash("Admin access only.", "danger")
        return redirect(url_for('index'))

    pending_requests = db.session.query(
        EwasteRequest
    ).filter(EwasteRequest.status == 'pending').all()

    return render_template('admin_dashboard.html', requests=pending_requests)

@app.route('/submit-request', methods=['GET', 'POST'])
@cognito.auth_required
def submit_request():
    from flask import request
    user_id = cognito.claims.get("sub")

    if request.method == 'POST':
        waste_type = request.form['waste_type']
        quantity = int(request.form['quantity'])
        location = request.form['location']
        coins = quantity * 10

        new_request = EwasteRequest(
            user_id=user_id,
            waste_type=waste_type,
            quantity=quantity,
            location=location,
            coins_awarded=coins
        )
        db.session.add(new_request)
        db.session.commit()
        flash('Request submitted successfully!', 'success')
        return redirect(url_for('user_dashboard'))

    return render_template('submit_request.html')

@app.route('/admin/approve/<int:request_id>')
@cognito.auth_required
def approve_request(request_id):
    user_email = cognito.claims.get("email")
    if user_email != "admin@cloudbin.com":
        flash("Admin access only.", "danger")
        return redirect(url_for('index'))

    ewaste_request = EwasteRequest.query.get(request_id)
    if ewaste_request:
        ewaste_request.status = 'approved'
        db.session.commit()
        flash('Request approved!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject/<int:request_id>')
@cognito.auth_required
def reject_request(request_id):
    user_email = cognito.claims.get("email")
    if user_email != "admin@cloudbin.com":
        flash("Admin access only.", "danger")
        return redirect(url_for('index'))

    ewaste_request = EwasteRequest.query.get(request_id)
    if ewaste_request:
        ewaste_request.status = 'rejected'
        db.session.commit()
        flash('Request rejected!', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/vouchers')
@cognito.auth_required
def vouchers():
    user_email = cognito.claims.get("email")
    user_id = cognito.claims.get("sub")

    available_vouchers = Voucher.query.filter(Voucher.stock > 0).all()
    return render_template('vouchers.html', user_email=user_email, vouchers=available_vouchers)

@app.route('/redeem/<int:voucher_id>')
@cognito.auth_required
def redeem_voucher(voucher_id):
    user_id = cognito.claims.get("sub")
    voucher = Voucher.query.get(voucher_id)

    if not voucher or voucher.stock <= 0:
        flash('Voucher not available', 'danger')
        return redirect(url_for('vouchers'))

    # You'd usually fetch and update user's coins in DB
    voucher.stock -= 1
    db.session.commit()
    flash(f'Voucher redeemed! Code: {voucher.code}', 'success')
    return redirect(url_for('vouchers'))

@app.route('/logout')
@cognito.logout
def logout():
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
