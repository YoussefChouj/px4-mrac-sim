uint64 timestamp      # time since system start (microseconds)

float32[3] xm         # reference model rate [rad/s]
float32[3] e          # x - xm [rad/s]
float32[3] u_ad       # adaptive torque added (normalized)
float32[9] theta      # Theta per axis, Phi = [x, r, 1]
float32[3] theta_norm # |Theta| over all active terms (three-block feature mask, MRL_*_FEAT)
float32[3] sched_cut  # v2 block 2: 1 - scheduler scale (0 = no cut; rate layer only, MRL_R_V2 bits 2/4)
float32 dly_est       # online delay estimate [s], mean of roll and pitch (rate layer, MRL_R_DEST >= 1; -1 = off)
uint8 n_phi          # regressor length in use
uint8 mode            # MRL_EN_RATE
bool adapting
