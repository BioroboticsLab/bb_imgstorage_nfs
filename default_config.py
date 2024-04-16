computer_name = "YOUR COMPUTER NAME"  # this will be added to messages
telegram_bot_token = "FILL IN API TOKEN"
telegram_chat_id = "FILL IN TELEGRAM CHAT ID"

directory_watchdog_sleep_timer = 1.0 # in seconds.
directory_watchdog_sleep_timer_on_error = 10.0 # in seconds.

input_directory = "/mnt/local_storage/beesbook_2019/hd_recording/out"
output_directory = "/mnt/zedat/beesbook/2019/hd_recording"  # for using local file transfer
# output_directory = "user@server:/basedir"  # for using ssh
directory_that_needs_to_be_a_mount_point = "/mnt/zedat"
use_ssh_for_transfer = False

stats_file = "/mnt/local_storage/beesbook_2019/hd_recording/imgstorage_stats"
checksum_file = "/mnt/local_storage/beesbook_2019/hd_recording/imgstorage.sha256.txt"