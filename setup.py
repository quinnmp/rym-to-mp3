from setuptools import setup, find_packages

setup(
    name="rym-to-mp3",
    version="0.1.5",
    description="Use the RYM music database and media links to download music with correct metadata.",
    author="Quinn Pfeifer",
    author_email="quinnpfeifer@icloud.com",
    license="Unlicense",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.8",
    install_requires=[
        "beautifulsoup4>=4.12.3",
        "mutagen>=1.47.0",
        "requests>=2.31.0",
        "selenium>=4.21.0",
        "webdriver-manager>=4.0.1",
        "yt-dlp>=2024.4.9",
        "ffmpeg-python==0.2.0"
    ],
    packages=find_packages(),
    package_data={'': ['*.py']},
    entry_points={
        "console_scripts": [
            "rym-to-mp3=src.rym_to_mp3.main:main",
            "r2m=src.rym_to_mp3.main:main",
        ]
    },
    url="https://github.com/quinnmp/rym-to-mp3"
)
