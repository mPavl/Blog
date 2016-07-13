from setuptools import setup, find_packages
setup(
	name='resize_image',
        version='0.1',
        description='Python API',
        author='mPavl',
        packages=find_packages(),
        platforms='any',
        include_package_data=True,
        install_requires=['tkFileDialog'])

