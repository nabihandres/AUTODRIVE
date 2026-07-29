cmake_minimum_required(VERSION 3.8)
project(gap_follow)

# Utilizar C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Advertencias del compilador
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Sistema de construcción
find_package(ament_cmake REQUIRED)

# Dependencias del nodo
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(ackermann_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(visualization_msgs REQUIRED)

# Crear el ejecutable C++
add_executable(
  reactive_node
  src/reactive_node.cpp
)

# Vincular dependencias ROS 2
ament_target_dependencies(
  reactive_node
  rclcpp
  geometry_msgs
  nav_msgs
  ackermann_msgs
  sensor_msgs
  std_msgs
  visualization_msgs
)

# Instalar el ejecutable para que ros2 run pueda encontrarlo
install(
  TARGETS reactive_node
  DESTINATION lib/${PROJECT_NAME}
)

# Configuración de pruebas
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
