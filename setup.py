from setuptools import setup, find_packages

setup(
    name='CurryBot',
    author='Liam Mencel',
    version='0.1dev',
    description='Discord bot for Azure Dreams',
    packages=find_packages(exclude=('tests', 'docs', 'data')),
    license='MIT',
    long_description=open('README.md').read(),
    python_requires='>=3.6.0',
    install_requires=['beautifulsoup4', 'discord.py', 'gspread', 'oauth2client', 'requests'],
)
