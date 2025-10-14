print("installing and importing libraries...")
from urllib.request import urlretrieve
import os
from zipfile import ZipFile
import time
import socket
import string
import sqlite3
from sqlite3 import Error
import subprocess
import sys
import datetime
import re
import threading
import operator
import ssl
# problem with pandas, certifi and requests while running on pycharm venv. installing them
subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas"])
import pandas as pd
subprocess.check_call([sys.executable, "-m", "pip", "install", "certifi"])
import certifi
subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
import requests
print("successfully installed and imported libraries")


def clean_stop_dups(stops):
    """
    removes all stops with similar names
    :param stops: [[name, id], [,]]
    """
    i = 0
    stops_to_remove = []  # a list of the indexes of the similar stops
    while i < len(stops):
        t = i + 1
        while t < len(stops):
            if stops[t][0] == stops[i][0]:
                stops_to_remove.append(t)
            t += 1
        i += 1
    stops_to_remove.reverse()
    stops_to_remove = list(dict.fromkeys(stops_to_remove))
    for stop in stops_to_remove:
        stops.remove(stops[stop])


class Moovit:

    def files_exist(self):
        """
        checks if the required files for server exist
        """
        for f in self.files:
            f = os.path.join(os.getcwd(), f)
            if not os.path.isfile(f) and not os.path.isfile(str(f.split('.')[0]) + ".csv"):
                return False
        return True

    def download_files(self):
        """
        downloads and extracts .txt files required for server (if not exist)
        """
        if self.files_exist():  # extracted .txt files already exist
            print("All_Files_Exist")
            return
        try:
            if not os.path.exists("israel-public-transportation.zip"):  # zip file does not exist
                url = "https://gtfs.mot.gov.il/gtfsfiles/israel-public-transportation.zip"  # israeli GTFS data url
                filename = "israel-public-transportation.zip"  # for the local file to write data into
                dst = os.path.join(os.getcwd(), filename)
                print("Downloading_Files... (using requests)")
                response = requests.get(url, stream=True, verify=False)  # verify=False because had SSL certificate problems while running via PyCharm venv
                response.raise_for_status()  # checks if response got successfully, if not raises exception

                # writing the data into the local new file
                with open(dst, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print("Files_Downloaded_Successfully")
            else:  # zip file already exists
                print("ZIP_File_Exists")

        except Error as e:  # error in download
            print(e)

        try:
            print("Extracting_Files...")
            # delete existing files to prevent duplications
            for file in self.files:
                if os.path.isfile(file):
                    os.remove(file)
            # extracting files
            with ZipFile('israel-public-transportation.zip', 'r') as zipObj:
                zipObj.extractall()
                print("Files_Extracted_Successfully")
        except Error:
            print(Error)

    def convert_files_to_csv(self):
        """
        converts all .txt files to .csv for further importing to db
        """
        for file in self.files:
            if not os.path.isfile(file.split('.')[0] + ".csv"):
                try:
                    new_path = file.split('.')[0] + ".csv"
                    os.rename(file, new_path)
                except Error as e:
                    print(e)
        print("Files_Converted_Successfully")

    def db_setup(self):
        """
        sets up db file, including making tables and reading files
        """
        print("Setting_Up_DB")
        if os.path.isfile(self.db_file):
            print("DB_Exists")
            return
        self.download_files()  # downloads and extracts the files needed
        self.convert_files_to_csv()
        self.create_tables()  # creating tables on self.db_file (sqlite 3)
        self.import_data_to_db()  # import the data from csv files to the tables in the db_file
        print("DB_Ready")

    def create_tables(self):
        """
        creates all required tables on db file
        """
        print("Creating_Tables...")
        cur = self.get_cur()  # gets cursor in the self.db_file
        try:
            # create table for agency.csv
            cur.execute("""CREATE TABLE agency (
                                    agency_id INTEGER NOT NULL PRIMARY KEY,
                                    agency_name TEXT NOT NULL,
                                    agency_url TEXT NOT NULL,
                                    agency_timezone TEXT,
                                    agency_lang TEXT,
                                    agency_phone TEXT,
                                    agency_fare_url TEXT
                                    );""")  # agency
            # create table for stops.csv
            cur.execute("""CREATE TABLE stops (
                                    stop_id INTEGER NOT NULL,
                                    stop_code INTEGER,
                                    stop_name TEXT,
                                    stop_desc TEXT,
                                    stop_lat REAL,
                                    stop_lon REAL,
                                    location_type INTEGER,
                                    parent_station INTEGER,
                                    zone_id INTEGER,
                                    FOREIGN KEY (parent_station)
                                        REFERENCES stops(stop_id)
                                    );""")
            cur.execute("""
                CREATE INDEX idx_stops_stop_id
                ON stops(stop_id);
                """)  # stop_id index for faster search
            cur.execute("""
                CREATE INDEX idx_stops_stop_code
                ON stops(stop_code);
                """)  # stop_code index
            cur.execute("""
                CREATE INDEX idx_stops_stop_name
                ON stops(stop_name);
                """)  # stop_name index
            cur.execute("""
                CREATE INDEX idx_stops_stop_lat
                ON stops(stop_lat);
                """)  # stop_lat index
            cur.execute("""
                CREATE INDEX idx_stops_stop_lon
                ON stops(stop_lon);
                """)  # stop_lon index
            cur.execute("""
                CREATE INDEX idx_stops_zone_id
                ON stops(zone_id);
                """)  # zone_id index

            # create table for routes.csv
            cur.execute("""CREATE TABLE routes (
                                    route_id INTEGER NOT NULL,
                                    agency_id INTEGER,
                                    route_short_name TEXT,
                                    route_long_name TEXT,
                                    route_desc TEXT,
                                    route_type INTEGER NOT NULL,
                                    route_color TEXT,
                                    FOREIGN KEY (agency_id)
                                        REFERENCES agency(agency_id)
                                    );""")  # routes
            cur.execute("""
                            CREATE INDEX idx_routes_route_id
                            ON routes(route_id);
                            """)  # route_id index
            cur.execute("""
                            CREATE INDEX idx_routes_route_short_name
                            ON routes(route_short_name);
                            """)  # route_short_name index

            # create table for calendar.csv
            cur.execute("""CREATE TABLE calendar (
                                    service_id INTEGER NOT NULL,
                                    sunday INTEGER NOT NULL,
                                    monday INTEGER NOT NULL,
                                    tuesday INTEGER NOT NULL,
                                    wednesday INTEGER NOT NULL,
                                    thursday INTEGER NOT NULL,
                                    friday INTEGER NOT NULL,
                                    saturday INTEGER NOT NULL,
                                    start_date INTEGER NOT NULL,
                                    end_date INTEGER NOT NULL
                                    );""")
            cur.execute("""
                                CREATE INDEX idx_calendar_service_id
                                ON calendar(service_id);
                                """)  # service_id index

            # create table for shapes.csv
            cur.execute("""CREATE TABLE shapes (
                                    shape_id INTEGER NOT NULL,
                                    shape_pt_lat INTEGER NOT NULL,
                                    shape_pt_lon INTEGER NOT NULL,
                                    shape_pt_sequence INTEGER NOT NULL
                                );""")
            cur.execute("""
                                CREATE INDEX idx_shapes_shape_id_seq
                                ON shapes(shape_id, shape_pt_sequence);
                                """)  # shape_id, shape__pt_sequence index
            cur.execute("""
                                CREATE INDEX idx_shapes_shape_pt_lat
                                ON shapes(shape_pt_lat);
                                """)  # shape_pt_lat index
            cur.execute("""
                                CREATE INDEX idx_shapes_shape_pt_lon
                                ON shapes(shape_pt_lon);
                                """)  # shape_pt_lon index

            # create table for trips.csv
            cur.execute("""CREATE TABLE trips (
                                    route_id INTEGER NOT NULL,
                                    service_id INTEGER NOT NULL,
                                    trip_id TEXT NOT NULL,
                                    trip_headsign TEXT,
                                    direction_id INTEGER,
                                    shape_id INTEGER,
                                    wheelchair_accessible INTEGER,
                                    FOREIGN KEY (route_id)
                                        REFERENCES route(route_id)
                                    FOREIGN KEY (service_id)
                                        REFERENCES calendar(service_id)
                                    FOREIGN KEY (shape_id)
                                        REFERENCES shapes(shape_id)
                                    );""")
            cur.execute("""
                            CREATE INDEX idx_trips_route_id
                            ON trips(route_id);
                            """)  # route_id index
            cur.execute("""
                            CREATE INDEX idx_trips_service_id
                            ON trips(service_id);
                            """)  # service_id index
            cur.execute("""
                            CREATE INDEX idx_trips_trip_id
                            ON trips(trip_id);
                            """)  # trip_id index
            cur.execute("""
                            CREATE INDEX idx_trips_shape_id
                            ON trips(shape_id);
                            """)  # shape_id index

            # create table for stop_times.csv
            cur.execute("""CREATE TABLE stop_times (
                                    trip_id INTEGER NOT NULL,
                                    arrival_time TEXT,
                                    departure_time TEXT,
                                    stop_id INTEGER NOT NULL,
                                    stop_sequence INTEGER NOT NULL,
                                    pickup_type INTEGER,
                                    drop_off_type INTEGER,
                                    shape_dist_traveled REAL,
                                    FOREIGN KEY (trip_id)
                                        REFERENCES trips(trip_id)
                                    FOREIGN KEY (stop_id)
                                        REFERENCES stops(stop_id)
                                    );""")
            cur.execute("""
                            CREATE INDEX idx_stop_times_trip_id
                            ON stop_times(trip_id);
                            """)  # trip_id index
            cur.execute("""
                            CREATE INDEX idx_stop_times_arrival_time
                            ON stop_times(arrival_time);
                            """)  # arrival_time index
            cur.execute("""
                            CREATE INDEX idx_stop_times_departure_time
                            ON stop_times(departure_time);
                            """)  # departure_time index
            cur.execute("""
                            CREATE INDEX idx_stop_times_stop_id
                            ON stop_times(stop_id);
                            """)  # stop_id index
            cur.execute("""
                            CREATE INDEX idx_stop_times_stop_sequence
                            ON stop_times(stop_sequence);
                            """)  # stop_sequence index
        except Error as e:
            print(e)
            return
        print("All_Tables_Created")

    def import_data_to_db(self):
        """
        imports all csv files to tables on db file
        """
        print("Importing_Data:")
        for file in self.files:  # goes over all the relevant csv files
            try:
                conn = sqlite3.connect(self.db_file)
                df = pd.read_csv(file.split('.')[0] + ".csv")  # pd reads the csv and converts it to sql
                df.to_sql(file.split('.')[0], conn, if_exists='append', index=False)  # loads it to db file
                conn.commit()  # ends the connections
                print("     ", file.split('.')[0], "imported")
            except Error as e:
                print(e)
        print("All_Data_Imported")

    def find_trips_to_dest(self, origin_id, dest_id):
        """
        find route to destination
        :param origin_id:
        :param dest_id:
        :return: trips:
        [0] - trip_id
        [3] - minutes till departure
        returns a raw list of trips between 2 exact stops, the trips may contain duplicates and reverse trips
        """
        daydict = {
            6: "sunday",
            0: "monday",
            1: "tuesday",
            2: "wednesday",
            3: "thursday",
            4: "friday",
            5: "saturday"
        }
        weekday = daydict[datetime.datetime.today().weekday()]  # gets the weekday by name
        cursor = self.get_cur()
        cursor.execute("""
                        SELECT
                            trips.trip_id AS trip,
                            routes.route_id AS route_id,
                            routes.route_short_name,
                            (strftime('%H', stop_times.departure_time) - strftime('%H', 'now', 'localtime')) * 60 + 
                            strftime('%M', stop_times.departure_time) - strftime('%M', 'now', 'localtime') AS minutes_till_arrival,
                            calendar.service_id AS service_id,
                            calendar.""" + str(weekday) + """ AS is_today,
                            stop_times.stop_id AS stop_id,
                            time('now', 'localtime'),
                            strftime('%d', 'now') + strftime('%m', 'now')*100 + strftime('%Y', 'now')*10000 AS now_date,
                            calendar.start_date,
                            calendar.end_date
                        FROM
                            stop_times
                            LEFT JOIN trips ON stop_times.trip_id = trips.trip_id
                            LEFT JOIN routes ON trips.route_id = routes.route_id
                            LEFT JOIN calendar ON trips.service_id = calendar.service_id
                        WHERE 
                            stop_times.stop_id = """ + str(origin_id) + """
                            AND calendar.""" + str(weekday) + """ = 1
                            AND now_date >= calendar.start_date
                            AND now_date <= calendar.end_date
                            """ +
                            # the line passes in the origin
                            # the line works in this weekday
                            # the line service is working in this date (starts before today and ends after
                            """
                            AND trips.trip_id IN(
                                SELECT
                                    trip_id
                                FROM
                                    stop_times
                                WHERE 
                                    (strftime('%H', departure_time) - strftime('%H', 'now', 'localtime')) * 60 + 
                                    strftime('%M', departure_time) - strftime('%M', 'now', 'localtime') > 0
                                    """ +
                                    # the time until the line passes is positive
                                    """
                                    AND stop_times.trip_id IN(
                                        SELECT
                                            stop_times.trip_id
                                        FROM
                                            stop_times
                                        WHERE
                                            stop_id = """ + str(dest_id)
                                            # the line passes in the destination
                                            + """
                                    )
                                    AND stop_times.stop_id = """ + str(origin_id) + """
                                ORDER BY
                                    (strftime('%H', departure_time) - strftime('%H', 'now', 'localtime')) * 60 + 
                                    strftime('%M', departure_time) - strftime('%M', 'now', 'localtime')
                                    """
                                    # order it by the lines that pass ONLY THE DESTINATION the earliest, and takes only the first 10
                                     + """
                                LIMIT 10
                                )
                        ORDER BY
                            minutes_till_arrival
                        LIMIT 4
                    """  # orders the lines that pass both the destination and origin by time to arrival, and limits to 4
                       )
        """
        search logic summarized, the terms of the query:
        1. the trips passes in the origin
        2. the trip works today
        3. the service is up to date (today is after the start date and before the end date)
        4. it passes in the destination
        5. it passes in a positive number of minutes in the origin and destination (it havent passed yet)
        all ordered by the minutes till departure from the origin (ascending) 
        the trips may contain reversed or duplicates, that are cleaned in the "find_trips_coord" func
        """
        trips = cursor.fetchall()
        if not trips:
            return
        print("trips found")
        return trips

    def find_stop_id(self, stop_name):
        """
        find a stop id
        :param stop_name:
        :return: stop_id
        """
        cur = self.get_cur()
        cur.execute("""
                    SELECT
                        stop_id
                        stop_name
                    FROM
                        stops
                    WHERE
                        stop_name = '""" + stop_name + "'")
        info = cur.fetchall()
        stop_id = info[0][0]
        return stop_id

    def get_route_details_of_trip(self, trip_id):
        """
        gets a trip_id
        :return: [0] - agency_name
                [1] - route_short_name
        """
        cur = self.get_cur()
        cur.execute("""
                            SELECT
                                route_id
                            FROM
                                trips
                            WHERE
                                trip_id = '""" + str(trip_id) + "'")
        route_id = cur.fetchall()[0][0]
        cur.execute("""
                            SELECT
                                agency_id,
                                agency_name,
                                route_short_name                                
                            FROM
                                routes
                            INNER JOIN agency USING(agency_id)
                            WHERE
                                route_id = """ + str(route_id))
        route_details = cur.fetchall()[0][1:]
        return route_details

    def find_all_stops_in_city(self, city):
        """
        gets a name of city, returns all stops in the city
        :param city: name of city to search for stops in
        :return: [0] - stop_name
                [1] - stop_id
        """
        cur = self.get_cur()
        cur.execute(
            """
            SELECT
                stop_name,
                stop_desc,
                stop_id
            FROM
                stops
            WHERE
                stop_desc LIKE '%""" + str(city) + """ רציף%'
            """
        )
        info = cur.fetchall()
        sorted_info = []
        for stop in info:
            sorted_info.append((stop[0], stop[2]))
        sorted_info.sort(key=operator.itemgetter(0))
        return sorted_info

    def get_all_cities(self):
        """
        finds all the cities in db from desc of stops
        """
        cur = self.get_cur()
        cur.execute(
            """
            SELECT
                stop_desc
            FROM
                stops
            """
        )
        info = cur.fetchall()  # all desc of all stops
        newinfo = []
        for inf in info:
            newinfo.append(inf[0])
        cities = []
        for desc in newinfo:
            try:
                result = re.search('עיר: (.*) רציף', desc)  # getting the name of city from a description
                if result.group(1) not in cities:
                    cities.append(result.group(1))
            except:
                pass
        cities.sort()
        return cities

    def find_stop_name(self, stop_id):
        """
        find a stop name
        """
        cur = self.get_cur()
        cur.execute("""
                    SELECT
                        stop_name
                        stop_id
                    FROM
                        stops
                    WHERE
                        stop_id = '""" + str(stop_id) + "'")
        stop_name = cur.fetchall()[0][0]
        return stop_name

    def get_cur(self):
        """
        creates a cursor
        :return: a cursor to db file
        """
        return sqlite3.connect(self.db_file).cursor()

    def get_city_of_stop(self, stop_id):
        """
        gets an id of a stop and returns the name of it's city
        :param stop_id: id of stops
        :return: city name
        """
        cur = self.get_cur()
        cur.execute("""
        SELECT
            stop_id,
            stop_desc
        FROM
            stops
        WHERE
            stop_id = """ + str(stop_id) + """
        """)
        desc = cur.fetchall()[0][1]
        result = re.search('עיר: (.*) רציף', desc)
        return result.group(1)

    def get_close_stops(self, stop_id):
        """
        finds stops in distance of estimated 150 meters or less
        :return: a list of close stop ids
        """
        cur = self.get_cur()
        stops = []
        name = self.find_stop_name(stop_id)
        city = self.get_city_of_stop(stop_id)
        print(str(city))
        cur.execute(
            """
            SELECT
                stop_id,
                stop_name,
                stop_desc
            FROM
                stops
            WHERE
                stop_name = '""" + str(name) + """'
                        AND stop_desc LIKE '%""" + str(city) + """ רציף%'
                    """
        )
        info = cur.fetchall()
        for stop in info:
            stops.append(stop[0])
        lat_lon = self.get_lat_lon(stop_id)
        lat = lat_lon[0]
        lon = lat_lon[1]
        cur.execute(
            """
            SELECT
                stop_id,
                stop_name,
                stop_desc,
                abs(stop_lat-""" + str(lat) + """) + abs(stop_lon-""" + str(lon) + """) AS diff
            FROM
                stops
            WHERE
                diff < 0.0015
            ORDER BY
                diff
            LIMIT 3
            """
        )
        info = cur.fetchall()
        for stop in info:
            stops.append(stop[0])
        stops = list(dict.fromkeys(stops))
        return stops[:4]

    def get_lat_lon(self, stop_id):
        """
        gets an id of stop, returns the coordinates of it
        :param stop_id
        :return: [0] - stop lat
                 [1] - stop lon
        """
        cur = self.get_cur()
        cur.execute(
            """
            SELECT
                stop_id,
                stop_lat,
                stop_lon
            FROM
                stops
            WHERE
                stop_id = """ + str(stop_id) + """
            LIMIT 1
            """
        )
        info = cur.fetchall()
        lat = info[0][1]
        lon = info[0][2]
        place = [lat, lon]
        return place

    def find_arrival_time(self, trip_id, dest_id):
        """
        calculates the number of minutes until the trip of given trip_id leaves stop of stop_id
        :param trip_id: the id of the trip
        :param dest_id: the id of the stop the trip leaves from
        :return: minutes till trip leaves stop
        """
        cur = self.get_cur()
        cur.execute("""
        SELECT
            (strftime('%H', arrival_time) - strftime('%H', 'now', 'localtime')) * 60 + 
            strftime('%M', arrival_time) - strftime('%M', 'now', 'localtime') AS minutes_till_arrival,
            stop_id,
            trip_id
        FROM
            stop_times
        WHERE
            stop_id = """ + str(dest_id) + """
            AND trip_id = '""" + trip_id + """'
        LIMIT 1
        """)
        # arrival_time = at
        # calculation sum up: (hour of at - hour now)*60 + minutes of at - minutes now
        data = cur.fetchall()
        return data[0][0]  # number of minutes until the trip of given_id leaves stop of stop_id

    def find_trips_coord(self, origin_id, dest_id):
        """
        finds trips between 2 stops including close stops, returns only checked trips
        uses find trips to dest on any possible combination of origin and destination
        :param origin_id:the id of the origin of trip searched
        :param dest_id: the id of the destination
        :return:[0] - trip_id
                [1] - origin name
                [2] - dest name
                [3] - agency
                [4] - route short name
                [5] - minutes till depart
                [6] - minutes till arrival
        """
        origin_stops = self.get_close_stops(origin_id)
        dest_stops = self.get_close_stops(dest_id)
        trips = []
        print("finding trips from", origin_stops, "to", dest_stops)
        print("on", datetime.datetime.now().time())
        # searches any combination of origin and destination for trips:
        number_of_searches = len(origin_stops) * len(dest_stops)
        search_number = 1
        for origin in origin_stops:
            for dest in dest_stops:
                print("search", search_number, "of", number_of_searches, "in progress", origin, "to", dest)
                trips_to_add = self.find_trips_to_dest(origin, dest)
                print("search", search_number, "of", number_of_searches, "completed", origin, "to", dest)
                print("found", trips_to_add)
                search_number += 1
                if trips_to_add:
                    # there are trips matching this combination
                    for trip in trips_to_add:
                        new_trip = [origin, dest]  # adding the origin and dest to the start of list
                        for info in trip:
                            new_trip.append(info)
                        trips.append(new_trip)
        # organizing all the information about the trips:
        newtrips = []
        for trip in trips:
            details = self.get_route_details_of_trip(trip[2])
            new_trip = [trip[2], self.find_stop_name(trip[0]), self.find_stop_name(trip[1]), details[0], details[1],
                        trip[5], self.find_arrival_time(trip[2], trip[1])]
            newtrips.append(new_trip)
        newtrips.sort(key=lambda tup: tup[6])  # sorting on the arrival time
        # clean wrong lines (reversed):
        return_trips = []
        for trip in newtrips:
            if trip[5] < trip[6]:  # comparing the leaving time to the arrival time
                return_trips.append(trip)
        return return_trips[:4]  # the GUI gets a maximum of 4 trips

    def handle_client(self, client_socket):
        """
        gets a socket and manages the search of a client, ends when the search is completed
        (a new search will open a new socket)
        """
        print(client_socket)
        # send all cities:
        cities = self.get_all_cities()
        cities_str = ""
        for city in cities:
            cities_str += city + "@"
        print(f"sending list of cities")
        client_socket.send(cities_str.encode())  # city1@city2@city3@...
        print("sent cities")
        # get selected city1:
        try:
            city = client_socket.recv(1024).decode()
            print("got city", city)
        except Exception as e:
            print("client", client_socket, "disconnected")
            client_socket.close()
            return
        # send all stops in selected city1:
        stops = self.find_all_stops_in_city(city)
        stops_str = ""
        clean_stop_dups(stops)  # remove stops with similar names
        for stop in stops:
            stops_str += str(stop[0]) + "#" + str(stop[1]) + "@"
        try:
            client_socket.send(stops_str.encode())
            print("sent stops in", city)
        except Exception as e:
            print("client", client_socket, "disconnected")
            client_socket.close()
            return
        # get selected city2:
        try:
            city = client_socket.recv(1024).decode()
            print("got city", city)
        except Exception as e:
            print("client", client_socket, "disconnected")
            client_socket.close()
            return
        # send all stops in selected city2:
        stops = self.find_all_stops_in_city(city)
        clean_stop_dups(stops)  # remove stops with similar names
        stops_str = ""
        for stop in stops:
            stops_str += str(stop[0]) + "#" + str(stop[1]) + "@"
        try:
            client_socket.send(stops_str.encode())
            print("sent stops in", city)
        except Exception as e:
            print("client", client_socket, "disconnected")
            client_socket.close()
            return
        # get origin and destination from client:
        try:
            print("getting origin and dest of client")
            origin_dest = client_socket.recv(1024).decode().split("@")
            print("successfully received origin and dest")
        except Exception as e:
            print("client", client_socket, "disconnected")
            client_socket.close()
            return
        origin_id = origin_dest[0]
        dest_id = origin_dest[1]
        print("got request:", origin_id, "to", dest_id)
        # find trips for client:
        trips = self.find_trips_coord(origin_id, dest_id)
        # trips = [['585262610_111025', 'עירייה', 'לשם/טורקיז', 'אלקטרה אפיקים תחבורה', '183', 18, 1426]]  # manually insert trips for client check
        print("enter this as trips:", trips)
        trips_str = ""  # the string that eventually will be sent to the client
        for trip in trips:
            for info in trip:
                trips_str += str(info)
                trips_str += "#"
            trips_str = trips_str[:-1]
            trips_str += "@"
        trips_str = trips_str[:-1]
        if not trips_str:
            trips_str = "no_trips_found"
        try:
            print("sending these trips to client:", trips_str)
            client_socket.send(trips_str.encode())
            print("successfully sent trips to client")
        except Exception as e:
            print("client", client_socket, "disconnected")
            client_socket.close()
            return
        print("client", client_socket, "finished")
        client_socket.close()

    def print_db_format_example(self, tables_to_print):
        cur = self.get_cur()
        print("example for tables format:")
        for table in tables_to_print:
            cur.execute(f"""
                                    SELECT
                                        *
                                    FROM
                                        {table}
                                    LIMIT 3
                                    """)
            first_row = cur.fetchall()
            print(f"{table}: {first_row}")

    def __init__(self):
        """
        main server actions
        """
        # basic setup:
        self.db_file = r"pythonsqlite.db"  # server database file
        self.files = ["agency.txt", "calendar.txt", "routes.txt", "shapes.txt", "stop_times.txt", "stops.txt",
                      "trips.txt"]
        self.db_setup()
        #
        # # problem with trips table
        # file = "trips.csv"
        # conn = sqlite3.connect(self.db_file)
        # df = pd.read_csv(file.split('.')[0] + ".csv")  # pd reads the csv and converts it to sql
        # df.to_sql(file.split('.')[0], conn, if_exists='append', index=False)  # loads it to db file
        # conn.commit()
        # print("     ", file.split('.')[0], "imported")
        #
        #basic DB check
        tables_to_print = ["calendar", "routes", "shapes", "stop_times", "stops", "trips"]
        self.print_db_format_example(tables_to_print)

        # socket setup:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('0.0.0.0', 1973))
        server_socket.listen(3)
        print("waiting")

        while True:  # a loop that connects clients and handles them
            client_socket, address = server_socket.accept()
            t = threading.Thread(target=self.handle_client, args=(client_socket,))
            t.start()


if __name__ == '__main__':
    Moovit()
