import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from scipy.signal import decimate
import matplotlib.pyplot as plt

import tkinter as tk
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import webbrowser

### Threshold Estimation ###################################

def three_lines(t, y, delta_l, delta_u):
    It = (t >= t[0] + delta_l) & (t < t[-1] - delta_u)
    t_fit, y = t[It], y[It]
    y_fit, threshold_time, threshold_signal = perform_fit(t_fit, y)
    return t_fit, y_fit, threshold_time, threshold_signal

def perform_fit(t, y):
    error_matrix = calculate_error_matrix(t, y)
    a, b = sorted(np.unravel_index(np.nanargmin(error_matrix), error_matrix.shape))
    y_fit, c = linreg(t, y, a, b)
    threshold_time = np.array([t[a], t[b]])
    threshold_signal = np.array([c[1], c[-2]])
    return y_fit, threshold_time, threshold_signal

def calculate_error_matrix(t, y):
    len_t = len(t)
    error_matrix = np.full((len_t, len_t), np.nan)

    for i in range(len_t - 1):
        temp_error_matrix = np.full(len_t, np.nan)
        for j in range(i + 1, len_t):
            y_fit, _ = linreg(t, y, i, j)
            e = np.linalg.norm(y - y_fit) ** 2
            temp_error_matrix[j] = e
            temp_error_matrix[i] = e
        error_matrix[i, :] = temp_error_matrix

    return error_matrix

def linreg(t, y, i, j):
    thresholds = np.sort([i, j])
    if invalid_indices(thresholds, t):
        return np.full_like(t, 1e10), np.array([1, 2])
    k = np.array([t[0], t[thresholds[0]], t[thresholds[1]], t[-1]])
    phi = create_spline_matrix(t, k)
    c = np.linalg.lstsq(phi, y, rcond=None)[0]
    y_fit = np.dot(phi, c)

    return y_fit, c

def invalid_indices(thresholds, t):
    if len(thresholds) == 0 or len(t) == 0:
        return True

    t_min = int(len(t) * 0.2)
    t_max = int(len(t) * 0.6)
    t_max2 = int(len(t) * 0.9)
    delta_min = int(len(t) * 0.2)

    return (thresholds[0] == 0 or thresholds[1] == t[-1] or thresholds[1] >= t_max2 or
            thresholds[0] == thresholds[1] or thresholds[0] <= t_min or thresholds[1] <= t_max or
            thresholds[1] - thresholds[0] <= delta_min or thresholds[0] > t_max)

def create_spline_matrix(t, k):
    return np.column_stack([
        1 - np.maximum(0, np.minimum(1, (t - k[0]) / (k[1] - k[0]))),
        np.maximum(0, np.minimum(1, (t - k[0]) / (k[1] - k[0]))) - np.maximum(0, np.minimum(1, (t - k[1]) / (k[2] - k[1]))),
        np.maximum(0, np.minimum(1, (t - k[1]) / (k[2] - k[1]))) - np.maximum(0, np.minimum(1, (t - k[2]) / (k[3] - k[2]))),
        np.maximum(0, np.minimum(1, (t - k[2]) / (k[3] - k[2])))
    ])

def perform_fit_3lines(time, meas, delta_l, delta_u):
    split_point = round(len(time) * 0.8) # Adjust as needed. 
    time_train, meas_train = time[:split_point], meas[:split_point]
    time_test, meas_test = time[split_point+1:-1], meas[split_point+1:-1]

    sort_idx_train = np.argsort(time_train)
    time_train, meas_train = time_train[sort_idx_train], meas_train[sort_idx_train]

    tr, yr, tc, _ = three_lines(time_train, meas_train, delta_l, delta_u)

    meas_pred = interp1d(tr, yr, kind='linear', fill_value='extrapolate')(time_test)
    err = meas_test - meas_pred
    mse = np.mean(err**2) / len(time_test)
    
    return mse, np.sort(tc)

def inflection_points(filename, runs, titlename='Signal with Estimated Thresholds', xlabel='Time (minutes)', ylabel='Filtered Signal'):
    data = pd.read_csv(filename)
    
    time_seconds = data.iloc[:, 0].values
    signal = data.iloc[:, 1].values

    time_minutes = time_seconds / 60
    time_minutes -= min(time_minutes)
    n_dec = 10
    
    filtered_signal = decimate(signal, n_dec, ftype='iir', zero_phase=False)
    filtered_time = decimate(time_minutes, n_dec, ftype='iir', zero_phase=False)
    delta_l, delta_u = 0.1, 0.1

    
    MSE = np.zeros(runs)
    time_threshold_pred = np.zeros((runs, 2))

    for rep in range(runs):
        p = np.random.permutation(len(filtered_time))

        if len(p) < 3:
            continue

        mse, time_threshold = perform_fit_3lines(filtered_time[p], filtered_signal[p], delta_l, delta_u)

        if len(time_threshold) != 2:
            time_threshold = np.array([filtered_time[0], filtered_time[-1]])

        time_threshold_pred[rep, :] = np.sort(time_threshold)
        MSE[rep] = mse


    mean_time_threshold = np.mean(time_threshold_pred, axis=0)
    
    fig = plt.figure(figsize=(6,4))
    plt.plot(time_minutes, signal, label='Original Signal', color='gray', alpha=0.5)
    plt.plot(filtered_time, filtered_signal, label='Filtered Signal', color='black', linewidth=1)
    for time_threshold in time_threshold_pred:
        plt.axvline(time_threshold[0], color='blue', linestyle='--', alpha=0.3)
        plt.axvline(time_threshold[1], color='green', linestyle='--', alpha=0.3)
    plt.axvline(mean_time_threshold[0], color='red', linestyle='-', linewidth=2, label='Threshold 1 (mean)')
    plt.axvline(mean_time_threshold[1], color='darkgreen', linestyle='-', linewidth=2, label='Threshold 2 (mean)')
    plt.grid(visible=True, which='both', linestyle='--', linewidth=0.5)
    plt.minorticks_on()
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(titlename)

    return [mean_time_threshold[0], mean_time_threshold[1], np.median(MSE)], fig


### GUI ######################################################

version = "GUI version 2026-04-15"
number_runs = 3     # should be changed to 10 !!!


global source_file

source_file = ""

def select():
    global source_file
    source_file = filedialog.askopenfilename()

    # ToDo: Error handling!
    if source_file != "":
        select_label.configure(text="File: " + source_file)
        plot_label.configure(text="[Info] Plotting may take some time.")
        plot_button.configure(state=tk.NORMAL)
    else:
        select_label.configure(text="[no file selected]")
        plot_label.configure(text="")
        plot_button.configure(state=tk.DISABLED)



    

def plot():
    plot_label.configure(text="[Info] please wait. this may take some time...")

    # ToDo: Error handling!
    if source_file == "":
        plot_label.configure(text="[Error] No file selected or file does not exist.")
        return
    
    for widget in canvas_frame.winfo_children():
        widget.destroy()

    title = title_entry.get()
    xlabel = xlabel_entry.get()
    ylabel = ylabel_entry.get()

    result, fig = inflection_points(source_file, number_runs, title, xlabel, ylabel)
    
    plot_label.configure(text=f"First BP: {result[0]:.3f}    Second BP: {result[1]:.3f}    Median MSE: {result[2]:.3f}   Runs: {number_runs}")

    # creating the Tkinter canvas
    # containing the Matplotlib figure
    canvas = FigureCanvasTkAgg(fig, master = canvas_frame)  
    canvas.draw()

    # placing the canvas on the Tkinter window
    canvas.get_tk_widget().pack()

    save_button.configure(state=tk.NORMAL)


def save():
    save_file = ""
    save_label.configure(text="")
    save_file = filedialog.asksaveasfilename(filetypes=(("PNG files", "*.png"), ("all files", "*.*")))

    if save_file != "":
        save_label.configure(text="Saved to: " + save_file)
        plt.savefig(save_file)

def on_exit():
    window.quit()
    window.destroy()
    

# create window
window = tk.Tk()


# window settings
window.title("Threshold Estimation")
window.minsize(640, 730)
window.maxsize(640, 730)
window.geometry("640x720+100+100")


# title
tk.Label(window, text="Threshold Estimation", font=("TkDefaultFont", 16)).pack(padx=20, pady=5, side="top", anchor="w")


# info text
info_text = "This is a GUI version of Threshold Estimation written by Gudrun Schappacher-Tilp.\nFor more information, see link below:"
tk.Label(window, text=info_text, anchor="w", justify="left").pack(padx=20, side="top", anchor="w")

link = tk.Label(window, text="https://github.com/schappag/threshold_estimation", font=("TkDefaultFont", 9, "underline"), fg="blue", cursor="hand2")
link.pack(padx=20, anchor="w")
link.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/schappag/threshold_estimation"))

# select file
select_frame = tk.Frame(window)
select_frame.pack(padx=20, pady=5, side="top", anchor="w")

tk.Button(select_frame, text="Select File", width=13, command=select).pack(side="left")

select_label = tk.Label(select_frame, text="[no file selected]")
select_label.pack(padx=10, side="right")


# title for plot
title_frame = tk.Frame(window, width=300, height=20)
title_frame.pack_propagate(False)
title_frame.pack(padx=20, pady=2, anchor="w")

tk.Label(title_frame, text="Plot Title:").place(x=10, y=0)

title_entry = tk.Entry(title_frame, width=100)
title_entry.place(x=110, y=0)


# x-label
xlabel_frame = tk.Frame(window, width=300, height=20)
xlabel_frame.pack_propagate(False)
xlabel_frame.pack(padx=20, pady=2, anchor="w")

tk.Label(xlabel_frame, text="x-Axis Label:").place(x=10, y=0)

xlabel_entry = tk.Entry(xlabel_frame, width=100)
xlabel_entry.place(x=110, y=0)


# y-label
ylabel_frame = tk.Frame(window, width=300, height=20)
ylabel_frame.pack_propagate(False)
ylabel_frame.pack(padx=20, pady=2, anchor="w")

tk.Label(ylabel_frame, text="y-Axis Label:").place(x=10, y=0)

ylabel_entry = tk.Entry(ylabel_frame, width=160)
ylabel_entry.place(x=110, y=0)


# run plot
plot_frame = tk.Frame(window)
plot_frame.pack(padx=20, pady=5, side="top", anchor="w")

plot_button = tk.Button(plot_frame, text="Plot", width=13, command=plot, state=tk.DISABLED)
plot_button.pack(side="left")

plot_label = tk.Label(plot_frame, text="")
plot_label.pack(padx=10, side="right")


# save plot as png
save_frame = tk.Frame(window)
save_frame.pack(padx=20, pady=5, side="top", anchor="w")

save_button = tk.Button(save_frame, text="Save Plot", width=13, command=save, state=tk.DISABLED)
save_button.pack(side="left")

save_label = tk.Label(save_frame, text="")
save_label.pack(padx=10, side="right")


# canvas for plot
canvas_frame = tk.Frame(window, bg="lightblue", width=600, height=400)
canvas_frame.pack(padx=20, pady=5)


# bottom line
bottom_frame = tk.Frame(window, width=600, height=30)
bottom_frame.pack_propagate(False)
bottom_frame.pack(padx=20, pady=5, anchor="w")

bottom_label = tk.Label(bottom_frame, text=version)
bottom_label.pack(side="left")

exit = tk.Button(bottom_frame, text="Exit", width=10, command=on_exit)
exit.pack(side="right")


# main loop
window.mainloop()