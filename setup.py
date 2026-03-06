from setuptools import find_packages, setup

package_name = 'scrabe_bot_app'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='adil',
    maintainer_email='adil@todo.todo',
    description='API: Send til API',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'scrabe_sub = scrabe_bot_app.subscriber:main'
            'scrabe_pub = scrabe_bot_app.publisher:main'
        ],
    },
)
