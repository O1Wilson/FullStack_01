import os
from dotenv import load_dotenv

load_dotenv()

print(os.environ.get('SQLALCHEMY_DATABASE_URI'))
print(os.environ.get('OPENAI_API_KEY'))
print(os.environ.get('STABILITY_KEY'))
print(os.environ.get('OKTA_SECRET_KEY'))
print(os.environ.get('OKTA_CLIENT_ID'))
print(os.environ.get('OKTA_CLIENT_SECRET'))
print(os.environ.get('OKTA_DOMAIN'))
print(os.environ.get('SERVER_DOMAIN'))