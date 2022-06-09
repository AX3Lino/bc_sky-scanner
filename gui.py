import rx
from rx.scheduler import NewThreadScheduler
from datetime import *
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

version = 10  # "10nm" or "40nm"
debugging = False

''' create exe file with command
pyinstaller --onefile -w gui.py
move dist\gui.exe .
'''

def sub_frame(field, num, side, expand=False, fill=None, pad_x=1, pad_y=1, last_e=True, bg=None):
    for index in range(0, num):
        field[index + 1] = [Frame(field[0], bg=bg), []]
        field.append([])
        field[index + 1][0].pack(side=side, expand=expand, fill=fill, padx=pad_x, pady=pad_y)
    field[len(field) - 2][0].pack(expand=last_e)


def switch_frame(inc, to):
    inc.pack_forget()
    to()


def path_leaf(road):
    head, tail = ntpath.split(road)
    return tail or ntpath.basename(head)


def add_option(options, last):
    options.pop()
    options.append(last)
    options.append('...')


def gif(gif_listed, label, run):
    ind = 0
    while run.get():
        giff = gif_listed[ind]
        time.sleep(0.05)
        ind += 1
        if ind == 30:
            ind = 0
        label.config(image=giff)


def new_thread(fun):
    rx.empty(pool_scheduler).subscribe(on_completed=fun)


class GUI:
    def __init__(self):
        self.win = Tk()
        self.win.geometry('900x675')
        self.win.minsize(800, 600)
        self.defaultFont = font.nametofont('TkDefaultFont')
        self.defaultFont.configure(family='Helvetica', size=16)

        # make_variables
        self.reset = True
        self.stopper = False
        self.cwd = str(Path().resolve()) + '\\'
        self.my_head_port = None
        self.my_head_port_device = None
        self.ser_head = serial.Serial()
        self.my_body_port = None
        self.my_body_port_device = None
        self.ser_body = serial.Serial()
        self.head_found = False
        self.body_found = False
        self.headline = ''
        self.time = ''
        self.custom = False
        self.file_positions_path = ''
        self.file_measurements_path = ''
        self.filename_out = ''
        self.file_settings = None
        self.positions = []
        self.commands = []
        self.running_commands = []
        self.value_list = []
        self.reset_ok = False
        self.times = 0
        self.paused_time = 0
        self.continuing = False
        self.continue_no = 0
        self.index = 0
        self.page = 0
        self.measure_rdy = [False, False, False]

        # load_files
        self.img_loc = self.cwd + 'icons\\'
        self.img1 = Image.open(self.img_loc + 'sky_scanner.png')
        self.img1a = self.img1
        self.img_refresh = Image.open(self.img_loc + 'refresh.png')
        self.img_red = Image.open(self.img_loc + 'red.png')
        self.img_orange = Image.open(self.img_loc + 'warning.png')
        self.img_green = Image.open(self.img_loc + 'green.png')
        self.options1_loc = self.cwd + 'default_measurement_commands\\'
        self.options1 = []
        self.open_def_mes()
        self.options2_loc = self.cwd + 'default_position_commands\\'
        self.options2 = []
        self.open_def_pos()
        self.photo = ImageTk.PhotoImage(self.img1)
        self.photo_refresh = ImageTk.PhotoImage(self.img_refresh)
        self.photo_red = ImageTk.PhotoImage(self.img_red)
        self.photo_orange = ImageTk.PhotoImage(self.img_orange)
        self.photo_green = ImageTk.PhotoImage(self.img_green)
        self.gif_ref = [PhotoImage(file=self.img_loc + 'refresh_gif.gif', format=f'gif -index {i}') for i in range(30)]
        self.gif_dots = [PhotoImage(file=self.img_loc + 'dots4.gif', format=f'gif -index {i + 1}') for i in range(30)]
        self.photo_polar = [PhotoImage(file=self.img_loc + f'{i}.png').subsample(2, 2) for i in range(0, 220, 30)]

        # build_frames
        self.frame = Frame(self.win)
        self.frame.pack(side=BOTTOM, fill=BOTH)
        self.frame_status_1 = Frame(self.frame)
        self.frame_status_2 = Frame(self.frame)
        self.frame_nav_buttons = Frame()
        self.frame_menu = Frame(self.win)
        self.frames_menu = [self.frame_menu, []]
        self.frame_page1 = Frame(self.win)
        self.frames_page1 = [self.frame_page1, []]
        self.frame_page2 = Frame(self.win)
        self.frames_page2 = [self.frame_page2, []]
        self.frame_page3 = Frame(self.win)
        self.frames_page3 = [self.frame_page3, []]
        self.frame_page4 = Frame(self.win)
        self.frames_page4 = [self.frame_page4, []]

        # build_sub-frames
        sub_frame(self.frames_menu, 1, BOTTOM, False, BOTH, 10, 10, True)
        sub_frame(self.frames_menu[1], 1, LEFT, True, BOTH, 1, 1, True)
        sub_frame(self.frames_page1, 4, TOP, True, BOTH, 10, 10, True)
        sub_frame(self.frames_page1[1], 4, TOP, False, BOTH, 10, 1, True)
        sub_frame(self.frames_page1[2], 4, TOP, False, BOTH, 10, 1, True)
        sub_frame(self.frames_page1[3], 3, TOP, False, BOTH, 10, 1, True)
        sub_frame(self.frames_page1[4], 3, TOP, False, BOTH, 10, 1, True)
        sub_frame(self.frames_page2, 7, TOP, True, BOTH, 10, 1, True)
        for i in range(7):
            sub_frame(self.frames_page2[i + 1], 3, TOP, False, BOTH, 1, 1, True)
        sub_frame(self.frames_page2[3][1], 2, LEFT, True, BOTH)
        sub_frame(self.frames_page2[3][2], 2, LEFT, True, BOTH)
        sub_frame(self.frames_page3, 4, TOP, True, BOTH, 10, 1, True)
        sub_frame(self.frames_page4, 2, TOP, False, BOTH, 10, 10, True)

        # status_build
        self.label_head_status = Label(self.frame_status_1, image=self.photo_red)
        self.label_body_status = Label(self.frame_status_2, image=self.photo_red)
        self.label_head_com = Label(self.frame_status_1, text='Measurement head')
        self.label_body_com = Label(self.frame_status_2, text='Measurement body')
        self.button_refresh1 = Button(self.frame_status_1, image=self.photo_refresh,
                                      command=lambda: new_thread(self.connect_head), bd=1)
        self.button_refresh2 = Button(self.frame_status_2, image=self.photo_refresh,
                                      command=lambda: new_thread(self.connect_body), bd=1)
        self.status_build()

        # menu_build
        self.button_continue = Button(self.frames_menu[1][1][0], text="Continue",
                                      command=lambda: switch_frame(self.frame_menu, self.continue_menu), state=DISABLED)
        self.button_files = Button(self.frames_menu[1][1][0], text="File configuration",
                                   command=lambda: switch_frame(self.frame_menu, self.page1), state=DISABLED)
        self.button_settings = Button(self.frames_menu[1][1][0], text="Settings",
                                      command=lambda: switch_frame(self.frame_menu, self.page2), state=DISABLED)
        self.label_img = Label(self.frames_menu[1][0], image=self.photo)
        self.menu_build()

        # page1_build
        self.label_meas_file_resB = Label(self.frames_page1[1][2][0], image=self.photo_red)
        self.combo_p2_a = ttk.Combobox(self.frames_page1[1][2][0], values=self.options1, state="readonly",
                                       width=len(max(self.options1)) + 5)
        self.label_meas_file_resA = Label(self.frames_page1[1][3][0], text='', font=10)
        self.label_pos_file_resB = Label(self.frames_page1[2][2][0], image=self.photo_red)
        self.combo_p2_b = ttk.Combobox(self.frames_page1[2][2][0], values=self.options2, state="readonly",
                                       width=len(max(self.options2)) + 5)
        self.label_pos_file_resA = Label(self.frames_page1[2][3][0], text='', font=10)
        self.label_output_file_path = StringVar()
        self.entry1 = Entry(self.frames_page1[3][2][0], state="readonly", bd=0,
                            textvariable=self.label_output_file_path)
        self.time = str(date.today()) + '_' + str(datetime.now().hour) + '-' + str(datetime.now().minute)
        self.output_file_name = StringVar()
        self.entry2 = Entry(self.frames_page1[3][2][0], textvariable=self.output_file_name)
        self.button_measure_p1 = Button(self.frames_page1[4][0], text='Start measurement', state=DISABLED,
                                        command=lambda: switch_frame(self.frame_page1, self.page3))
        self.page1_build()

        # page2_build
        self.var_p = StringVar()
        self.var_f = StringVar()
        self.voltage = DoubleVar()
        self.num_mes = IntVar()
        self.tp = DoubleVar()
        self.button_measure_p2 = Button(self.frames_page2[7][2][0], text='Start measurement', state=DISABLED,
                                        command=lambda: switch_frame(self.frame_page2, self.page3))
        self.page2_build()

        # page3_build
        self.est_time_var = StringVar()
        self.label_time = Label(self.frames_page3[2][0], text='Estimated time: ')
        self.label_time1 = Label(self.frames_page3[2][0], textvariable=self.est_time_var)
        self.canvas_width = self.canvas_height = 400
        self.canvas = Canvas(self.frames_page3[3][0], width=self.canvas_width, height=self.canvas_height)
        self.page3_build()

        # page4_build
        self.label_end_status = Label(self.frames_page4[1][0])
        self.page4_build()

        new_thread(self.menu)
        new_thread(self.connect_body)
        new_thread(self.connect_head)

    def status_build(self):
        self.button_refresh1.pack(side=LEFT)
        self.button_refresh2.pack(side=LEFT)
        self.label_head_com.pack(side=LEFT)
        self.label_body_com.pack(side=LEFT)
        self.frame_status_1.pack(fill=X, pady=5, padx=10)
        self.frame_status_2.pack(fill=X, pady=5, padx=10)

    def menu_build(self):
        self.frames_menu[1][0].bind('<Configure>', self.resize_img)
        self.button_continue.pack(fill=BOTH, expand=True, pady=5)
        self.button_files.pack(fill=BOTH, expand=True, pady=5)
        self.button_settings.pack(fill=BOTH, expand=True, pady=5)
        self.label_img.pack(side=LEFT, fill=BOTH, expand=True)

    def page1_build(self):
        label1 = Label(self.frames_page1[1][1][0], text='Measurement commands:')
        self.combo_p2_a.bind("<<ComboboxSelected>>", self.selection_head_commands)
        self.combo_p2_a.set('Select...')
        label1.pack(side=LEFT)
        self.label_meas_file_resB.pack(side=LEFT)
        self.combo_p2_a.pack(side=LEFT)
        self.label_meas_file_resA.pack(side=LEFT)

        label2 = Label(self.frames_page1[2][1][0], text='Position commands:')
        self.combo_p2_b.bind("<<ComboboxSelected>>", self.selection_body_commands)
        self.combo_p2_b.set('Select...')

        label2.pack(side=LEFT)
        self.label_pos_file_resB.pack(side=LEFT)
        self.combo_p2_b.pack(side=LEFT)
        self.label_pos_file_resA.pack(side=LEFT)

        label4 = Label(self.frames_page1[3][1][0], text='Output file')
        button1 = Button(self.frames_page1[3][2][0], text='Browse', command=self.chose_output_file, font='10')

        self.label_output_file_path.set(self.cwd)

        self.output_file_name.set('Output_' + self.time + '.txt')
        self.filename_out = self.cwd + self.output_file_name.get()
        self.entry1.config(width=len(self.label_output_file_path.get()) + 5)
        self.entry2.config(width=len(self.output_file_name.get()) + 5)
        self.entry2.bind('<KeyPress>', self.resize_entry2)
        self.entry2.bind('<KeyRelease>', self.resize_entry2)
        label4.pack(side=LEFT)
        button1.pack(side=RIGHT)
        self.entry1.pack(side=LEFT)
        self.entry2.pack(side=LEFT)

        button_settings = Button(self.frames_page1[4][0], text='Settings',
                                 command=lambda: switch_frame(self.frame_page1, self.page2))

        button_menu = Button(self.frames_page1[4][0], text='Menu',
                             command=lambda: switch_frame(self.frame_page1, self.menu))
        button_menu.pack(side=LEFT)
        self.button_measure_p1.pack(side=RIGHT)
        button_settings.pack(side=RIGHT)

    def page2_build(self):
        label1 = Label(self.frames_page2[1][1][0], text='Set polarization filter:')
        label1.pack(side=LEFT)

        self.var_p.set('SFL000XX')
        polarization_buttons = []
        options_polar = [('close', 'SFL000XX', self.photo_polar[6]), ('0°', 'SFL001XX', self.photo_polar[0]),
                         ('30°', 'SFL002XX', self.photo_polar[1]), ('60°', 'SFL003XX', self.photo_polar[2]),
                         ('90°', 'SFL007XX', self.photo_polar[3]), ('120°', 'SFL008XX', self.photo_polar[4]),
                         ('150°', 'SFL009XX', self.photo_polar[5]), ('open', 'SFL006XX', self.photo_polar[7])]
        for count, item in enumerate(options_polar):
            polarization_buttons.append(
                Radiobutton(self.frames_page2[1][2][0], text=item[0], variable=self.var_p, value=item[1], image=item[2],
                            compound=CENTER, fg='black',
                            command=lambda: new_thread(lambda: self.setup_command(self.var_p.get())),
                            indicatoron=False, width=37, font=10, bg='white'))
            polarization_buttons[count].pack(side=LEFT, padx=3)
        polarization_buttons[0].config(fg='white', bg='grey', selectcolor='grey')
        polarization_buttons[-1].config(bg='white')

        label2 = Label(self.frames_page2[2][1][0], text='Set color filter [nm]:')
        label2.pack(side=LEFT)

        self.var_f.set('SFL100XX')
        filter_buttons = []
        if version == 40:
            options_color = [('close', 'SFL100XX', 'grey'),
                             ('400', 'SFL101XX', '#8300b5'),
                             ('450', 'SFL102XX', '#0046ff'),
                             ('500', 'SFL103XX', '#00ff92'),
                             ('550', 'SFL104XX', '#a3ff00'),
                             ('600', 'SFL105XX', '#ffbe00'),
                             ('650', 'SFL107XX', '#ff0000'),
                             ('700', 'SFL108XX', '#F10000'),
                             ('750', 'SFL109XX', '#a10000'),
                             ('800', 'SFL110XX', '#610000'),
                             ('850', 'SFL111XX', '#401010'),
                             ('open', 'SFL106XX', '#FFFFFF')]
        else:
            options_color = [('close', 'SFL100XX', 'grey'),
                             ('350', 'SFL101XX', '#430065'),
                             ('400', 'SFL102XX', '#8300b5'),
                             ('450', 'SFL103XX', '#0046ff'),
                             ('500', 'SFL104XX', '#00ff92'),
                             ('550', 'SFL105XX', '#a3ff00'),
                             ('600', 'SFL107XX', '#ffbe00'),
                             ('650', 'SFL108XX', '#ff0000'),
                             ('700', 'SFL109XX', '#F10000'),
                             ('750', 'SFL110XX', '#a10000'),
                             ('800', 'SFL111XX', '#610000'),
                             ('open', 'SFL106XX', '#FFFFFF')]
        for count, item in enumerate(options_color):
            filter_buttons.append(
                Radiobutton(self.frames_page2[2][2][0], text=item[0], variable=self.var_f, value=item[1],
                            command=lambda: new_thread(lambda: self.setup_command(self.var_f.get())),
                            indicatoron=False, width=5, font=10, bg=item[2], fg='white',
                            selectcolor=item[2]))
            filter_buttons[count].pack(side=LEFT, fill=BOTH, padx=3)
        filter_buttons[-1].config(fg='black')

        label3 = Label(self.frames_page2[3][1][1][0], text='Get carousel:')
        label3a = Label(self.frames_page2[3][1][2][0], text='Reset carousel:')
        label3.pack(side=LEFT)
        label3a.pack(side=LEFT)
        get_c0_button = Button(self.frames_page2[3][2][1][0], text='Get carousel 0', font=10,
                               command=lambda: new_thread(lambda: self.setup_command('GFL0XXXX')))
        get_c1_button = Button(self.frames_page2[3][2][1][0], text='Get carousel 1', font=10,
                               command=lambda: new_thread(lambda: self.setup_command('GFL1XXXX')))
        reset_c0_button = Button(self.frames_page2[3][2][2][0], text='Reset carousel 0', font=10,
                                 command=lambda: new_thread(lambda: self.setup_command('RFL0XXXX')))
        reset_c1_button = Button(self.frames_page2[3][2][2][0], text='Reset carousel 1', font=10,
                                 command=lambda: new_thread(lambda: self.setup_command('RFL1XXXX')))
        get_c0_button.pack(side=LEFT)
        get_c1_button.pack(side=LEFT, padx=10)
        reset_c0_button.pack(side=LEFT, padx=10)
        reset_c1_button.pack(side=LEFT)

        label4 = Label(self.frames_page2[4][1][0], text='Voltage control [V]:')

        self.voltage.set(0.4)
        scale1 = Scale(self.frames_page2[4][2][0], variable=self.voltage, from_=0.4, to=1.1, resolution=0.001,
                       orient=HORIZONTAL, showvalue=False)
        spinbox1 = Spinbox(self.frames_page2[4][2][0], from_=0.4, to=1.1, width=6, font=15, textvariable=self.voltage,
                           increment=0.001, justify=RIGHT)
        voltage_set_button = Button(self.frames_page2[4][2][0], text='Set', font=10,
                                    command=lambda: new_thread(lambda: self.setup_command
                                    ('SCV' + str("%0.4f" % self.voltage.get()).replace('.', ''))))
        voltage_get_button = Button(self.frames_page2[4][2][0], text='Get control voltage', font=10,
                                    command=lambda: new_thread(lambda: self.setup_command('GCVXXXXX')))
        voltage_now_button = Button(self.frames_page2[4][2][0], text='Get signal voltage', font=10,
                                    command=lambda: new_thread(lambda: self.setup_command('GSVXXXXX')))
        label4.pack(side=LEFT)
        voltage_set_button.pack(side=LEFT)
        spinbox1.pack(side=LEFT, padx=10)
        scale1.pack(side=LEFT, expand=True, fill=X)
        voltage_now_button.pack(side=RIGHT)
        voltage_get_button.pack(side=RIGHT, padx=10)

        label5 = Label(self.frames_page2[5][1][0], text='Number of measurements averaged:')

        self.num_mes.set(100)
        scale2 = Scale(variable=self.num_mes, from_=1, to=99999, resolution=1)
        spinbox2 = Spinbox(self.frames_page2[5][2][0], from_=1, to=99999, increment=10, textvariable=self.num_mes,
                           font=15,
                           width=6, justify=RIGHT)
        num_mes_set_button = Button(self.frames_page2[5][2][0], text='Set', font=10,
                                    command=lambda: new_thread(lambda: self.setup_command
                                    ('SNM' + str("%0.4f" % (float(self.num_mes.get()) / 10000)).replace('.', ''))))
        num_mes_get_button = Button(self.frames_page2[5][2][0], text='Get number of measurements', font=10,
                                    command=lambda: new_thread(lambda: self.setup_command('GNMXXXXX')))
        num_mes_set_button.pack(side=LEFT)
        label5.pack(side=LEFT)
        spinbox2.pack(side=LEFT, padx=10)
        num_mes_get_button.pack(side=RIGHT)

        label6 = Label(self.frames_page2[6][1][0], text='Min temperature [°C]:')

        self.tp.set(5)
        scale3 = Scale(self.frames_page2[6][2][0], variable=self.tp, from_=5, to=30, resolution=0.1,
                       orient=HORIZONTAL, showvalue=False)
        spinbox3 = Spinbox(self.frames_page2[6][2][0], from_=5, to=30, increment=0.1, textvariable=self.tp, font=15,
                           width=5,
                           justify=RIGHT)
        temp_set_button = Button(self.frames_page2[6][2][0], text='Set', font=10,
                                 command=lambda: new_thread(lambda: self.setup_command
                                 ('STP+' + str("%0.3f" % (float(self.tp.get()) / 100)).replace('.', ''))))
        temp_get_button = Button(self.frames_page2[6][2][0], text='Get temperature', font=10,
                                 command=lambda: new_thread(lambda: self.setup_command('GTPXXXXX')))
        label6.pack(side=LEFT)
        temp_set_button.pack(side=LEFT)
        spinbox3.pack(side=LEFT, padx=10)
        scale3.pack(side=LEFT, expand=True, fill=X)
        temp_get_button.pack(side=RIGHT)

        self.frames_page2[7][0] = self.frame_status_1

        button_menu = Button(self.frames_page2[7][2][0], text='Menu',
                             command=lambda: switch_frame(self.frame_page2, self.menu))
        button_files = Button(self.frames_page2[7][2][0], text='File configuration',
                              command=lambda: switch_frame(self.frame_page2, self.page1))
        button_menu.pack(side=LEFT)
        self.button_measure_p2.pack(side=RIGHT)
        button_files.pack(side=RIGHT)
        self.buttons_p2 = [polarization_buttons, filter_buttons, get_c0_button, get_c1_button, reset_c0_button,
                           reset_c1_button, voltage_get_button, voltage_set_button, voltage_now_button,
                           num_mes_get_button, num_mes_set_button, temp_get_button, temp_set_button, button_menu,
                           button_files]

    def page3_build(self):
        label1 = Label(self.frames_page3[1][0], text='page3')
        label1.pack()
        self.label_time.pack(side=LEFT)
        self.label_time1.pack(side=LEFT)
        self.canvas.pack()
        self.win.bind('<Control_L>', self.stop)
        self.win.bind('<Shift_L>', self.resume)

    def page4_build(self):
        self.label_end_status.pack()
        button_menu = Button(self.frames_page4[2][0], text='Menu',
                             command=lambda: new_thread(lambda: self.page4_end(1)))
        button_close = Button(self.frames_page4[2][0], text='Close',
                              command=lambda: new_thread(lambda: self.page4_end(0)))
        button_menu.pack(side=LEFT)
        button_close.pack(side=RIGHT)

    def open_def_mes(self):
        temp = glob.glob(self.options1_loc + '/*.txt')
        for i in temp:
            self.options1.append(path_leaf(i))
        self.options1.append('...')

    def open_def_pos(self):
        temp = glob.glob(self.options2_loc + '/*.txt')
        for i in temp:
            self.options2.append(path_leaf(i))
        self.options2.append('...')

    def menu(self):
        self.page = 0
        self.frame_menu.pack(expand=True, fill=BOTH)
        self.win.wm_title('Sky_scanner: Menu')

    def continue_menu(self):
        self.continuing = True
        self.page3()

    def page1(self):
        self.page = 1
        self.frame_page1.pack(expand=True, fill=BOTH)
        self.win.wm_title('Sky_scanner: File configuration')
        if not self.custom:
            self.time = str(date.today()) + '_' + str(datetime.now().hour) + '-' + str(datetime.now().minute)
            self.output_file_name.set('Output_' + self.time + '.txt')
            self.filename_out = self.cwd + self.output_file_name.get()
        self.ready_check_measure()

    def page2(self):
        self.page = 2
        self.frame_page2.pack(expand=True, fill=BOTH)
        self.win.wm_title('Sky_scanner: Settings')
        self.measure_rdy[2] = True
        if self.head_found:
            self.label_head_status.config(image=self.photo_green)
        else:
            self.win.after(50, lambda: self.gui_change('RefreshH'))
        self.ready_check_measure()

    def page3(self):
        self.win.wm_title('Sky_scanner: Measurement')
        self.page = 3
        self.frame_page3.pack(expand=True, fill=BOTH)

        self.canvas.delete('all')
        self.frame.update()
        new_thread(self.create_coordinates)
        if self.continuing:
            new_thread(self.read_running)
        else:
            self.file_settings = open(self.cwd + 'running_commands.txt', 'w')
            self.file_settings.write(self.var_p.get() + '\n')
            self.file_settings.write(self.var_f.get() + '\n')
            self.file_settings.write('SCV' + str("%0.4f" % self.voltage.get()).replace('.', '') + '\n')
            self.file_settings.write('SNM' + str("%0.4f" % (float(self.num_mes.get()) / 10000)).replace('.', '') + '\n')
            self.file_settings.write('STP+' + str("%0.3f" % (float(self.tp.get()) / 100)).replace('.', '') + '\n')
            self.file_settings.close()
            fileout = open(self.filename_out, "w")  # clears / create new file
            fileout.write('z.angle' + '\t' + 'azimuth' + '\t' + '%s\n' % self.headline)
            fileout.close()
            file = open(self.cwd + 'running.txt', 'w')
            file.write(self.file_positions_path + '\n')
            file.write(self.file_measurements_path + '\n')
            file.write(self.filename_out + '\n')
            file.write(str(self.index) + '\n')
            new_thread(self.measure)

    def page4(self):
        self.win.wm_title('Sky_scanner: Final screen')
        self.frame_page4.pack(expand=True, fill=BOTH)
        self.page = 4
        if self.reset_ok:
            self.label_end_status.config(text='Measurement successful')
        else:
            self.label_end_status.config(text='Measurement failed')

    def page4_end(self, button):
        if button:
            self.ready_check_menu()
            self.running_commands.clear()
            self.value_list.clear()
            self.times = 0
            self.paused_time = 0
            self.continuing = False
            self.continue_no = 0
            self.index = 0
            self.custom = False
            self.time = str(date.today()) + '_' + str(datetime.now().hour) + '-' + str(datetime.now().minute)
            switch_frame(self.frame_page4, self.menu)
        else:
            self.win.destroy()

    def gui_change(self, case, *args):
        if case == 'TextH':
            self.label_head_com.config(text=args[0])
        elif case == 'TextB':
            self.label_body_com.config(text=args[0])
        elif case == 'SearchH':
            self.label_head_status.config(relief='groove')
            new_thread(lambda: gif(self.gif_ref, self.label_head_status, args[0]))
            self.label_head_status.pack(side=LEFT)
            self.label_head_com.pack_forget()
            self.label_head_com.pack(side=LEFT)
            self.button_refresh1.pack_forget()
            self.label_head_com.config(text='Searching for the measurement head...')
        elif case == 'SearchB':
            self.label_body_status.config(relief='groove')
            new_thread(lambda: gif(self.gif_ref, self.label_body_status, args[0]))
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
        elif case == 'MenuRdy':
            self.button_settings.config(state=NORMAL)
            self.button_files.config(state=NORMAL)
        elif case == 'ContinueRdy':
            self.button_continue.config(state=NORMAL)
        elif case == 'ContinueNoRdy':
            self.button_continue.config(state=DISABLED)
        elif case == 'Combo_p2_a':
            self.combo_p2_a.config(values=args[0])
            self.combo_p2_a.config(width=args[1])
        elif case == 'Combo_p2_b':
            self.combo_p2_b.config(values=args[0])
            self.combo_p2_b.config(width=args[1])
        elif case == 'MeasureRdy':
            self.button_measure_p1.config(state=args[0])
            self.button_measure_p2.config(state=args[0])
        elif case == 'Paused':
            self.est_time_var.set('Paused')
        elif case == 'WorkingH':
            new_thread(lambda: gif(self.gif_dots, self.label_head_status, args[0]))
        elif case == 'WorkingB':
            new_thread(lambda: gif(self.gif_dots, self.label_body_status, args[0]))
        elif case == 'SetH':
            self.label_head_com.config(text=args[0])
            self.label_head_com.config(relief=FLAT)
            self.label_head_status.config(image=self.photo_green)
        elif case == 'SetB':
            self.label_body_com.config(text=args[0])
            self.label_body_status.config(image=self.photo_green)
        elif case == 'WarningH':
            self.label_head_com.config(text=args[0])
            self.label_head_status.config(image=self.photo_orange)
        elif case == 'ReadPosFile':
            self.label_pos_file_resB.config(text=args[0])
            self.label_pos_file_resB.config(image=args[1])
        elif case == 'ReadMesFile':
            self.label_meas_file_resA.config(text=args[0])
            self.label_meas_file_resB.config(image=args[1])
        elif case == 'OutputFile':
            self.entry2.delete(0, END)
            self.entry2.insert(0, path_leaf(self.filename_out))
            self.label_output_file_path.set(str(Path(self.filename_out).parent.absolute()) + '\\')
            self.entry1.config(width=args[0])
            self.entry2.config(width=args[1])
            self.entry1.pack(side=LEFT)
            self.entry2.pack(side=LEFT)
        else:
            print("PEPEGA: ", case)

    def connect_head(self):
        gif_run = BooleanVar(value=True)
        self.win.after(50, lambda: self.gui_change('SearchH', gif_run))
        self.head_found = False
        ports = serial.tools.list_ports.comports(include_links=False)
        if self.my_body_port is not None:
            ports.remove(self.my_body_port)
        if self.my_head_port and self.my_head_port_device:
            self.port_head(self.my_head_port, self.my_head_port_device)
        else:
            for port in ports:
                str_port = port.description
                if str_port.find('luetooth') < 0:
                    if self.port_head(port, port.device):
                        break
        gif_run.set(False)
        time.sleep(0.1)
        if self.head_found:
            self.reset_carousels()
            if self.page == 0:
                self.ready_check_menu()
            elif self.page == 3:
                self.restore_connection()
            self.frame.update()
        else:
            self.win.after(50, lambda: self.gui_change('RefreshH'))

    def connect_body(self):
        gif_run = BooleanVar(value=True)
        self.win.after(50, lambda: self.gui_change('SearchB', gif_run))
        self.body_found = False
        ports = serial.tools.list_ports.comports(include_links=False)
        if self.my_head_port:
            ports.remove(self.my_head_port)
        if self.my_body_port and self.my_body_port_device:
            self.port_body(self.my_body_port, self.my_body_port_device)
        else:
            for port in ports:
                str_port = port.description
                if str_port.find('luetooth') < 0:
                    if self.port_body(port, port.device):
                        break
        gif_run.set(False)
        time.sleep(0.1)
        if self.body_found:
            self.win.after(50, lambda: self.gui_change('GreenB'))
            if self.page == 0:
                self.ready_check_menu()
            elif self.page == 3:
                self.restore_connection()
            self.frame.update()
        else:
            self.win.after(50, lambda: self.gui_change('RefreshB'))
            if debugging:
                self.win.after(50, lambda: self.gui_change('MenuRdy'))  # testing purposes

    def port_head(self, port, port_device):
        try:
            self.win.after(50, lambda: self.gui_change('TextH', 'Checking ' + port_device))
            time.sleep(3)
            self.ser_head = serial.Serial(port_device, 115200, timeout=1)  # open serial port
            time.sleep(5)  # wait for the reboot of the device
            self.ser_head.write(b'IDNXXXXX')
            s = self.ser_head.read(8)
            if s == b'SKY-SCAN':
                self.win.after(50, lambda: self.gui_change('TextH', 'Measurement head found on ' + port_device))
                self.my_head_port = port
                self.my_head_port_device = port_device
                self.head_found = True
                return self.head_found
        except Exception as ex:
            print(ex)
            self.win.after(50, lambda: self.gui_change('TextH', 'Not found'))
        if self.ser_head:
            self.ser_head.close()
        return self.head_found

    def port_body(self, port, port_device):
        try:
            self.win.after(50, lambda: self.gui_change('TextB', 'Checking ' + port_device))
            self.ser_body = serial.Serial(port_device, 115200, timeout=1)  # open serial port
            self.ser_body.write(b':01INF#')
            s = self.ser_body.read(11)
            if s == b':10INF3600#':
                self.win.after(50, lambda: self.gui_change('TextB', 'iPANO mount found on ' + port_device))
                self.my_body_port = port
                self.my_body_port_device = port_device
                self.body_found = True
                return self.body_found
        except Exception as ex:
            print(ex)
            self.win.after(50, lambda: self.gui_change('TextB', 'Not found'))
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

    def ready_check_menu(self):
        if self.head_found and self.body_found:
            self.win.after(50, lambda: self.gui_change('MenuRdy'))
            if os.path.isfile(self.cwd + 'running.txt'):
                self.win.after(50, lambda: self.gui_change('ContinueRdy'))
            else:
                self.win.after(50, lambda: self.gui_change('ContinueNoRdy'))

    def read_running(self):
        file_run = open(self.cwd + "running.txt", "r")
        self.file_positions_path = file_run.readline().strip()
        self.read_position_fail()
        self.combo_p2_a.set(path_leaf(self.file_measurements_path))
        self.file_measurements_path = file_run.readline().strip()
        self.read_measurement_fail()
        self.combo_p2_b.set(path_leaf(self.file_positions_path))
        self.filename_out = file_run.readline().strip()
        self.continue_no = int(file_run.readline().strip())
        file_run.close()
        self.read_running_commands()
        self.measure()

    def read_running_commands(self):
        file = open(self.cwd + 'running_commands.txt', 'r')
        command = file.readline().strip()
        while command != '':
            self.running_commands.append(command)
            self.head_communicate(command)
            command = file.readline().strip()
        self.command_to_var()
        file.close()

    def command_to_var(self):
        self.var_p.set(self.running_commands[0])
        self.var_f.set(self.running_commands[1])
        self.voltage.set(int(self.running_commands[2][3:]) / 1000)
        self.num_mes.set(int(self.running_commands[3][3:]))
        self.tp.set(int(self.running_commands[4][3:]) / 10)

    def ready_check_measure(self):
        if debugging:
            self.win.after(50, lambda: self.gui_change('MeasureRdy', NORMAL))
            return True
        for i in self.measure_rdy:
            if not i:
                self.win.after(50, lambda: self.gui_change('MeasureRdy', DISABLED))
                return False
            self.win.after(50, lambda: self.gui_change('MeasureRdy', NORMAL))
        return True

    def measure(self):
        self.stopper = False
        first = True
        first_time = 0
        countdown = False
        for (height, azimuth) in self.positions:
            if self.index < self.continue_no:
                self.index += 1
                continue
            if first:
                self.est_time_var.set('Calculating...')
                first_time = time.time()
            else:
                self.estimate_time(first_time, countdown)
                countdown = True
            first = False
            buf = -1
            while buf == -1:
                self.set_ipano_position(height, azimuth)
                buf = self.measure_head('%.2f\t%.2f\t' % (90.0 - height, azimuth))
                if self.stopper:  # check for key pressed
                    buf = -1  # to restart last measurement
                    self.win.after(50, lambda: self.gui_change('Paused'))
                    while self.stopper:  # loop until problem is solved
                        time.sleep(1)
            self.create_dot(height, azimuth, average(self.value_list))
            buf = buf + '\n'
            fileout = open(self.filename_out, "a")
            fileout.write(buf)
            fileout.close()
            self.index += 1
            file = open(self.cwd + 'running.txt', 'w')
            file.write(self.file_positions_path + '\n')
            file.write(self.file_measurements_path + '\n')
            file.write(self.filename_out + '\n')
            file.write(str(self.index) + '\n')
            file.close()
        self.finish_measurement()

    def stop(self, event):
        self.stopper = True

    def resume(self, event):
        self.stopper = False

    def measure_head(self, buf):
        for command in self.commands:
            if self.stopper:  # check for key pressed: loop until another key pressed
                self.win.after(50, lambda: self.gui_change('Paused'))
                while self.stopper:
                    time.sleep(1)
            answer = self.head_communicate(command)
            if answer == 'Error':
                break
            if answer.find('SVT') == 0:
                value = int(answer[3:8])
                value = value / 10000
                self.value_list.append(value)
                buf = buf + '%.4f\t' % value
        return buf

    def set_ipano_position(self, height, azimuth):
        gif_run = BooleanVar(value=True)
        try:
            command = ':01SSL+%s%s#' % (str(int(100 * height)).zfill(5), str(int(100 * azimuth)).zfill(5))
            command = command.encode()  # prerobit na postupnot 8-bit znakov
            self.win.after(50, lambda: self.gui_change('WorkingB', gif_run))
            self.ser_body.write(command)  # move to the given position
            self.ser_body.read(19)  # odpoveď
            time.sleep(0.1)  # aby sa montáž stihla rozbehnúť
            gif_run.set(False)
            self.ser_body.write(b':01GAS#')  # get current position and state
            answer = self.ser_body.read(19)
            while answer[17] == ord('1'):  # kód jednotky - je v pohybe
                self.ser_body.write(b':01GAS#')  # get current position and state
                answer = self.ser_body.read(19)
            self.win.after(50, lambda: self.gui_change('SetB',
                                                       'Height: ' + str(height) + ' Azimuth: ' + str(azimuth) + ' set'))
            return answer.decode
        except PortNotOpenError:
            print('port not open')
            gif_run.set(False)
            self.body_found = False
            self.win.after(50, lambda: self.gui_change('RefreshB'))
            self.stopper = True
        except Exception as ex:
            print(ex)
            print('body discnected')
            gif_run.set(False)
            self.body_found = False
            self.ser_body.close()
            self.win.after(50, lambda: self.gui_change('RefreshB'))
            self.stopper = True

    def create_coordinates(self):
        for i in range(10, 100, 10):
            r = cos(i * pi / 180) * self.canvas_height / 2
            x0 = self.canvas_width / 2 + r
            x1 = self.canvas_width / 2 - r
            y0 = self.canvas_height / 2 + r
            y1 = self.canvas_height / 2 - r
            self.win.after(50, self.draw(x0, y0, x1, y1))

    def create_dot(self, x_cor, y_cor, buf):
        diam = self.canvas.winfo_width() / 200
        safe_y = self.canvas.winfo_height() - 2 * diam
        safe_x = self.canvas.winfo_width() - 2 * diam
        r = cos(x_cor * pi / 180) * safe_y / 2
        x0 = safe_x / 2 + r * cos((y_cor - 90) * pi / 180) - diam
        x1 = safe_x / 2 + r * cos((y_cor - 90) * pi / 180) + diam
        y0 = safe_y / 2 + r * sin((y_cor - 90) * pi / 180) - diam
        y1 = safe_y / 2 + r * sin((y_cor - 90) * pi / 180) + diam
        hex_color = "#%6.6X" % int(buf * 4194303)
        self.win.after(50, self.draw(x0, y0, x1, y1, hex_color))

    def draw(self, x0, y0, x1, y1, color='#FFFFFF'):
        self.canvas.create_oval(x0, y0, x1, y1, fill=color)

    def estimate_time(self, first_time, countdown):
        t = (len(self.positions) - self.index) * (time.time() - first_time - self.paused_time) / (
                self.index - self.continue_no)
        convert = timedelta(seconds=t)
        self.times = int(convert.total_seconds())
        if not countdown:
            new_thread(self.countdown_timer)

    def countdown_timer(self):
        while self.times > -1:
            while self.stopper:
                time.sleep(1)
                self.paused_time += 1
            minute, second = (self.times // 60, self.times % 60)
            hour = 0
            if minute > 60:
                hour, minute = (minute // 60, minute % 60)
            self.est_time_var.set('%0.2d' % hour + ":" + '%0.2d' % minute + ":" + '%0.2d' % second)
            self.frame.update()
            time.sleep(1)
            if self.times == 0:
                self.est_time_var.set("00:00:00")
            self.times -= 1

    def finish_measurement(self):
        if os.path.isfile(self.cwd + 'running.txt'):
            os.remove(self.cwd + 'running.txt')
        if os.path.isfile(self.cwd + 'running_commands.txt'):
            os.remove(self.cwd + 'running_commands.txt')
        self.reset_ok = self.reset_carousels()
        self.set_ipano_position(0, 0)
        switch_frame(self.frame_page3, self.page4)

    def disconnect(self):
        self.ser_body.close()
        self.ser_head.close()
        print('disconnected')

    def restore_connection(self):
        self.read_running_commands()
        # self.stopper = False
        self.frame.update()

    def resize_entry2(self, event):
        self.custom = True
        self.entry2.config(width=(len(self.output_file_name.get())) + 5)
        self.filename_out = self.cwd + self.output_file_name.get()

    def setup_command(self, com):
        if not self.head_found:
            self.win.after(50, lambda: self.gui_change('RefreshH'))

        else:
            while len(com) < 8:
                com += '0'
            self.head_communicate(com)

    def head_communicate(self, comm):
        answer = b'Error'
        gif_run = BooleanVar(value=True)
        self.win.after(50, self.buttons_switch(DISABLED))
        self.win.after(50, lambda: self.gui_change('WorkingH', gif_run))
        try:
            while self.ser_head.in_waiting > 0:
                self.ser_head.read(1)
            self.ser_head.write(comm.encode())
            while self.ser_head.in_waiting < 8:
                pass
            answer = self.ser_head.read(8)
            time.sleep(0.05)  # wait for rest of data
            while self.ser_head.in_waiting > 0:
                self.ser_head.read(1)
        except SerialException:
            print('head disconnected')
            self.head_found = False
            self.stopper = True
            try:
                self.ser_head.close()
            except AttributeError:
                print('not ports')
            self.win.after(50, lambda: self.gui_change('RefreshH'))
            self.stopper = True
        gif_run.set(False)
        self.win.after(50, self.buttons_switch(NORMAL))
        return self.decode_answer(answer)

    def decode_answer(self, ans):
        ans = ans.decode()
        if ans == 'Error':
            self.head_found = False
            self.ser_head.close()
            self.win.after(50, lambda: self.gui_change('RefreshH'))
            return ans
        if ans == 'UNKNOWN!':
            text = 'Prototype does not have this function'
            self.win.after(50, lambda: self.gui_change('WarningH', text))
            return ans
        suf = ans[3:]
        if ans.startswith('FLT'):
            if ans.endswith('LOST'):
                text = 'Position lost on carousel ' + suf[:1]
                self.win.after(50, lambda: self.gui_change('SetH', text))
            elif ans.endswith('ISOK'):
                text = 'Position ok on carousel ' + suf[:1]
                self.win.after(50, lambda: self.gui_change('SetH', text))
            else:
                text = 'On carousel ' + suf[:1] + ' filter ' + str(int(suf[1:3])) + ' set'
                self.win.after(50, lambda: self.gui_change('SetH', text))
                self.reset = False
        elif ans.startswith('CVT'):
            text = 'Current voltage: ' + suf[:1] + '.' + suf[1:4] + 'V'
            self.win.after(50, lambda: self.gui_change('SetH', text))
        elif ans.startswith('SVT'):
            text = 'Signal voltage: ' + suf[:1] + '.' + suf[1:] + 'V'
            self.win.after(50, lambda: self.gui_change('SetH', text))
        elif ans.startswith('NMA'):
            text = 'Number of measurements averaged: ' + str(int(suf))
            self.win.after(50, lambda: self.gui_change('SetH', text))
        elif ans.startswith('TPV'):
            text = 'Temperature: ' + suf[:1] + suf[2:4] + '.' + suf[4:] + '°C'
            self.win.after(50, lambda: self.gui_change('SetH', text))
        return ans

    def selection_head_commands(self, event):
        if self.combo_p2_a.get() == self.options1[-1]:
            self.file_measurements_path = filedialog.askopenfilename()
            self.combo_p2_a.set(path_leaf(self.file_measurements_path))
            add_option(self.options1, path_leaf(self.file_measurements_path))
            length = len(max(self.options1, key=len)) + 5
            self.win.after(50, lambda: self.gui_change('Combo_p2_a', self.options1, length))
        else:
            self.file_measurements_path = self.options1_loc + self.combo_p2_a.get()
        self.read_measurement_fail()

    def selection_body_commands(self, event):
        if self.combo_p2_b.get() == self.options2[-1]:
            self.file_positions_path = filedialog.askopenfilename()  # parent=root - dialog on top
            self.combo_p2_b.set(path_leaf(self.file_positions_path))
            add_option(self.options2, path_leaf(self.file_positions_path))
            length = len(max(self.options2, key=len)) + 5
            self.win.after(50, lambda: self.gui_change('Combo_p2_b', self.options2, length))
        else:
            self.file_positions_path = self.options2_loc + self.combo_p2_b.get()
        self.read_position_fail()

    def chose_output_file(self):
        self.filename_out = filedialog.asksaveasfilename()
        if self.filename_out == '':  # asksaveasfile return `None` if dialog closed with "cancel".
            self.time = str(date.today()) + '_' + str(datetime.now().hour) + '-' + str(datetime.now().minute)
            self.filename_out = str(self.cwd) + 'Output_' + self.time + '.txt'
            self.custom = False
        else:
            self.custom = True
        length1 = len(self.label_output_file_path.get())
        length2 = len(self.output_file_name.get()) + 5
        self.win.after(50, lambda: self.gui_change('OutputFile', length1, length2))

    def read_measurement_fail(self):
        err = ''
        self.commands.clear()
        try:
            file = open(self.file_measurements_path, 'r')
            self.headline = file.readline()
            self.headline = self.headline.strip()
            line = file.readline()
            line = line.strip()
            while line != '':
                self.commands.append(line)
                line = file.readline()
                line = line.strip()
                if len(line) > 8 or not (line.startswith('SFL') or line.startswith('GSV') or not len(line)):
                    raise ValueError
            file.close()
            if not self.commands:
                img = self.photo_orange
                self.measure_rdy[0] = True
                self.commands.append(0)
                err = 'Configuration file "' + self.file_measurements_path + '" is empty...'
            else:
                self.measure_rdy[0] = True
                img = self.photo_green
        except FileNotFoundError:
            self.commands.clear()
            self.measure_rdy[0] = False
            img = self.photo_red
            err = 'Configuration file "' + self.file_measurements_path + '" not found...'
        except UnicodeError:
            self.commands.clear()
            self.measure_rdy[0] = False
            img = self.photo_red
            err = 'Configuration file "' + self.file_measurements_path + '" is wrong format...'
        except ValueError:
            self.commands.clear()
            self.measure_rdy[0] = False
            img = self.photo_red
            err = 'Configuration file "' + self.file_measurements_path + '" have wrong commands...'
        if self.page == 1:
            self.ready_check_measure()
        self.win.after(50, lambda: self.gui_change('ReadMesFile', err, img))

    def read_position_fail(self):
        err = ''
        self.positions.clear()
        try:
            file = open(self.file_positions_path, 'r')
            line = file.readline()
            while line != '':
                coordinates = line.split("\t")
                height = float(coordinates[0].strip())
                azimuth = float(coordinates[1].strip())
                self.positions.append((height, azimuth))
                line = file.readline()
            file.close()
            if not self.positions:
                img = self.photo_orange
                self.positions.append(0)
                self.measure_rdy[1] = True
                err = 'Configuration file "' + self.file_positions_path + '" is empty...'
            else:
                img = self.photo_green
                self.measure_rdy[1] = True
        except FileNotFoundError:
            img = self.photo_red
            self.measure_rdy[1] = False
            err = 'Configuration file "' + self.file_positions_path + '" not found...'
        except UnicodeError:
            img = self.photo_red
            self.positions.clear()
            self.measure_rdy[1] = False
            err = 'Configuration file "' + self.file_positions_path + '" is wrong format...'
        except ValueError:
            img = self.photo_red
            self.positions.clear()
            self.measure_rdy[1] = False
            err = 'Configuration file "' + self.file_positions_path + '" have wrong commands...'
        if self.page == 1:
            self.ready_check_measure()
        self.win.after(50, lambda: self.gui_change('ReadPosFile', err, img))

    def reset_carousels(self):
        gif_run = BooleanVar(value=True)
        self.win.after(50, lambda: self.gui_change('TextH', 'Resetting carousel 0'))
        ans1 = self.head_communicate('RFL0XXXX')
        self.win.after(50, lambda: self.gui_change('TextH', 'Resetting carousel 1'))
        ans2 = self.head_communicate('RFL1XXXX')
        gif_run.set(False)
        self.win.after(50, lambda: self.gui_change('TextH', 'Measurement head ready'))
        self.win.after(50, lambda: self.gui_change('GreenH'))
        self.reset = True
        if ans1 == 'FLT0ISOK' and ans2 == 'FLT1ISOK':
            return True
        else:
            return False

    def buttons_switch(self, state):
        for but in self.buttons_p2[0]:
            but.config(state=state)
        for but in self.buttons_p2[1]:
            but.config(state=state)
        for but in self.buttons_p2[2:]:
            but.config(state=state)
        if state == NORMAL and self.measure_rdy[0] and self.measure_rdy[1] and self.measure_rdy[2]:
            self.button_measure_p2.config(state=state)
        else:
            self.button_measure_p2.config(state=DISABLED)


if __name__ == "__main__":
    pool_scheduler = NewThreadScheduler()
    ui = GUI()
    ui.win.mainloop()
