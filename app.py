from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from pymongo import MongoClient
import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"

def get_db_connection():
    client = MongoClient("mongodb://127.0.0.1:27017/")
    return client["bike_rental"]

ADMIN_EMAIL = "bike123@gmail.com"
ADMIN_PASSWORD = "bike123"

@app.route('/')
def base():
    db = get_db_connection()
    raw = db['reviews'].find().sort('created_at', -1)
    reviews = []
    for r in raw:
        u = db['users'].find_one({'_id': ObjectId(r['user_id'])})
        reviews.append({
            'name': u['name'] if u else 'Anonymous',
            'rating': r['rating'],
            'comment': r['comment'],
            'created_at': r['created_at'].strftime("%Y-%m-%d %H:%M")
        })
    return render_template('base.html', reviews=reviews)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        email = request.form['email']; pw = request.form['password']
        if email==ADMIN_EMAIL and pw==ADMIN_PASSWORD:
            session['admin']=True
            return redirect(url_for('admin_dashboard'))
        db = get_db_connection()
        user = db['users'].find_one({'email':email})
        if user and check_password_hash(user['password'],pw):
            session['user_id']=str(user['_id'])
            flash('Logged in','success')
            return redirect(url_for('index'))
        flash('Bad credentials','error')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        name,email,cc,phone,pw = (request.form[k] for k in ('full_name','email','country_code','mobile','password'))
        if not all((name,email,cc,phone,pw)):
            flash('All required','error'); return redirect(url_for('register'))
        db = get_db_connection()
        if db['users'].find_one({'email':email}):
            flash('Exists','error'); return redirect(url_for('login'))
        db['users'].insert_one({
            'name':name,'email':email,'country_code':cc,'phone':phone,
            'password':generate_password_hash(pw),'role':'user'
        })
        flash('Registered','success'); return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/index')
def index():
    if 'user_id' not in session:
        flash('Login first','error'); return redirect(url_for('login'))
    db=get_db_connection()
    bikes=list(db['bikes'].find())
    for b in bikes: b['_id']=str(b['_id'])
    # also pass reviews
    raw=db['reviews'].find().sort('created_at',-1)
    reviews=[{
        'name':(db['users'].find_one({'_id':ObjectId(r['user_id'])}) or {}).get('name','Anonymous'),
        'rating':r['rating'],'comment':r['comment'],
        'created_at':r['created_at'].strftime("%Y-%m-%d %H:%M")
    } for r in raw]
    return render_template('index.html', bikes=bikes, reviews=reviews)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Login first','error'); return redirect(url_for('login'))
    db=get_db_connection()
    user=db['users'].find_one({'_id':ObjectId(session['user_id'])})
    if not user:
        flash('Not found','error'); return redirect(url_for('login'))
    bookings=list(db['bookings'].find({'user_id':session['user_id']}))
    return render_template('profile.html', user=user, bookings=bookings)

@app.route('/bookbike/<bike_type>', methods=['GET','POST'])
def bookbike_dynamic(bike_type):
    if 'user_id' not in session:
        flash('Login first','error'); return redirect(url_for('login'))
    if request.method=='POST':
        f=request.form; 
        try:
            from_dt=datetime.datetime.strptime(f"{f['fromdate']} {f['fromtime']}","%Y-%m-%d %H:%M")
            to_dt  =datetime.datetime.strptime(f"{f['todate']} {f['totime']}","%Y-%m-%d %H:%M")
        except:
            flash('Bad date','error'); return redirect(request.url)
        now=datetime.datetime.now().replace(second=0,microsecond=0)
        if from_dt<now or to_dt<=from_dt:
            flash('Invalid range','error'); return redirect(request.url)
        db=get_db_connection()
        db['bookings'].insert_one({
            'user_id':session['user_id'],'bike_type':bike_type,
            'from_datetime':from_dt,'to_datetime':to_dt,
            'message':f.get('message',''),'status':'Pending','created_at':now
        })
        flash('Requested','success'); return redirect(url_for('index'))
    return render_template(f'{bike_type}.html', bike_type=bike_type)

@app.route('/add_review', methods=['GET','POST'])
def add_review():
    if 'user_id' not in session:
        flash('Login first','error'); return redirect(url_for('login'))
    if request.method=='POST':
        r=request.form['rating']; c=request.form['comment']
        if not (r and c):
            flash('All fields','error'); return redirect(url_for('add_review'))
        db=get_db_connection()
        db['reviews'].insert_one({
            'user_id':session['user_id'],'rating':int(r),
            'comment':c,'created_at':datetime.datetime.now()
        })
        flash('Thanks!','success'); return redirect(url_for('index'))
    return render_template('add_review.html')

# -- Admin panel --

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        flash('Admin login','error'); return redirect(url_for('login'))
    db=get_db_connection()
    bookings=list(db['bookings'].find({'status':'Pending'}))
    bikes=list(db['bikes'].find())
    for b in bookings: b['_id']=str(b['_id'])
    for b in bikes:    b['_id']=str(b['_id'])
    return render_template('admin_dashboard.html', bookings=bookings, bikes=bikes)

@app.route('/admin/approve_booking/<booking_id>', methods=['POST'])
def approve_booking(booking_id):
    if not session.get('admin'): return redirect(url_for('login'))
    get_db_connection()['bookings'].update_one({'_id':ObjectId(booking_id)},{'$set':{'status':'Approved'}})
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject_booking/<booking_id>', methods=['POST'])
def reject_booking(booking_id):
    if not session.get('admin'): return redirect(url_for('login'))
    get_db_connection()['bookings'].update_one({'_id':ObjectId(booking_id)},{'$set':{'status':'Rejected'}})
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_bike', methods=['GET','POST'])
def admin_add_bike():
    if not session.get('admin'): return redirect(url_for('login'))
    if request.method=='POST':
        m=request.form['model']; u=int(request.form['total_units'])
        get_db_connection()['bikes'].insert_one({'model':m,'total_units':u,'available_units':u})
        flash('Bike added','success'); return redirect(url_for('admin_dashboard'))
    return render_template('admin_add_bike.html')

@app.route('/admin/delete_bike/<bike_id>', methods=['POST'])
def admin_delete_bike(bike_id):
    if not session.get('admin'): return redirect(url_for('login'))
    get_db_connection()['bikes'].delete_one({'_id':ObjectId(bike_id)})
    flash('Bike removed','success'); return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('base'))

if __name__ == '__main__':
    app.run(debug=True)
