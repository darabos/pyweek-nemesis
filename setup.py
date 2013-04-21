from setuptools import setup
import glob

setup(
  name='The Sea of Good and Bad',
  data_files=[
    ('art', glob.glob('art/*')),
    ('models', glob.glob('models/*')),
    ('music', glob.glob('music/*')),
    ('voice', glob.glob('voice/*')),
    ('', ['OpenSans-Regular.ttf']),
    ],

  app=['bundle.py'],
  setup_requires=['py2app'],
  options={'py2app': {'iconfile': 'icon.icns'}},
)
