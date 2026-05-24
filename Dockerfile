FROM ros:humble-ros-base

WORKDIR /app

COPY . /app/src/scrabe_bot_app

RUN apt-get update && apt-get install -y python3-pip
RUN pip3 install requests

RUN /bin/bash -c "source /opt/ros/humble/setup.bash && colcon build"

CMD ["/bin/bash", "-c", "source install/setup.bash && ros2 run scrabe_bot_app scrabe_sub"]