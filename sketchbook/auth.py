import functools
from pathlib import Path

from flask import (
	Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app
)
from werkzeug.security import check_password_hash, generate_password_hash

from sketchbook.db import get_db
from sketchbook.utils import load_projects

bp = Blueprint('auth', __name__, url_prefix='/auth')


def create_userdir(username):
	user_path = Path('sketchbook') / 'static' / 'users' / username
	try:
		user_path.mkdir()
	except Exception as e:
		raise e 
	return Path(current_app.config['UPLOAD_DIR']) / username 


@bp.route('/register', methods=('GET', 'POST'))
def register():
	if request.method == 'POST':
		db = get_db()
		error = None
		displayname = request.form['displayname']
		password = request.form['password']
		email = request.form['email']
		picture = request.form['picture']
		description = request.form['description']
		# We don't need to go into all possible combinations of missing parameters here,
		# it is enough to check them one by one (frontend should do proper form validation)
		if not displayname:
			error = "Username is required"
		if not password:
			error = "Password is required"
		if not email:
			error = "E-Mail is required"
		if db.execute("SELECT * FROM user WHERE email = ?;", (email, )).fetchone() is not None:
			error = "You have already registered an account with this email address"
		if db.execute("SELECT * FROM user WHERE displayname = ?;", (displayname, )).fetchone() is not None:
			error = "This username is not available"
		if error is None:
			user_dir = create_userdir(displayname)
			cur = db.execute(
				"""INSERT INTO 
					user (displayname, password, email, img_link, description, user_dir) 
					VALUES (?, ?, ?, ?, ?, ?)
				""", 
				(displayname, generate_password_hash(password), email, picture, description, str(user_dir))
			)
			db.commit()
			flash(f"Created user directory at {user_dir}")

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
	load_projects()


@bp.route('/logout')
def logout():
	session.clear()
	return redirect(url_for('index'))


def login_required(view):
	@functools.wraps(view)
	def wrapped_view(**kwargs):
		if g.user is None:
			return redirect(url_for('auth.login'))
		return view(**kwargs)
	return wrapped_view
	
