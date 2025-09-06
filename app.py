from flask import Flask, jsonify, render_template, redirect, request, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, PasswordField, SubmitField, BooleanField, SelectField, FloatField, TextAreaField, DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import email_validator
from datetime import datetime

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'login'

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('sponsor', 'Sponsor'), ('influencer', 'Influencer')], validators=[DataRequired()])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already in use. Please choose a different one.')

class CampaignForm(FlaskForm):
    name = StringField('Campaign Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    budget = FloatField('Budget', validators=[DataRequired()])
    visibility = SelectField('Visibility', choices=[('public', 'Public'), ('private', 'Private')], validators=[DataRequired()])
    goals = TextAreaField('Goals', validators=[DataRequired()])
    submit = SubmitField('Create Campaign')
    

class AdRequestForm(FlaskForm):
    campaign_id = SelectField('Campaign', coerce=int, validators=[DataRequired()])
    influencer_id = SelectField('Influencer', coerce=int, validators=[DataRequired()])
    messages = TextAreaField('Messages')
    requirements = TextAreaField('Requirements', validators=[DataRequired()])
    payment_amount = FloatField('Payment Amount', validators=[DataRequired()])
    status = SelectField('Status', choices=[('Pending', 'Pending'), ('Accepted', 'Accepted'), ('Rejected', 'Rejected')], validators=[DataRequired()])
    submit = SubmitField('Create Ad Request')

class ManageAdRequestForm(FlaskForm):
    request_id = HiddenField('Request ID', validators=[DataRequired()])
    action = HiddenField('Action', validators=[DataRequired()])
    submit = SubmitField('Submit')

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    budget = db.Column(db.Float, nullable=False)
    visibility = db.Column(db.String(10), nullable=False)
    goals = db.Column(db.Text, nullable=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)    

class AdRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    messages = db.Column(db.Text, nullable=True)
    requirements = db.Column(db.Text, nullable=False)
    payment_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(10), nullable=False) 
    sponsor_id = db.Column(db.Integer, db.ForeignKey('user.id'))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///influencer_platform.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @app.route('/')
    def home():
        return render_template('home.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember.data)

           
                if user.role == 'admin':
                    return redirect(url_for('admin_dashboard'))  
                elif user.role == 'sponsor':
                    return redirect(url_for('sponsor_dashboard'))  
                elif user.role == 'influencer':
                    return redirect(url_for('influencer_dashboard'))  

            flash('Login Unsuccessful. Please check email and password', 'danger')
        return render_template('login.html', form=form)



    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('home'))
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(username=form.username.data, email=form.email.data, role=form.role.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created!', 'success')
            return redirect(url_for('login'))
        return render_template('register.html', form=form)


    from datetime import datetime
    @app.route('/dashboard')
    @login_required
    def dashboard():
  
        if current_user.role == 'sponsor':
            return redirect(url_for('sponsor_dashboard'))
        elif current_user.role == 'influencer':
            return redirect(url_for('influencer_dashboard'))
        return redirect(url_for('home'))

    @app.route('/create_campaign', methods=['GET', 'POST'])
    @login_required
    def create_campaign():
        if current_user.role != 'sponsor':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            name = request.form['name']
            description = request.form['description']
            try:
                start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
                end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
                return render_template('create_campaign.html')

            budget = float(request.form['budget'])
            visibility = request.form['visibility']
            goals = request.form['goals']

            new_campaign = Campaign(
                name=name,
                description=description,
                start_date=start_date,
                end_date=end_date,
                budget=budget,
                visibility=visibility,
                goals=goals,
                sponsor_id=current_user.id
            )
            db.session.add(new_campaign)
            db.session.commit()
            flash('Campaign created successfully!', 'success')
            return redirect(url_for('dashboard'))
        return render_template('create_campaign.html')
        
    @app.route('/campaigns')
    @login_required
    def view_campaigns():
        if current_user.role != 'sponsor':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard'))
    
        campaigns = Campaign.query.all()
        return render_template('view_campaigns.html', campaigns=campaigns)


    @app.route('/edit_campaign/<int:campaign_id>', methods=['GET', 'POST'])
    @login_required
    def edit_campaign(campaign_id):
        campaign = Campaign.query.get_or_404(campaign_id)
    
 
        if campaign.sponsor_id != current_user.id:
            flash('You do not have permission to edit this campaign.', 'danger')
            return redirect(url_for('sponsor_dashboard'))

        form = CampaignForm(obj=campaign)
    
        if form.validate_on_submit():
            form.populate_obj(campaign)
            db.session.commit()  
            flash('Campaign updated successfully!', 'success')
            return redirect(url_for('sponsor_dashboard'))
    
        return render_template('edit_campaign.html', form=form, campaign=campaign)


    @app.route('/delete_campaign/<int:campaign_id>', methods=['POST'])
    @login_required
    def delete_campaign(campaign_id):

        campaign = Campaign.query.get_or_404(campaign_id)
    

        if campaign.sponsor_id != current_user.id:
            flash('You do not have permission to delete this campaign.', 'danger')
            return redirect(url_for('sponsor_dashboard'))

        ad_requests = AdRequest.query.filter_by(campaign_id=campaign_id).all()
        for ad_request in ad_requests:
            db.session.delete(ad_request)


        db.session.delete(campaign)
        db.session.commit()
    
        flash('Campaign and associated ad requests deleted successfully!', 'success')
        return redirect(url_for('sponsor_dashboard'))



    @app.route('/influencer_dashboard', methods=['GET', 'POST'])
    @login_required
    def influencer_dashboard():
        if current_user.role != 'influencer':
            flash('Unauthorized access.', 'danger')
            return redirect(url_for('index'))

        ad_requests = AdRequest.query.filter_by(influencer_id=current_user.id).all()
        ad_requests_with_campaigns = [(ad_request, Campaign.query.get(ad_request.campaign_id)) for ad_request in ad_requests]

        if request.method == 'POST':
            ad_request_id = request.form.get('ad_request_id')
            status = request.form.get('status')
            ad_request = AdRequest.query.get(ad_request_id)
            if ad_request and ad_request.influencer_id == current_user.id:
                ad_request.status = status
                db.session.commit()
                flash('Ad request status updated.', 'success')
            else:
                flash('Failed to update ad request status.', 'danger')
            return redirect(url_for('influencer_dashboard'))

        return render_template('influencer_dashboard.html', ad_requests_with_campaigns=ad_requests_with_campaigns)


    
    @app.route('/search_sponsors', methods=['GET'])
    @login_required
    def search_sponsors():
        search_query = request.args.get('search_query', '')

        sponsors = User.query.filter(User.username.ilike(f'%{search_query}%'), User.role == 'sponsor').all()
    

        sponsor_campaigns = {}
        for sponsor in sponsors:
            campaigns = Campaign.query.filter_by(sponsor_id=sponsor.id).all()
            sponsor_campaigns[sponsor] = campaigns
    
        return render_template('influencer_dashboard.html', sponsors_campaigns=sponsor_campaigns)
    
    @app.route('/manage_ad_request', methods=['POST'])
    @login_required
    def manage_ad_request():
        form = ManageAdRequestForm()
        if form.validate_on_submit():
            request_id = form.request_id.data
            action = form.action.data

            print(f"Form validated: Request ID: {request_id}, Action: {action}")

            ad_request = AdRequest.query.get(request_id)
            if not ad_request:
                flash('Ad request not found', 'danger')
                return redirect(url_for('influencer_dashboard'))

            if action == 'accept':
                ad_request.status = 'Accepted'
            elif action == 'reject':
                ad_request.status = 'Rejected'

            db.session.commit()

            updated_ad_request = AdRequest.query.get(request_id)
            print(f"Updated Request Status: {updated_ad_request.status}")

            flash('Ad request updated successfully', 'success')
        else:
            print(f"Form errors: {form.errors}")
            flash('Form validation failed', 'danger')
        return redirect(url_for('influencer_dashboard'))

    @app.route('/sponsor_dashboard')
    def sponsor_dashboard():
        current_sponsor_id = current_user.id  
        campaigns = Campaign.query.filter_by(sponsor_id=current_sponsor_id).all()
    
        ad_requests = AdRequest.query.filter_by(sponsor_id=current_sponsor_id).all()
    

        ad_requests_with_details = []
        for request in ad_requests:
            influencer = User.query.get(request.influencer_id)
            campaign = Campaign.query.get(request.campaign_id)

            ad_requests_with_details.append({
                'id': request.id,
                'influencer_name': influencer.username if influencer else 'Unknown',
                'campaign_name': campaign.name if campaign else 'Unknown',
                'messages': request.messages,
                'requirements': request.requirements,
                'payment_amount': request.payment_amount,
                'status': request.status,
            })
        print(f"Campaigns: {campaigns}")
        print(f"Ad Requests with Details: {ad_requests_with_details}")
        return render_template('sponsor_dashboard.html', ad_requests=ad_requests_with_details, campaigns=campaigns)

    @app.route('/search_influencers', methods=['GET'])
    @login_required
    def search_influencers():
        search_query = request.args.get('search_query', '')

 
        influencers = User.query.filter(User.username.ilike(f'%{search_query}%'), User.role == 'influencer').all()


        campaigns = Campaign.query.filter_by(sponsor_id=current_user.id).all()


        return render_template('sponsor_dashboard.html', campaigns=campaigns, influencers=influencers)
    


    @app.route('/send_ad_request/<int:influencer_id>', methods=['POST'])
    @login_required
    def send_ad_request(influencer_id):
        campaign_id = request.form.get('campaign_id')
        requirements = request.form.get('requirements')
        payment_amount = request.form.get('payment_amount')
        messages = request.form.get('messages', '')  

        if not campaign_id or not requirements or not payment_amount:
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('sponsor_dashboard'))

        try:
            payment_amount = float(payment_amount)
        except ValueError:
            flash('Invalid payment amount', 'danger')
            return redirect(url_for('sponsor_dashboard'))

        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            flash('Invalid campaign', 'danger')
            return redirect(url_for('sponsor_dashboard'))

        ad_request = AdRequest(
            influencer_id=influencer_id,
            sponsor_id=current_user.id,
            campaign_id=campaign_id,
            requirements=requirements,
            payment_amount=payment_amount,
            messages=messages,
            status='pending'
        )

        db.session.add(ad_request)
        db.session.commit()

        flash('Ad request sent successfully!', 'success')
        return redirect(url_for('sponsor_dashboard'))
    
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
