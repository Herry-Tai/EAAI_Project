from app import create_app
from models import db, User, Role

ADMIN_ROLE = 'admin'
USER_ROLE = 'user'

def main():
    app = create_app()
   
    with app.app_context():
        db.create_all()
    
        # Create admin role
        admin_role = Role.query.filter_by(name=ADMIN_ROLE).first()
        if not admin_role:
            admin_role = Role(name=ADMIN_ROLE, description='Full administration', permissions="All")
            db.session.add(admin_role)
        db.session.flush()

        # Create user role with minimal permission
        user_role = Role.query.filter_by(name=USER_ROLE).first()
        if not user_role:
            user_role = Role(name=USER_ROLE, description='User access', permissions="View")
            db.session.add(user_role)
        db.session.flush()

        # Create admin user
        admin_user = User.query.filter_by(email='admin@example.com').first()
        if not admin_user:
            admin_user = User(email='admin@example.com', name='Admin', role=admin_role, active=True)
            admin_user.set_password('Admin@1234')
            db.session.add(admin_user)

        # Create view user
        user_user = User.query.filter_by(email='user01@example.com').first()
        if not user_user:
            user_user = User(email='user01@example.com', name='User', role=user_role, active=True)
            user_user.set_password('User@1234')
            db.session.add(user_user)

        db.session.commit()
        print("Seed complete.")
        print("Admin: admin@example.com / Admin@1234")
        print('User: user01@example.com / User@1234')

if __name__ == '__main__':
    main()
    