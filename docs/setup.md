# Setup (Ubuntu 22.04, native or WSL 2)

> Commands below follow the ArduPilot and ardupilot_gazebo documentation.
> TEST EVERY COMMAND ON A CLEAN MACHINE BEFORE TAGGING THE RELEASE.

## 1. ArduPilot SITL
    sudo apt update && sudo apt upgrade -y
    sudo apt install -y git python3-pip python3-venv build-essential cmake
    git clone --recurse-submodules https://github.com/ArduPilot/ardupilot.git
    cd ardupilot
    Tools/environment_install/install-prereqs-ubuntu.sh -y
    . ~/.profile
    ./waf configure --board sitl
    ./waf copter
Record the exact version: `git rev-parse HEAD`.

## 2. Gazebo Harmonic and the plugin
Install Gazebo Harmonic from https://gazebosim.org/docs/harmonic/install, then:

    sudo apt install libgz-sim8-dev rapidjson-dev
    export GZ_VERSION=harmonic
    mkdir -p ~/gz_ws/src && cd ~/gz_ws/src
    git clone https://github.com/ArduPilot/ardupilot_gazebo.git
    cd ardupilot_gazebo && mkdir build && cd build
    cmake .. -DCMAKE_BUILD_TYPE=RelWithDebInfo && make -j4
    echo 'export GZ_SIM_SYSTEM_PLUGIN_PATH=$HOME/gz_ws/src/ardupilot_gazebo/build:${GZ_SIM_SYSTEM_PLUGIN_PATH}' >> ~/.bashrc
    echo 'export GZ_SIM_RESOURCE_PATH=$HOME/gz_ws/src/ardupilot_gazebo/models:$HOME/gz_ws/src/ardupilot_gazebo/worlds:${GZ_SIM_RESOURCE_PATH}' >> ~/.bashrc
Record the plugin version: `git rev-parse HEAD`.

## 3. Run
Terminal 1:  `gz sim -v4 -r iris_runway.sdf`
Terminal 2:  `cd ~/ardupilot && sim_vehicle.py -v ArduCopter -f gazebo-iris --model JSON --map --console --out 127.0.0.1:5555`

## 4. Mission scripts (separate venv, Python 3.9)
    python3.9 -m venv ~/venv-dronekit && . ~/venv-dronekit/bin/activate
    pip install -r requirements.txt
    python missions/run_mission.py grid --connect 127.0.0.1:5555

## 5. WSL notes
Use WSL 2 with WSLg, or an X server such as VcXsrv, for GUI forwarding. Run scripts inside WSL, not on Windows.
