from util.commons import *
from util.configureExperiment import setup_configuration
from util.exprunner import validate_ip_list, add_ipv6_list, run_ping_measurments
from util.postprocess import process_logs
from argparse import ArgumentParser


usage = """Run this script without arguments or, if you have a configuration-file, pass it via the -c (--config) option.
    -h gives you a help message
    -c (or --config)      OPTIONAL argument to provide a configuration file
    -n (or --numping)     OPTIONAL argument to indicate the number of icmp_echo_request to be sent
                          with each ping command. The default value is 100
    -p (or --postprocess) OPTIONAL argument to provide the folder that contains the log that must be postprocessed.
                          If --postprocess is set, the script will just postprocess logs, without performing new experiments
    -j (or --numcores)    OPTIONAL argument to indicate how many processes shall be used to launch many ping commands in parallel
    \n"""
examplescript = "Try with this:\npython3 autoping.py"
desc = """This is a script to configure and perform ping experiments, also elaborating and recording data.
    The script is prepared for the project -RTT measures- of the course Elementi di Reti,
    University of Brescia, AA 2020/21.
    The || sign means a choice -logical OR. Options are case sensitive."""

parser = ArgumentParser(description=desc, usage=usage+examplescript)
parser.add_argument("-c", "--config", dest="configfile", required=False,
                    default="", action="store")
parser.add_argument("-n", "--numping", dest="numping", required=False,
                    default="100", action="store")
parser.add_argument("-p", "--postprocess", dest="postprocess", required=False,
                    default="", action='store')
parser.add_argument("-j", "--numcores", dest="numcores", required=False, type=int, choices=range(1, 33),
                    default=4, action='store')

OS = 'undefined'

def check_OS():
    global OS
    OS = os.name
    if OS not in ['posix', 'nt']:
        print("Unsupported Operating System")
        exit()


def check_requirements():
    global iplistfile4
    iplistfile4 = 'IPv4list.txt'
    global iplistfile6
    iplistfile6 = 'IPv6list.txt'

    # verifica che IPlist.csv esiste nella working directory
    if not (os.path.isfile(iplistfile4) or os.path.isfile(iplistfile6)):
        print("""The folder where you run this script must contain the file IPlist.txt,
              which is the file that lists all the IP addresses or QDNs to be pinged.
              Your working directory is: {}
              but it does not contain the IPlist.txt file""".format(os.getcwd()))
        exit()


if __name__ == "__main__":
    args = parser.parse_args()
    only_postprocess = args.postprocess

    # FASE 0: controllo requisiti e customizzazione OS-dependent
    check_OS()
    if not only_postprocess:
        check_requirements() # Aggiunta controllo per file di IPv6

        # FASE 1: configurazione esperimento (con o senza configuration file)
        config = setup_configuration(args.configfile)

        # FASE 2: scelta versione IP
        ip_version = 6 if input("Vuoi utilizzare IPv4? Y/n ").lower() == "n" else 4

        # FASE 3: esecuzione esperimenti
        if ip_version == 4:     
            ping_list = validate_ip_list(iplistfile4, ip_version)
        else:
            ping_list = validate_ip_list(iplistfile6, ip_version)

        howmany = args.numping
        numcores = args.numcores
        outdir = run_ping_measurments(ping_list, howmany, config, OS, numcores, ip_version)

        print("-"*60)

    # FASE 4: elaborazione risultati
    if only_postprocess:
        if not os.path.isdir(args.postprocess):
            print("Log folder {} cannot be found ".format(args.postprocess))
            exit()
    logfolder = args.postprocess if only_postprocess else outdir
    errors = process_logs(logfolder, OS, ip_version)