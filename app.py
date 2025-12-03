from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///academiamatch.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

db = SQLAlchemy(app)

# Database Models
class Researcher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(320), unique=True, nullable=False)
    organization = db.Column(db.String(200), nullable=False)
    researcher_type = db.Column(db.String(20), nullable=False)  # 'internal' or 'external'
    
    # Internal researcher fields
    faculty_department = db.Column(db.Text)
    primary_areas = db.Column(db.Text)
    experience_summary = db.Column(db.Text)
    sectors_interested = db.Column(db.Text)
    
    # External researcher fields
    organization_focus = db.Column(db.Text)
    challenge_description = db.Column(db.Text)
    expertise_sought = db.Column(db.Text)
    lab_tours_interested = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Routes
@app.route('/')
def index():
    internal_count = Researcher.query.filter_by(researcher_type='internal').count()
    external_count = Researcher.query.filter_by(researcher_type='external').count()
    return render_template('index.html', 
                         internal_count=internal_count, 
                         external_count=external_count)

@app.route('/register/external', methods=['GET', 'POST'])
def register_external():
    if request.method == 'POST':
        try:
            researcher = Researcher(
                name=request.form['name'],
                email=request.form['email'],
                organization=request.form['organization'],
                researcher_type='external',
                organization_focus=request.form.get('organization_focus', ''),
                challenge_description=request.form.get('challenge_description', ''),
                expertise_sought=request.form.get('expertise_sought', ''),
                lab_tours_interested=request.form.get('lab_tours_interested', '')
            )
            db.session.add(researcher)
            db.session.commit()
            return redirect(url_for('success', email=researcher.email))
        except Exception as e:
            return render_template('register_external.html', error=str(e))
    return render_template('register_external.html')

@app.route('/register/internal', methods=['GET', 'POST'])
def register_internal():
    if request.method == 'POST':
        try:
            researcher = Researcher(
                name=request.form['name'],
                email=request.form['email'],
                organization='Humber Polytechnic',
                researcher_type='internal',
                faculty_department=request.form.get('faculty_department', ''),
                primary_areas=request.form.get('primary_areas', ''),
                experience_summary=request.form.get('experience_summary', ''),
                sectors_interested=request.form.get('sectors_interested', '')
            )
            db.session.add(researcher)
            db.session.commit()
            return redirect(url_for('success', email=researcher.email))
        except Exception as e:
            return render_template('register_internal.html', error=str(e))
    return render_template('register_internal.html')

@app.route('/success')
def success():
    email = request.args.get('email', '')
    return render_template('success.html', email=email)

@app.route('/search', methods=['POST'])
def search():
    email = request.form.get('email', '').strip()
    if not email:
        return redirect(url_for('index'))
    
    researcher = Researcher.query.filter_by(email=email).first()
    if not researcher:
        return render_template('not_found.html', email=email)
    
    return redirect(url_for('matches', email=email))

@app.route('/matches/<email>')
def matches(email):
    from matching import find_matches
    
    researcher = Researcher.query.filter_by(email=email).first()
    if not researcher:
        return render_template('not_found.html', email=email)
    
    # Find matches
    matches_data = find_matches(researcher, top_n=5)
    
    return render_template('matches.html', 
                         researcher=researcher, 
                         matches=matches_data)

@app.route('/api/counts')
def api_counts():
    internal_count = Researcher.query.filter_by(researcher_type='internal').count()
    external_count = Researcher.query.filter_by(researcher_type='external').count()
    return jsonify({
        'internal': internal_count,
        'external': external_count,
        'total': internal_count + external_count
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
