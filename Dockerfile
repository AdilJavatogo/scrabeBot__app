# Brug det officielle ROS 2 Humble image
FROM ros:humble-ros-base

# Sæt arbejdsmappe
WORKDIR /app

# Kopier din source code ind i containeren
COPY . /app/src/scrabe_bot_app

# Installer pip og requests biblioteket (som din subscriber bruger)
RUN apt-get update && apt-get install -y python3-pip
RUN pip3 install requests

# Byg ROS 2 pakken
RUN /bin/bash -c "source /opt/ros/humble/setup.bash && colcon build"

# Kør subscriberen når containeren starter
CMD ["/bin/bash", "-c", "source /opt/ros/humble/setup.bash && source install/setup.bash && ros2 run scrabe_bot_app scrabe_sub"]