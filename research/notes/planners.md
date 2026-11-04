# Planners (P2 2026-11-03, decided at P14 2026-11-04)

| Candidate | Finding (source) | Verdict |
|---|---|---|
| PX4 Collision Prevention | "can be enabled for multicopter vehicles in Position mode" with MPC_POS_MODE acceleration based; input is `obstacle_distance` / `distance_sensor`; sim with `gz_x500_lidar_2d` (docs.px4.io/main/en/computer_vision/collision_prevention) | Reject as planner: it acts only in Position mode (stick input), our decks fly offboard. Possible later as a reactive safety layer test. |
| PX4-Avoidance (local_planner) | "archived by the owner on Aug 1, 2024. It is now read-only"; ROS Noetic on Ubuntu 20.04 (github.com/PX4/PX4-Avoidance) | Reject: archived, ROS 1, we run Ubuntu 24.04 + ROS-free MAVSDK. |
| EGO-Planner / FUEL type local planners | ROS 1 research stacks, need a depth camera + mapping [A, not installed] | Defer: a perception track, not needed for a known course. |
| **Known-map A* + shortcutting (built)** | `agent/planner.py`: grid 0.1 m over `worlds/<world>.json`, each obstacle inflated by drone radius + margin, line-of-sight shortcut | **Adopted.** Deterministic, controller-agnostic, same table the world and the clearance check use. |

Deck step: `{"do": "plan", "n": N, "e": E, "margin": M}` in `agent/scenario.py`.
On the P13 course, from (0, 0) to (16, 0):
- margin 0.6 m: the 1.2 m gate is too narrow, so the route goes around the gate wall. Length 18.2 m, clearance 0.86 m [D].
- margin 0.3 m: threads the gate. Length 16.3 m, clearance 0.56 m [D].
