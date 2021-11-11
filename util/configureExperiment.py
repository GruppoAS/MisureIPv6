from .commons import *
import json

def read_config_file(configfile):
    if os.path.isfile(configfile):
        with open(configfile) as json_file:
            config = json.load(json_file)
        return config
    else:
        raise Exception("{} not found".format(configfile))

def configure_experiment():
    print("Please, insert the requested parameters to configure the experiments")
    # student name, surname, CAP
    name = input("Enter your first-name: ")
    while not namesurnamecode.match(name):
        name = input(
            "Please, enter your first-name as alphabetic string only: ")
    name = name.upper()

    surname = input("Enter your surname: ")
    while not namesurnamecode.match(surname):
        surname = input(
            "Please, enter your surname as alphabetic string only: ")
    surname = surname.upper()

    cap = input("Enter your CAP code: ")
    while not capcode.match(cap):
        cap = input("Please, enter your CAP code as a sequence of 5 digits: ")

    # Operator and type of Internet Connection
    poa = 'not selected'
    while poa not in points_of_access:
        poa = input(
            "Your connected to Internet from? {}\n".format(points_of_access))
        if poa.isalpha():
            poa = poa.upper()

    skipOperator = False
    if poa == 'UNIBS':
        operator = 'GARR'
        skipOperator = True

    if not skipOperator:
        operator = input("Who is your Internet Operator?: ")
        while not alphanumeric.match(operator):
            operator = input("Please, enter your operator as alphanumeric "
                             "string only (no special characters, no spaces): ")

    skip = False
    if poa == 'HOME':
        options = ["FTTC", "FTTH", "ADSL", "FWA"]
    elif poa == 'MOBILE':
        options = ["3G", "4G", "5G"]
    elif poa == "UNIBS":
        tech = "FTTC"
        skip = True
    else:
        options = ["FTTC", "FTTH", "ADSL", "FWA", "3G", "4G", "5G"]

    if not skip:
        tech = 'not selected'
    while tech not in access_technologies:
        tech = input("What's your access technology? {}\n".format(options))
        tech = tech.upper()

    if poa in ["HOME", "UNIBS"]:
        options = ["WIFI", "ETHERNET"]
        message = "You connection is over WiFi or Ethernet?"
    elif poa == "MOBILE":
        options = ["HOTSPOT", "TETHERING"]
        message = "What kind of Mobile connection?"
    elif poa == 'OTHER':
        options = ["WIFI", "ETHERNET", "HOTSPOT", "TETHERING"]
        message = "What describes better your kind of connection?"

    localtech = 'not selected'
    while localtech not in options:
        localtech = input("{} {}\n".format(message, options))
        localtech = localtech.upper()

    # Saving configurations in a config file
    config = {'name': name, 'surname': surname, 'cap': cap, 'operator': operator,
              'poa': poa, 'tech': tech, 'localtech': localtech}
    configfilename = "conf"+"_".join(config.values())+'.json'
    with open(configfilename, 'w') as fp:
        json.dump(config, fp, indent=True)

    print("Configuration concluded: this setup has been saved to {}".format(
        os.getcwd()+os.sep+configfilename))
    print("You can reuse it later using the --config option")
    return config


def setup_configuration(cfgfile=None):
    print('\n# CONFIGURING EXPERIMENTS'.ljust(60, '-'))
    need_config = True
    if cfgfile:
        try:
            config = read_config_file(cfgfile)
            need_config = False
        except Exception as e:
            print(e)
            print("Something wrong with {} configfile".format(cfgfile))
            ans = input(
                "Initialize a new configuration? {} ".format(['yes', 'no']))
            if re.match("^[Yy]", ans):
                need_config = True
            else:
                print("You can retry at anytime")
                exit()
    if need_config:
        config = configure_experiment()
    print("Configuration Summary: ")
    pprint(config)
    return config
