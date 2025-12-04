from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# Use PostgreSQL (Supabase) if DATABASE_URL is set, otherwise fallback to SQLite
database_url = os.environ.get('DATABASE_URL', 'sqlite:///academiamatch.db')

# Fix for SQLAlchemy 1.4+ (Render/Heroku use 'postgres://' but SQLAlchemy needs 'postgresql://')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
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

class Match(db.Model):
    """Pre-computed matches between internal and external researchers"""
    id = db.Column(db.Integer, primary_key=True)
    internal_researcher_id = db.Column(db.Integer, db.ForeignKey('researcher.id'), nullable=False)
    external_researcher_id = db.Column(db.Integer, db.ForeignKey('researcher.id'), nullable=False)
    similarity_percentage = db.Column(db.Float, nullable=False)
    match_rank = db.Column(db.Integer, nullable=False)  # 1 = best match
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    internal_researcher = db.relationship('Researcher', foreign_keys=[internal_researcher_id])
    external_researcher = db.relationship('Researcher', foreign_keys=[external_researcher_id])

class EmailLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    internal_researcher_id = db.Column(db.Integer, db.ForeignKey('researcher.id'), nullable=False)
    external_researcher_id = db.Column(db.Integer, db.ForeignKey('researcher.id'), nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    internal_researcher = db.relationship('Researcher', foreign_keys=[internal_researcher_id])
    external_researcher = db.relationship('Researcher', foreign_keys=[external_researcher_id])

# Helper function to ensure tables exist (called on first request)
_tables_created = False
def ensure_tables():
    global _tables_created
    if not _tables_created:
        try:
            with app.app_context():
                db.create_all()
            _tables_created = True
        except Exception as e:
            print(f"Warning: Could not create tables: {e}")
            # Don't crash, just log the error

# Routes
@app.route('/')
def index():
    ensure_tables()  # Create tables on first request if needed
    try:
        internal_count = Researcher.query.filter_by(researcher_type='internal').count()
        external_count = Researcher.query.filter_by(researcher_type='external').count()
    except:
        # If database not accessible, show 0
        internal_count = 0
        external_count = 0
    return render_template('index.html', 
                         internal_count=internal_count, 
                         external_count=external_count)

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
    ensure_tables()
    try:
        internal_count = Researcher.query.filter_by(researcher_type='internal').count()
        external_count = Researcher.query.filter_by(researcher_type='external').count()
    except:
        internal_count = 0
        external_count = 0
    return jsonify({
        'internal': internal_count,
        'external': external_count,
        'total': internal_count + external_count
    })

# Admin route to load initial data from Excel files
@app.route('/admin/load-data')
def admin_load_data():
    """
    Load data from Excel files into the database.
    Visit this URL once after deployment to populate the database.
    URL: https://academiamatch.onrender.com/admin/load-data
    """
    # Ensure tables exist before loading data
    ensure_tables()
    
    try:
        from load_data import load_all_data
        
        # Check if data already loaded
        existing_count = Researcher.query.count()
        if existing_count > 0:
            return f"""
            <html>
            <head><title>Data Already Loaded</title></head>
            <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
                <h1 style="color: #f39c12;">⚠️ Data Already Exists</h1>
                <p>The database already contains <strong>{existing_count} researchers</strong>.</p>
                <p>Loading data again might create duplicates.</p>
                <h3>Current Database Status:</h3>
                <ul>
                    <li>Internal Researchers: {Researcher.query.filter_by(researcher_type='internal').count()}</li>
                    <li>External Researchers: {Researcher.query.filter_by(researcher_type='external').count()}</li>
                    <li>Total: {existing_count}</li>
                </ul>
                <p><a href="/" style="color: #3498db;">← Go to Homepage</a></p>
                <hr>
                <p style="font-size: 12px; color: #666;">
                    If you want to reload data, delete the database first or clear all researchers.
                </p>
            </body>
            </html>
            """
        
        # Load data
        total = load_all_data()
        
        # Get final counts
        internal_count = Researcher.query.filter_by(researcher_type='internal').count()
        external_count = Researcher.query.filter_by(researcher_type='external').count()
        
        return f"""
        <html>
        <head><title>Data Loading Complete</title></head>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1 style="color: #27ae60;">✅ Success!</h1>
            <p>Successfully loaded <strong>{total} researchers</strong> into the Supabase database.</p>
            <h3>Loading Summary:</h3>
            <ul>
                <li>Internal Researchers (Humber): <strong>{internal_count}</strong></li>
                <li>External Researchers: <strong>{external_count}</strong></li>
                <li>Total: <strong>{total}</strong></li>
            </ul>
            <p><a href="/" style="display: inline-block; background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Go to Homepage</a></p>
            <hr>
            <p style="font-size: 12px; color: #666;">
                Data loaded from Excel files into PostgreSQL (Supabase). Your data is now persistent!
            </p>
        </body>
        </html>
        """
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return f"""
        <html>
        <head><title>Error Loading Data</title></head>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1 style="color: #e74c3c;">❌ Error</h1>
            <p>Failed to load data from Excel files.</p>
            <h3>Error Details:</h3>
            <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto;">{str(e)}</pre>
            <h3>Full Traceback:</h3>
            <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 11px;">{error_details}</pre>
            <p><a href="/" style="color: #3498db;">← Go to Homepage</a></p>
            <hr>
            <p style="font-size: 12px; color: #666;">
                Make sure the Excel files are in the root directory of your repository.
            </p>
        </body>
        </html>
        """, 500

@app.route('/admin/force-reload')
def admin_force_reload():
    """
    Force clear database and reload data from Excel files.
    URL: https://academiamatch.onrender.com/admin/force-reload
    """
    ensure_tables()
    
    try:
        from load_data import load_all_data
        
        # Force clear all data
        Researcher.query.delete()
        db.session.commit()
        
        # Load fresh data
        total = load_all_data()
        
        # Get final counts
        internal_count = Researcher.query.filter_by(researcher_type='internal').count()
        external_count = Researcher.query.filter_by(researcher_type='external').count()
        
        return f"""
        <html>
        <head><title>Data Reloaded Successfully</title></head>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1 style="color: #27ae60;">✅ Database Cleared and Reloaded!</h1>
            <p>Successfully cleared old data and loaded <strong>{total} researchers</strong> from Excel files.</p>
            <h3>New Database Status:</h3>
            <ul>
                <li>Internal Researchers (Humber): <strong>{internal_count}</strong></li>
                <li>External Researchers: <strong>{external_count}</strong></li>
                <li>Total: <strong>{total}</strong></li>
            </ul>
            <p><a href="/" style="display: inline-block; background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Go to Homepage</a></p>
            <hr>
            <p style="font-size: 12px; color: #666;">
                Old data has been cleared. New data loaded with correct column mapping.
            </p>
        </body>
        </html>
        """
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return f"""
        <html>
        <head><title>Error Reloading Data</title></head>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1 style="color: #e74c3c;">❌ Error</h1>
            <p>Failed to reload data from Excel files.</p>
            <h3>Error Details:</h3>
            <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto;">{str(e)}</pre>
            <h3>Full Traceback:</h3>
            <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 11px;">{error_details}</pre>
            <p><a href="/" style="color: #3498db;">← Go to Homepage</a></p>
        </body>
        </html>
        """, 500

@app.route('/api/track-email', methods=['POST'])
def track_email():
    """
    Track when an email is sent from internal to external researcher.
    """
    try:
        data = request.get_json()
        internal_email = data.get('internal_email')
        external_email = data.get('external_email')
        
        # Get researcher IDs
        internal = Researcher.query.filter_by(email=internal_email).first()
        external = Researcher.query.filter_by(email=external_email).first()
        
        if not internal or not external:
            return jsonify({'error': 'Researcher not found'}), 404
        
        # Check if already logged
        existing = EmailLog.query.filter_by(
            internal_researcher_id=internal.id,
            external_researcher_id=external.id
        ).first()
        
        if not existing:
            # Create new log entry
            log = EmailLog(
                internal_researcher_id=internal.id,
                external_researcher_id=external.id
            )
            db.session.add(log)
            db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/match-list')
def match_list():
    """
    Show all pre-computed matches between internal and external researchers with email status.
    This reads from the Match table (no AI computation needed - super fast!).
    """
    ensure_tables()
    
    try:
        # Get all pre-computed matches from database (sorted by similarity)
        matches = Match.query.order_by(Match.similarity_percentage.desc()).all()
        
        # Get email logs for status
        email_logs = EmailLog.query.all()
        email_status = {}
        for log in email_logs:
            key = f"{log.internal_researcher_id}_{log.external_researcher_id}"
            email_status[key] = log.sent_at
        
        # Format matches for template
        all_matches = []
        for idx, match in enumerate(matches, 1):
            key = f"{match.internal_researcher_id}_{match.external_researcher_id}"
            
            all_matches.append({
                'match_rank': idx,
                'internal_name': match.internal_researcher.name,
                'internal_email': match.internal_researcher.email,
                'faculty_department': match.internal_researcher.faculty_department or 'N/A',
                'external_name': match.external_researcher.name,
                'external_email': match.external_researcher.email,
                'organization': match.external_researcher.organization,
                'similarity_percentage': round(match.similarity_percentage, 1),
                'email_sent': key in email_status,
                'email_sent_at': email_status.get(key)
            })
        
        return render_template('match_list.html', matches=all_matches)
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return f"Error loading matches: {str(e)}<br><br><pre>{error_details}</pre>", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
