from flask import Flask, render_template, request, session, redirect, jsonify
import firebase, json, os

app = Flask(__name__)
env = os.environ['WEB_SECRETKEY_FAM_TREE']
app.config['SECRET_KEY'] = env


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        json_data = request.get_json()
        email = json_data.get('email')
        password = json_data.get('password')
        GmailListed = firebase.GmailListed(email)
        if GmailListed:
            if not firebase.Verified(email):
                return jsonify({'success': False, 'message': 'Email already exists! Wait For Verification.'}), 401
            return jsonify({'success': False, 'message': 'Email already exists! Please Login.'}), 200

        uid, isVerified = firebase.signup(email, password)
        
        if isVerified:
            return jsonify({'success': True, 'message': 'Signup sent! Please Login.'}), 200
        else:
            return jsonify({'success': False, 'message': 'Signup sent! Please wait for verification.'}), 200

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        json_data = request.get_json()
        email = json_data.get('email')
        password = json_data.get('password')
        uid, isVerified = firebase.login(email, password)
        
        if uid and isVerified:
            session['uid'] = uid
            session["verified"] = True
            return jsonify({'success': True, 'message': 'Login successful! Redirecting...'}), 200
        elif firebase.UidInRequests(uid) and isVerified:
            return jsonify({'success': False, 'message': 'Invalid email or password.'}), 401
        elif firebase.UidInRequests(uid) and not isVerified:
            return jsonify({'success': False, 'message': 'Please wait for verification.'}), 401
        elif not firebase.UidInRequests(uid):
            return jsonify({'success': False, 'message': 'Please signup first.'}), 401

    return render_template('login.html')


@app.route('/get_all_members')
def get_all_members():
    members = firebase.get_all_members()
    return jsonify(members), 200

@app.route('/get_all_requests')
def get_all_requests():
    if not session.get('admin'):
        return jsonify({'success': False, 'message': 'Unauthorized access!'}), 401
    requests = firebase.get_all_requests()
    return jsonify(requests), 200

@app.route('/update_request', methods=['POST', 'GET'])
def update_request():
    if request.method == 'POST':
        if not session.get('admin'):
            return jsonify({'success': False, 'message': 'Unauthorized access!'}), 401
        json_data = request.get_json()
        uid = json_data.get('uid')
        data = json_data.get('data')

        firebase.update_request(uid, data)

        return jsonify({'success': True, 'message': 'Request updated successfully!'}), 200

@app.route('/update_member', methods=['POST'])
def update_member():
    firebase.update_member(request.json['key'], request.json['member'])
    return jsonify({'success': True, 'message': 'Member updated successfully!'}), 200

@app.route('/add_member', methods=['POST'])
def add_member():
    uniqueId = 0
    while True:
        if not firebase.check_member(request.json['name'], uniqueId):
            break
        uniqueId += 1
    
    firebase.add_member(request.json['name'], uniqueId, request.json['gender'], request.json['birthDate'])
    return jsonify({'success': True, 'message': 'Member added successfully!'}), 200

@app.route('/adminCheck', methods=['POST']  )
def admin_check():
    if request.method == 'POST':
        json_data = request.get_json()
        password = json_data.get('password')

        if password == app.config['SECRET_KEY']:
            session['admin'] = True
            return jsonify({'success': True, 'message': 'Login successful! Redirecting...', 'redirect': '/admin/dashboard'})
        else:
            session['admin'] = False
            return jsonify({'success': False, 'message': 'Login failed!', 'redirect': '/signup'})

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin') or session.get('admin') == None:
        return redirect('/admin')
    return render_template('adminDashboard.html')

@app.route('/admin')
def admin_login():
    return render_template('adminLogin.html')

@app.route('/', methods=['GET', 'POST'])
def main():
    if 'uid' not in session:
        return redirect('/signup')

    if not session["verified"]:
        return redirect('/login')
    
    if firebase.UidInRequests(session['uid']):
        if not firebase.VerifiedUid(session['uid']):
            return redirect('/login')
        
    else:
        return redirect('/signup')
    
    
    return render_template('main_update.html')

if __name__ == "__main__":
    app.run()