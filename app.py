from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash 

app = Flask(__name__)

# --- Configuration ---
app.config['SECRET_KEY'] = 'a_very_secret_and_unique_key_for_security' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///employees.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Flask-Login Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Database Models ---

# 1. User Model (for Authentication)
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password_hash = db.Column(db.String(255))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 2. Employee Model (for Records)
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True, nullable=False)
    # --- NEW FIELD ---
    salary = db.Column(db.Float, nullable=True) 
    
    def __repr__(self):
        return f'<Employee {self.name}>'

# --- Initialization and Database Creation ---
# NOTE: If you run this, you will get an error on the Employee table because the schema changed.
# To fix this, you must DELETE the old 'employees.db' file before running app.py again.
with app.app_context():
    db.create_all()
    
    # Create a default admin user if one doesn't exist
    if not User.query.first():
        admin = User(username='admin')
        admin.set_password('password123') # Default password is 'password123'
        db.session.add(admin)
        db.session.commit()
        print("--- Default user 'admin' created with password 'password123' ---")

# --- Authentication Routes ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login failed. Check your username and password.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Protected CRUD Routes ---

@app.route('/')
@login_required 
def index():
    employees = Employee.query.all()
    return render_template('index.html', employees=employees)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        salary_input = request.form.get('salary')

        if not name or not email:
            flash("Error: Name and Email fields are required.", 'danger')
            return redirect(url_for('add_employee')) 

        if Employee.query.filter_by(email=email).first():
            flash("Error: This email address is already registered.", 'danger')
            return redirect(url_for('add_employee'))
            
        # Handle salary conversion and error checking
        try:
            salary = float(salary_input) if salary_input else 0.0
        except ValueError:
            flash("Error: Salary must be a valid number.", 'danger')
            return redirect(url_for('add_employee'))

        new_employee = Employee(
            name=name,
            position=request.form['position'],
            department=request.form['department'],
            email=email,
            salary=salary # --- NEW FIELD VALUE ---
        )
        
        db.session.add(new_employee)
        db.session.commit()
        flash(f"Employee {name} added successfully!", 'success')
        return redirect(url_for('index'))
        
    return render_template('add_employee.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def update_employee(id):
    employee = Employee.query.get_or_404(id) 

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        salary_input = request.form.get('salary') # --- NEW FIELD INPUT ---

        if not name or not email:
            flash("Error: Name and Email fields are required.", 'danger')
            return redirect(url_for('update_employee', id=id))

        existing_employee = Employee.query.filter_by(email=email).first()
        if existing_employee and existing_employee.id != id:
            flash("Error: This email address is already registered to another employee.", 'danger')
            return redirect(url_for('update_employee', id=id))
            
        # Handle salary conversion and error checking
        try:
            salary = float(salary_input) if salary_input else 0.0
        except ValueError:
            flash("Error: Salary must be a valid number.", 'danger')
            return redirect(url_for('update_employee', id=id))

        employee.name = name
        employee.position = request.form['position']
        employee.department = request.form['department']
        employee.email = email
        employee.salary = salary # --- NEW FIELD VALUE ---
        
        db.session.commit()
        flash(f"Employee {name} updated successfully!", 'success')
        return redirect(url_for('index'))

    return render_template('update_employee.html', employee=employee)

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_employee(id):
    employee = Employee.query.get_or_404(id)
    employee_name = employee.name
    
    db.session.delete(employee)
    db.session.commit()
    flash(f"Employee {employee_name} deleted successfully!", 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)