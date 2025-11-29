from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import db, Expense, User, Category

# create the app instance 
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expense.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    return '<h1>Hello World</h1>'


@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        # check if username is unique
        if User.query.filter_by(username = username).first():
            flash('Username already exists', 'error')
        else:
            new_user = User(username = username, password = password)
            db.session.add(new_user)
            db.session.commit()

            flash('Regiastratiion Successfull', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username = request.form['username']).first()

        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'error')
        
    return render_template('login.html')



@app.route('/dashboard')
@login_required
def dashboard():
    expenses = Expense.query.filter_by(user_id = current_user.id).all()
    category_totals = {}

    # calculate total amt spent on all categories
    for exp in expenses:
        cat_name = exp.category.name if exp.category else 'Uncategorized'
        category_totals['cat_name'] = category_totals.get(cat_name, 0) + exp.amount

    # create a suggestion based on amt spent on each category 
    suggestions = []
    if category_totals :
        max_cat = max(category_totals, key = category_totals.get)
        max_amt = category_totals[max_cat]

        if max_amt > 3000:
            suggestions.append(f"You spent ${max_amt} on {max_cat}. Consider reducing it.")
        else:
            suggestions.append("You are within healthy spending limits")

    
    return render_template(
        'dashboard.html',
        username = current_user.username,
        expenses = expenses,
        categories = list(category_totals.keys()),
        totals = list(category_totals.values()),
        suggestions = suggestions
    )



# expense routes
@app.route('/add-expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    categories = Category.query.all()

    if request.method == 'POST':
        title = request.form['title']
        amount = float(request.form['amount'])
        date = request.form['date']
        category_id = request.form['category_id']

        new_expense = Expense(
            title = title,
            amount = amount,
            date = date,
            user_id = current_user.id,
            category_id = category_id
        )

        db.session.add(new_expense)
        db.session.commit()
        flash('Expense Added', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('add_expense.html', categories = categories)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    app.run(debug=True)

