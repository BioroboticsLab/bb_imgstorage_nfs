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

# Typical usage and workflow
A typical workflow involves first starting the video recording software, such as [bb_imgacquisition](https://github.com/BioroboticsLab/bb_imgacquisition) or [bb_raspicam](https://github.com/BioroboticsLab/bb_raspicam), which will save the recorded videos to the operating system's drive (e.g., an SSD).

While recording is running, use `bb_imgstorage_nfs` to transfer the saved files to the desired storage location. Common use cases include:

1. **Transfer to Network-Attached Storage (NAS):**  
   E.g., a network-attached storage device that is mounted locally via NFS or CIFS.
2. **Transfer to Another Computer or Location on the Network Using SSH:**  
3. **Transfer to a Locally-Attached Hard Drive:**  
