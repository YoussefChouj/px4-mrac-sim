uint64 timestamp      # time since system start (microseconds)

float32[3] xm         # reference model rate [rad/s]
float32[3] e          # x - xm [rad/s]
float32[3] u_ad       # adaptive torque added (normalized)
float32[9] theta      # Theta per axis, Phi = [x, r, 1]
float32[3] theta_norm # |Theta| over all active terms (three-block feature mask, MRL_*_FEAT)
uint8 n_phi          # regressor length in use
uint8 mode            # MRL_EN_RATE
bool adapting
