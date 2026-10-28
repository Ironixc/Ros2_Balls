cmake_minimum_required(VERSION 3.8)
project(camera_node__cpp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(OpenCV REQUIRED)
find_package(cv_bridge REQUIRED)

add_executable(Camera_node src/Camera_node.cpp)
ament_target_dependencies(Camera_node rclcpp sensor_msgs cv_bridge OpenCV)

install(TARGETS
  Camera_node
  DESTINATION lib/${PROJECT_NAME}
)
  
ament_package()