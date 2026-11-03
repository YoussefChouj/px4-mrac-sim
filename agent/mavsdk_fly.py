#!/usr/bin/env python3
"""Fly a running PX4 instance by MAVSDK: params, telemetry rate, takeoff, move, land.

Usage: mavsdk_fly.py [INSTANCE] [ALT_M]. Prints one plain-text line per event, so an
agent reads the outcome from stdout. The same code flies a real board: only the URL changes.
"""
import asyncio
import sys
import time

# mavsdk>=4 is a new native binding; the gRPC API used here ships as mavsdk-grpc.
from mavsdk_grpc import System
from mavsdk_grpc.offboard import OffboardError, PositionNedYaw

inst = int(sys.argv[1]) if len(sys.argv) > 1 else 8
alt = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
t0 = time.monotonic()


def say(msg):
    print(f'{time.monotonic() - t0:6.1f}s {msg}', flush=True)


async def wait_until(gen, ok, timeout):
    async def run():
        async for v in gen:
            if ok(v):
                return v
    return await asyncio.wait_for(run(), timeout)


async def main():
    # PX4 SITL instance N sends its onboard MAVLink link to UDP 14540 + N.
    drone = System(port=50051 + inst)
    await drone.connect(system_address=f'udpin://0.0.0.0:{14540 + inst}')
    await wait_until(drone.core.connection_state(), lambda s: s.is_connected, 60)
    say('connected')
    await wait_until(drone.telemetry.health(),
                     lambda h: h.is_global_position_ok and h.is_home_position_ok, 90)
    say('position ok')
    for name in ('MPC_THR_HOVER', 'MC_ROLLRATE_P', 'MPC_Z_VEL_P_ACC'):
        say(f'param {name} = {await drone.param.get_param_float(name):.3f}')
    await drone.telemetry.set_rate_position_velocity_ned(50)
    await drone.action.set_takeoff_altitude(alt)
    await drone.action.arm()
    await drone.action.takeoff()
    say(f'takeoff to {alt} m')
    await wait_until(drone.telemetry.position_velocity_ned(),
                     lambda p: -p.position.down_m > alt - 0.3, 60)
    say('at altitude')
    await asyncio.sleep(3)
    # Offboard needs a setpoint streaming before start; hold here, then move 10 m north.
    await drone.offboard.set_position_ned(PositionNedYaw(0, 0, -alt, 0))
    try:
        await drone.offboard.start()
    except OffboardError as e:
        say(f'offboard refused: {e._result.result}')
        await drone.action.land()
        return
    await drone.offboard.set_position_ned(PositionNedYaw(10, 0, -alt, 0))
    say('offboard: 10 m north')
    peak = 0.0
    async for p in drone.telemetry.position_velocity_ned():
        peak = max(peak, p.position.north_m)
        if abs(p.position.north_m - 10) < 0.2 and abs(p.velocity.north_m_s) < 0.1:
            break
    say(f'arrived; peak north {peak:.2f} m (overshoot {peak - 10:.2f} m)')
    await drone.offboard.stop()
    await drone.action.land()
    await wait_until(drone.telemetry.in_air(), lambda a: not a, 90)
    say('landed')
    await wait_until(drone.telemetry.armed(), lambda a: not a, 30)
    say('disarmed')


asyncio.run(main())
