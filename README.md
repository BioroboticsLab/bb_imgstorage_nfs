# bb_imgstorage_nfs
Synchronization software for transferring files and reporting errors.  The code monitors a specified directory for new files and uses rsync to transfer them to a destination location, with the option to use SSH. On the destination, it organizes files into date-sorted folders. The code also includes error handling and logging via Telegram messages.  Runs/tested on Linux and Mac.

# Installation
Needed python packages:

```bash
conda install requests
```
# Setup and running

Before running the script, create a file called user_config.py in the same directory as imgstorage.py. This file allows you to override the default values provided in default_config.py. The script will first attempt to load settings from user_config.py, and if not found, it will fall back to default_config.py.

Once you’ve configured your user_config.py file, run the script with:

```bash
python imgstorage.py
```
