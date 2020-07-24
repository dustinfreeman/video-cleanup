import argparse
import os
import time
import subprocess
from subprocess import PIPE


video_exts = ['.avi', '.mov', '.mp4', '.flv', '.mkv', '.MTS', '.mpeg', '.m4v', '.ogv', '.mpeg']

def video_search(path, output='avifound.txt', modified_filter=None):
    print(f'Video Searching {path}')
    
    video_files = []

    for root, dirs, files in os.walk(path):
        for file in files:
            ext = os.path.splitext(file)[1]
            # print(file, ext)
            full_path = os.path.join(root, file)
            if modified_filter:
                modified_time = os.path.getmtime(full_path)
                modified_time_struct = time.localtime(modified_time)
                if modified_time < modified_filter:
                    continue
            if ext in video_exts:
                video_files.append(f'\"{full_path}\"')

    count = 0
    f = open(output, 'w')
    for vf in video_files:
        count += 1
        f.write(vf)
        f.write('\n')
    f.close()
    print(f'Videos found: {count}')

def ffquery(path, query):
    path = path.replace('\"', '')
    # path = path.replace(' ', '\\ ')

    call = f'ffprobe -v error -show_entries format={query} -of default=noprint_wrappers=1:nokey=1'.split(' ')
    call.append(f'{path}')

    value = subprocess.run(call, stdout=PIPE)
    return float(value.stdout)

def compute_bitrate(path):
    print(f'computing bitrate for {path}')
    # bitrate = ffquery(path, 'size') / ffquery(path, 'duration') 
    bit_rate = ffquery(path, 'bit_rate')
    # units of bytes/second
    size = ffquery(path, 'size')
    # units of bytes
    return bit_rate, size

def compute_bitrate_txt(list_file, output='bitrates.txt'):
    f = open(list_file, 'r')
    of = open(output, 'w')
    for line in f:
        video_file = line.strip()
        bit_rate, size = compute_bitrate(video_file)
        of.write(f'{bit_rate},\t{size},\t{video_file}')
        of.write('\n')
    f.close()
    of.close()

def filter_bit_rate(input_file, output_file="filtered_bitrates.txt"):
    if output_file is None:
        output_file = "filtered_bitrates.txt"
    f = open(input_file, 'r')
    of = open(output_file, 'w')
    for line in f:
        if len(line.split(',')) < 2:
            continue
        bit_rate = float(line.split(',')[0])
        BIT_RATE_CUTOFF = 10*(10**6)
        if bit_rate >= BIT_RATE_CUTOFF:
            of.write(line)
    f.close()
    of.close()

def reduce_bit_rate(input_file, dry_run=True, output_log_file=None):
    if output_log_file is None:
        output_log_file = 'compression_log.txt'

    f = open(input_file, 'r')
    of = open(output_log_file, 'a+')

    def log(msg):
        print(msg)
        of.write(msg + '\n')

    net_size_saving = 0

    for line in f:
        video_file = line.split(',')[2].strip()
        file_base, ext = os.path.splitext(video_file)
        video_file_compressed = file_base + '_comp' + '.mp4'
        CRF = 26
        log(video_file)
        call = ['ffmpeg', '-loglevel', 'error', \
        '-i', video_file.replace('\"', ''), \
        '-vcodec', 'libx265', '-x265-params', 'log-level=error',\
        '-async', '1', '-vsync', '1',\
        '-threads', '8', \
        # Copies original file creation date:
        # (Maybe doesn't work consistently?)
        '-map_metadata', '0:s:0', \
        # Apple Quicktime compatibility:
        '-pix_fmt', 'yuv420p', '-tag:v', 'hvc1', \
        '-crf', str(CRF), \
        '-y', video_file_compressed.replace('\"', '')]
        # print(call)
        subprocess.call(call)

        # transfer dates (macOS only)
        value = subprocess.run('GetFileInfo -d ' + video_file, shell=True, stdout=PIPE)
        original_c_date = value.stdout.decode('utf-8').strip()
        call = 'SetFile -d \"' + original_c_date + '\" \"' + video_file_compressed.replace('\"', '') + '\"'
        # print(call)
        subprocess.run(call, shell=True)

        #compare bitrate
        old_size = ffquery(video_file, 'size')
        new_size = ffquery(video_file_compressed, 'size')
        comp_factor = new_size / old_size

        log(f'Compressed {video_file} from {old_size/(10**6)} mb to {new_size/(10**6)} mb, a factor of {comp_factor} ')

        if comp_factor >= 0.5:
            log("\tNot replacing this video, as compression factor wasn't exciting enough.")
            if not dry_run:
                subprocess.run(['rm', video_file_compressed.replace('\"', '')])
        else:
            if not dry_run:
                # DANGER
                new_video_file = file_base.replace('\"', '') + ".mp4"

                #delete original file, as new file may have different extension
                subprocess.run(['rm', video_file.replace('\"', '')])
                
                subprocess.run(['mv', video_file_compressed.replace('\"', ''), new_video_file])
                log(f'Replaced {new_video_file}')

            net_size_saving += old_size - new_size
            
        #HACK testing
        # break

    f.close()
    log(f'Net disk space saved: {net_size_saving} bytes, {net_size_saving / 10**9} GB-ish')
    of.close()

def pix_fmt_fix(input_file, dry_run=True):
    # On conversion, some files defaulted to pix_fmt yuv444p. 
    # On Apple devices, this may be incompatible. Need to bulk convert these to -pix_fmt yuv420p

    f = open(input_file, 'r')

    net_size_saving = 0

    for line in f:
        video_file = line.strip() #line.split(',')[2].strip()
        file_base, ext = os.path.splitext(video_file)
        video_file_compressed = file_base + '_comp' + '.mp4'
        CRF = 26
        print(video_file)
        call = ['ffmpeg', '-loglevel', 'error', \
        '-i', video_file.replace('\"', ''), \
        '-vcodec', 'libx265', '-x265-params', 'log-level=error',\
        '-async', '1', '-vsync', '1',\
        '-threads', '8', \
        # Copies original file creation date:
        # (Maybe doesn't work consistently?)
        '-map_metadata', '0:s:0', \
        # Apple Quicktime compatibility:
        '-pix_fmt', 'yuv420p', '-tag:v', 'hvc1', \
        '-crf', str(CRF), \
        '-y', video_file_compressed.replace('\"', '')]
        # print(call)
        subprocess.call(call)

        #compare bitrate
        old_size = ffquery(video_file, 'size')
        new_size = ffquery(video_file_compressed, 'size')
        comp_factor = new_size / old_size

        print(f'Compressed {video_file} from {old_size/(10**6)} mb to {new_size/(10**6)} mb, a factor of {comp_factor} ')

        if not dry_run:
            # DANGER
            new_video_file = file_base.replace('\"', '') + ".mp4"
            #delete original file, as new file may have different extension
            subprocess.run(['rm', video_file.replace('\"', '')])
            
            subprocess.run(['mv', video_file_compressed.replace('\"', ''), new_video_file])
        net_size_saving += old_size - new_size

        #HACK testing
        # break

    f.close()
    print(f'Net disk space saved: {net_size_saving} bytes, {net_size_saving / 10**9} GB-ish')

def tmutil_restore(input_file, dry_run=True):
    f = open(input_file, 'r')
    for line in f:
        dst = line.replace("\"", "").strip()
        no_ext = os.path.splitext(dst)[0]
        # print(no_ext)

        tm_root = '/Volumes/Knossos/Backups.backupdb/Cydonia/2020-06-14-110450/Macintosh HD - Data'
        call = 'ls \"' + tm_root + no_ext + '\".*'
        # print(call)
        value = subprocess.run(call, shell=True, stdout=PIPE)
        file_found = value.stdout.strip().decode('utf-8')

        call = 'tmutil restore \"' + file_found + '\" \"' + dst + '\"'
        print(call)
        if not dry_run:
            subprocess.run('rm \"' + dst + '\"', shell=True, stdout=PIPE)
            subprocess.run(call, shell=True, stdout=PIPE)

    f.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Video cleanup')
    parser.add_argument('step_number', action='store')
    parser.add_argument('input', help='input path or file')
    parser.add_argument('-o', dest='output_file', help='output file')
    parser.add_argument('--not-dry-run', dest='not_dry_run', action='store_true', help='include flag to actually overwrite original video files')
    args = parser.parse_args()
    
    if args.step_number == '0':
        video_search(args.input)
    elif args.step_number == '1':
        # compute_bitrate(args.input)
        compute_bitrate_txt(args.input)
    elif args.step_number == '2':
        filter_bit_rate(args.input, args.output_file)
    elif args.step_number == '4':
        reduce_bit_rate(args.input, not args.not_dry_run, args.output_file)
    elif args.step_number == '0-fix':
        video_search(args.input, modified_filter=time.mktime((2020, 6, 19, 0, 0, 0, 0, 0, 0)))
    elif args.step_number == '1-fix':
        tmutil_restore(args.input, not args.not_dry_run)
    elif args.step_number == '4-fix':
        pix_fmt_fix(args.input, not args.not_dry_run)
    else:
        print(f'Invalid step number: {args.step_number}')
