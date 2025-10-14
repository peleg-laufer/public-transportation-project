import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import socket
import threading
from datetime import datetime
import time
import sys


def minutes_to_hours(minutes):
    """
    gets a number of minutes, returns it in hours and minutes
    :param minutes: number of minutes
    :return: [hours, minutes]
    """
    hours = int(int(minutes) / 60)
    mins = int(minutes) - (hours * 60)
    ret = [hours, mins]
    return ret


def split_trips(trip):
    """
    splits a trip
    :return:
    """
    trip.split("#")
    return trip


class Client:
    def got_city1(self):

        """
        activated when user entered a city of origin, sends a req to server for the stops in the city, and puts the
        stops in the designated combobox
        """
        if self.city_combobox1.current() != -1:  # the selected city is from the list
            try:
                self.my_socket.send(self.cities[self.city_combobox1.current()].encode())  # sending the city name
            except:
                self.city_label1['text'] = "an error occurred! no internet or servers are down, try again later"
                self.no_internet()
                return

            time.sleep(0.25)  # to let the server process the request
            # info format: stop1_name#stop1_id@stop2_name#stop2_id@...
            if self.city_combobox1.current() != -1:
                try:
                    self.stops1 = self.my_socket.recv(999999).decode().split("@")[:-1]
                except:
                    self.city_label1['text'] = "an error occurred! no internet or servers are down, try again later"
                    self.no_internet()
                    return
            temp_stops = []
            for stop in self.stops1:
                temp_stops.append(stop.split("#"))
            self.stops1 = temp_stops
            stops_names = []
            for stop in self.stops1:
                stops_names.append(stop[0])
            self.origin_combobox['values'] = stops_names  # putting the names in the combobox
            self.origin_combobox['state'] = 'normal'
            self.city_combobox1['state'] = 'disabled'
            self.city_button1['state'] = 'disabled'

        else:
            print("wrong city selected")
            self.city_label1['text'] = "choose city from options!:"

    def got_city2(self):
        """
        activated when user entered a city of destination, sends a req to server for the stops in the city, and puts
        the stops in the designated combobox
        """
        if self.city_combobox2.current() != -1:
            try:
                self.my_socket.send(self.cities[self.city_combobox2.current()].encode())  # sending the city name
            except:
                self.city_label1['text'] = "an error occurred! no internet or servers are down, try again later"
                self.no_internet()
                return

            time.sleep(0.25)  # to let the server process the request
            # info format: stop1_name#stop1_id@stop2_name#stop2_id@...
            if self.city_combobox2.current() != -1:
                try:
                    self.stops2 = self.my_socket.recv(999999).decode().split("@")[:-1]
                except:
                    self.city_label1['text'] = "an error occurred! no internet or servers are down, try again later"
                    self.no_internet()
                    return
            # splitting the ids from the names:
            temp_stops = []
            for stop in self.stops2:
                temp_stops.append(stop.split("#"))
            self.stops2 = temp_stops
            stop_names = []
            for stop in self.stops2:
                stop_names.append(stop[0])
            self.dest_combobox['values'] = stop_names
            self.dest_combobox['state'] = 'normal'
            self.city_combobox2['state'] = 'disabled'
            self.city_button2['state'] = 'disabled'
            self.stops_btn['state'] = 'normal'
        else:
            print("wrong city selected")
            self.city_label2['text'] = "choose city from options!:"

    def got_stops(self):
        """
        activated when the clients enters the origin and destination
        """
        if self.dest_combobox.current() != -1 and self.origin_combobox.current() != -1:  # checks that both are valid
            # disabling all inputs:
            self.dest_combobox['state'] = 'disabled'
            self.origin_combobox['state'] = 'disabled'
            self.stops_btn['state'] = 'disabled'
            self.wait_label.grid()
            # threading the request to keep mainloop going:
            origin_id = self.stops1[self.origin_combobox.current()][1]
            dest_id = self.stops2[self.dest_combobox.current()][1]
            print("got request", origin_id, "to", dest_id)
            t = threading.Thread(target=self.handle_user_req, args=(origin_id, dest_id,))
            t.start()
        else:
            self.origin_label['text'] = "Choose stop from options!"

    def no_internet(self):
        """
        disables all inputs except new search
        :return:
        """
        messagebox.showerror('error', 'no internet', icon='error')
        sys.exit(0)

    def handle_user_req(self, origin_id, dest_id):
        """
        handles the user request as a thread to keep mainloop looping
        :param origin_id: the id of origin stop
        :param dest_id: the id of destination stop
        """
        try:
            self.my_socket.send((origin_id + "@" + dest_id).encode())
            print("request successfully sent to server")
        except:
            self.city_label1['text'] = "an error occurred! no internet or servers are down, try again later"
            self.no_internet()
            return
        self.new_button['state'] = 'disabled'
        trips = ""
        if self.city_combobox2.current() != -1:
            try:
                print("waiting to receive trips from server'")
                trips = self.my_socket.recv(99999).decode()
                print("raw trips successfully received:", trips)
            except:
                self.city_label1['text'] = "an error occurred! no internet or servers are down, try again later"
                self.no_internet()
                return


        if trips != "no_trips_found":
            trips = trips.split("@")
            print("first split:", trips)

            i = 0
            for trip in trips:
                trips[i] = trip.split("#")
                i += 1

            print("sorted cleaned splitted trips:", trips)
            # sets the texts for trip buttons and labels:
            trip_counter = 0
            for trip in trips:
                button_text = "קו " + str(trip[4])
                print("trip button text:", button_text)
                self.trip_buttons[trip_counter]['text'] = button_text
                self.trip_buttons[trip_counter].grid()
                label_text = "דרך " + str(trip_counter+1) + ": קו " + str(trip[4]) + " של " + str(trip[3]) + ". יוצא בעוד "
                print("trip label text", label_text)
                if int(trip[5]) <= 60:
                    label_text += str(trip[5]) + " דקות מ"
                else:
                    label_text += str(minutes_to_hours(trip[5])[0]) + " שעות ו-" + str(minutes_to_hours(trip[5])[1]) +\
                                  " דקות מ"
                label_text += str(trip[1].replace('.', '')) + ". הגעה משוערת אל " + str(trip[2]) + " בעוד "
                if int(trip[6]) <= 60:
                    label_text += str(trip[6]) + " דקות"
                else:
                    label_text += str(minutes_to_hours(trip[6])[0]) + " שעות ו-" + str(minutes_to_hours(trip[6])[1]) + \
                                  " דק"
                print("finished label text:", label_text)
                self.trip_labels[trip_counter]['text'] = label_text
                trip_counter += 1

        else:  # no trips found
            self.trip_labels[0]['text'] = "לא נמצאו דרכים"
            self.trip_labels[0].grid()
        self.wait_label.grid_remove()
        self.new_button['state'] = 'enabled'

    def new_search(self):
        """
        activated when "new search" button is pressed. re runs the client
        """
        self.app.destroy()
        self.my_socket.close()
        self.__init__()

    def show_det(self, n):
        """
        show the label of the chosen trip or unshow it if it is on screen
        :param n: index number of button pressed from self.trip_buttons
        """
        if self.trip_labels_flag[n]:
            self.trip_labels[n].grid_remove()
        else:
            self.trip_labels[n].grid()
        self.trip_labels_flag[n] = not self.trip_labels_flag[n]

    def show_det0(self):
        self.show_det(0)

    def show_det1(self):
        self.show_det(1)

    def show_det2(self):
        self.show_det(2)

    def show_det3(self):
        self.show_det(3)

    def __init__(self):
        """
        the set up of the client's variables and tkinter stuff
        """
        # trying to connect until connected:
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("trying to connect...")
        while True:
            try:
                self.my_socket.connect(('127.0.0.1', 1973))
                break
            except:
                pass
        # tkinter variables setup:
        print("connected")
        self.cities = []
        self.stops1 = []
        self.stops2 = []
        self.app = tk.Tk()
        self.app.geometry('1100x450')
        self.app.wm_iconbitmap('logo.ico')
        self.app.iconbitmap("logo.ico")
        self.app.title("De Wey™")
        print("assembling tkinter")
        self.city_label1 = tk.Label(self.app, text="בחר את העיר של המקור")
        self.city_combobox1 = ttk.Combobox(self.app, values=[], width=40)
        self.city_button1 = ttk.Button(self.app, text="Enter", command=self.got_city1)
        self.origin_label = tk.Label(self.app, text="בחר את המקור")
        self.origin_combobox = ttk.Combobox(self.app, values=[], state='disabled', width=40)
        self.city_label2 = tk.Label(self.app, text="בחר את העיר של היעד")
        self.city_combobox2 = ttk.Combobox(self.app, values=[], width=40)
        self.city_button2 = ttk.Button(self.app, text="Enter", command=self.got_city2)
        self.dest_label = tk.Label(self.app, text="בחר את היעד")
        self.dest_combobox = ttk.Combobox(self.app, values=[], state='disabled', width=40)
        self.stops_btn = ttk.Button(self.app, text="Enter", command=self.got_stops, state='disabled')
        self.wait_label = tk.Label(self.app, text="...טוען (עלול לקחת 2-3 דקות)")
        print("assembling buttons")
        self.trip_buttons = [None, None, None, None]
        self.trip_buttons[0] = ttk.Button(self.app, text=0, command=lambda: self.show_det0())
        self.trip_buttons[1] = ttk.Button(self.app, text=1, command=lambda: self.show_det1())
        self.trip_buttons[2] = ttk.Button(self.app, text=2, command=lambda: self.show_det2())
        self.trip_buttons[3] = ttk.Button(self.app, text=3, command=lambda: self.show_det3())
        self.trip_labels = [None, None, None, None]
        self.trip_labels_flag = [False, False, False, False]
        for i in range(4):
            self.trip_labels[i] = tk.Label(self.app, text=i)
        self.new_button = ttk.Button(self.app, text="new search", command=self.new_search)
        self.copyright_label = tk.Label(self.app, text="Copyright © 2020 Pelegman53™. All rights preserved")
        txt = ""
        for i in range(140):
            txt += " "
        txt += " Welcome to De Wey™" + txt
        self.big_label = tk.Label(self.app, text=txt)
        print("setup finished")
        self.run_client()  # running the client after setup

    def run_client(self):
        """
        griding all tkinter objects and starting mainloop
        """

        try:
            print("getting city names from server")
            info = self.my_socket.recv(99999).decode()  # all city names from server. format: city1@city2@city3@...
            print("successfully got city names")
        except:
            self.city_label1['text'] = "an error occurred! no internet or servers are down, try again later"
            print("exceptes")
            self.no_internet()

        self.cities = info.split("@")[:-1]
        self.city_combobox1['values'] = self.cities
        self.city_combobox2['values'] = self.cities
        # gridding objects:
        self.big_label.grid(row=0, column=1)
        self.city_label1.grid(row=2, column=1)
        self.city_combobox1.grid(row=3, column=1)
        self.city_button1.grid(row=4, column=1)
        self.origin_label.grid(row=5, column=1)
        self.origin_combobox.grid(row=6, column=1)
        self.city_label2.grid(row=7, column=1)
        self.city_combobox2.grid(row=8, column=1)
        self.city_button2.grid(row=9, column=1)
        self.dest_label.grid(row=10, column=1)
        self.dest_combobox.grid(row=11, column=1)
        self.stops_btn.grid(row=13, column=1)
        self.wait_label.grid(row=14, column=1)
        for i in range(4):
            self.trip_buttons[i].grid(row=15+i, column=2)
            self.trip_labels[i].grid(row=15+i, column=1)
        self.new_button.grid(row=19, column=1)
        self.copyright_label.place(relx=0.0, rely=1.0, anchor='sw')

        for i in range(4):
            self.trip_buttons[i].grid_remove()
            self.trip_labels[i].grid_remove()
        self.wait_label.grid_remove()

        self.app.mainloop()


if __name__ == '__main__':
    Client()
