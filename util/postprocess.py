from .commons import *
from glob import glob
import pandas as pd

def compile_regex_logs(OS):
    global rttPattern, packetsPattern
    # Compiling regular expressions to be used to parse logs
    if OS == 'posix':
        # Linux Mac OS...
        linux_rttStats_regex = "([0-9]+.[0-9]+)/([0-9]+.[0-9]+)/([0-9]+.[0-9]+)/([0-9]+.[0-9]+)"
        linux_packets_regex = "([0-9]+) [\s\w]+,\s+([0-9]+) [\s\w]+,"
        rttPattern = re.compile(linux_rttStats_regex)
        packetsPattern = re.compile(linux_packets_regex)
    elif OS == 'nt':
        # Windows (in theory not used anymore...)
        windows_rttStats_regex = "[\w\s]+ =\s+([0-9]+)ms, [\s\w]+=\s+([0-9]+)ms, [\s\w]+=\s+([0-9]+)ms"
        windows_packets_regex = "[\w]+ = ([0-9]+), [\w]+ =\s+([0-9]+),"
        rttPattern = re.compile(windows_rttStats_regex)
        packetsPattern = re.compile(windows_packets_regex)


def build_stats(rttStats, packetsStats):
    rs, ps = rttStats, packetsStats
    rttDict = {'minRTT': rs[0], 'avgRTT': rs[1],
               'maxRTT': rs[2], 'mdevRTT': rs[3]}

    # Lost packets are computed here, using the number of TX and RX packets
    TX, RX = int(packetsStats[0]), int(packetsStats[1])
    lost = round((1 - RX/TX) * 100, 2)
    packetsDict = {'TX': TX, 'RX': RX, 'Lost': lost}

    return rttDict, packetsDict


def parse_log(file, OS, ip_version):

    rttStats, packetsStats = None, None
    # reading the whole log as a single filestring
    f = open(file, 'r')
    filestring = f.read()
    f.close()
    # First of all, get the IP address
    if ip_version == 4:
        match = re.search(IPv4regex, filestring)
    elif ip_version == 6:
        ip_da_verificare = filestring.split('g ')[1]
        match = re.search(IPv6regex, ip_da_verificare)
    if not match:
        raise Exception(
            "Cannot find an IP address in this log")
    IPaddress = match.group()

    if OS == 'nt':
        # for Windows, easier and equivalent to go directly with deep_parse_log
        rttStats, packetsStats = deep_parse_log(file, OS)
    elif OS == 'posix':
        match = rttPattern.search(filestring)
        if match:
            # extracting the rtt statistics
            rttStats = list(map(float, match.groups()))
        match = packetsPattern.search(filestring)
        if match:
            # extracting the packets counters statistics
            packetsStats = list(map(float, match.groups()))

    # let's handle all the bad things that could have happened...
    if not rttStats and not packetsStats:
        raise Exception("{} cannot be parsed as expected".format(file))

    # if you are here it means you miss either rttStats or packetsStats (not both)
    if not rttStats:
        if OS == 'posix':
            # 7 packets transmitted, 0 received, +7 errors, 100% packet loss, time 6336ms
            # probably you never got a reply...as commented above
            TX, RX = packetsStats
            if RX == 0:
                # You can't do nothing more than reporting NaN
                nan = float('NaN')
                rttStats = [nan, nan, nan, nan]
            else:
                # I surrender in this case, a clever student can invent something better :)
                nan = float('NaN')
                rttStats = [nan, nan, nan, nan]
        else:
            raise Exception(
                "{}: weird error with rttStats of this Windows log".format(file))

    if not packetsStats:
        if OS == 'posix':
            raise Exception(
                "{}: A non-empty Linux log should always have the packets stats".format(file))
        elif OS == 'nt':
            raise Exception(
                "{}: weird error with packetsStats of this windows log".format(file))
    # whatever I have here, I can't do much more than this!
    # so I pack results in a dict and return them
    rttDict, packetsDict = build_stats(rttStats, packetsStats)
    return rttDict, packetsDict, IPaddress


def deep_parse_log(file, OS):
    if OS == 'nt':
        goodLine = re.compile("\w+=([0-9]+)ms")
        missedReply = re.compile("[a-zA-Z ]+\.")
        expiredMessages = ['TTL scaduto', 'TTL expired']
    elif OS == 'posix':
        raise Exception(
            "Deep parsing with Linux should not be necessary: something wrong happened")
    # TX is a counter of transmitted packets
    # rtt_values will list all values of rtt found in the log
    TX, RX, rtt_values = 0, 0, []
    with open(file) as reader:
        for line in reader.readlines():
            # if the line contains "...=Xms"
            if re.search("\w+=([0-9]+)ms", line):
                TX += 1
                RX += 1
                # this is to catch the rtt values
                match = goodLine.findall(line)
                if match:
                    # which is appended to the list
                    rtt_values.append(float(match[0]))
            elif missedReply.match(line) or any(x in line for x in expiredMessages):
                TX += 1
    if rtt_values != []:
        rttStats = [min(rtt_values), np.mean(rtt_values),
                    max(rtt_values), np.std([rtt_values])]
    else:
        # if no icmp_reply, ergo, no values of rtt
        nan = float('NaN')
        rttStats = [nan, nan, nan, nan]
    packetsStats = [TX, RX]
    return rttStats, packetsStats


def parse_file_name(filename):
    # Removing path prefix and suffix
    filename = filename.split(os.sep)[-1]

    if not filename.startswith('ping') or not filename.endswith('.txt'):
        raise Exception(
            "All logs filenames should start with the prefix \'ping\'"
            "and be saved as .txt files")

    # Checking that all elements of the filename are well formatted and valid
    try:
        elements = filename[:-4].split('_')[1:]
        name, surname, cap, oper, poa, tech, localtech, nickname, where, datestring = elements
    except:
        raise Exception(
            "Cannot parse the experiment parameters from the log filename")

    # checking name and surname
    if not namesurnamecode.match(name):
        raise Exception("""{} is not a valid name
                        Please, type your name using only capital letters.""".format(name))

    if not namesurnamecode.match(surname):
        raise Exception("""{} is not a valid surname
                        Please, type your surname using only capital letters.""".format(surname))

    # checking CAP
    if not capcode.match(cap):
        raise Exception("""{} is not a valid CAP
                        To specify the place where you performed the ping test,
                        provide the CAP code of your municipality.""".format(cap))

    # checking that oper is an alphanumeric string
    if not alphanumeric.match(oper):
        raise Exception("""{} is not a valid Operator
                        Please, specify your operator only using an
                        alphanumeric string (no special char, no spaces...)""".format(oper))

    # checking that poa is one of the allowed options
    if poa not in points_of_access:
        raise Exception("""{} is not a valid point of access
                        The supported points of access are\n{}""".format(poa, "\n".join(points_of_access)))

    # checking that technology of access is one of the allowed options
    if tech not in access_technologies:
        raise Exception("""{} is not a valid technology of access
                        The allowed tech of access are {}""".format(tech, "\n".join(access_technologies)))

    # checking local technology of access is valid
    if localtech not in local_techs:
        raise Exception("""{} is not a valid local technology of access
                        The allowed local tech of access are {}""".format(localtech, "\n".join(local_techs)))

    # checking country-codes
    if not countrycode.match(where):
        raise Exception("""{} is not a valid country code
                        To specify a country, use its 2 digits ISO
                        country code (check it on countrycode.org)""".format(where))

    # checking that the datetime is formatted as expected.
    # E.g 9 nov 2020 10:50 (12sec) --> 09112020-10h50m12s
    date = datetime.strptime(datestring, '%d%m%Y-%Hh%Mm%Ss')

    # if you are here it means your filename is well formatted! :)
    return [name, surname, cap, oper, poa, tech, localtech, where, date]


def print_mistakes(found_mistakes):
    # if everything ok...
    if found_mistakes == []:
        print(
            "\nALL RIGHT! All logs are well formatted and provided useful results, thank you!")
    # if not... print a summary of raised Exceptions :(
    else:
        print("\nThere have been some problems while parsing your log files")
        print("Here is the list of detected problems")
        for e in found_mistakes:
            print("* {}\n  {}".format(e[0], e[1]))


def process_logs(folder, OS, ip_version):
    compile_regex_logs(OS)

    # Retrieving log files
    print("Looking for logs inside {}".format(folder))
    logs = glob(folder+os.sep+"*.txt")
    print("Found these log-files:")
    for log in logs:
        print(" --> {}".format(log.replace(folder+os.sep, '', 1)))

    bad_formatted_logs = []
    found_mistakes = []
    print("\nChecking if logs have a valid filename...\n")
    for log in logs:
        logname = log.replace(folder+os.sep, '', 1)
        print(logname.ljust(90, ' '), end='\r')
        try:
            params = parse_file_name(log)
            #print("\twell-formatted :)")
        except Exception as e:
            # if log has a bad filename it will not be parsed
            # for this purpose it is added to the list of bad logs
            print("ERROR: -> {}".format(logname).ljust(90, ' '))
            print(e)
            found_mistakes.append((log, e))
            bad_formatted_logs.append(log)

    # Only valid logs will be parsed. Bad logs are removed from
    # the larger set of logs found in the provided folder
    valid_logs = set(logs) - set(bad_formatted_logs)

    print('CHECK COMPLETED. ValidLogs={} NotValid={}'.format(
        len(valid_logs), len(bad_formatted_logs)).ljust(90, ' '))
    print('-'*60)

    results_matrix = []
    print("\nScanning valid logs to extract ping statistics...\n")
    for log in valid_logs:
        # print('-'*60)
        logname = log.replace(folder+os.sep, '', 1)
        # print(logname)
        print(logname.ljust(90, ' '), end='\r')
        try:
            rttDict, packetsDict, IPaddress = parse_log(log, OS, ip_version)
            #print("{}\n{}".format(rttDict, packetsDict), end='\r')
        except Exception as e:
            print("ERROR: -> {}".format(logname).ljust(90, ' '))
            print(e)
            found_mistakes.append((log, e))
            continue

        # Adding this log result to overall results
        params = parse_file_name(log)
        row = params + [IPaddress]
        row += [rttDict['minRTT'], rttDict['avgRTT'],
                rttDict['maxRTT'], rttDict['mdevRTT']]
        row += [packetsDict['TX'], packetsDict['RX'], packetsDict['Lost']]
        results_matrix.append(row)

    # ALL RESULTS AVAILABLE HERE
    print('SCAN COMPLETED'.ljust(90, ' '))
    print('-'*60)
    columns = ['name', 'surname', 'cap', 'operator', 'poa', 'accessTech', 'localTech',
               'country', 'datetime', 'IP', 'minRTT', 'avgRTT', 'maxRTT', 'mdevRTT', 'TX', 'RX', 'lost']
    index = ['name', 'surname', 'IP', 'datetime']

    if results_matrix != []:
        # retrieving name and surname from last parsed log
        name, surname = params[0], params[1]
        outputfile = "_".join(["results", name, surname, "v"+str(ip_version)])+'.csv'
        df = pd.DataFrame(results_matrix, columns=columns)
        df.set_index(index)
        df.to_csv(outputfile, sep=',', encoding='utf-8',
                  float_format="%.5f", date_format='%Y-%m-%d %H:%M:%S', index=False)
        print("\n\n", df)
        print("All your valid results have been saved to {}".format(outputfile))
    else:
        print("No useful results to be recorded :(")

    print_mistakes(found_mistakes)
