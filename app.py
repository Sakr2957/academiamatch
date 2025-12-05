from flask import Flask, render_template, request, jsonify, redirect, url_for, session, make_response
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
    matches_data = find_matches(researcher, top_n=3)
    
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

@app.route('/register/internal', methods=['GET', 'POST'])
def register_internal():
    """
    Internal researcher registration form.
    GET: Show form
    POST: Save to database
    """
    ensure_tables()
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            faculty_department = request.form.get('faculty_department', '').strip()
            primary_areas = request.form.get('primary_areas', '').strip()
            experience_summary = request.form.get('experience_summary', '').strip()
            sectors_interested = request.form.get('sectors_interested', '').strip()
            
            # Validate required fields
            if not all([name, email, faculty_department, primary_areas, sectors_interested]):
                return render_template('register_internal.html', error='Please fill in all required fields')
            
            # Check if email already exists
            existing = Researcher.query.filter_by(email=email).first()
            if existing:
                return render_template('register_internal.html', error='This email is already registered')
            
            # Create new researcher
            researcher = Researcher(
                name=name,
                email=email,
                researcher_type='internal',
                organization='Humber Polytechnic',
                faculty_department=faculty_department,
                primary_areas=primary_areas,
                experience_summary=experience_summary,
                sectors_interested=sectors_interested
            )
            
            db.session.add(researcher)
            db.session.commit()
            
            # Redirect to success page (matches page)
            return redirect(url_for('matches', email=email))
            
        except Exception as e:
            db.session.rollback()
            return render_template('register_internal.html', error=f'Registration failed: {str(e)}')
    
    # GET request - show form
    return render_template('register_internal.html')

@app.route('/register/external', methods=['GET', 'POST'])
def register_external():
    """
    External researcher registration form.
    GET: Show form
    POST: Save to database
    """
    ensure_tables()
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            organization = request.form.get('organization', '').strip()
            organization_focus = request.form.get('organization_focus', '').strip()
            challenge_description = request.form.get('challenge_description', '').strip()
            expertise_sought = request.form.get('expertise_sought', '').strip()
            lab_tours_interested = request.form.get('lab_tours_interested', '').strip()
            
            # Validate required fields
            if not all([name, email, organization, organization_focus, expertise_sought]):
                return render_template('register_external.html', error='Please fill in all required fields')
            
            # Check if email already exists
            existing = Researcher.query.filter_by(email=email).first()
            if existing:
                return render_template('register_external.html', error='This email is already registered')
            
            # Create new researcher
            researcher = Researcher(
                name=name,
                email=email,
                researcher_type='external',
                organization=organization,
                organization_focus=organization_focus,
                challenge_description=challenge_description,
                expertise_sought=expertise_sought,
                lab_tours_interested=lab_tours_interested
            )
            
            db.session.add(researcher)
            db.session.commit()
            
            # Redirect to success page (matches page)
            return redirect(url_for('matches', email=email))
            
        except Exception as e:
            db.session.rollback()
            return render_template('register_external.html', error=f'Registration failed: {str(e)}')
    
    # GET request - show form
    return render_template('register_external.html')

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

@app.route('/admin/nuclear-reset')
def admin_nuclear_reset():
    """
    NUCLEAR OPTION: Drop and recreate all tables.
    This will completely wipe the database and start fresh.
    URL: https://academiamatch.onrender.com/admin/nuclear-reset
    """
    try:
        # Drop all tables
        db.session.execute(db.text('DROP TABLE IF EXISTS email_log CASCADE'))
        db.session.execute(db.text('DROP TABLE IF EXISTS match CASCADE'))
        db.session.execute(db.text('DROP TABLE IF EXISTS researcher CASCADE'))
        db.session.commit()
        
        # Recreate all tables
        db.create_all()
        
        return """
        <html>
        <head>
            <title>Database Reset Complete</title>
            <meta http-equiv="refresh" content="3;url=/admin/force-reload">
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1 style="color: #27ae60;">✅ Database Reset Complete!</h1>
            <p>All tables have been dropped and recreated.</p>
            <h2 style="color: #f39c12;">⏳ Redirecting to load data in 3 seconds...</h2>
            <p>If not redirected, <a href="/admin/force-reload" style="color: #3498db; font-weight: bold;">click here</a> to load data.</p>
        </body>
        </html>
        """
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return f"""
        <html>
        <head><title>Reset Error</title></head>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1 style="color: #e74c3c;">❌ Error</h1>
            <p>Failed to reset database.</p>
            <h3>Error Details:</h3>
            <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto;">{str(e)}</pre>
            <details>
                <summary>Full Traceback</summary>
                <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 12px;">{error_details}</pre>
            </details>
            <p><a href="/" style="color: #3498db;">← Go to Homepage</a></p>
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
        
        # Force clear all data using TRUNCATE CASCADE (nuclear option)
        # This bypasses foreign key checks and forcefully empties all tables
        db.session.execute(db.text('TRUNCATE TABLE email_log, match, researcher RESTART IDENTITY CASCADE'))
        db.session.commit()
        
        # Load fresh data
        total = load_all_data()
        
        # Get final counts
        internal_count = Researcher.query.filter_by(researcher_type='internal').count()
        external_count = Researcher.query.filter_by(researcher_type='external').count()
        
        return f"""
        <html>
        <head>
            <title>Step 1 Complete - Data Loaded</title>
            <meta http-equiv="refresh" content="0;url=/admin/compute-matches">
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1 style="color: #27ae60;">✅ Step 1: Data Loaded Successfully!</h1>
            <p>Successfully loaded <strong>{total} researchers</strong> from Excel files.</p>
            <h3>Database Status:</h3>
            <ul>
                <li>Internal Researchers (Humber): <strong>{internal_count}</strong></li>
                <li>External Researchers: <strong>{external_count}</strong></li>
            </ul>
            <hr>
            <h2 style="color: #f39c12;">⏳ Step 2: Computing Matches...</h2>
            <p>Redirecting to match computation (takes 5-10 minutes)...</p>
            <p>If not redirected automatically, <a href="/admin/compute-matches" style="color: #3498db; font-weight: bold;">click here</a>.</p>
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

@app.route('/admin/compute-matches')
def admin_compute_matches():
    """
    Compute and store matches for all internal researchers.
    This should be run AFTER /admin/force-reload to populate the Match table.
    URL: https://academiamatch.onrender.com/admin/compute-matches
    """
    ensure_tables()
    
    try:
        from load_data import compute_and_store_matches_incremental
        
        # Check if we have researchers
        internal_count = Researcher.query.filter_by(researcher_type='internal').count()
        external_count = Researcher.query.filter_by(researcher_type='external').count()
        
        if internal_count == 0 or external_count == 0:
            return f"""
            <html>
            <head><title>No Data Found</title></head>
            <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
                <h1 style="color: #f39c12;">⚠️ No Researchers Found</h1>
                <p>Please load data first by visiting <a href="/admin/force-reload">/admin/force-reload</a></p>
                <p>Current database status:</p>
                <ul>
                    <li>Internal Researchers: {internal_count}</li>
                    <li>External Researchers: {external_count}</li>
                </ul>
                <p><a href="/" style="color: #3498db;">← Go to Homepage</a></p>
            </body>
            </html>
            """
        
        # Get current progress
        current_matches = Match.query.count()
        batch_number = (current_matches // 10) + 1
        
        # Compute next batch of matches (10 at a time)
        print(f"\n{'='*60}")
        print(f"Starting incremental match computation - Batch {batch_number}")
        print(f"This will process 10 researchers (takes ~2-3 minutes)")
        print(f"{'='*60}\n")
        
        result = compute_and_store_matches_incremental(batch_number=batch_number, batch_size=10)
        
        # Check if complete or more batches needed
        if result['status'] == 'complete':
            return f"""
            <html>
            <head><title>All Matches Computed!</title></head>
            <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
                <h1 style="color: #27ae60;">✅ All Matches Computed!</h1>
                <p>All <strong>{result['total_matches']}</strong> researchers have been matched!</p>
                <h3>Summary:</h3>
                <ul>
                    <li>Total Internal Researchers: {result['total_researchers']}</li>
                    <li>Total Matches Computed: {result['total_matches']}</li>
                    <li>Remaining: {result['remaining']}</li>
                </ul>
                <p style="margin-top: 30px;">
                    <a href="/match-list" style="background: #27ae60; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        📄 View Top 10 Matches
                    </a>
                </p>
                <p style="margin-top: 20px;"><a href="/" style="color: #3498db;">← Back to Home</a></p>
            </body>
            </html>
            """
        else:
            return f"""
            <html>
            <head>
                <title>Batch {result['batch_number']} Complete</title>
                <meta http-equiv="refresh" content="3;url=/admin/compute-matches">
            </head>
            <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
                <h1 style="color: #3498db;">✅ Batch {result['batch_number']} Complete!</h1>
                <p>Processed <strong>{result['processed_this_batch']}</strong> researchers in this batch.</p>
                <h3>Progress:</h3>
                <div style="background: #ecf0f1; border-radius: 10px; padding: 3px; margin: 20px 0;">
                    <div style="background: #3498db; width: {(result['total_matches']/result['total_researchers'])*100}%; height: 30px; border-radius: 8px; text-align: center; line-height: 30px; color: white; font-weight: bold;">
                        {result['total_matches']}/{result['total_researchers']} ({int((result['total_matches']/result['total_researchers'])*100)}%)
                    </div>
                </div>
                <ul>
                    <li>Total Matches: {result['total_matches']}/{result['total_researchers']}</li>
                    <li>Remaining: {result['remaining']}</li>
                    <li>Next Batch: {result['next_batch']}</li>
                </ul>
                <h2 style="color: #f39c12;">⏳ Auto-starting Batch {result['next_batch']} in 3 seconds...</h2>
                <p>If not redirected, <a href="/admin/compute-matches" style="color: #3498db; font-weight: bold;">click here</a> to continue.</p>
                <p style="color: #7f8c8d; font-size: 14px; margin-top: 30px;">⚠️ Keep this tab open until all batches complete!</p>
            </body>
            </html>
            """
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return f"""
        <html>
        <head><title>Error Computing Matches</title></head>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1 style="color: #e74c3c;">❌ Error</h1>
            <p>Failed to compute matches.</p>
            <h3>Error Details:</h3>
            <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto;">{str(e)}</pre>
            <h3>Full Traceback:</h3>
            <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 11px;">{error_details}</pre>
            <p><a href="/" style="color: #3498db;">← Go to Homepage</a></p>
        </body>
        </html>
        """, 500

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """
    Admin login page for accessing match-list.
    Authorized emails: ahmed.sakr@humber.ca, Stefanie.Bernaudo@humber.ca, Rita.Liu@humber.ca
    Password: Enzo@1939
    """
    AUTHORIZED_EMAILS = [
        'ahmed.sakr@humber.ca',
        'stefanie.bernaudo@humber.ca',
        'rita.liu@humber.ca'
    ]
    ADMIN_PASSWORD = 'Enzo@1939'
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if email in AUTHORIZED_EMAILS and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_email'] = email
            return redirect('/match-list')
        else:
            return render_template('admin_login.html', error='Invalid email or password')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Logout admin user"""
    session.pop('admin_logged_in', None)
    session.pop('admin_email', None)
    return redirect('/')

@app.route('/match-list')
def match_list():
    """
    Show all pre-computed matches between internal and external researchers with email status.
    This reads from the Match table (no AI computation needed - super fast!).
    """
    # Check if user is logged in as admin
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    
    ensure_tables()
    
    try:
        # Get top 20 highest-scoring matches from database
        matches = Match.query.order_by(Match.similarity_percentage.desc()).limit(20).all()
        
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
        
        # Clear session after viewing to force login next time
        response = make_response(render_template('match_list.html', matches=all_matches))
        session.pop('admin_logged_in', None)
        return response
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return f"Error loading matches: {str(e)}<br><br><pre>{error_details}</pre>", 500

@app.route('/admin/reset-email-logs')
def admin_reset_email_logs():
    """
    Reset all email logs (clear 'Sent' status for all matches).
    URL: https://academiamatch.onrender.com/admin/reset-email-logs
    """
    ensure_tables()
    
    try:
        # Delete all email logs
        deleted_count = EmailLog.query.delete()
        db.session.commit()
        
        return f"""
        <html>
        <head><title>Email Logs Reset</title></head>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1 style="color: #27ae60;">✅ Email Logs Reset Complete!</h1>
            <p>Deleted <strong>{deleted_count}</strong> email log entries.</p>
            <p>All match statuses are now "Not Sent".</p>
            <p><a href="/match-list" style="background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Match List</a></p>
            <p><a href="/" style="color: #3498db;">← Go to Homepage</a></p>
        </body>
        </html>
        """
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return f"""
        <html>
        <head><title>Reset Error</title></head>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1 style="color: #e74c3c;">❌ Error</h1>
            <p>Failed to reset email logs.</p>
            <h3>Error Details:</h3>
            <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto;">{str(e)}</pre>
            <details>
                <summary>Full Traceback</summary>
                <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 12px;">{error_details}</pre>
            </details>
            <p><a href="/" style="color: #3498db;">← Go to Homepage</a></p>
        </body>
        </html>
        """, 500

@app.route('/admin/load-top20')
def admin_load_top20():
    """
    Load Top 20 matches from Excel file into database.
    This replaces all matches in the Match table with the curated Top 20.
    URL: https://academiamatch.onrender.com/admin/load-top20
    """
    ensure_tables()
    
    try:
        import pandas as pd
        import os
        
        # Path to the top20 Excel file
        excel_file = 'top20_matches.xlsx'
        
        if not os.path.exists(excel_file):
            return f"""
            <html>
            <head><title>File Not Found</title></head>
            <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
                <h1 style="color: #e74c3c;">❌ Error</h1>
                <p>Top 20 matches file not found: <code>{excel_file}</code></p>
                <p>Please ensure the file exists in the application directory.</p>
                <p><a href="/" style="color: #3498db;">← Go to Homepage</a></p>
            </body>
            </html>
            """, 404
        
        # Read Excel file
        df = pd.read_excel(excel_file)
        
        # Clear existing matches
        deleted_count = Match.query.delete()
        db.session.commit()
        
        # Load new matches
        loaded_count = 0
        for idx, row in df.iterrows():
            # Get or create researchers
            internal = Researcher.query.filter_by(email=row['internal_email']).first()
            external = Researcher.query.filter_by(email=row['external_email']).first()
            
            if internal and external:
                match = Match(
                    internal_researcher_id=internal.id,
                    external_researcher_id=external.id,
                    similarity_percentage=float(row['similarity_percentage']),
                    match_rank=idx + 1
                )
                db.session.add(match)
                loaded_count += 1
        
        db.session.commit()
        
        return f"""
        <html>
        <head><title>Top 20 Loaded</title></head>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1 style="color: #27ae60;">✅ Top 20 Matches Loaded!</h1>
            <p>Deleted <strong>{deleted_count}</strong> old matches.</p>
            <p>Loaded <strong>{loaded_count}</strong> new Top 20 matches.</p>
            <h3>Summary:</h3>
            <ul>
                <li>Match table cleared</li>
                <li>Top 20 highest-scoring matches loaded</li>
                <li>Email logs preserved (not affected)</li>
            </ul>
            <p><a href="/match-list" style="background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Top 20 List</a></p>
            <p><a href="/" style="color: #3498db;">← Go to Homepage</a></p>
        </body>
        </html>
        """
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        db.session.rollback()
        return f"""
        <html>
        <head><title>Load Error</title></head>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1 style="color: #e74c3c;">❌ Error</h1>
            <p>Failed to load Top 20 matches.</p>
            <h3>Error Details:</h3>
            <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto;">{str(e)}</pre>
            <details>
                <summary>Full Traceback</summary>
                <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 12px;">{error_details}</pre>
            </details>
            <p><a href="/" style="color: #3498db;">← Go to Homepage</a></p>
        </body>
        </html>
        """, 500

@app.route('/admin/safe-check-researchers')
def admin_safe_check_researchers():
    """
    Safely check for missing researchers and add them if needed.
    Does NOT delete anything - only adds missing researchers.
    URL: https://academiamatch.onrender.com/admin/safe-check-researchers
    """
    ensure_tables()
    
    try:
        import pandas as pd
        
        # Read Excel files
        internal_df = pd.read_excel('HumberInternalResearch.xlsx')
        external_df = pd.read_excel('ExternalResearch.xlsx')
        
        # Rename columns
        internal_df = internal_df.rename(columns={
            "Your Name": "name",
            "Email Address": "email",
            "Your Faculty/Department": "faculty_department",
            internal_df.columns[4]: "primary_areas",
            internal_df.columns[5]: "experience_summary",
            internal_df.columns[6]: "sectors_interested"
        })
        
        external_df = external_df.rename(columns={
            "Your Name": "name",
            "Email Address": "email",
            "Your Orgnization": "organization",
            external_df.columns[4]: "organization_focus",
            external_df.columns[5]: "challenge_description",
            external_df.columns[6]: "expertise_sought",
            external_df.columns[7]: "lab_tours_interested"
        })
        
        added_internal = 0
        added_external = 0
        
        # Check and add internal researchers
        for _, row in internal_df.iterrows():
            email = str(row['email']).strip().lower()
            existing = Researcher.query.filter_by(email=email).first()
            
            if not existing:
                researcher = Researcher(
                    name=row['name'],
                    email=email,
                    researcher_type='internal',
                    organization='Humber Polytechnic',
                    faculty_department=row.get('faculty_department'),
                    primary_areas=row.get('primary_areas'),
                    experience_summary=row.get('experience_summary'),
                    sectors_interested=row.get('sectors_interested')
                )
                db.session.add(researcher)
                added_internal += 1
        
        # Check and add external researchers
        for _, row in external_df.iterrows():
            email = str(row['email']).strip().lower()
            existing = Researcher.query.filter_by(email=email).first()
            
            if not existing:
                researcher = Researcher(
                    name=row['name'],
                    email=email,
                    researcher_type='external',
                    organization=row.get('organization'),
                    organization_focus=row.get('organization_focus'),
                    challenge_description=row.get('challenge_description'),
                    expertise_sought=row.get('expertise_sought'),
                    lab_tours_interested=row.get('lab_tours_interested')
                )
                db.session.add(researcher)
                added_external += 1
        
        db.session.commit()
        
        # Get current counts
        total_internal = Researcher.query.filter_by(researcher_type='internal').count()
        total_external = Researcher.query.filter_by(researcher_type='external').count()
        
        return f"""
        <html>
        <head><title>Safe Check Complete</title></head>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1 style="color: #27ae60;">✅ Safe Check Complete!</h1>
            <h3>Added Missing Researchers:</h3>
            <ul>
                <li>Internal: <strong>{added_internal}</strong> added</li>
                <li>External: <strong>{added_external}</strong> added</li>
            </ul>
            <h3>Current Database Status:</h3>
            <ul>
                <li>Total Internal: <strong>{total_internal}</strong></li>
                <li>Total External: <strong>{total_external}</strong></li>
            </ul>
            <h3>What Was NOT Touched:</h3>
            <ul>
                <li>✅ Existing researchers - preserved</li>
                <li>✅ Match table - preserved</li>
                <li>✅ Email logs - preserved</li>
            </ul>
            <p><a href="/admin/load-top20" style="background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Now Load Top 20</a></p>
            <p><a href="/" style="color: #3498db;">← Go to Homepage</a></p>
        </body>
        </html>
        """
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        db.session.rollback()
        return f"""
        <html>
        <head><title>Check Error</title></head>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1 style="color: #e74c3c;">❌ Error</h1>
            <p>Failed to check researchers.</p>
            <h3>Error Details:</h3>
            <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto;">{str(e)}</pre>
            <details>
                <summary>Full Traceback</summary>
                <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 12px;">{error_details}</pre>
            </details>
            <p><a href="/" style="color: #3498db;">← Go to Homepage</a></p>
        </body>
        </html>
        """, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
