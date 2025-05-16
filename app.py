from flask import Flask, render_template, redirect, url_for, flash, request, session
from models import db, EwasteRequest, Voucher
from config import Config
import jwt
import requests
from functools import wraps

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# === JWT Utility Functions ===
def get_cognito_public_keys():
    region = app.config["COGNITO_REGION"]
    user_pool_id = app.config["COGNITO_USERPOOL_ID"]
    url = f'https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json'
    response = requests.get(url)
    return response.json()['keys']

def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('id_token') or session.get('id_token')
        if not token:
            return redirect(url_for('login'))
        keys = get_cognito_public_keys()
        for key in keys:
            try:
                decoded = jwt.decode(token, key=jwt.algorithms.RSAAlgorithm.from_jwk(key),
                                     algorithms=['RS256'],
                                     audience=app.config["COGNITO_AUDIENCE"],
                                     issuer=f"https://cognito-idp.{app.config['COGNITO_REGION']}.amazonaws.com/{app.config['COGNITO_USERPOOL_ID']}")
                session['claims'] = decoded
                session['id_token'] = token
                return f(*args, **kwargs)
            except jwt.ExpiredSignatureError:
                return "Token expired", 401
            except jwt.InvalidTokenError:
                continue
        return "Invalid token", 403
    return decorated

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
    return redirect("https://" + app.config["COGNITO_DOMAIN"] + "/login?response_type=token&client_id=" + app.config["COGNITO_AUDIENCE"] + "&redirect_uri=" + app.config["COGNITO_REDIRECT_URI"] + "&scope=email+openid+profile")

@app.route('/callback')
@jwt_required
def callback():
    return redirect(url_for('user_dashboard'))

@app.route('/user/dashboard')
@jwt_required
def user_dashboard():
    user_email = session['claims'].get("email")
    user_id = session['claims'].get("sub")
    requests_data = EwasteRequest.query.filter_by(user_id=user_id).all()
    return render_template('user_dashboard.html', user_email=user_email, requests=requests_data)

@app.route('/admin/dashboard')
@jwt_required
def admin_dashboard():
    user_email = session['claims'].get("email")
    if user_email != "admin@cloudbin.com":
        flash("Admin access only.", "danger")
        return redirect(url_for('index'))
    pending_requests = EwasteRequest.query.filter(EwasteRequest.status == 'pending').all()
    return render_template('admin_dashboard.html', requests=pending_requests)

@app.route('/submit-request', methods=['GET', 'POST'])
@jwt_required
def submit_request():
    user_id = session['claims'].get("sub")
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
@jwt_required
def approve_request(request_id):
    user_email = session['claims'].get("email")
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
@jwt_required
def reject_request(request_id):
    user_email = session['claims'].get("email")
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
@jwt_required
def vouchers():
    user_email = session['claims'].get("email")
    user_id = session['claims'].get("sub")
    available_vouchers = Voucher.query.filter(Voucher.stock > 0).all()
    return render_template('vouchers.html', user_email=user_email, vouchers=available_vouchers)

@app.route('/redeem/<int:voucher_id>')
@jwt_required
def redeem_voucher(voucher_id):
    user_id = session['claims'].get("sub")
    voucher = Voucher.query.get(voucher_id)
    if not voucher or voucher.stock <= 0:
        flash('Voucher not available', 'danger')
        return redirect(url_for('vouchers'))
    voucher.stock -= 1
    db.session.commit()
    flash(f'Voucher redeemed! Code: {voucher.code}', 'success')
    return redirect(url_for('vouchers'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect("https://" + app.config["COGNITO_DOMAIN"] + "/logout?client_id=" + app.config["COGNITO_AUDIENCE"] + "&logout_uri=" + app.config["COGNITO_REDIRECT_URI"])

if __name__ == '__main__':
    app.run(debug=True)
