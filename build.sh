#!/usr/bin/env bash
#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput

python manage.py migrate

# Create custom admin user (your User model)
python manage.py shell <<EOF
from api.models import User

if not User.objects.filter(name="admin").exists():
    user = User(
        name="admin",
        phone="9999999999",
        role="admin"
    )
    user.set_password("admin123")
    user.save()
    print("Admin user created")
else:
    print("Admin already exists")
EOF