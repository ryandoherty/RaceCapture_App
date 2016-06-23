#!/usr/bin/env python
import math

input_filename = '/Users/rdoherty/Desktop/RC_6 - possible final 10-25 17.LOG'
output_filename = '/Users/rdoherty/Desktop/RC_6 - possible final 10-25 17 - FIXED.LOG'


def within_circle(point, circle_center, radius_deg):
    r_squared = radius_deg * radius_deg
    x_delta = circle_center["longitude"] - point["longitude"]
    y_delta = circle_center["latitude"] - point["latitude"]
    d_squared = (x_delta * x_delta) + (y_delta * y_delta)
    return r_squared >= d_squared


def meters_to_degrees(meters, bearing_angle, point):
    d = meters / 1000.0
    brng = math.radians(bearing_angle)

    lat1 = point["latitude"]
    lon1 = point["longitude"]

    lat2 = math.degrees((d / RADIUS_EARTH_KM) * math.cos(brng)) + lat1
    lon2 = math.degrees((d / (RADIUS_EARTH_KM * math.sin(math.radians(lat2)))) * math.sin(brng)) + lon1

    distance_degrees = math.fabs(math.sqrt(math.pow((lat1 - lat2), 2) + math.pow((lon1 - lon2), 2)))
    return distance_degrees

start_finish = {"latitude": 45.011127, "longitude": -74.893387}
armed = False
last_lap_timestamp = None
radius_meters = 20
bearing = 360
RADIUS_EARTH_KM = 6371
search_radius = meters_to_degrees(radius_meters, bearing, start_finish)
laps = 0
channels = []
speed_index = None
lapcount_index = None
laptime_index = None
distance_index = None
currentlap_index = None
previous_sf_distance = None
latitude_index = None
longitude_index = None
indexes = {}

input_file = open(input_filename, 'r')
output_file = open(output_filename, 'w')

header = input_file.readline().strip()

channel_metas = header.split(',')

for index, meta in enumerate(channel_metas):
    name, units, min, max, samplerate = meta.replace('"', '').split('|')

    indexes[name] = index

line = input_file.readline()

if not (indexes["LapCount"] and indexes["LapTime"] and indexes["Latitude"] and indexes["Longitude"] and indexes["Speed"]):
    print("Missing required channels, aborting")
    exit(1)

if "Distance" not in indexes:
    channel_metas.append('"Distance"|"mi"|0|0|10')
    indexes["Distance"] = len(channel_metas) - 1

if "ElapsedTime" not in indexes:
    channel_metas.append('"ElapsedTime"|"min"|0|0|10')
    indexes["ElapsedTime"] = len(channel_metas) - 1


output_file.write(",".join(channel_metas) + "\n")

speed = None
latitude = None
longitude = None
distance = 0
armed = False
previous_sf_cross_time = None
prev_timestamp = None
prev_speed = None
laptime_minutes = 0
elapsed_time_minutes = 0

while line != "":
    line = line.strip()
    values = line.split(',')

    if len(values) != len(channel_metas):
        diff = len(channel_metas) - len(values)
        additional_values = [''] * diff
        values.extend(additional_values)

    cur_speed = float(values[indexes['Speed']]) if values[indexes['Speed']] != "" else None
    cur_latitude = float(values[indexes['Latitude']]) if values[indexes['Latitude']] != "" else None
    cur_longitude = float(values[indexes['Longitude']]) if values[indexes['Longitude']] != "" else None
    timestamp = int(values[indexes['Utc']])

    # Need to compute elapsed time for old app versions
    if previous_sf_cross_time is not None:
        elapsed_time_ms = timestamp - previous_sf_cross_time
        elapsed_time_minutes = round(elapsed_time_ms/60000.0, 3)

    # Need to compute distance
    speed = values[indexes['Speed']]
    speed = float(speed) if speed != '' else prev_speed

    if prev_timestamp is not None and prev_speed is not None:
        # Compute distance
        time_diff_ms = timestamp - prev_timestamp
        avg_speed_mph = (speed + prev_speed)/2
        distance_traveled_miles = time_diff_ms * (avg_speed_mph/(1 * 60 * 60 * 1000))
        distance += distance_traveled_miles

    if cur_latitude and cur_longitude:
        # We can do our work here
        cur_pos = {"latitude": cur_latitude, "longitude": cur_longitude}

        if within_circle(cur_pos, start_finish, search_radius):
            if not armed:
                armed = True

                if previous_sf_cross_time is not None:
                    # Hey a lap!

                    laptime_ms = timestamp - previous_sf_cross_time
                    laptime_minutes = round(laptime_ms/60000.0, 3)

                    previous_sf_cross_time = timestamp
                    laps += 1
                    distance = 0
                else:
                    previous_sf_cross_time = timestamp

        elif armed:
            armed = False

    values[indexes["LapTime"]] = str(laptime_minutes)
    values[indexes["LapCount"]] = str(laps)
    values[indexes["CurrentLap"]] = str(laps+1)
    values[indexes["Distance"]] = str(distance)
    values[indexes["ElapsedTime"]] = str(elapsed_time_minutes)

    prev_timestamp = timestamp
    prev_speed = speed

    output_file.write(",".join(values) + "\n")

    line = input_file.readline()


print "Laps: " + str(laps)
output_file.close()

