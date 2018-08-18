import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='pyDLib',
    version='0.0.1',
    packages=setuptools.find_packages(),
    url='https://github.com/benoitkugler/abstractDataLibrary',
    license='MIT License',
    author='Benoit KUGLER',
    author_email='x.ben.x@free.fr',
    description='Base tools to create data-driven PyQt application',
    long_description = long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)


