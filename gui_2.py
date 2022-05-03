import concurrent.futures
import logging
import threading
import traceback
import rx
import reactivex
from rx.scheduler import NewThreadScheduler
from threading import currentThread
import asyncio
from concurrent.futures import ProcessPoolExecutor
import datetime
import glob
import ntpath
import time
import serial.tools.list_ports
from numpy import *
from tkinter import *
from pathlib import Path
import os
from tkinter import filedialog, ttk, font
import serial
from PIL import Image, ImageTk
from serial import SerialException, PortNotOpenError


def sub_frame(field, num=1, side=TOP, expand=False, fill=None, padx=1, pady=1, last_e=True, bg=None):
    for index in range(0, num):
        field[index + 1] = [Frame(field[0], bg=bg), []]
        field.append([])
        field[index + 1][0].pack(side=side, expand=expand, fill=fill, padx=padx, pady=pady)
    field[len(field) - 2][0].pack(expand=last_e)


def switch_frame(inc, to):
    inc.pack_forget()
    to()


def _asyncio_thread(async_loop ,fun):
    # async_loop = asyncio.get_event_loop()
    async_loop.run_until_complete(fun())


def new_thread(async_loop ,fun):
    """ Button-Event-Handler starting the asyncio part. """
    threading.Thread(target=_asyncio_thread, args=(async_loop,fun,)).start()


class GUI:
    def __init__(self):
        self.pool_scheduler = NewThreadScheduler()  # thread pool with worker thread
        self.reset = True
        self.stopper = False
        self.win = Tk()
        self.win.geometry('800x600')
        self.win.minsize(800, 600)
        self.frame = Frame(self.win)
        self.frame.pack(side=BOTTOM, fill=BOTH)
        self.cwd = os.path.dirname(__file__) + '\\'
        self.img_loc = self.cwd + 'icons\\'
        self.img1 = Image.open(self.img_loc + 'sky_scanner.png')
        self.img_refresh = Image.open(self.img_loc + 'refresh.png')
        self.img_red = Image.open(self.img_loc + 'red.png')
        self.img_orange = Image.open(self.img_loc + 'warning.png')
        self.img_green = Image.open(self.img_loc + 'green.png')
        self.options1_loc = self.cwd + 'default_measurement_commands\\'
        self.options1 = []
        # self.open_def_mes()
        self.options2_loc = self.cwd + 'default_position_commands\\'
        self.options2 = []
        # self.open_def_pos()
        self.photo = ImageTk.PhotoImage(self.img1)
        self.photo_refresh = ImageTk.PhotoImage(self.img_refresh)
        self.photo_red = ImageTk.PhotoImage(self.img_red)
        self.photo_orange = ImageTk.PhotoImage(self.img_orange)
        self.photo_green = ImageTk.PhotoImage(self.img_green)
        self.gif_ref = [PhotoImage(file=self.img_loc + 'refresh_gif.gif', format=f'gif -index {i}') for i in
                        range(30)]
        self.gif_dots = [PhotoImage(file=self.img_loc + 'dots2.gif', format=f'gif -index {i}') for i in
                         range(28)]
        self.photo_polar = [PhotoImage(file=self.img_loc + f'{i}.png').subsample(2, 2) for i in range(0, 220, 30)]
        self.defaultFont = font.nametofont('TkDefaultFont')
        self.defaultFont.configure(family='Helvetica', size=18)
        self.my_head_port = None
        self.my_head_port_device = None
        self.ser_head = False
        self.my_body_port = None
        self.my_body_port_device = None
        self.ser_body = False
        self.head_found = False
        self.body_found = False
        self.file_positions_path = ''
        self.file_measurements_path = ''
        self.filename_out = ''
        self.file_settings = None
        self.positions = []
        self.commands = []
        self.continue_no = 0
        self.index = 0
        self.page = 0
        self.measure_rdy = [False, False, False]

        self.frame_menu = Frame(self.win)
        self.frames_menu = [self.frame_menu, []]
        self.frame_page1 = Frame(self.win)
        self.frames_page1 = [self.frame_page1, []]
        self.frame_page2 = Frame(self.win)
        self.frames_page2 = [self.frame_page2, []]
        self.frame_page3 = Frame(self.win)
        self.frames_page3 = [self.frame_page3, []]
        self.frame_status_1 = Frame(self.frame)
        self.frame_status_2 = Frame(self.frame)
        self.frame_nav_buttons = Frame()
        self.status_build()
        self.menu_build()
        self.lock = asyncio.Lock()
        # self.main()
        # self.menu()
        # self.loop = asyncio.get_event_loop()
        self.loop = asyncio.get_event_loop()
        # asyncio.to_thread(self.connect_body)
        # asyncio.to_thread(self.connect_head)
        # self.new_thread(self.connect_body)
        # self.new_thread(self.connect_head)



    async def start(self):
        self.menu()
        new_loop= asyncio.new_event_loop()
        new_loop2= asyncio.new_event_loop()
        new_thread(new_loop,self.connect_body)
        new_thread(new_loop2,self.connect_head)
        # await self.loop.run_in_executor(self.p,self.connect_body)
        # await asyncio.gather(asyncio.to_thread(self.connect_body), asyncio.sleep(1))
        # await asyncio.to_thread(self.connect_head)
        self.win.mainloop()

        # self.loop.run_until_complete(self.updater())
        # self.loop.run_forever()
        # return await asyncio.new_event_loop().run_until_complete(self.win.mainloop())

    # async def updater(self):
    #     while self.win.state == 'Normal':
    #         self.win.update()
    #         return self.loop



    def menu(self):
        self.page = 0
        self.frame_menu.pack(expand=True, fill=BOTH)
        self.win.wm_title('Sky_scanner: Menu')

    def menu_build(self):
        sub_frame(self.frames_menu, 1, BOTTOM, False, BOTH, 10, 10, True)
        sub_frame(self.frames_menu[1], 1, LEFT, True, BOTH, 1, 1, True)
        self.frames_menu[1][0].bind('<Configure>', self.resize_img)

        self.button_continue = Button(self.frames_menu[1][1][0], text="Continue",
                                      command=lambda: switch_frame(self.frame_menu, self.continue_menu), state=DISABLED)
        self.button_files = Button(self.frames_menu[1][1][0], text="File config",
                                   command=lambda: switch_frame(self.frame_menu, self.page1), state=DISABLED)
        self.button_settings = Button(self.frames_menu[1][1][0], text="Settings",
                                      command=lambda: switch_frame(self.frame_menu, self.page2), state=DISABLED)
        self.button_continue.pack(fill=BOTH, expand=True, pady=5)
        self.button_files.pack(fill=BOTH, expand=True, pady=5)
        self.button_settings.pack(fill=BOTH, expand=True, pady=5)

        self.label_img = Label(self.frames_menu[1][0], image=self.photo)
        self.label_img.pack(side=LEFT, fill=BOTH, expand=True)

    def status_build(self):
        self.label_head_status = Label(self.frame_status_1, image=self.photo_red)
        self.label_body_status = Label(self.frame_status_2, image=self.photo_red)
        self.label_head_status.pack(side=LEFT)
        self.label_body_status.pack(side=LEFT)
        self.label_head_com = Label(self.frame_status_1, text='Measurement head')
        self.label_body_com = Label(self.frame_status_2, text='Measurement body')
        self.label_head_com.pack(side=LEFT)
        self.label_body_com.pack(side=LEFT)
        self.button_refresh1 = Button(self.frame_status_1, image=self.photo_refresh,
                                      command=lambda: self.new_thread(self.connect_head), bd=1)
        self.button_refresh2 = Button(self.frame_status_2, image=self.photo_refresh,
                                      command=lambda: self.new_thread(self.connect_body), bd=1)
        self.frame_status_1.pack(fill=X, pady=5, padx=10)
        self.frame_status_2.pack(fill=X, pady=5, padx=10)

    def continue_menu(self):
        pass

    def page1(self):
        pass

    def page2(self):
        pass

    def page3(self):
        pass

    def gui_change(self, case, *args):
        # print("gui_status {1}: {0}, {2} ".format(currentThread(),case,time.time()))
        if case == 'CheckingH':
            self.label_head_com.config(text='Checking ' + args[0])
        elif case == 'CheckingB':
            self.label_body_com.config(text='Checking ' + args[0])
        elif case == 'FoundH':
            self.label_head_com.config(text='Measurement head found on ' + args[0])
        elif case == 'FoundB':
            self.label_body_com.config(text='iPANO mount found on ' + args[0])
        elif case == 'NotFoundH':
            self.label_head_com.config(text='Not found')
        elif case == 'NotFoundB':
            self.label_body_com.config(text='Not found')
        elif case == 'SearchH':
            self.label_head_status.config(relief='groove')
            self.new_thread(lambda: self.gif(self.gif_ref, self.label_head_status, args[0], 30))
            self.label_head_status.pack(side=LEFT)
            self.label_head_com.pack_forget()
            self.label_head_com.pack(side=LEFT)
            self.button_refresh1.pack_forget()
            self.label_head_com.config(text='Searching for the measurement head...')
        elif case == 'SearchB':
            self.label_body_status.config(relief='groove')
            self.new_thread(lambda: self.gif(self.gif_ref, self.label_body_status, args[0], 30))
            self.label_body_status.pack(side=LEFT)
            self.label_body_com.pack_forget()
            self.label_body_com.pack(side=LEFT)
            self.button_refresh2.pack_forget()
            self.label_body_com.config(text='Searching for iPANO mount...')
        elif case == 'GreenH':
            self.label_head_status.pack_forget()
            self.label_head_com.pack_forget()
            self.button_refresh1.pack_forget()
            self.label_head_status.config(relief='flat', image=self.photo_green)
            self.label_head_status.pack(side=LEFT)
            self.label_head_com.pack(side=LEFT)
        elif case == 'GreenB':
            self.label_body_status.pack_forget()
            self.label_body_com.pack_forget()
            self.button_refresh2.pack_forget()
            self.label_body_status.config(relief='flat', image=self.photo_green)
            self.label_body_status.pack(side=LEFT)
            self.label_body_com.pack(side=LEFT)
        elif case == 'RefreshH':
            self.label_head_com.pack_forget()
            self.label_head_status.pack_forget()
            self.button_refresh1.pack(side=LEFT)
            self.button_refresh1.config(relief='ridge')
            self.label_head_com.config(text='Measurement head mount not found')
            self.label_head_com.pack(side=LEFT)
        elif case == 'RefreshB':
            self.label_body_status.pack_forget()
            self.label_body_com.pack_forget()
            self.button_refresh2.pack(side=LEFT)
            self.button_refresh2.config(relief='ridge')
            self.label_body_com.config(text='iPANO mount not found')
            self.label_body_com.pack(side=LEFT)

    async def connect_head(self):
        gif_run = BooleanVar(value=True)
        gif_run.set(True)
        self.win.after(5, lambda: self.gui_change('SearchH', gif_run))
        self.head_found = False
        ports = serial.tools.list_ports.comports(include_links=False)
        if self.my_body_port is not None:
            ports.remove(self.my_body_port)
        if self.my_head_port and self.my_head_port_device:
            await self.port_head(self.my_head_port, self.my_head_port_device)
        else:
            for port in ports:
                str_port = port.description
                if str_port.find('luetooth') < 0:
                    if await self.port_head(port, port.device):
                        break
        gif_run.set(False)
        if self.head_found:
            self.win.after(50, lambda: self.gui_change('GreenH'))
            # self.reset_carousels()
            if self.page == 0:
                pass
                # self.ready_check_menu()
            elif self.page == 3:
                pass
                # self.restore_connection()
            self.frame.update()
        else:
            self.win.after(5, lambda: self.gui_change('RefreshH'))
        return True

    async def connect_body(self):
        gif_run = BooleanVar(value=True)
        gif_run.set(True)
        self.win.after(5, lambda: self.gui_change('SearchB', gif_run))
        self.body_found = False
        ports = serial.tools.list_ports.comports(include_links=False)
        if self.my_head_port:
            ports.remove(self.my_head_port)
        if self.my_body_port and self.my_body_port_device:
            await self.port_body(self.my_body_port, self.my_body_port_device)
        else:
            for port in ports:
                str_port = port.description
                if str_port.find('luetooth') < 0:
                    if await self.port_body(port, port.device):
                        break
        gif_run.set(False)
        if self.body_found:
            self.win.after(50, lambda: self.gui_change('GreenB'))
            if self.page == 0:
                # self.ready_check_menu()
                pass
            elif self.page == 3:
                # self.restore_connection()
                pass
            self.frame.update()
        else:
            self.win.after(5, lambda: self.gui_change('RefreshB'))
        return True

    async def port_head(self, port, port_device):
        self.win.after(5, lambda: self.gui_change('CheckingH', port_device))
        await self.lock.acquire()
        try:
            self.ser_head = serial.Serial(port_device, 115200, timeout=1)  # open serial port
            # rx.concat(self.ser_head).lock.acquire(blocking=True)
            time.sleep(5)  # wait for the reboot of the device
            self.ser_head.write(b'IDNXXXXX')
            s = self.ser_head.read(8)

            # rx.of(port).lock.release()
            print('head')
            if s == b'SKY-SCAN':
                self.win.after(5, lambda: self.gui_change('FoundH', port_device))
                self.my_head_port = port
                self.my_head_port_device = port_device
                self.head_found = True
                return self.head_found
        except Exception as e:
            print('HEAD: ', e)
            self.win.after(5, lambda: self.gui_change('NotFoundH', port_device))
        self.lock.release()
        if self.ser_head:
            self.ser_head.close()
        return self.head_found

    async def port_body(self, port, port_device):
        self.win.after(5, lambda: self.gui_change('CheckingB', port_device))
        await self.lock.acquire()
        try:
            # rx.Observable.pipe(port).lock.acquire(blocking=True)
            # self.lock.acquire()
            self.ser_body = serial.Serial(port_device, 115200, timeout=1)  # open serial port
            # rx.of(self.ser_head).lock.acquire(blocking=False)
            self.ser_body.write(b':01INF#')
            s = self.ser_body.read(11)
            # self.lock.release()
            # rx.of(self.ser_head).lock.release()
            print('body')
            if s == b':10INF3600#':
                self.win.after(5, lambda: self.gui_change('FoundB', port_device))
                self.my_body_port = port
                self.my_body_port_device = port_device
                self.body_found = True
                return self.body_found
        except Exception as e:
            print('BODY: ', e)
            self.win.after(5, lambda: self.gui_change('NotFoundB', port_device))
        self.lock.release()
        if self.ser_body:
            self.ser_body.close()
        return self.body_found

    def resize_img(self, event):
        width = int(event.width)
        height = int(event.height)
        if width > height:
            img1a = self.img1.resize((height, height))
        else:
            img1a = self.img1.resize((width, width))
        self.photo = ImageTk.PhotoImage(img1a)
        self.label_img.config(image=self.photo)

    def gif(self, gif_listed, label, run, inds):
        ind = 0
        while run.get():
            giff = gif_listed[ind]
            time.sleep(0.05)
            ind += 1
            if ind == inds:
                ind = 0
            label.config(image=giff)

    def new_thread(self, fun, *args):
        rx.empty(self.pool_scheduler).subscribe(on_completed=fun)

    def long_running_task(self):
        self.win.after(5, self.on_task_complete)

        print("Long_running_task: {0}".format(currentThread()))
        # your long running task here... eg:
        time.sleep(3)
        print('task complete')
        # if you want a callback on the main thread:
        self.win.after(5, self.on_task_complete)

    def on_task_complete(self):
        print("on_task_complete: {0}".format(currentThread()))
        # pass  # runs on main thread


if __name__ == "__main__":
    ui = GUI()
    asyncio.run(ui.start())
