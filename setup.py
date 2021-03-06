# Try using setuptools first, if it's installed
try:
    from setuptools import setup
except:
    from distutils.core import setup

from distutils.extension import Extension


extension1 = Extension('epistasis.decomposition', ["epistasis/decomposition.c"])

setup(name='epistasis',
      version='0.1',
      description='High Order Epistasis Models/Regressions for Genotype-Phenotype Maps',
      author='Zach Sailer',
      author_email='zachsailer@gmail.com',
      packages=['epistasis'],
      install_requires=[
          'seqspace',
          'numpy',
          'scipy',
          'scikit-learn',
          'networkx',
          'lmfit'
      ],
      ext_modules=[extension1],
      zip_safe=False)
