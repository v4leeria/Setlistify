from setuptools import setup, find_packages

requires = [
    'flask',
    'spotipy',
]

setup(
    name='Setlistify',
    version='1.0',
    description='An application that gets your top spotify tracks and turns them into a setlist',
    author='duhkhazen',
    author_email='duhkhazen@gmail.com',
    keywords='web flask',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requires
)