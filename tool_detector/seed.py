from app import create_app
from models import db, User, Role, Permission

BASE_PERMS = [
    'user.view',
    'user.create',
    'user.update',
    'user.deactivate',
]

ADMIN_ROLE = 'admin'

def main():
    app = create_app()
    with app.app_context():
        db.create_all()

        # Create base permissions if missing
        perms = []
        for code in BASE_PERMS:
            p = Permission.query.filter_by(code=code).first()
            if not p:
                p = Permission(code=code)
                db.session.add(p)
            perms.append(p)

        # Create admin role
        admin_role = Role.query.filter_by(name=ADMIN_ROLE).first()
        if not admin_role:
            admin_role = Role(name=ADMIN_ROLE, description='Full administration')
            db.session.add(admin_role)
        db.session.flush()
        # Admin role gets all base permissions
        admin_role.permissions = perms

        # Create viewer role with minimal permission
        viewer_role = Role.query.filter_by(name='viewer').first()
        if not viewer_role:
            viewer_role = Role(name='viewer', description='Read-only access')
            db.session.add(viewer_role)
        db.session.flush()
        viewer_role.permissions = [Permission.query.filter_by(code='user.view').first()]

        # Create admin user
        admin_user = User.query.filter_by(email='admin@example.com').first()
        if not admin_user:
            admin_user = User(email='admin@example.com', name='Admin', role=admin_role, active=True)
            admin_user.set_password('Admin@123456')
            db.session.add(admin_user)

        db.session.commit()
        print('Seed complete. Admin: admin@example.com / Admin@123456')

if __name__ == '__main__':
    main()
    