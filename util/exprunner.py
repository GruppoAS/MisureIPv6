from .commons import *
import urllib.request
import subprocess
import threading
from subprocess import TimeoutExpired
import concurrent.futures
import progressbar

queryParams = "?fields=status,message,continent,continentCode,country,countryCode,"\
    "region,regionName,city,zip,lat,lon,timezone,isp,org,as,query,reverse"


def ipapi_query(query, slow=False):
    if slow:
        # Max Rate 45queries/minute ==> Freq = 0.75 Hz ==> Periodo = 1.33
        # Going slower than 1 query every 1.33 sec is enough to not exceed the max rate
        sleep(1.34)
    ask = "http://ip-api.com/json/"+query+queryParams
    try:
        resp = urllib.request.urlopen(ask)
    except urllib.error.HTTPError:
        print("""Without a pro service, ip-api.com tolerates up to 45 queries per minute.
            Please, retry autoping.py after having waited for a while.""")
        exit()
    except Exception as e:
        print("""ip-api.com is not replying as expected.
            Problems with your Internet Connection?""")
        exit()
    data = json.load(resp)
    return data


def is_slowing_needed(lines):
    validLines = []
    for index, line in enumerate(lines):
        index += 1
        if line.startswith('#') or line.startswith('//'):
            continue
        line = line.strip()
        if line == '':
            continue
        validLines.append((index, line))
    # qui abbiamo solo le righe che contengono qualche info da validare
    flag = len(validLines) >= 45
    if flag:
        print("SLOWING DOWN QUERIES")
    return validLines, flag


def validate_ip_list(iplistfile, ip_version):
    print('\n# BUILDING LIST OF PING COMMANDS TO BE EXECUTED'.ljust(60, '-'))
    pingable_list = []
    print("Scanning IPlist.csv to validate IP addresses and QDNs...")

    if ip_version == 4:
        with open(iplistfile, 'r') as f:
            lines = f.readlines()
            validLines, slowFlag = is_slowing_needed(lines)
            pbar = progressbar.ProgressBar(max_value=len(validLines), redirect_stdout=True)
            pbar.start()
            for i, l in enumerate(validLines):
                line = l[1]
                index = l[0]
                elems = line.split(',')
                elems = [e.strip() for e in elems]
                print("Validating line {}: {}".format(str(index).rjust(2, ' '), line))
                if len(elems) == 2:
                    try:
                        qdn = QDNregex.match(elems[0]).group()
                        indirizzoIP = IPv4regex.match(elems[1]).group()
                    except:
                        print("Not a valid sequence of QDN, IP on line {} of {}".format(
                            index, iplistfile))
                        print("Please, correct this line: {}".format(line))
                        continue
                    data = ipapi_query(qdn, slowFlag)
                    if data['status'] != 'success':
                        print(
                            "ip-api.com has not been able to resolve this QDN: {}".format(qdn))
                        continue
                    if indirizzoIP != data['query']:
                        print("Line {} of {}: IP address mismatches QDN".format(
                            index, iplistfile))
                        print("Please, correct this line: {}".format(line))
                        print(
                            "NB: ip-api.com tells that {} --> {}".format(qdn, data['query']))
                        continue

                elif len(elems) == 1:
                    match = IPv4regex.match(elems[0])
                    if not match:
                        match = QDNregex.match(elems[0])
                    if not match:
                        print("Not valid QDN or IP on line {} of {}".format(
                            index, iplistfile))
                        print("Please, correct this line: {}".format(line))
                        continue
                    query = match.group()
                    data = ipapi_query(query, slowFlag)
                    if data['status'] != 'success':
                        print(
                            "ip-api.com has not been able to resolve this query: {}".format(query))
                        continue
                    qdn = data['reverse'] if query == data['query'] else query
                else:
                    print("Line {}: {} is NOT VALID".format(index, line))
                    continue

                pingable = Pingable(
                    data['query'], data['reverse'], data['countryCode'], data, qdn=qdn)
                pingable_list.append(pingable)
                pbar.update(i)
            pbar.finish()
    
    elif ip_version == 6:
        with open(iplistfile, 'r') as f:
            lines = f.readlines()
            validLines, slowFlag = is_slowing_needed(lines)
            pbar = progressbar.ProgressBar(max_value=len(validLines), redirect_stdout=True)
            pbar.start()
            for i, l in enumerate(validLines):
                line = l[1]
                index = l[0]
                elems = line.split(',')
                elems = [e.strip() for e in elems]
                print("Validating line {}: {}".format(str(index).rjust(2, ' '), line))
                if len(elems) == 2:
                    try:
                        qdn = QDNregex.match(elems[0]).group()
                        indirizzoIP = IPv6regex.match(elems[1]).group()
                    except:
                        print("Not a valid sequence of QDN, IP on line {} of {}".format(
                            index, iplistfile))
                        print("Please, correct this line: {}".format(line))
                        continue
                    data = ipapi_query(elems[1], slowFlag)
                    if data['status'] != 'success':
                        print(
                            "ip-api.com has not been able to resolve this QDN: {}".format(qdn))
                        continue
                    if indirizzoIP != data['query']:
                        print("Line {} of {}: IP address mismatches QDN".format(
                            index, iplistfile))
                        print("Please, correct this line: {}".format(line))
                        print(
                            "NB: ip-api.com tells that {} --> {}".format(qdn, data['query']))
                        continue

                elif len(elems) == 1:
                    match = IPv6regex.match(elems[0])
                    if not match:
                        match = QDNregex.match(elems[0])
                    if not match:
                        print("Not valid QDN or IP on line {} of {}".format(
                            index, iplistfile))
                        print("Please, correct this line: {}".format(line))
                        continue
                    query = match.group()
                    query = elems[0]
                    data = ipapi_query(query, slowFlag)
                    if data['status'] != 'success':
                        print(
                            "ip-api.com has not been able to resolve this query: {}".format(query))
                        continue
                    qdn = data['reverse'] if query == data['query'] else query
                else:
                    print("Line {}: {} is NOT VALID".format(index, line))
                    continue

                pingable = Pingable(
                    data['query'], data['reverse'], data['countryCode'], data, qdn=qdn)
                pingable_list.append(pingable)
                pbar.update(i)
            pbar.finish()

            

    print("\nFound #{} valid IP that will be pinged:".format(len(pingable_list)))
    for e in pingable_list:
        print("  {}".format(e))
    return pingable_list


def build_out_dir(outfolder='out'):
    outdir = outfolder
    print("\nBuilding output folder {}/\n".format(outdir))
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    return outfolder


def build_ping_args(IPaddress, howmany, OS, ip_version):
    command = "ping"
    ip_version_option = "-4" if ip_version == 4 else "-6"
    if OS == "posix":
        countarg, bytesizearg, numbytes, intervalarg, definterval = "-c", "-s", "56", "-i", "1"
    elif OS == "nt":
        countarg, bytesizearg, numbytes, intervalarg, definterval = "-n", "-l", "64", "-w", "1"
    return [command, IPaddress, countarg, howmany, bytesizearg, numbytes, intervalarg, definterval, ip_version_option]


def build_log_name(outdir, config, pingable):
    c = config
    elems = [c['name'], c['surname'], c['cap'],
             c['operator'], c['poa'], c['tech'], c['localtech']]
    formattedTime = datetime.now().strftime("%d%m%Y-%Hh%Mm%Ss")
    elems = [outdir+os.sep+"ping"] + elems
    elems += [pingable.nickname(), pingable.countryCode, formattedTime]
    return "_".join(elems)+".txt"

def ping(args, logname, timeout):
    #random sleep to avoid perfect synchronization
    sleep(random())
    with open(logname, 'w') as log:
        pingproc = subprocess.Popen(args, stdout=log)
        try:
            stdout, stderr = pingproc.communicate(timeout=timeout)
        except TimeoutExpired as te:
            pingproc.terminate()
            return te
        except Exception as e:
            pingproc.terminate()
            return e
    return "OK"

def run_ping_measurments(ping_list, howmany, config, OS, num_cpu, ip_version):
    outdir = build_out_dir()
    
    # timeout 50% in piu' del numero di pacchetti inviati
    num_icmp_req = int(howmany)
    timeout = num_icmp_req * 1.5

    print("PERFORMING PING COMMANDS...(in {} parallel subprocesses)".format(num_cpu))

    pbar = progressbar.ProgressBar(max_value=len(ping_list), redirect_stdout=True)
    pbar.start()

    with concurrent.futures.ProcessPoolExecutor(max_workers=num_cpu) as executor:
        futures = {}
        results = {}
        for pingable in ping_list:
            logname = build_log_name(outdir, config, pingable)
            args = build_ping_args(pingable.ip, howmany, OS, ip_version)
            fut = executor.submit(ping, args, logname, timeout)
            futures[fut] = pingable

        for future in concurrent.futures.as_completed(futures):
            arg = futures[future]
            results[arg] = future.result()
            print('Finished to ping: {}, Result: {}'.format(arg, results[arg]))
            pbar.update(len(results))
    
    pbar.finish()

    
    return outdir


def add_ipv6_list(ip):
    return Pingable(ip, "fqdn", "countrycode", "more", "qdn")