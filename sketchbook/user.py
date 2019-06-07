import shutil
from flask import (
	Blueprint, request, render_template, redirect, flash, url_for, g, session, current_app
)

bp = Blueprint('user', __name__, url_prefix='/user')

from sketchbook.auth import login_required
from sketchbook.db import get_db


def delete_user_dir():
	shutil.rmtree(current_app.root_path + g.user['user_dir'])


def get_projects():
	db = get_db()
	if not g.user:
		return redirect(url_for('login'))
	return db.execute("SELECT * FROM project WHERE user_fk = ?;", (g.user['id'], )).fetchall()
	

@bp.route('/')
@login_required
def view():
	return render_template('user/view.html', projects=get_projects())


@bp.route('/delete', methods=('GET', 'POST'))
@login_required
def delete():
	if request.method == 'POST':
		delete_user_dir()
		db = get_db()
		db.execute("DELETE FROM project WHERE user_fk = ?;", (g.user['id'], ))
		db.execute("DELETE FROM item WHERE user_fk = ?;", (g.user['id'], ))
		db.execute("DELETE FROM user WHERE id = ?;", (g.user['id'], ))
		db.commit()
		flash("User and all user data deleted successfully")
		return redirect(url_for('index'))
	return render_template('user/delete.html')


@bp.route('/edit', methods=('GET', 'POST'))
@login_required
def edit():
	return render_template('user/edit.html')
