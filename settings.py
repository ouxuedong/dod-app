import os
DEBUG = os.environ.get('SERVER_SOFTWARE', 'Dev').startswith('Dev')

# change SECRET_KEY in production
SECRET_KEY = 'b\xc2\xd1\xbd\x18\xc1\x9e\xe2\xdc\xf7H5\xe0*C\xb7\xaeh[\x7f\xc0\xd5n\x8d'
