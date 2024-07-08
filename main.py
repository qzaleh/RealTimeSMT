import threading
import queue
import time
from collections import deque

# Define resources with mutexes for mutual exclusion
resource_locks = {}
available_resources = {}

# Shared waiting queue for EDF
waiting_queue_edf = queue.PriorityQueue()
# Shared waiting queue for RMS
waiting_queue_rms = deque()


# Define task structure
class Task:
    def __init__(self, name, period, execution_time, resource_one_usage, resource_two_usage, resource_three_usage,
                 processor_dest_id, repeat_count):
        self.name = name
        self.period = period
        self.execution_time = execution_time
        self.resource_one_usage = resource_one_usage
        self.resource_two_usage = resource_two_usage
        self.resource_three_usage = resource_three_usage
        self.processor_dest_id = processor_dest_id
        self.repeat_count = repeat_count
        self.deadline = time.time() + self.period
        self.remaining_time = execution_time

    def __lt__(self, other):
        return self.deadline < other.deadline


# Define a class for processors
class Processor:
    def __init__(self, processor_id):
        self.processor_id = processor_id
        self.ready_queue = queue.PriorityQueue()
        self.thread = None
        self.utilization = 0
        self.running_task = None


def is_schedulable(task, processor):
    # Check if the task can be scheduled on the given processor
    total_utilization = processor.utilization + (task.execution_time / task.period)
    return total_utilization <= 1.0


def assign_tasks_to_processors(tasks, processors, scheduling_algo):
    unschedulable_tasks = []
    for task in tasks:
        processor = processors[task.processor_dest_id]
        if is_schedulable(task, processor):
            processor.ready_queue.put(task)
            processor.utilization += (task.execution_time / task.period)
        else:
            unschedulable_tasks.append(task)

    for task in unschedulable_tasks:
        if scheduling_algo == 'EDF':
            waiting_queue_edf.put(task)
        elif scheduling_algo == 'RMS':
            waiting_queue_rms.append(task)


def reassign_tasks(processors, scheduling_algo):
    # Reassign tasks from highly utilized processors or waiting queues to less utilized processors
    for processor in processors:
        if processor.utilization < 0.5:  # Example threshold for low utilization
            # First, try to get tasks from the waiting queue
            if scheduling_algo == 'EDF':
                if not waiting_queue_edf.empty():
                    task = waiting_queue_edf.get()
                    if is_schedulable(task, processor):
                        processor.ready_queue.put(task)
                        processor.utilization += (task.execution_time / task.period)
                    else:
                        waiting_queue_edf.put(task)
            elif scheduling_algo == 'RMS':
                if waiting_queue_rms:
                    task = waiting_queue_rms.popleft()
                    if is_schedulable(task, processor):
                        processor.ready_queue.put(task)
                        processor.utilization += (task.execution_time / task.period)
                    else:
                        waiting_queue_rms.append(task)

            # Then, try to steal tasks from highly utilized processors
            for other_processor in processors:
                if other_processor.utilization > 0.75:  # Example threshold for high utilization
                    if not other_processor.ready_queue.empty():
                        task = other_processor.ready_queue.get()
                        if is_schedulable(task, processor):
                            processor.ready_queue.put(task)
                            processor.utilization += (task.execution_time / task.period)
                            other_processor.utilization -= (task.execution_time / task.period)
                        else:
                            other_processor.ready_queue.put(task)


def worker(processor, stop_event, scheduling_algo):
    while not stop_event.is_set():
        try:
            task = processor.ready_queue.get(timeout=1)
        except queue.Empty:
            continue

        acquired_resources = []
        resources_acquired = True

        resource_usage = {
            'R1': task.resource_one_usage,
            'R2': task.resource_two_usage,
            'R3': task.resource_three_usage
        }

        for resource, amount in resource_usage.items():
            if amount > 0:
                if not resource_locks[resource].acquire(blocking=False):
                    resources_acquired = False
                    break
                acquired_resources.append(resource)
                available_resources[resource] -= amount

        if not resources_acquired:
            for r in acquired_resources:
                resource_locks[r].release()
                available_resources[r] += resource_usage[r]
            if scheduling_algo == 'EDF':
                waiting_queue_edf.put(task)
            elif scheduling_algo == 'RMS':
                waiting_queue_rms.append(task)
            processor.ready_queue.task_done()
            continue

        processor.running_task = task
        start_time = time.time()

        while task.remaining_time > 0 and not stop_event.is_set():
            task.remaining_time -= 1
            time.sleep(1)  # Simulate processing time

        print(f"Processor {processor.processor_id}, Task {task.name} processed")

        for resource in acquired_resources:
            resource_locks[resource].release()
            available_resources[resource] += resource_usage[resource]

        task.repeat_count -= 1
        if task.repeat_count > 0:
            task.deadline = time.time() + task.period
            task.remaining_time = task.execution_time
            processor.ready_queue.put(task)
        processor.running_task = None
        processor.ready_queue.task_done()


def main_thread(processors, stop_event, scheduling_algo):
    # Create worker threads for each processor
    for processor in processors:
        t = threading.Thread(target=worker, args=(processor, stop_event, scheduling_algo))
        t.start()
        processor.thread = t

    while not stop_event.is_set():
        # Move tasks from waiting queue to ready queues of processors
        if scheduling_algo == 'EDF':
            while not waiting_queue_edf.empty():
                task = waiting_queue_edf.get()
                processor = processors[task.processor_dest_id]
                if is_schedulable(task, processor):
                    processor.ready_queue.put(task)
                    processor.utilization += (task.execution_time / task.period)
                else:
                    waiting_queue_edf.put(task)
                    break
        elif scheduling_algo == 'RMS':
            while waiting_queue_rms:
                task = waiting_queue_rms.popleft()
                processor = processors[task.processor_dest_id]
                if is_schedulable(task, processor):
                    processor.ready_queue.put(task)
                    processor.utilization += (task.execution_time / task.period)
                else:
                    waiting_queue_rms.append(task)
                    break

        # Perform load balancing
        reassign_tasks(processors, scheduling_algo)

        time.sleep(1)

        # Check if all queues are empty to stop the execution
        if all(p.ready_queue.empty() for p in processors) and waiting_queue_edf.empty() and not waiting_queue_rms:
            stop_event.set()

    for processor in processors:
        processor.ready_queue.join()


def print_status(processors):
    resource_status = ' '.join([f"{res}:{count}" for res, count in available_resources.items()])
    waiting_tasks_edf = list(waiting_queue_edf.queue)
    waiting_tasks_rms = list(waiting_queue_rms)
    waiting_tasks_str_edf = ', '.join([t.name for t in waiting_tasks_edf])
    waiting_tasks_str_rms = ', '.join([t.name for t in waiting_tasks_rms])
    print(
        f"Resources: {resource_status} Waiting Queue EDF: [{waiting_tasks_str_edf}] Waiting Queue RMS: [{waiting_tasks_str_rms}]")

    for processor in processors:
        ready_tasks = list(processor.ready_queue.queue)
        ready_tasks_str = ', '.join([f"{t.name}:{t.repeat_count}" for t in ready_tasks])
        running_task = processor.running_task.name if processor.running_task else "idle"
        utilization = (processor.utilization / 1.0) * 100  # Utilization is in percentage
        print(f"CPU{processor.processor_id + 1}:")
        print(f"CPU Utilization: {utilization:.2f}%")
        print(f"Ready Queue[{ready_tasks_str}]")
        print(f"Running Task: {running_task}")


def main():
    input_resources = "R3:2 R2:4 R1:3"
    input_tasks = [
        "T1,50,2,1,0,0,0,4",
        "T2,70,3,0,2,0,1,5",
        "T3,30,1,0,0,1,2,6",
        "T4,50,2,1,1,0,0,3",
        "T5,60,3,0,2,1,1,2",
    ]
    scheduling_algo = 'EDF'  # Change to 'RMS' for Rate-Monotonic Scheduling

    global resource_locks, available_resources

    # Parse resources
    for resource in input_resources.split():
        res, count = resource.split(':')
        resource_locks[res] = threading.Lock()
        available_resources[res] = int(count)

    # Initialize processors
    processors = [Processor(i) for i in range(3)]

    # Parse tasks and distribute them among processors
    tasks = []
    for task_str in input_tasks:
        name, period, exec_time, r1, r2, r3, proc_id, repeat = task_str.split(',')
        task = Task(name, int(period), int(exec_time), int(r1), int(r2), int(r3), int(proc_id), int(repeat))
        tasks.append(task)

    assign_tasks_to_processors(tasks, processors, scheduling_algo)

    # Print task deadlines
    for task in tasks:
        deadlines = [task.period * i for i in range(1, task.repeat_count + 1)]
        print(f"{task.name} Deadlines: {', '.join(map(str, deadlines))}")

    # Start the main thread
    stop_event = threading.Event()
    main_thread_thread = threading.Thread(target=main_thread, args=(processors, stop_event, scheduling_algo))
    main_thread_thread.start()

    try:
        while main_thread_thread.is_alive():
            print_status(processors)
            time.sleep(1)
    except KeyboardInterrupt:
        stop_event.set()

    main_thread_thread.join()

    # Print final resource status and queues
    print_status(processors)


if __name__ == "__main__":
    start_time = time.time()
    main()
