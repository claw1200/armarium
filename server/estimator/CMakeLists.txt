cmake_minimum_required(VERSION 3.16)
project(armarium-loop-tempo LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
option(BUILD_TESTS "Build tests" OFF)
option(BUILD_VAMP_PLUGIN "Build Vamp plugin" OFF)

include(FetchContent)
FetchContent_Declare(
  loop-tempo-estimator
  URL https://github.com/saintmatthieu/loop-tempo-estimator/releases/download/v0.0.5/loop-tempo-estimator-v0.0.5.tar.gz
  URL_HASH SHA256=e70f2356bbea1bcec3a77e26dddd87b1dd0d5f24c8aed6351aa9d6ec42a66be0
  SOURCE_SUBDIR source
)
FetchContent_MakeAvailable(loop-tempo-estimator)

add_executable(armarium-loop-tempo main.cpp)
target_link_libraries(armarium-loop-tempo PRIVATE loop-tempo-estimator)
install(TARGETS armarium-loop-tempo RUNTIME DESTINATION bin)
