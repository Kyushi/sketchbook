import functools

from flask import (
	Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from sketchbook.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
	if request.method == 'POST':
		db = get_db()
		error = None
		username = request.form['username']
		password = request.form['password']
		email = request.form['email']
		picture = request.form['picture']
		description = request.form['description']
		# We don't need to go into all possible combinations of missing parameters here,
		# it is enough to check them one by one (frontend should do proper form validation)
		if not username:
			error = "Username is required"
		if not password:
			error = "Password is required"
		if not email:
			error = "E-Mail is required"
		if db.execute("SELECT * FROM user WHERE email = ?;", (email, )).fetchone() is not None:
			error = "You have already registered an account with this email address"
		if error is None:
			db.execute(
				"""INSERT INTO 
					user (username, password, email, img_link, description) 
					VALUES (?, ?, ?, ?, ?)
				""", 
				(username, generate_password_hash(password), email, picture, description)
			)
			db.commit()
			return redirect(url_for('auth.login'))
		flash(error)

	return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
	if request.method == 'POST':
		db = get_db()
		error = None
		email = request.form['email']
		password = request.form['password']
		user = db.execute("SELECT * FROM user WHERE email = ?", (email, )).fetchone()
		if user is None or not check_password_hash(user['password'], password):
			error = "Email unknown or password incorrect"
		if error is None:
			session.clear()
			session['uid'] = user['id']
			return redirect(url_for('index'))
		flash(error)
	return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
	user_id = session.get('uid')
	
	if user_id is None:
		g.user = None
	else:
		g.user = get_db().execute("SELECT * FROM user WHERE id = ?;", (user_id, )).fetchone()


@bp.route('/logout')
def logout():
	session.clear()
	return redirect(url_for('index'))

def login_required(view):
	functools.wraps(view)
	def wrapped_view(**kwargs):
		if g.user is None:
			return redirect(url_for('auth.login'))
		return view(**kwargs)
	return wrapped_view
	
