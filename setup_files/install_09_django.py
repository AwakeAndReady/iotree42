from .setup_utils import get_setup_dir, get_linux_user, run_bash, log, get_random_string, set_setup_dir_rights

DJANGO_INSTALL_LOG_FILE_NAME = 'install_09_django.log'


def install_django(django_admin_email, django_admin_name, django_admin_pass, auto_generate_django_admin_credentials):
	"""
	Setup Django environment, including virtual environment creation,
	dependencies installation, migrations, and superuser creation.
	"""
	linux_user = get_linux_user()
	setup_dir = get_setup_dir()

	django_secret = get_random_string(50, incl_symbols=True)
	if auto_generate_django_admin_credentials:
		django_admin_name = 'admin-' + get_random_string(5)
		django_admin_pass = 'Dj4' + get_random_string(2) + '-' + get_random_string(5) + '-' + get_random_string(5)

	# Create the Django virtual environment
	set_setup_dir_rights()
	output = run_bash(f'runuser -u {linux_user} -- python3 -m venv {setup_dir}/biomed_iot/venv')
	log(output, DJANGO_INSTALL_LOG_FILE_NAME)

	# Install requirements and do Db migrations (written in one command to keep venv active)
	requirements_command = (
		f"runuser -u {linux_user} -- bash -c 'source {setup_dir}/biomed_iot/venv/bin/activate && "
		f'pip install -r {setup_dir}/biomed_iot/requirements.txt && '
		f'{setup_dir}/biomed_iot/venv/bin/python {setup_dir}/biomed_iot/manage.py makemigrations && '
		f'{setup_dir}/biomed_iot/venv/bin/python {setup_dir}/biomed_iot/manage.py migrate && '
		f"deactivate'"
	)
	set_setup_dir_rights()
	requirements_install_output = run_bash(requirements_command)
	log(requirements_install_output, DJANGO_INSTALL_LOG_FILE_NAME)

	# Create Django superuser
	django_superuser_command = (
		f'echo "from users.models import CustomUser; '
		f"CustomUser.objects.create_superuser('{django_admin_name}', '{django_admin_email}', '{django_admin_pass}')\" | "  # noqa: E501
		f'runuser -u {linux_user} -- {setup_dir}/biomed_iot/venv/bin/python {setup_dir}/biomed_iot/manage.py shell'
	)
	set_setup_dir_rights()
	run_bash(django_superuser_command)
	msg = 'After Attempt to create Django Superuser'
	print(msg)
	log(msg, DJANGO_INSTALL_LOG_FILE_NAME)

	# Prepare static files directory and deploy static files
	# see: https://docs.djangoproject.com/en/5.0/howto/static-files/
	# and https://forum.djangoproject.com/t/django-and-nginx-permission-issue-on-ubuntu/26804
	out = run_bash('mkdir -p /var/www/biomed-iot/static/')
	log(out, DJANGO_INSTALL_LOG_FILE_NAME)

	# Add 'linux_user' to the 'www-data' group
	out = run_bash(f'usermod -aG www-data {linux_user}')
	log(out, DJANGO_INSTALL_LOG_FILE_NAME)

	# Change the group ownership of the directory to 'www-data'
	out = run_bash(f'chown -R {linux_user}:www-data /var/www/biomed-iot/')
	log(out, DJANGO_INSTALL_LOG_FILE_NAME)

	# Set permissions to allow group members to write
	out = run_bash('chmod 2775 /var/www/biomed-iot/')
	log(out, DJANGO_INSTALL_LOG_FILE_NAME)

	# Collect static files
	collect_static_command = (
		f"runuser -u {linux_user} -- bash -c 'source {setup_dir}/biomed_iot/venv/bin/activate && "  # was www-data
		f'{setup_dir}/biomed_iot/venv/bin/python {setup_dir}/biomed_iot/manage.py collectstatic --noinput && '
		f"deactivate'"
	)
	set_setup_dir_rights()
	collectstatic_output = run_bash(collect_static_command)
	log(collectstatic_output, DJANGO_INSTALL_LOG_FILE_NAME)

	config_data = {
		'DJANGO_SECRET_KEY': django_secret,
		'DJANGO_ADMIN_MAIL': django_admin_email,
		'DJANGO_ADMIN_NAME': django_admin_name,
		'DJANGO_ADMIN_PASS': django_admin_pass,
	}

	log('Django setup done', DJANGO_INSTALL_LOG_FILE_NAME)
	return config_data
