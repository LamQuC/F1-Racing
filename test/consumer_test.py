import fastf1

# Lấy session
session = fastf1.get_session(2023, 'Monaco', 'R')
session.load()

# Lấy telemetry của MỘT tay đua để kiểm tra
driver_laps = session.laps.pick_driver('VER')
telemetry = driver_laps.get_telemetry() 

# TRƯỚC KHI INSERT: Kiểm tra xem các cột này có data không
print(telemetry[['Throttle', 'Brake', 'X', 'Y']].head())