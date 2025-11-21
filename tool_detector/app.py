from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_required, current_user
from models import db, User, Role, Detection 
from forms import UserForm, RoleForm
from auth import auth_bp
from rbac import require_permission, require_role
from detect import ToolDetector
from sqlalchemy import func
import os
from datetime import datetime, timedelta

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Ensure instance folder exists for SQLite
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    db.init_app(app)

    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(auth_bp)

    main_bp = create_main_blueprint()
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()

    return app

def create_main_blueprint():
    from flask import Blueprint
    main = Blueprint('main', __name__)

    @main.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('main.dashboard'))
        return redirect(url_for('auth.login'))

    @main.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html')

    # ----- User Management -----
    @main.route('/users')
    @login_required
    def users_list():
        if current_user.role.name == 'admin':
            users = User.query.all()
        else:
            users = [User.query.filter_by(email=current_user.email.lower()).first()]

        return render_template('users_list.html', users=users)

    @main.route('/users/create', methods=['GET', 'POST'])
    @login_required
    @require_role('admin')
    def users_create():
        form = UserForm(request.form)
        form.role_id.choices = [(r.id, r.name) for r in Role.query.all()]
        if request.method == 'POST' and form.validate():
            if User.query.filter_by(email=form.email.data.lower()).first():
                flash('Email already exists', 'error')
            else:
                user = User(
                    email=form.email.data.lower(),
                    name=form.name.data,
                    active=form.active.data,
                    role_id=form.role_id.data
                )
                if form.password.data:
                    user.set_password(form.password.data)
                else:
                    flash('Password is required for new user', 'error')
                    return render_template('user_form.html', form=form)
                db.session.add(user)
                db.session.commit()
                flash('User created', 'success')
                return redirect(url_for('main.users_list'))
        return render_template('user_form.html', form=form)

    @main.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
    @login_required
    @require_role('admin')
    def users_edit(user_id):
        user = User.query.get_or_404(user_id)
        form = UserForm(request.form, obj=user)
        form.role_id.choices = [(r.id, r.name) for r in Role.query.all()]
        if request.method == 'POST' and form.validate():
            user.email = form.email.data.lower()
            user.name = form.name.data
            user.active = form.active.data
            user.role_id = form.role_id.data
            if form.password.data:
                user.set_password(form.password.data)
            db.session.commit()
            flash('User updated', 'success')
            return redirect(url_for('main.users_list'))
        return render_template('user_form.html', form=form)

    @main.route('/users/<int:user_id>/deactivate', methods=['POST'])
    @login_required
    @require_role('admin')
    def users_deactivate(user_id):
        user = User.query.get_or_404(user_id)
        if user.id == current_user.id:
            flash('You cannot deactivate your own account', 'error')
            return redirect(url_for('main.users_list'))
        user.active = False
        db.session.commit()
        flash('User deactivated', 'success')
        return redirect(url_for('main.users_list'))

    # ----- Role & Permission Maintenance -----
    @main.route('/roles')
    @login_required
    @require_role('admin')
    def roles_list():
        roles = Role.query.all()
        return render_template('roles_list.html', roles=roles)

    @main.route('/roles/create', methods=['GET', 'POST'])
    @login_required
    @require_role('admin')
    def roles_create():
        form = RoleForm(request.form)
        if request.method == 'POST' and form.validate():
            role = Role(name=form.name.data, description=form.description.data)
            db.session.add(role)
            db.session.commit()
            flash('Role created', 'success')
            return redirect(url_for('main.roles_list'))
        return render_template('role_form.html', form=form)

    @main.route('/roles/<int:role_id>/edit', methods=['GET', 'POST'])
    @login_required
    @require_role('admin')
    def roles_edit(role_id):
        role = Role.query.get_or_404(role_id)
        form = RoleForm(request.form, obj=role)
        if request.method == 'POST' and form.validate():
            role.name = form.name.data
            role.description = form.description.data
            db.session.commit()
            flash('Role updated', 'success')
            return redirect(url_for('main.roles_list'))
        return render_template('role_form.html', form=form)

    # ----- Detector -----
    @main.route('/detect', methods=["GET"])
    @login_required
    def detector():

        tool_source = request.args.get("tool_source", "")

        class_names = ['drill', 'hammer', 'pliers', 'scissors', 'screwdriver', 'tape-measure', 'wrench']

        if tool_source == "":
            return render_template('detector.html', class_sources=class_names)
        else:
            # Initialize detector
            model_path = 'model/yolo_model_v11.pt'

            detector = ToolDetector(model_path, class_names)

            # tool1.MOV = Full classes | tool2.MOV = One by one | tool3.MOV = Checking missing
            video_path = os.path.join('demo', os.path.basename(tool_source))   # e.g. demo/tool1.mp4
            try:
                df = detector.process_video(video_path)
            except FileNotFoundError:
                return f"Video {video_path} not found", 404
            except Exception as e:
                return f"Error processing video: {str(e)}", 500

            # Convert DataFrame to list
            records = df.to_dict(orient="records")

            return render_template('detector.html', table=records, columns=df.columns, class_sources=class_names)

    @main.route('/report', methods=["GET"])
    @login_required
    def report():
        # Get date filters from query parameters
        start_date = request.args.get("start_date")  # e.g. "2025-11-01"
        end_date = request.args.get("end_date")      # e.g. "2025-11-21"

        query = db.session.query(
            func.sum(Detection.drill).label("total_drill"),
            func.sum(Detection.hammer).label("total_hammer"),
            func.sum(Detection.pliers).label("total_pliers"),
            func.sum(Detection.scissors).label("total_scissors"),
            func.sum(Detection.screwdriver).label("total_screwdriver"),
            func.sum(Detection.tape_measure).label("total_tape_measure"),
            func.sum(Detection.wrench).label("total_wrench")
        ).filter(Detection.login_id == str(current_user.id))

        # Apply date filters if provided
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(Detection.created_at >= start_dt)

        if end_date:
            # add one day so you include the whole day
            end_dt = datetime.fromisoformat(end_date) + timedelta(days=1)
            query = query.filter(Detection.created_at < end_dt)
        totals = query.first()

        report_data = {
            "drill": totals.total_drill or 0,
            "hammer": totals.total_hammer or 0,
            "pliers": totals.total_pliers or 0,
            "scissors": totals.total_scissors or 0,
            "screwdriver": totals.total_screwdriver or 0,
            "tape_measure": totals.total_tape_measure or 0,
            "wrench": totals.total_wrench or 0
        }

        return render_template("report.html", report=report_data, start_date=start_date, end_date=end_date)

    @main.app_errorhandler(403)
    def forbidden(_):
        return render_template('403.html'), 403

    return main

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
