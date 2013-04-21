import glob
import zipfile

with zipfile.ZipFile('the-sea-of-good-and-bad.zip', 'w') as z:
  for f in glob.glob('*.py'):
    z.write(f)
  for f in glob.glob('*.txt'):
    z.write(f)
  for f in glob.glob('*.ttf'):
    z.write(f)
  for f in glob.glob('art/*.png'):
    z.write(f)
  for f in glob.glob('art/*/*.png'):
    z.write(f)
  for f in glob.glob('models/*/*.png'):
    z.write(f)
  for f in glob.glob('models/*/*.obj'):
    z.write(f)
  for f in glob.glob('music/*.ogg'):
    z.write(f)
  for f in glob.glob('voice/*.wav'):
    z.write(f)
