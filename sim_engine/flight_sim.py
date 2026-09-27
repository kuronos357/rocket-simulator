"""
Flight Dynamics Simulator (Ascent, Coast, Apogee, Ejection, Descent)
Simulates launch rod clearance, powered flight, inertia coasting, and recovery descent.
"""

import numpy as np

class FlightSimulator:
    def __init__(self, rocket_model, aero_engine):
        self.model = rocket_model
        self.aero = aero_engine
        self.motor = rocket_model.motor_part["motor_data"] if rocket_model.motor_part else None
        
        self.air_density = 1.225 # kg/m3
        self.g = 9.80665         # m/s2
        self.rod_length_m = 0.9  # Standard launch rod length (0.9m / 3ft)

    def run_simulation(self, dt=0.005, max_time_s=120.0):
        """
        Run forward simulation using Euler / RK integration.
        Returns time series log and key performance indicators (KPIs).
        """
        t = 0.0
        z = 0.0 # altitude [m]
        v = 0.0 # vertical velocity [m/s]
        
        # State tracking
        stage = "BOOST" # BOOST -> COAST -> APOGEE -> DESCENT -> LANDED
        
        time_log = []
        alt_log = []
        vel_log = []
        acc_log = []
        thrust_log = []
        mass_log = []
        
        apogee_alt_m = 0.0
        apogee_time_s = 0.0
        rod_speed_m_s = 0.0
        rod_cleared = False
        max_vel_m_s = 0.0
        max_acc_g = 0.0
        landing_speed_m_s = 0.0
        landing_time_s = 0.0
        ejection_triggered = False
        ejection_time_s = 0.0
        ejection_alt_m = 0.0
        ejection_vel_m_s = 0.0
        
        burn_time = self.motor.burn_time if self.motor else 0.0
        ejection_target_t = burn_time + (self.motor.delay_sec if self.motor else 0.0)
        
        # Recovery properties
        rec = self.model.recovery_part
        is_streamer = (rec and rec["type"] == "streamer")
        
        # Descent drag area product (Cd * S)
        if is_streamer:
            # Streamer (film): Cd ~ 0.2, Area ~ 0.05 m2 (5cm x 100cm)
            descent_CdS = 0.20 * 0.05
        else:
            # Parachute (e.g. 30cm dome or flat)
            # Cd ~ 0.75, Area ~ pi * 0.15^2 ~ 0.07 m2
            descent_CdS = 0.80 * 0.070
            
        # Add lateral rocket body + fin drag if horizontal descent is active
        if rec and rec.get("horizontal_descent", False):
            # Calculate true lateral projected area from STL mesh
            # X/Z direction projection of 3D mesh
            mesh = self.aero.mesh
            normals = mesh.face_normals
            areas = mesh.area_faces * 1e-6 # mm2 -> m2
            
            # Flight axis is Y (or Z in std)
            # Lateral projection: sum of areas facing lateral wind
            if self.aero.flight_axis == "y":
                # Lateral is X or Z
                area_proj_lat = np.sum(areas * np.maximum(0, normals[:, 0]))
            else:
                area_proj_lat = np.sum(areas * np.maximum(0, normals[:, 0]))
                
            # Lateral flat plate / cylinder Cd ~ 1.25
            lateral_Cd = 1.25
            lateral_CdS = lateral_Cd * max(0.005, area_proj_lat)
            descent_CdS += lateral_CdS

        while t < max_time_s:
            # Current motor state
            thrust_N = self.motor.get_thrust(t) if self.motor else 0.0
            motor_mass_g = self.motor.get_mass_g(t) if self.motor else 0.0
            
            # Current total mass (kg)
            dry_mass_kg = self.model.dry_mass_g * 1e-3
            current_mass_kg = dry_mass_kg + (motor_mass_g * 1e-3)
            
            # 1. State machine transitions
            if stage == "BOOST" and t >= burn_time:
                stage = "COAST"
                
            if stage in ["BOOST", "COAST"]:
                if v > max_vel_m_s:
                    max_vel_m_s = v
                    
                # Check apogee
                if v <= 0.0 and z > 1.0:
                    stage = "APOGEE"
                    apogee_alt_m = z
                    apogee_time_s = t
                    
            if not ejection_triggered and t >= ejection_target_t:
                ejection_triggered = True
                ejection_time_s = t
                ejection_alt_m = z
                ejection_vel_m_s = v
                if stage in ["BOOST", "COAST", "APOGEE"]:
                    stage = "DESCENT"

            # Check launch rod clearance
            if not rod_cleared and z >= self.rod_length_m:
                rod_cleared = True
                rod_speed_m_s = v

            # 2. Aerodynamic Drag Calculation
            if stage in ["BOOST", "COAST", "APOGEE"]:
                # Ascent aero drag
                aero_res = self.aero.compute_aerodynamics(abs(v), alpha_deg=1.0)
                Cd = aero_res["Cd"]
                ref_area = self.aero.ref_area_m2
                drag_force_N = 0.5 * self.air_density * (v**2) * Cd * ref_area * np.sign(v)
            else:
                # Descent aero drag (parachute/streamer deploy)
                drag_force_N = 0.5 * self.air_density * (v**2) * descent_CdS * np.sign(v)

            # 3. Equation of motion: m * a = Thrust - Drag - m * g
            gravity_force_N = current_mass_kg * self.g
            total_force_N = thrust_N - drag_force_N - gravity_force_N
            
            acc = total_force_N / current_mass_kg
            acc_g = acc / self.g
            if acc_g > max_acc_g:
                max_acc_g = acc_g

            # Integration (Symplectic Euler / Verlet step)
            v_next = v + acc * dt
            z_next = z + v_next * dt
            
            # Ground impact check
            if z_next <= 0.0 and t > 1.0:
                z = 0.0
                landing_speed_m_s = abs(v)
                landing_time_s = t
                stage = "LANDED"
                break
                
            t += dt
            v = v_next
            z = z_next
            
            # Log
            time_log.append(t)
            alt_log.append(z)
            vel_log.append(v)
            acc_log.append(acc_g)
            thrust_log.append(thrust_N)
            mass_log.append(current_mass_kg * 1000.0)

        # Calculate real apogee from flight log
        if alt_log:
            real_apogee_alt = max(alt_log)
            apogee_idx = alt_log.index(real_apogee_alt)
            real_apogee_time = time_log[apogee_idx]
        else:
            real_apogee_alt = z
            real_apogee_time = t

        # Terminal descent speed based on actual burnout descent mass
        descent_mass_kg = getattr(self.model, "burnout_mass_g", current_mass_kg * 1000.0) * 1e-3
        terminal_vel_m_s = np.sqrt((2.0 * descent_mass_kg * self.g) / (self.air_density * max(1e-4, descent_CdS)))

        return {
            "apogee_alt_m": round(real_apogee_alt, 2),
            "apogee_time_s": round(real_apogee_time, 2),
            "max_velocity_km_h": round(max_vel_m_s * 3.6, 1),
            "max_velocity_m_s": round(max_vel_m_s, 2),
            "max_accel_G": round(max_acc_g, 1),
            "rod_clear_speed_m_s": round(rod_speed_m_s, 2),
            "is_rod_speed_safe": bool(rod_speed_m_s >= 12.0),
            "ejection_time_s": round(ejection_time_s, 2),
            "ejection_alt_m": round(ejection_alt_m, 2),
            "ejection_vel_m_s": round(ejection_vel_m_s, 2),
            "terminal_velocity_m_s": round(terminal_vel_m_s, 2),
            "landing_speed_m_s": round(landing_speed_m_s if landing_speed_m_s > 0 else terminal_vel_m_s, 2),
            "total_flight_time_s": round(t, 2),
            "time_series": {
                "t": time_log,
                "alt": alt_log,
                "vel": vel_log,
                "acc": acc_log
            }
        }
