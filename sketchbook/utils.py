from pathlib import Path
from flask import g, current_app
from sketchbook.db import get_db


def load_projects():
	if not g.user:
		g.projects = None
	else:
		g.projects = get_db().execute("SELECT * FROM project WHERE user_fk = ?;", (g.user['id'], )).fetchall()


def get_project(id):
    db = get_db()
    project = db.execute("SELECT * FROM project WHERE id = ?;", (id, )).fetchone()
    if project is None:
        abort(404, f"Could not find project with id {id}")

    if project['user_fk'] != g.user['id']:
        abort(403, "You can only edit projects that you own")
    return project


def get_items(project_id):
    db = get_db()
    items = db.execute("SELECT * FROM item WHERE project_fk = ? AND user_fk = ?;", (project_id, g.user['id'] )).fetchall()
    return items


def is_unique_name(name):
    db = get_db()
    project = db.execute("SELECT * FROM project WHERE name = ? AND user_fk = ?;", (name, g.user['id'])).fetchone()
    if project is not None:
        return False
    return True


def get_local_path(item):
	if item['filepath'] is None:
		return None
	return Path(item['user_dir']) / item['filepath'] 


def get_displaypath(item):
	return 
	

def delete_item(item):
	local_path = current_app.root_path + item['local_path']
	db = get_db()
	db.execute("DELETE FROM item WHERE id = ?;", (item['id'], ))
	db.commit()
	iid = item['id']
	del item
	return iid

	
