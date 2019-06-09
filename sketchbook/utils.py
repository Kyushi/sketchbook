from pathlib import Path
from flask import g, current_app
from sketchbook.db import get_db
from werkzeug.utils import secure_filename
from werkzeug.exceptions import abort


def load_projects():
	"""Load projects of a logged in user and keep in g to make available for menu etc"""
	if not g.user:
		g.projects = None
	else:
		g.projects = get_db().execute("SELECT * FROM project WHERE user_fk = ? AND name NOT LIKE '.%';", (g.user['id'], )).fetchall()


def get_projects():
	"""Load all projects for a logged in user"""
	db = get_db()
	return db.execute("SELECT * FROM project WHERE user_fk = ?", (g.user['id'], )).fetchall()


def get_project(id):
	"""
	Load a single project by id
	:param id: <int> id of project to load
	:returns: <sqlite3.Row> project
	"""
	db = get_db()
	project = db.execute("SELECT * FROM project WHERE id = ?;", (id, )).fetchone()
	if project is None:
		abort(404, f"Could not find project with id {id}")
	if project['user_fk'] != g.user['id']:
		abort(403, "You can only edit projects that you own")
	return project


def get_project_byname(name):
	db = get_db()
	project = db.execute("SELECT * FROM project WHERE name = ?;", (name, )).fetchone()
	if project is None:
		abort(404, f"Could not find project with name {name}")
	if project['user_fk'] != g.user['id']:
		abort(403, "You can only edit projects that you own")
	return project


def get_items(project_id):
	"""
	Load all items belonging to a certain project.
	:param project_id: <int> id of project
	:return: <list> list of items
	"""
	db = get_db()
	items = db.execute("SELECT * FROM item WHERE project_fk = ? AND user_fk = ?;", (project_id, g.user['id'] )).fetchall()
	return items


def get_item(id):
	"""
	Get one item by id
	:param id: <int> id of item to get
	:return: <sqlite3.Row> item
	"""
	db = get_db()
	item = db.execute("SELECT * FROM item WHERE id = ?;", (id, )).fetchone()
	if item is None:
		abort(404, f"Could not find item with id {id}")
	if item['user_fk'] != g.user['id']:
		abort(403, "You can only edit and view items that you own")
	return item


def is_unique_name(name):
	"""
	Check if a project name is unique.
	:param name: <str> name to check
	:return: <bool> True or False
	"""
	db = get_db()
	project = db.execute("SELECT * FROM project WHERE name = ? AND user_fk = ?;", (name, g.user['id'])).fetchone()
	if project is not None:
		return False
	return True


def delete_item(item):
	"""
	Delete an item. Deletes the copy of the item if it's an image or pdf
	:param item: <sqlite.Row> item
	:return: <int> item id
	"""
	if item['local_path']:
		local_path = current_app.root_path + item['local_path']
		Path(local_path).unlink()
	db = get_db()
	db.execute("DELETE FROM item WHERE id = ?;", (item['id'], ))
	db.commit()
	iid = item['id']
	del item
	return iid


def is_allowed_type(filename):
	extension = filename.split('.')[-1].lower()
	return '.' in filename and extension in current_app.config['ALLOWED_EXTENSIONS']


def save_uploaded_file(file):
	if not '.' in file.filename:
		error = "no . in filename"
		return False, error
	if not is_allowed_type(file.filename):
		error = f"Illegal filetype ({file.filename.split('.')[-1].lower()})"
		return False, error
	filename = secure_filename(file.filename)
	local_path = g.user['user_dir'] + '/' + filename
	save_path = current_app.root_path + local_path 
	file.save(save_path)
	return local_path, None
	
