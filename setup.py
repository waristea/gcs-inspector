from distutils.core import setup
setup(
  name = 'gcs-inspector',
  packages = ['gcs-inspector'],
  version = '0.1',
  license='MIT',
  description = 'A small library used for monitoring public instances of Google Cloud Storage using Google Service Account',
  author = 'William Aristea Tantiono',
  author_email = 'waristea@gmail.com',
  url = 'https://github.com/waristea/gcs-inspector',
  download_url = 'https://github.com/waristea/gcs-inspector/archive/v_01.tar.gz',
  keywords = [
          'GCS',
          'Google Cloud Storage',
          'Inspector'
          'GCS Inspector',
          'Google Cloud Storage Inspector',
          'Cloud Storage Inspector',
          'Storage Inspector',
          'Cloud Inspector'
          'Monitoring',
          'GCS Monitoring',
          'Google Cloud Storage Monitoring',
          'Cloud Storage Monitoring',
          'Storage Monitoring',
          'Cloud Monitoring'
           ],
  install_requires=[
          'pp-ez',
          'requests',
          'google'
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8'
  ],
)
