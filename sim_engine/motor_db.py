"""
Rocket Motor Database and Thrust Curve Management
Supports standard Estes/Aerotech motors with thrust curves.
"""

import numpy as np

class MotorData:
    def __init__(self, motor_id, total_mass_g, propellant_mass_g, delay_sec, thrust_curve):
        """
        thrust_curve: list of (time_sec, thrust_N)
        """
        self.motor_id = motor_id
        self.total_mass_g = total_mass_g
        self.propellant_mass_g = propellant_mass_g
        self.burnout_mass_g = total_mass_g - propellant_mass_g
        self.delay_sec = delay_sec
        
        # Sort curve by time
        tc = sorted(thrust_curve, key=lambda x: x[0])
        self.time_points = np.array([pt[0] for pt in tc])
        self.thrust_points = np.array([pt[1] for pt in tc])
        self.burn_time = float(self.time_points[-1])
        
        # Total impulse calculation
        self.total_impulse = float(np.trapezoid(self.thrust_points, self.time_points))

    def get_thrust(self, t):
        """Get thrust [N] at time t [s] from ignition"""
        if t < 0.0 or t > self.burn_time:
            return 0.0
        return float(np.interp(t, self.time_points, self.thrust_points))

    def get_mass_g(self, t):
        """Get motor mass [g] at time t [s] (mass decreases linearly with burnt impulse)"""
        if t <= 0.0:
            return self.total_mass_g
        if t >= self.burn_time:
            return self.burnout_mass_g
        
        # Approximate fuel consumption proportional to time or integral
        # Here we interpolate mass reduction proportional to integral of thrust
        t_sub = self.time_points[self.time_points <= t]
        if len(t_sub) < 2:
            frac = t / self.burn_time
        else:
            thrust_sub = np.interp(t_sub, self.time_points, self.thrust_points)
            imp_now = np.trapezoid(thrust_sub, t_sub)
            frac = min(1.0, max(0.0, imp_now / self.total_impulse)) if self.total_impulse > 0 else (t / self.burn_time)
            
        return self.total_mass_g - (self.propellant_mass_g * frac)


# Standard Built-in Motor Catalog (Estes)
BUILTIN_MOTORS = {
    # 1/2A6-2 (1/2A class, 18mm x 70mm)
    "1/2A6-2": MotorData(
        motor_id="1/2A6-2",
        total_mass_g=15.0,
        propellant_mass_g=1.56,
        delay_sec=2.0,
        thrust_curve=[
            (0.00, 0.0),
            (0.03, 14.0),
            (0.08, 9.0),
            (0.15, 6.0),
            (0.24, 4.5),
            (0.28, 3.0),
            (0.32, 0.0)
        ]
    ),
    "1/2A6": MotorData(
        motor_id="1/2A6-2",
        total_mass_g=15.0,
        propellant_mass_g=1.56,
        delay_sec=2.0,
        thrust_curve=[
            (0.00, 0.0),
            (0.03, 14.0),
            (0.08, 9.0),
            (0.15, 6.0),
            (0.24, 4.5),
            (0.28, 3.0),
            (0.32, 0.0)
        ]
    ),
    # A8-3 (A class, 18mm x 70mm)
    "A8-3": MotorData(
        motor_id="A8-3",
        total_mass_g=16.0,
        propellant_mass_g=3.12,
        delay_sec=3.0,
        thrust_curve=[
            (0.00, 0.0),
            (0.05, 13.5),
            (0.10, 10.0),
            (0.20, 6.5),
            (0.35, 4.8),
            (0.50, 0.0)
        ]
    ),
    # B6-4 (B class, 18mm x 70mm)
    "B6-4": MotorData(
        motor_id="B6-4",
        total_mass_g=20.0,
        propellant_mass_g=6.24,
        delay_sec=4.0,
        thrust_curve=[
            (0.00, 0.0),
            (0.05, 12.0),
            (0.15, 6.0),
            (0.40, 5.2),
            (0.70, 4.5),
            (0.83, 0.0)
        ]
    ),
    # C6-5 (C class, 18mm x 70mm)
    "C6-5": MotorData(
        motor_id="C6-5",
        total_mass_g=25.0,
        propellant_mass_g=12.48,
        delay_sec=5.0,
        thrust_curve=[
            (0.00, 0.0),
            (0.05, 14.0),
            (0.18, 6.5),
            (0.50, 5.0),
            (1.00, 4.6),
            (1.50, 4.0),
            (1.65, 0.0)
        ]
    )
}

def get_motor(motor_id_str):
    """Find motor data by ID or fuzzy matching"""
    clean_id = motor_id_str.strip().upper()
    
    # Direct match
    if clean_id in BUILTIN_MOTORS:
        return BUILTIN_MOTORS[clean_id]
        
    # Check key containment
    for key, motor in BUILTIN_MOTORS.items():
        if key in clean_id or clean_id in key:
            return motor
            
    # Default fallback to 1/2A6-2 if contains 1/2A
    if "1/2A" in clean_id:
        return BUILTIN_MOTORS["1/2A6-2"]
    if "A8" in clean_id:
        return BUILTIN_MOTORS["A8-3"]
    if "B6" in clean_id:
        return BUILTIN_MOTORS["B6-4"]
    if "C6" in clean_id:
        return BUILTIN_MOTORS["C6-5"]
        
    raise ValueError(f"Motor '{motor_id_str}' not found in database.")
