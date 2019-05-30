from pathlib import Path

from flask import Flask

def create_app(test_config=None):
	app = Flask(__name__, instance_relative_config=True)
	instance_path = Path(app.instance_path)
	app.config.from_mapping(
		SECRET_KEY='dev',
		DATABASE=str(instance_path / 'sketchbook.db')
	)
	
	if test_config is None:
		app.config.from_pyfile('config.py', silent=True)
	else:
		app.config.from_mapping(test_config)
	
	instance_path.mkdir(exist_ok=True)
	
	@app.route('/hello')
	def hello():
		return "Ohayooooou!"
	
	from . import db
	db.init_app(app)
	
	from . import auth
	app.register_blueprint(auth.bp)
	
	from . import index
	app.register_blueprint(index.bp)
	app.add_url_rule('/', endpoint='index')
			
	return app
