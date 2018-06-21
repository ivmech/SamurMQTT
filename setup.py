from setuptools import find_packages, setup

setup(
    name="SamurMQTT",
    version="0.1.2",
    author="Caner Durmusoglu",
    author_email="cnr437@gmail.com",
    include_package_data=True,
    packages=find_packages(),

    url="",
    # license="LICENSE.txt",
    description="Samur MainBoard MQTT Daemon",
    # long_description=open("README.md").read(),
    # Dependent packages (distributions)
    install_requires=[
        "RPi.GPIO",
        "samur",
    ],

    scripts=['bin/samur_mqttd.py'],
    data_files=[
                ('/etc', ['etc/samur.conf']),
                ('/etc/systemd/system', ['etc/samur_mqttd.service']),
    ],
)
