#!/usr/bin/env bash
# Run as the WSL user: XRCE agent + flycart30 on instance 8, check PX4 topics in ROS 2, shut down what we started.
T=~/px4-tools
set +u; source /opt/ros/jazzy/setup.bash; source ~/ros2_ws/install/setup.bash
mkdir -p ~/.cache/hl
setsid MicroXRCEAgent udp4 -p 8888 > ~/.cache/hl/agent.log 2>&1 < /dev/null &
apid=$!
setsid $T/px4ctl gz 8 flycart30 > ~/.cache/hl/sim4.log 2>&1 < /dev/null &
for i in {1..60}; do grep -q 'Ready for takeoff' ~/.cache/hl/sim4.log && break; sleep 1; done
for i in {1..15}; do
  sleep 2; ros2 topic list --no-daemon > ~/.cache/hl/topics.txt
  grep -q fmu/out ~/.cache/hl/topics.txt && break
done
echo "topics visible after $((i * 2)) s"
echo "fmu topics: $(grep -c fmu ~/.cache/hl/topics.txt) (out $(grep -c fmu/out ~/.cache/hl/topics.txt), in $(grep -c fmu/in ~/.cache/hl/topics.txt))"
grep fmu/out ~/.cache/hl/topics.txt | head -4
odo=$(grep 'fmu/out/vehicle_odometry' ~/.cache/hl/topics.txt | head -1)
[ -n "$odo" ] && timeout 30 python3 ~/px4-tools/agent/ros_hz.py "$odo" 10
grep -i -e 'session established' -e error ~/.cache/hl/agent.log | head -3
$T/px4ctl cmd 8 shutdown; sleep 3
kill $apid 2>/dev/null; pkill -u "$USER" -f 'MicroXRCEAgent udp4 -p 8888'
echo "gz left: $(pgrep -f 'gz sim' -u "$USER" | wc -l), agent left: $(pgrep -u "$USER" -f MicroXRCEAgent | wc -l)"
