# video-cleanup

This is set of python scripts to identify all videos of unusually high bitrate, and then replace them with a compressed version, in place.

### Motivation
I had thousands of short videos from various projects throughout my project directories, and wanted to reduce overall size. I had already used tools to find the largest videos, and manually reduced their bitrate. However, this left out the very many short videos that were at a needlessly high bitrate. Many recording devices and screen capture tools default to recording at high bitrate, but this is rarely needed for long-term archival.

### Usage

**Beware!** This is designed to be run manually and carefully, step-by-step, since the changes it makes are opinionated and destructive. Please be careful! Data deletion is forever! This script includes one instance where I had to restore many files from a Time Machine backup.

### Contributing

Please let me know if you find these useful! I will gladly accept pull requests.
