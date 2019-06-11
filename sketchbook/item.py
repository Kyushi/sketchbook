import requests
from pathlib import Path

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, g, session, current_app
)
from werkzeug.exceptions import abort

from sketchbook.auth import login_required
from sketchbook.db import get_db
from sketchbook.utils import delete_item, save_uploaded_file, get_projects

bp = Blueprint('item', __name__, url_prefix='/item')

IMAGE_ENDINGS = ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'webp', 'avif', 'heic']
TEXT_ENDINGS = ['pdf', 'txt', 'rtf']


def get_item(id):
	db = get_db()
	item = db.execute("SELECT * FROM item WHERE id = ?;", (id, )).fetchone()
	if item is None:
		abort(404, f"Could not find item with id {id}")
	if item['user_fk'] != g.user['id']:
		abort(403, "You can only edit and view items that you own")
	return item


def interpret_kind(string):
	try:
		res = requests.get(string)
	except Exception:
		return 'text', None
	if res.status_code == 200:
		if 'image' in res.headers['content-type']:
			return 'img', res
		if 'pdf' in res.headers['content-type']:
			return 'pdf', res
	return 'link', None


def download_file(url, res):
	filename = url.split('/')[-1] 
	static_path = g.user['user_dir'] + '/' + filename
	localpath = current_app.root_path + static_path 
	with open(localpath, 'wb') as f:
		f.write(res.content)
	return static_path


@bp.route('/')
def index():
	return redirect(url_for('item.new'))


@bp.route('/<int:id>')
@login_required
def view(id):
	projects = get_projects()
	item = get_item(id)
	return render_template('item/view.html', item=item, projects=projects)


@bp.route('/new', methods=('GET', 'POST'))
@login_required
def new():
	projects=get_projects(include_private=True)
	if not projects:
		flash("Please createa a project first")
		return redirect(url_for('project.new'))
	if request.method == 'POST':
		error = None
		link = request.form['link']
		body = request.form['body']
		tags = request.form['tags']
		project = request.form['project']
		local_path = None
		kind = 'text'
		if link:
			kind, res = interpret_kind(link)
			if kind == 'img' or kind == 'pdf':
				local_path = download_file(link, res)
		file = request.files.get('file', None)
		filetype = file.content_type
		if file and file.filename != '':
			local_path, error = save_uploaded_file(file)
			if local_path:
				link = local_path
				kind = 'img' if any([ft in filetype for ft in current_app.config['DISPLAYABLE_IMG']]) else 'link' 
		if not link:
			error = "You must enter a title or a link or upload a file"
		if error is None:
			db = get_db()
			cur = db.execute(
				"INSERT INTO item ('kind', 'project_fk', 'user_fk', 'link', 'local_path', 'body', 'tags') VALUES (?, ?, ?, ?, ?, ?, ?);",
				(kind, project, g.user['id'], link, local_path, body, tags)
			)
			db.commit()
			id = cur.lastrowid
			return redirect(url_for('item.view', id=id))
		flash(error)
	return render_template("item/new.html", projects=projects)


@bp.route('/<int:id>/edit', methods=('GET', 'POST'))
@login_required
def edit(id):
	item = get_item(id)
	projects = get_projects(include_private=True)
	if request.method == 'POST':
		error = None
		link = request.form['link']
		body = request.form['body']
		tags = request.form['tags']
		project = request.form['project']
		if not link:
			error = "You must enter a title or a link"
		if error is None:
			db = get_db()
			db.execute(
				"UPDATE item SET project_fk = ?, tags = ?, body = ?, link = ? WHERE id = ?;", 
				(project, tags, body, link, id)
			)
			db.commit()
			return redirect(url_for('item.view', id=id))
	return render_template('item/edit.html', item=item, projects=projects)


@bp.route('/<int:id>/delete', methods=('GET', 'POST'))
@login_required
def delete(id):
	item = get_item(id)
	if request.method == 'POST':
		iid = delete_item(item)
		success_message = f"Deleted item with id {iid}"
		flash(success_message)
		return redirect(url_for('project.view', id=item['project_fk']))
	return render_template('item/delete.html', item=item)
