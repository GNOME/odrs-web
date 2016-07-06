from setuptools import setup

setup(name='ODRS',
      version='1.0',
      description='Open Desktop Ratings Service',
      author='Richard Hughes',
      author_email='richard@hughsie.com',
      url='http://www.python.org/sigs/distutils-sig/',
      install_requires=['Flask>=0.10.1', 'Flask-Login', 'PyMySQL'],
      )
