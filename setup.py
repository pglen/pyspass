import setuptools
import os, sys

descx = '''
        Password manager.
'''

classx = [
          'Development Status :: Mature',
          'Environment :: GUI',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: Python Software Foundation License',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Topic :: Databases',
        ]

includex = ["*", "pyspass/", ]
versionx = "1.0.0"

#doclist = []; droot = "pydbase/docs/"
#doclistx = os.listdir(droot)
#for aa in doclistx:
#    doclist.append(droot + aa)
#print(doclist)
#sys.exit()

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyspass",
    version=versionx,
    author="Peter Glen",
    author_email="peterglen99@gmail.com",
    description="Password manager.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pglen/pyspass",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    packages=setuptools.find_packages(include=includex),
    scripts = ['pyspassgui.py', ],
    py_modules = ["pyvpacker",],
    package_data = {"icon" : ["noinfo.png",]},
    python_requires='>=3',
    entry_points={
        'console_scripts': [ "pyspassgui=pyspassgui:mainfunc",
                           ],
    },
)

# EOF
