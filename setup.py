from setuptools import setup, find_packages

setup(
    name="Palantir",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "customtkinter==5.2.2",
        "requests>=2.31.0",
        "aria2p==0.12.1",
        "unidecode==1.3.8",
        "ttkthemes==3.2.2",
        "pillow==11.1.0",
        "websocket-client==1.8.0",
        "loguru==0.7.3",
        "platformdirs==4.3.7",
        "colorama==0.4.6",
    ],
    entry_points={
        'console_scripts': [
            'palantir=Palantir:main',
        ],
    },
    author="Seu Nome",
    author_email="seu.email@exemplo.com",
    description="Palantir - Gerenciador de Mídia",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    include_package_data=True,
    package_data={
        '': ['assets/*', '*.json', '*.conf'],
    },
) 