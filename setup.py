from setuptools import setup, find_packages

setup(
    name="cliche-cli",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click>=8.0.0',
        'openai>=0.27.0',
        'anthropic>=0.3.0',
        'psutil>=5.9.0',
        'requests>=2.28.0',
        'google-generativeai>=0.1.0',
        'python-dotenv>=0.19.0',
        'asyncio>=3.4.3',
        'py3nvml>=0.2.7',
        'setuptools>=58.0.4',
        'ollama>=0.2.1',
    ],
    entry_points={
        'console_scripts': [
            'cliche=cliche.core:cli',
        ],
    },
)