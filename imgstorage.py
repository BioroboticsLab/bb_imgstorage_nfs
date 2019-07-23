
import config
import datetime
import subprocess
import os, time
import queue
from queue import Queue
import threading
import timeit
import sys

global_message_queue = Queue()

def send_message(message):
    global global_message_queue
    try:
        global_message_queue.put_nowait(message)
        print("Sending: {}".format(message))
    except queue.Full:
        print("Queue full. Message: {}".format(message))

def message_station():
    global global_message_queue
    
    if config.slack_api_token is None:
        print("Slack deactivated.")
        return

    import slack
    slack_client = slack.WebClient(token=config.slack_api_token)

    while True:
        message = global_message_queue.get()

        try:
            response = slack_client.chat_postMessage(
                            channel=config.slack_channel,
                            text=message)
        except Exception as e:
            print("Message station encountered exception: {}".format(str(e)))
            print("Message was: {}".format(message))
            time.sleep(10)
            continue

        if not response["ok"]:
            print("Slack message not sent: {}".format(message))

        time.sleep(5)

def recursive_listdir(path):
    # See https://stackoverflow.com/questions/19309667/recursive-os-listdir
    return [os.path.join(dp, f) for dp, dn, fn in os.walk(path) for f in fn]

def generate_checksum_of_file(full_filepath):
    os.system('sha256sum "{}" >> "{}"'.format(full_filepath, config.checksum_file))

def transfer_file(full_filepath, filename):
    sys.stdout.write("\rSending file {}         ".format(filename))
    p = subprocess.Popen(["rsync", "-a", "--ignore-times", "--checksum", "--remove-source-files",
                        full_filepath,
                        os.path.join(config.output_directory, filename)],
                    stderr=subprocess.PIPE)
    
    _, stderr_data = p.communicate()

    if p.returncode == 0:
        return None
    return stderr_data.decode()

def increment_file_counter():
    os.system('expr `cat "{}" 2>/dev/null` + 1 >"{}"'.format(config.stats_file, config.stats_file))

def directory_watchdog():

    already_checksummed_files = set()
    last_transferred_file_time = None
    last_no_file_found_message_time = None

    while True:
        
        files_to_transfer = []
        try:
            files_to_transfer = recursive_listdir(config.input_directory)
            files_to_transfer = list(sorted(files_to_transfer))
        except Exception as e:
            send_message("Watchdog: ls encountered exception: {}".format(str(e)))
            time.sleep(config.directory_watchdog_sleep_timer_on_error)
            continue
        
        # No files to transfer? If that happens for a longer time, report it.
        if len(files_to_transfer) == 0:
            
            # Print error message to slack?
            current_time = timeit.default_timer()
            if last_transferred_file_time is not None:
                should_print = True
                if last_no_file_found_message_time is not None:
                    last_print_time_delta_seconds = current_time - last_no_file_found_message_time
                    should_print = last_print_time_delta_seconds > 60.0 * 2.5

                last_transferred_file_time_delta_seconds = current_time - last_transferred_file_time
                if should_print and last_transferred_file_time_delta_seconds > 60.0 * 2.5:
                    delta = datetime.timedelta(seconds=last_transferred_file_time_delta_seconds)

                    n_total_files = 0
                    try:
                        with open(config.stats_file) as f:
                            n_total_files = f.readline().strip()
                    except:
                        pass

                    send_message("No new file transferred for {}. Total files transferred: {}.".format(delta, n_total_files))
                    last_no_file_found_message_time = current_time

            # No files to confuse. Remove checksums and sleep.
            already_checksummed_files = set()
            time.sleep(config.directory_watchdog_sleep_timer)
            continue

        # Mount point is not valid anymore? Report it.
        if config.directory_that_needs_to_be_a_mount_point is not None:
            if not os.path.ismount(config.directory_that_needs_to_be_a_mount_point):
                send_message("Output directory is not mounted anymore ({}).".format(config.directory_that_needs_to_be_a_mount_point))
                time.sleep(config.directory_watchdog_sleep_timer_on_error)
                continue

        filename_to_transfer = files_to_transfer[-1]
        full_filename_to_transfer = os.path.join(config.input_directory, filename_to_transfer)

        if filename_to_transfer not in already_checksummed_files:
            generate_checksum_of_file(full_filename_to_transfer)
            already_checksummed_files.add(filename_to_transfer)

        error = None
        try:
            error = transfer_file(full_filename_to_transfer, filename_to_transfer)
        except Exception as e:
            error = str(e)
        
        if error is not None:
            send_message("Watchdog: rsync encountered error: {}".format(error))
            time.sleep(config.directory_watchdog_sleep_timer_on_error)
            continue
        
        increment_file_counter()
        last_transferred_file_time = timeit.default_timer()

        sys.stdout.write("\rFile transferred at {}         ".format(datetime.datetime.now()))

if __name__ == "__main__":
    print("Starting watchdog..")
    message_thread = None
    try:
        message_thread = threading.Thread(target=message_station)
        message_thread.start()
    except:
        message_thread = None

    directory_watchdog()

    if message_thread is not None:
        message_thread.join()