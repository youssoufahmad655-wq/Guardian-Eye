from authlib.integrations.flask_client import OAuth

oauth = OAuth()

def init_oauth(app):
    """تهيئة OAuth مع التطبيق وتسجيل المزودين."""
    oauth.init_app(app)

    # Google
    oauth.register(
        name='google',
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

    # GitHub
    oauth.register(
        name='github',
        client_id=app.config.get('GITHUB_CLIENT_ID'),
        client_secret=app.config.get('GITHUB_CLIENT_SECRET'),
        access_token_url='https://github.com/login/oauth/access_token',
        authorize_url='https://github.com/login/oauth/authorize',
        api_base_url='https://api.github.com/',
        client_kwargs={'scope': 'user:email'},
    )

    # Apple (يتطلب إعداداً إضافياً لـ client_secret)
    oauth.register(
        name='apple',
        client_id=app.config.get('APPLE_CLIENT_ID'),
        client_secret=app.config.get('APPLE_CLIENT_SECRET'),
        server_metadata_url='https://appleid.apple.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'name email', 'response_mode': 'form_post'}
    )
