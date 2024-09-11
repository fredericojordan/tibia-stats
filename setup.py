from setuptools import setup, find_packages

setup(
    name="tibia-stats",
    version="1.0.0",
    url="https://github.com/fredericojordan/tibia-stats.git",
    author="Frederico Jordan",
    author_email="fredericojordan@gmail.com",
    description="Stats for Tibia",
    packages=find_packages(),
    install_requires=["numpy >= 1.11.1", "matplotlib >= 1.5.1"],
    entry_points={
        "console_scripts": ["tibia-stats=tibia_stats.cli:main"],
    },
)
