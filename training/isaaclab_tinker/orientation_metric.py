"""Maximum absolute roll/pitch from body-frame gravity, including inverted states."""
def max_abs_roll_pitch(gravity,lib):
    roll=lib.arctan2(-gravity[...,1],-gravity[...,2])
    pitch=lib.arctan2(gravity[...,0],lib.sqrt(gravity[...,1]**2+gravity[...,2]**2))
    return lib.maximum(lib.abs(roll),lib.abs(pitch))
