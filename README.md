# Task Scheduling Simulation

This project simulates task scheduling using the Earliest Deadline First (EDF) and Rate Monotonic Scheduling (RMS) algorithms. The simulation involves multiple processors and tasks that require resources, and it visualizes CPU utilization over time.

## Features

- Task scheduling using EDF and RMS algorithms.
- Resource management with mutual exclusion.
- Dynamic task assignment and load balancing.
- Real-time CPU utilization plotting.

## Requirements

- Python 3.x
- `matplotlib` for plotting

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/qzaleh/RealTimeSMT.git
Navigate to the project directory:
bash
Copy code
cd taskscheduling-simulation
Install the required Python packages:
bash
Copy code
pip install matplotlib
Usage
Define the resources and tasks in the main function:

python
Copy code
input_resources = "R3:2 R2:4 R1:3"
input_tasks = [
    "T1,50,2,1,0,0,0,4",
    "T2,70,3,0,2,0,1,5",
    "T3,30,1,0,0,1,2,6",
    "T4,50,2,1,1,0,0,3",
    "T5,60,3,0,2,1,1,2",
]
scheduling_algo = 'EDF'  # Change to 'RMS' for Rate Monotonic Scheduling
Run the simulation:

bash
Copy code
python taskscheduler.py
The terminal will display the status of resources, waiting queues, and CPU utilization. A real-time plot of CPU utilization will also be shown.

Code Overview
Task: Represents a task with its attributes and methods.
Processor: Represents a processor with its own ready queue, utilization, and thread.
is_schedulable: Checks if a task can be scheduled on a given processor.
assign_tasks_to_processors: Assigns tasks to processors based on the chosen scheduling algorithm.
reassign_tasks: Reassigns tasks from highly utilized processors or waiting queues to less utilized processors.
worker: Runs on each processor thread, handling task execution.
main_thread: Manages the overall scheduling process, including load balancing and stopping conditions.
print_status: Prints the current status of resources, waiting queues, and processors.
plot_utilization: Plots CPU utilization over time using matplotlib.
Example
Here is an example output from the terminal:

yaml
Copy code
T1 Deadlines: 50, 100, 150, 200
T2 Deadlines: 70, 140, 210, 280, 350
T3 Deadlines: 30, 60, 90, 120, 150, 180
T4 Deadlines: 50, 100, 150
T5 Deadlines: 60, 120
Resources: R3:2 R2:4 R1:3 Waiting Queue EDF: [] Waiting Queue RMS: []
CPU1:
CPU Utilization: 20.00%
Ready Queue[]
Running Task: T1
...
Processor 0, Task T1 processed
Processor 1, Task T2 processed
...
A real-time plot of CPU utilization will be displayed simultaneously.

License
This project is licensed under the MIT License. See the LICENSE file for details.

Acknowledgments
This project was inspired by real-time operating systems and scheduling algorithms. Special thanks to the developers of matplotlib for providing the tools for visualization
