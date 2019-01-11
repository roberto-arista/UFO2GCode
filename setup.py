from distutils.core import setup

setup(name='UFO2GCode',
      description='From UFO glyph to GCode commands using the Pen protocol',
      version='0.1',
      author='Roberto Arista',
      author_email='roberto@studioarista.xyz',
      py_modules=['UFO2GCode'],
      install_requires=['fontTools'],
      package_dir={'': 'Lib'},
      )
