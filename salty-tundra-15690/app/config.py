import os

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY',  "django-insecure-uhe#%klu=+(dfpnwm(xz7fmxak+3a8!m)xcj$w#nvd%s)5(ppk")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://kokor:sammy23476@localhost/repovuln_db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # RabbitMQ settings
    RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'localhost')
    RABBITMQ_QUEUE = os.environ.get('RABBITMQ_QUEUE', 'repo_analysis')

