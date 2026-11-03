uint64 timestamp      # time since system start (microseconds)

float32[3] xm         # reference model rate [rad/s]
float32[3] e          # x - xm [rad/s]
float32[3] u_ad       # adaptive torque added (normalized)
float32[9] theta      # Theta per axis, Phi = [x, r, 1]
uint8 mode            # MRL_EN_RATE
bool adapting
