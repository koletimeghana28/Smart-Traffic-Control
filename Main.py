from tkinter import *
from tkinter import filedialog, messagebox
import tkinter
import threading

from traffic_simulation import Simulation
from yolo_traffic import runYolo

main = tkinter.Tk()
main.title("Smart Control of Traffic Light Using Artificial Intelligence")
main.geometry("1300x1200")
main.config(bg='snow3')

filename = ""


def yoloTrafficDetection():
    global filename

    filename = filedialog.askopenfilename(
        title="Select Traffic Video",
        initialdir="Videos",
        filetypes=[
            ("Video Files", "*.mp4 *.avi *.mov *.mkv"),
            ("All Files", "*.*")
        ]
    )

    if not filename:
        messagebox.showerror("Error", "No video file selected!")
        return

    pathlabel.config(text=filename)

    text.delete('1.0', END)
    text.insert(END, filename + " loaded\n")
    text.insert(END, "Running YOLO Traffic Detection...\n")

    # Run in separate thread so Tkinter UI doesn't freeze
    threading.Thread(target=runYolo, args=(filename,), daemon=True).start()


def runSimulation():
    text.delete('1.0', END)
    text.insert(END, "Starting Traffic Simulation...\n")

    sim = Simulation()
    sim.runSimulation()


def closeApp():
    main.destroy()


# Title
font = ('times', 16, 'bold')

title = Label(
    main,
    text='Smart Control of Traffic Light Using Artificial Intelligence',
    bg='light cyan',
    fg='pale violet red',
    font=font,
    height=3,
    width=120
)
title.place(x=0, y=5)

# Buttons
font1 = ('times', 14, 'bold')

simulationButton = Button(
    main,
    text="Run Traffic Simulation",
    command=runSimulation,
    font=font1
)
simulationButton.place(x=50, y=100)

pathlabel = Label(
    main,
    bg='light cyan',
    fg='pale violet red',
    font=font1
)
pathlabel.place(x=460, y=100)

yoloButton = Button(
    main,
    text="Run Yolo Traffic Detection & Counting",
    command=yoloTrafficDetection,
    font=font1
)
yoloButton.place(x=50, y=150)

exitButton = Button(
    main,
    text="Exit",
    command=closeApp,
    font=font1
)
exitButton.place(x=460, y=150)

# Text area
font2 = ('times', 12, 'bold')

text = Text(main, height=20, width=150, font=font2)
text.place(x=10, y=250)

scroll = Scrollbar(main, command=text.yview)
scroll.place(x=1215, y=250, height=330)

text.configure(yscrollcommand=scroll.set)

main.mainloop()