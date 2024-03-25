
try:
    import user_config as config
except:
    print("Could not import user-defined config (user_config.py). Falling back to default config.")
    import default_config as config

import datetime
import subprocess
import os, time
import threading
import timeit
import sys
import requests


def send_message(message):
    send_url = f'https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage'
    data = {'chat_id': config.telegram_chat_id, 'text': config.computer_name+':  '+message}    
    response = requests.post(send_url, data=data).json()
    if not(response['ok']):
        print("Message not sent")
    return response['ok']

def recursive_listdir(path):
    # See https://stackoverflow.com/questions/19309667/recursive-os-listdir
    return [os.path.join(dp, f) for dp, dn, fn in os.walk(path) for f in fn]

def generate_checksum_of_file(full_filepath):
    os.system('shasum -a 256 "{}" >> "{}"'.format(full_filepath, config.checksum_file))

def transfer_file(full_filepath):
    sys.stdout.write("\rSending file {}         ".format(full_filepath))
    # Format today's date as YYYYMMDD
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    relative_path = os.path.relpath(full_filepath, start=config.input_directory)

    # Create path, preserving subdirectory structure for each date
    output_subdir = os.path.join(config.output_directory, today_str, os.path.dirname(relative_path))

    # Check if the subdirectory exists, and create it if it does not
    if not os.path.exists(output_subdir):
        os.makedirs(output_subdir)
    
    p = subprocess.Popen(["rsync", "-a", "--ignore-times", "--checksum", "--remove-source-files",
                        full_filepath, output_subdir + "/"],
                    stderr=subprocess.PIPE)
    
    _, stderr_data = p.communicate()

    if p.returncode == 0 and not stderr_data:
        return None
    return stderr_data.decode()

def increment_file_counter():
    try:
        # Attempt to read the current value from the file.
        with open(config.stats_file, 'r') as file:
            current_value = int(file.read().strip() or 0)
    except ValueError:
        # If the file does not contain an integer, start from 0.
        current_value = 0
    except FileNotFoundError:
        # If the file does not exist, start from 0.
        current_value = 0
    new_value = current_value + 1
    
    # Write the new value back to the file.
    with open(config.stats_file, 'w') as file:
        file.write(str(new_value))

    
    # os.system('expr `cat "{}" 2>/dev/null` + 1 >"{}"'.format(config.stats_file, config.stats_file))

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

        if filename_to_transfer not in already_checksummed_files:
            generate_checksum_of_file(filename_to_transfer)
            already_checksummed_files.add(filename_to_transfer)

        error = None
        try:
            error = transfer_file(filename_to_transfer)
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
    if send_message(config.computer_name+":  Started bb_imgstorage_nfs"):
        print("Telegram message bot connected")
    else:
        print("ERROR: check message bot settings")
    
    directory_watchdog()
