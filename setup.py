"""설치 스크립트"""

from setuptools import setup, find_packages

setup(
    name="sw-mcp",
    version="1.0.0",
    description="서머너즈워 룬 최적화 라이브러리",
    author="SW MCP Team",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "pydantic>=2.0.0",
    ],
    tests_require=["pytest>=7.0.0"],
    extras_require={
        "dev": ["pytest>=7.0.0", "black", "flake8"],
    },
)

