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
    flag = True # le queries saranno molto probabilmente più di 45 al minuto
    if flag:
        print("SLOWING DOWN QUERIES")
    return validLines, flag


def validate_ip_list(iplistfile):
    print('\n# BUILDING LIST OF PING COMMANDS TO BE EXECUTED'.ljust(60, '-'))
    print("Scanning IPlist.csv to validate IP addresses and QDNs...")
    
    # Numero di volte in cui si verifica se IPv4 e IP di QDN coincidono (nel caso in cui una QDN sia associata a piu' IPv4)
    n_prove = 5

    pingable_list_v4 = []
    pingable_list_v6 = []

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
            
            if len(elems) == 3:
                try:
                    qdn = QDNregex.match(elems[0]).group()
                    IPv4 = IPv4regex.match(elems[1]).group()
                    IPv6 = IPv6regex.match(elems[2]).group()
                except:
                    print("Not a valid sequence of QDN, IP on line {} of {}".format(
                        index, iplistfile))
                    print("Please, correct this line: {}".format(line))
                    continue

                data_QDN = ipapi_query(elems[0], slowFlag)
                if data_QDN['status'] != 'success':
                    print("ip-api.com has not been able to resolve this QDN: {}".format(qdn))
                    break

                check_v4 = False
                data_v4 = ipapi_query(elems[1], slowFlag)
                if data_v4['status'] != 'success':
                    print("ip-api.com has not been able to resolve this IPv4: {}".format(IPv4))
                    break
                for i in range(1, n_prove):
                    data_QDN = ipapi_query(elems[0], slowFlag)
                    if IPv4 != data_QDN['query']:
                        continue
                    else:
                        check_v4 = True
                        break

                if not check_v4:
                    print("Line {} of {}: IPv4 address mismatches QDN".format(index, iplistfile))
                    print("Please, correct this line: {}".format(line))
                    print("NB: ip-api.com tells that {} --> {}".format(qdn, data_v4['query']))
                else:
                    check_v6 = True
                    data_v6 = ipapi_query(elems[2], slowFlag)
                    if data_v6['status'] != 'success':
                        print("ip-api.com has not been able to resolve this IPv6: {}".format(IPv6))
                        break

                    #Controlliamo che l'IPv4 e l'IPv6 considerati provengano per lo meno dalla stessa regione.
                    #Abbiamo deciso di affidarci a questo stratagemma per evitare errori dovuti alla molteplicità
                    #di indirizzi IPv6 legati al medesimo sito locati in regioni differenti rispetto all'IPv4.
                    if data_v6['regionName'] != data_v4['regionName']:
                        check_v6 = False
                        print("IPv4 and IPv6 are not located in the same region.")
                
                if not check_v4 or not check_v6:
                    print("Line {}: {} is NOT VALID".format(index, line))
                    continue
            
            else:
                print("Line {}: {} is NOT VALID".format(index, line))
                continue
            
            if check_v4 and check_v6:
                pingable_v4 = Pingable(data_v4['query'], data_v4['reverse'], data_v4['countryCode'], data_v4, qdn=qdn)
                pingable_list_v4.append(pingable_v4)
                pingable_v6 = Pingable(data_v6['query'], data_v6['reverse'], data_v6['countryCode'], data_v6, qdn=qdn)
                pingable_list_v6.append(pingable_v6)
            pbar.update(i)
        pbar.finish()


    print("\nFound #{} valid IP that will be pinged:".format(len(pingable_list_v4)))
    pingable_list_v4[0].ip 
    for i in range(len(pingable_list_v4)):
        print("  IPv4: {}   IPv6: {}   QDN: {}   [{}]".format(pingable_list_v4[i].ip.ljust(16), pingable_list_v6[i].ip.ljust(40), 
            pingable_list_v4[i].qdn.ljust(30), pingable_list_v6[i].countryCode))

    return pingable_list_v4, pingable_list_v6


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

    # Creiamo due cartelle out, una per misurazioni con IPv4 ed una per misurazioni con IPv6
    outdir = build_out_dir(outfolder="out_v4") if ip_version == 4 else build_out_dir(outfolder="out_v6")
    
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