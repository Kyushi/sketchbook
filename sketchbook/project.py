from flask import (
	Blueprint, render_template, request, redirect, url_for, flash, g, session
)
from werkzeug.exceptions import abort

from sketchbook.auth import login_required
from sketchbook.db import get_db
from sketchbook.utils import load_projects, get_project, get_project_byname, get_items, is_unique_name, delete_item 

bp = Blueprint('project', __name__, url_prefix='/project')


@bp.route('/')
@login_required
def view_projects():
	db = get_db()
	error = None
	projects = db.execute("SELECT * FROM project WHERE user_fk = ? AND name NOT LIKE '.%'", (g.user['id'], )).fetchall()
	return render_template('project/projects.html', projects=projects)


@bp.route('/<int:id>')
@login_required
def view(id):
	project = get_project(id) if id != 0 else None
	items = get_items(id)
	return render_template('/project/view.html', project=project, items=items)


@bp.route('/<name>')
@login_required
def view_by_name(name):
	project = get_project_byname(name)
	items = get_items(project['id'])
	return render_template('/project/view.html', project=project, items=items)


@bp.route('/new', methods=('GET', 'POST'))
@login_required
def new():
	if request.method == 'POST':
		db = get_db()
		error = None
		name = request.form['name']
		description = request.form['description']
		if not name:
			error = "You need to give your project a name"
		elif not is_unique_name(name):
			error = f"You already have a project with this name: {name}"	
		if error is None:
			db.execute(
				"INSERT INTO project (name, description, user_fk) VALUES (?, ?, ?);",
				(name, description, g.user['id'])
			)
			db.commit()
			load_projects()
			return redirect(url_for('project.view_projects'))
		flash(error)
	return render_template('project/new.html')


@bp.route('/<int:id>/edit', methods=('GET', 'POST'))
@login_required
def edit(id):	
	project = get_project(id)
	if request.method == 'POST':
		db = get_db()
		error = None
		name = request.form['name']
		description = request.form['description']
		if not name:
			error = "You must name your project"
		elif not is_unique_name(name) and not name == project['name']:
			error = f"You already have another project with this name: {name}"
		if error is None:
			db.execute(
				"UPDATE project SET name = ?, description = ? WHERE id = ?;",
				(name, description, project['id'])
			)
			db.commit()
			return redirect(url_for('project.view', id=project['id']))
		flash(error)
	return render_template('project/edit.html', project=project)	


@bp.route('/<int:id>/delete', methods=('GET', 'POST'))
@login_required
def delete(id):
	project = get_project(id)
	if request.method == 'POST':
		db = get_db()
		if g.user['id'] == project['user_fk']:
			if request.form.get('delete-items'):
				items = get_items(id)
				for item in items:
					delete_item(item)
			db.execute(
				"DELETE FROM project WHERE id = ?;",
				(project['id'], )
			)
			flash(f"Deleted project {project['id']}")
			del project
			db.commit()
			return redirect(url_for('project.view_projects'))
		else:
			flash("You cannot delete a project that is not yours")
	return render_template('project/delete.html', project=project)

	
