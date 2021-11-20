import os
import sys
import pandas as pd
import pycountry_convert as pc
# pycountry.countries.get(alpha_2='DE')
import seaborn as sns
from argparse import ArgumentParser
from datetime import datetime
from glob import glob
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.ticker import FuncFormatter
from matplotlib.ticker import (AutoMinorLocator, MultipleLocator)
from pandas_schema import Column, Schema
from pandas_schema.validation import DateFormatValidation, MatchesPatternValidation, InRangeValidation, InListValidation
import code  # code.interact(local=dict(globals(), **locals()))

import warnings

def main():
    warnings.filterwarnings("ignore", 'This pattern has match groups')

    # Importante fornire come argomenti sia il file .csv dei risultati delle misure con IPv4
    # che quello dei risultati delle misure con IPv6.
    args = parser.parse_args()
    finput_v4 = args.finput_v4
    finput_v6 = args.finput_v6

    # Abbiamo deciso di differenziare le cartelle dei plot in base alla versione IP,
    # in modo tale da separare i due risultati.

    #IPv4
    if not os.path.exists(finput_v4):
        print("{} does not exists".format(finput_v4), file=sys.stderr)
        exit()

    print("Loading and Validating data from IPv4 measurements...")
    data = load_data(finput_v4)

    print("\nData Loading Completed!")
    print(data)

    '''
    BUILD OUTPUT FOLDERS
    '''
    out_folders = ['plot_v4', 'plot_v4/RTT', 'plot_v4/SD', 'plot_v4/LOSSES']
    for folder in out_folders:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # Plot something nice :)
    print("\nNow plotting...")
    plotting(data, out_folders[0])

    print("\n\n\n")

    #IPv6
    if not os.path.exists(finput_v6):
        print("{} does not exists".format(finput_v6), file=sys.stderr)
        exit()

    print("Loading and Validating data from IPv6 measurements...")
    data = load_data(finput_v6)

    print("\nData Loading Completed!")
    print(data)

    '''
    BUILD OUTPUT FOLDERS
    '''
    out_folders = ['plot_v6', 'plot_v6/RTT', 'plot_v6/SD', 'plot_v6/LOSSES']
    for folder in out_folders:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # Plot something nice :)
    print("\nNow plotting...")
    plotting(data, out_folders[0])


usage = """The user MUST use the -f (or --finput) option to let this script find a file or a folder with results
            to process and plot

        -h (or --help)                   show this help message and exit
        -fv4 (or --finputv4) REQUIRED    A path to a IPv4 result (csv) file or to a folder that contains
        -fv6 (or --finputv6) REQUIRED    A path to a IPv6 result (csv) file or to a folder that contains
        more of such csv files
    \n"""
examplescript = "Try with this:\npython3 rtt_plotter.py -f ./"
desc = """This is a script to post-process rtt measurements, analyse and plot them.
    The script is prepared for the project -RTT measures- of the course Elementi di Reti,
    University of Brescia, AA 2020/21."""

parser = ArgumentParser(description=desc, usage=usage+examplescript)
parser.add_argument("-fv4", "--finputv4", dest="finput_v4", required=True,
                    action="store")
parser.add_argument("-fv6", "--finputv6", dest="finput_v6", required=True,
                    action="store")


def validate(df, ip_version):

    if ip_version == 4:
        schema = Schema([
            Column('name', [MatchesPatternValidation('^[a-zA-Z]{1,20}$')]),
            Column('surname', [MatchesPatternValidation('^[a-zA-Z]{1,20}$')]),
            Column('cap', [MatchesPatternValidation('^[0-9]{5}$')]),
            Column('operator', [MatchesPatternValidation('^\w{1,25}$')]),
            Column('poa', [InListValidation(
                ["HOME", "MOBILE", "UNIBS", "OTHER"])]),
            Column('accessTech', [InListValidation([
                "FTTC", "FTTH", "ADSL", "FWA", "3G", "4G", "5G"])]),
            Column('localTech', [InListValidation([
                "WIFI", "ETHERNET", "HOTSPOT", "TETHERING"])]),
            Column('country', [MatchesPatternValidation('^[A-Z]{2}$')]),
            Column('datetime', [DateFormatValidation('%Y-%m-%d %H:%M:%S')]),
            Column('IP', [MatchesPatternValidation(
                '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+')]),
            Column('minRTT', [InRangeValidation(1.0, 2000.0)], allow_empty=True),
            Column('avgRTT', [InRangeValidation(1.0, 2000.0)], allow_empty=True),
            Column('maxRTT', [InRangeValidation(1.0, 3000.0)], allow_empty=True),
            Column('mdevRTT', [InRangeValidation(0, 400)], allow_empty=True),
            Column('TX', [InRangeValidation(50, 1000)]),
            Column('RX', [InRangeValidation(0, 1000)]),
            Column('lost', [InRangeValidation(0.0, 100.000000001)])
        ])

    elif ip_version == 6:
        schema = Schema([
            Column('name', [MatchesPatternValidation('^[a-zA-Z]{1,20}$')]),
            Column('surname', [MatchesPatternValidation('^[a-zA-Z]{1,20}$')]),
            Column('cap', [MatchesPatternValidation('^[0-9]{5}$')]),
            Column('operator', [MatchesPatternValidation('^\w{1,25}$')]),
            Column('poa', [InListValidation(
                ["HOME", "MOBILE", "UNIBS", "OTHER"])]),
            Column('accessTech', [InListValidation([
                "FTTC", "FTTH", "ADSL", "FWA", "3G", "4G", "5G"])]),
            Column('localTech', [InListValidation([
                "WIFI", "ETHERNET", "HOTSPOT", "TETHERING"])]),
            Column('country', [MatchesPatternValidation('^[A-Z]{2}$')]),
            Column('datetime', [DateFormatValidation('%Y-%m-%d %H:%M:%S')]),
            Column('IP', [MatchesPatternValidation(
                '(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$|^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])$|^\s*((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\s*')]),
            Column('minRTT', [InRangeValidation(1.0, 2000.0)], allow_empty=True),
            Column('avgRTT', [InRangeValidation(1.0, 2000.0)], allow_empty=True),
            Column('maxRTT', [InRangeValidation(1.0, 3000.0)], allow_empty=True),
            Column('mdevRTT', [InRangeValidation(0, 400)], allow_empty=True),
            Column('TX', [InRangeValidation(50, 1000)]),
            Column('RX', [InRangeValidation(0, 1000)]),
            Column('lost', [InRangeValidation(0.0, 100.000000001)])
        ])

    errors = schema.validate(df)

    for error in errors:
        print(error)

    errors_index_rows = set([e.row for e in errors])
    data_clean = df.drop(index=errors_index_rows)
    index = ['name', 'surname', 'IP', 'datetime']
    data_clean.set_index(index)
    return data_clean


def world_cat_setter(country, continent):
    if country == 'IT':
        return 'IT'
    elif continent == 'EU' and country != 'IT':
        return 'EU'
    elif continent != 'EU':
        return 'nonEU'


def load_data(finput):
    if os.path.isfile(finput):
        df = pd.read_csv(finput, header=0)
    elif os.path.isdir(finput):
        csvfiles = glob(finput+os.sep+'results_*_*_v*.csv')
        dataframes = []
        for file in csvfiles:
            df = pd.read_csv(file, header=0)
            dataframes.append(df)
        df = pd.concat(dataframes, ignore_index=True)
        aggregate_num_records = sum([len(df) for df in dataframes])
        assert aggregate_num_records == len(df)

    ip_version = 4 if "v4" in finput else 6

    valid = validate(df, ip_version)
    # add continent and world-category columns after validation
    valid['continent'] = valid.apply(
        lambda row: pc.country_alpha2_to_continent_code(row['country']), axis=1)
    valid['worldcat'] = valid.apply(lambda row: world_cat_setter(
        row['country'], row['continent']), axis=1)
    return valid


def plot_histograms(df, plot_folder):
    print("HIST RTT...")
    data = df.avgRTT
    bin_widths = [5, 10, 20]
    for bw in bin_widths:
        ax = data.hist(bins=range(1, int(max(data))+bw, bw))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: '{:.0f}'.format(
            y/len(data)*100)))  # '{0:.0%}'.format(y/len(data)
        plt.xlabel('Mean RTT [ms]')
        plt.ylabel('Relative Frequency [%]')
        plt.title(
            'Histogram for the Mean RTT (bin-width = {})'.format(bw, int(max(data)/bw)))
        plt.xlim(1, max(data))
        tick_factor = 2 if bw < 10 else 1
        ticks = range(1, int(max(data))+bw, tick_factor*bw)
        fs = 8
        plt.xticks(ticks, rotation=90, fontsize=fs)
        ax.xaxis.set_minor_locator(AutoMinorLocator(bw))
        ax.grid(which='minor', axis='x', alpha=0.5)
        ax.grid(which='major', axis='x', alpha=1)
        plt.minorticks_on()
        plt.tight_layout()
        plt.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.13)
        plt.savefig(plot_folder+'/RTT/hist_meanRTT_bw={}.pdf'.format(bw), format='pdf')
        plt.clf()

    '''
    HISTOGRAMS FOR MEAN SD
    '''
    print("HIST SD...")
    data = df.mdevRTT
    bin_widths = [1, 2, 5]
    for bw in bin_widths:
        ax = data.hist(bins=range(0, int(max(data))+bw, bw))
        ax.yaxis.set_major_formatter(FuncFormatter(
            lambda y, _: '{:.0f}'.format(y/len(data)*100)))
        plt.xlabel('standard deviation of RTT [ms]')
        plt.ylabel('Relative Frequency [%]')
        plt.title(
            'Histogram for the standard deviation of RTT (bin-width = {})'.format(bw, int(max(data)/bw)))
        plt.xlim(0, max(data))
        ticks = range(0, int(max(data))+bw, bw)
        fs = 8
        plt.xticks(ticks, rotation=90, fontsize=fs)
        # ax.xaxis.set_minor_locator(AutoMinorLocator(bw))
        #ax.grid(which='minor', axis='x', alpha=0.5)
        ax.grid(which='major', axis='x', alpha=1)
        # plt.minorticks_on()
        plt.tight_layout()
        plt.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.13)
        plt.savefig(plot_folder+'/SD/hist_sdRTT_bw={}.pdf'.format(bw), format='pdf')
        plt.clf()

    '''
    HISTOGRAMS FOR LOSSESS
    '''
    print("HIST LOSSES...")
    data = df.lost
    # log scale for percentage...disabled :)
    '''bin_widths = [1, 2, 5, 10]
    for bw in bin_widths:
        ax = data.hist(bins=range(0, int(max(data))+bw, bw))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: '{:.0f}'.format(y/len(data)*100)))
        plt.xlabel('Lost packets [%]')
        plt.ylabel('Relative Frequency [%] (log-scale)')
        plt.title(
            'Histogram for the Percentage of Lost Packets (bin-width = {})'.format(bw))
        plt.xlim(0, 100)
        plt.yscale('log')
        ax.xaxis.set_major_locator(MultipleLocator(5))
        ax.xaxis.set_minor_locator(AutoMinorLocator(1))
        ax.grid(which='minor', axis='x', alpha=0.5)
        ax.grid(which='major', axis='x', alpha=1)
        plt.minorticks_on()
        plt.tight_layout()
        plt.subplots_adjust(left=0.1, right=0.97, top=0.9, bottom=0.12)
        plt.savefig(
            plot_folder+'/LOSSES/histLOG_losses_bw={}.pdf'.format(bw), format='pdf')
        plt.clf()'''

    bin_widths = [1, 2, 3, 5]
    for bw in bin_widths:
        ax = data.hist(bins=range(0, int(max(data))+bw, bw))
        ax.yaxis.set_major_formatter(FuncFormatter(
            lambda y, _: '{:.0f}'.format(y/len(data)*100)))
        plt.xlabel('Lost packets [%]')
        plt.ylabel('Relative Frequency [%]')
        plt.title(
            'Histogram for the Percentage of Lost Packets (bin-width = {})'.format(bw))
        plt.xlim(0, 100)
        ax.xaxis.set_major_locator(MultipleLocator(5))
        ax.xaxis.set_minor_locator(AutoMinorLocator(1))
        ax.grid(which='minor', axis='x', alpha=0.5)
        ax.grid(which='major', axis='x', alpha=1)
        plt.minorticks_on()
        plt.tight_layout()
        plt.subplots_adjust(left=0.1, right=0.97, top=0.9, bottom=0.12)
        plt.savefig(
            plot_folder+'/LOSSES/hist_losses_bw={}.pdf'.format(bw), format='pdf')
        plt.clf()


def poa_comparison(df, plot_folder):
    print("Comparison plots for Point-Of-Access...")

    # 1) BarChart meanRTT 4 poa
    # Filtering data
    dfcasa = df[df['poa'] == 'HOME']
    dfcell = df[df['poa'] == 'MOBILE']
    dfubs = df[df['poa'] == 'UNIBS']
    dfother = df[df['poa'] == 'OTHER']

    casa = dfcasa.avgRTT.mean()
    cell = dfcell.avgRTT.mean()
    ubs = dfubs.avgRTT.mean()
    other = dfother.avgRTT.mean()

    meanRTTs = [casa, cell, ubs, other]
    x = range(len(meanRTTs))
    for i in x:
        plt.bar(x[i], meanRTTs[i], edgecolor='black')

    plt.ylabel("mean RTT [ms]")
    plt.xlabel("Point of Access")
    plt.xticks(x, ['HOME', 'MOBILE', 'UNIBS', 'OTHER'])
    plt.subplots_adjust(left=0.1, right=0.95, top=0.97, bottom=0.1)
    plt.savefig(plot_folder+"/meanRTTmeanCOMPARISON.pdf", format='pdf')
    plt.clf()

    # 2) Boxplot of meanRTT 4 poa
    meanpointprops = dict(marker='_', markeredgecolor='black',
                          markerfacecolor='firebrick')
    meanlineprops = dict(linestyle='--', linewidth=1.2, color='red')
    flierprops = dict(marker='x', markerfacecolor='black', markersize=5,
                      linestyle='none')

    ax = sns.boxplot(x=df['poa'], y=df['avgRTT'], showfliers=True,
                     flierprops=flierprops, showmeans=True, meanline=True, meanprops=meanlineprops)
    # plt.setp(ax.get_xticklabels(), rotation=70, fontsize=8)
    plt.xlabel('Point of Access')
    plt.ylabel('RTT distribution [ms]')
    plt.grid()
    ax.set_axisbelow(True)
    # plt.subplots_adjust(left=0.13, right=0.95, top=0.95, bottom=0.23)
    plt.savefig(plot_folder+"/meanRTT-distribCOMPARISON.pdf", format='pdf')
    plt.clf()

    # 3) Boxplot 4 poa X [ITA, EU, rest of the world]
    ax = sns.boxplot(x=df['poa'], y=df['avgRTT'], hue=df['worldcat'], showfliers=True,
                     flierprops=flierprops, showmeans=True, meanline=True, meanprops=meanlineprops)
    plt.xlabel('Point of Access')
    plt.ylabel('RTT distribution [ms]')
    plt.grid()
    ax.set_axisbelow(True)
    # plt.subplots_adjust(left=0.13, right=0.95, top=0.95, bottom=0.23)
    plt.savefig(
        plot_folder+"/meanRTT-distribCOMPARISON-by-WORLDCATEGORIES.pdf", format='pdf')
    plt.clf()

    # 3) Boxplot 4 poa X CONTINENT
    ax = sns.boxplot(x=df['poa'], y=df['avgRTT'], hue=df['continent'], showfliers=True,
                     flierprops=flierprops, showmeans=True, meanline=True, meanprops=meanlineprops)
    plt.xlabel('Point of Access')
    plt.ylabel('RTT distribution [ms]')
    plt.grid()
    ax.set_axisbelow(True)
    # plt.subplots_adjust(left=0.13, right=0.95, top=0.95, bottom=0.23)
    plt.savefig(plot_folder+"/meanRTT-distribCOMPARISON-by-CONTINENT.pdf", format='pdf')
    plt.clf()

def violin_plot_poa(df, plot_folder):
    print("Violin plots for Point-Of-Access...")
    #code.interact(local=dict(globals(), **locals()))

    # Violino con boxplot miniaturizzato
    ax = sns.violinplot(x=df['poa'], y=df['avgRTT'], inner='box')
    plt.xlabel('Point of Access')
    plt.ylabel('RTT distribution [ms]')
    plt.grid()
    ax.set_axisbelow(True)
    plt.savefig(plot_folder+"/POA-violin-box.pdf", format='pdf')
    plt.clf()

    # solo con 1o 2o e 3o quartile segnati
    ax = sns.violinplot(x=df['poa'], y=df['avgRTT'], inner='quartile')
    plt.xlabel('Point of Access')
    plt.ylabel('RTT distribution [ms]')
    plt.grid()
    ax.set_axisbelow(True)
    plt.savefig(plot_folder+"/POA-violin-quartili.pdf", format='pdf')
    plt.clf()
    
    # con osservazioni scatter allineate
    ax = sns.violinplot(x=df['poa'], y=df['avgRTT'], inner='point')
    plt.xlabel('Point of Access')
    plt.ylabel('RTT distribution [ms]')
    plt.grid()
    ax.set_axisbelow(True)
    plt.savefig(plot_folder+"/POA-violin-scatter.pdf", format='pdf')
    plt.clf()

    # strano simpatico stile "boxen"
    ax = sns.boxenplot(x=df['poa'], y=df['avgRTT'])
    plt.xlabel('Point of Access')
    plt.ylabel('RTT distribution [ms]')
    plt.grid()
    ax.set_axisbelow(True)
    plt.savefig(plot_folder+"/POA-violin-boxen.pdf", format='pdf')
    plt.clf()

    #ax = sns.violinplot(x=df['poa'], y=df['avgRTT'], inner=None)
    #sns.stripplot(x=df['poa'], y=df['avgRTT'], color="k", size=3, ax=ax)
    #plt.show()
    #plt.clf()

    #code.interact(local=dict(globals(), **locals()))

    dfCasaOrMobile = df[df['poa'] != 'OTHER']
    ax = sns.violinplot(x=dfCasaOrMobile['worldcat'], y=dfCasaOrMobile['avgRTT'],
        hue=dfCasaOrMobile['poa'], split=True, inner='quartile')
    plt.xlabel('Geographic Location')
    plt.ylabel('RTT distribution [ms]')
    plt.grid()
    plt.legend(title = 'Point of Access to Internet')
    ax.set_axisbelow(True)
    plt.savefig(plot_folder+"/POA-violin-HOMEvsMOBILE-byWORLDCAT.pdf", format='pdf')
    plt.clf()

    ax = sns.violinplot(x=dfCasaOrMobile['continent'], y=dfCasaOrMobile['avgRTT'],
        hue=dfCasaOrMobile['poa'], split=True, inner='quartile')
    plt.xlabel('Geographic Location')
    plt.ylabel('RTT distribution [ms]')
    plt.grid()
    plt.legend(title = 'Point of Access to Internet')
    ax.set_axisbelow(True)
    plt.savefig(plot_folder+"/POA-violin-HOMEvsMOBILE-byContinent.pdf", format='pdf')
    plt.clf()


def violin_plot_operators(df, plot_folder):
    
    meanlineprops = dict(linestyle='--', linewidth=1.2, color='red')
    df['operator'] = df['operator'].str.upper()
    

    df['operator'] = df['operator'].str.replace("TELECOMITALIA","TIM")
    df['operator'] = df['operator'].str.replace("TELECOM", "TIM")
    df['operator'] = df['operator'].str.replace("WINDTRE", "WIND")
    my_dict = {} #conto ping per operatore

    tot = 0 
    for op in df.operator.unique():
        numMis = len(df[df.operator == op])
        tot += numMis
        print("Num misurazioni x {} = {}".format(op, numMis))
        if numMis < 200: #rimuovi operatori con meno di 300 ping
            index = df[df['operator'] == op].index
            df.drop(index, inplace=True)

    print("Totale misurazioni: {}".format(tot))
    #code.interact(local=dict(globals(), **locals()))

    '''for d in df['operator']:
        if d in my_dict:
            my_dict[d] += 1
        else:
            my_dict[d] = 1

    for key, values in my_dict.items():
        if values < 300: #rimuovi operatori con meno di 300 ping
            index = df[df['operator'] == key].index
            df.drop(index, inplace=True)'''

    dfCasaOrMobile = df[df['poa'] != 'OTHER']
    ax = sns.violinplot(x=dfCasaOrMobile['operator'], y=dfCasaOrMobile['avgRTT'],
        hue=dfCasaOrMobile['poa'], split=True, inner='quartile')
    plt.xlabel('Operator')
    plt.ylabel('RTT distribution [ms]')
    plt.grid()
    plt.legend(title = 'Point of Access to Internet')
    ax.set_axisbelow(True)
    plt.setp(ax.get_xticklabels(), rotation=20, fontsize=8)
    plt.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.2)
    plt.savefig(plot_folder+"/OPERATOR-violin-HOMEvsMOBILE-byContinent.pdf", format='pdf')
    plt.clf()

    #confronto operatori HOME
    dfHOME = df[df['poa'] == 'HOME']
    ax = sns.violinplot(x=dfHOME['operator'], y=dfHOME['avgRTT'], inner='quartile')
    plt.xlabel('Operator at HOME')
    plt.ylabel('RTT distribution [ms]')
    plt.grid()
    ax.set_axisbelow(True)
    plt.setp(ax.get_xticklabels(), rotation=20, fontsize=8)
    #plt.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.2)
    plt.savefig(plot_folder+"/OPERATORcomparisonHOME.pdf", format='pdf')
    plt.clf()


    #confronto operatori MOBILE
    data = df[df['poa'] == 'MOBILE']
    ax = sns.violinplot(x=data['operator'], y=data['avgRTT'], inner='quartile')
    plt.xlabel('Mobile Operator')
    plt.ylabel('RTT distribution [ms]')
    plt.grid()
    ax.set_axisbelow(True)
    plt.setp(ax.get_xticklabels(), rotation=20, fontsize=8)
    #plt.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.2)
    plt.savefig(plot_folder+"/OPERATORcomparisonMOBILE.pdf", format='pdf')
    plt.clf()





def boxplot_accessTechs(df, plot_folder):
    pass

def plotting(data, plot_folder):

    # plot_folder specifica in quale cartella vanno salvati i plot, in base alla versione di IP.

    plt.rc('axes', axisbelow=True)
    plt.figure(figsize=(9, 4.5))

    # histograms of all RTT stats
    plot_histograms(data, plot_folder)

    # boxplot per punto-di-accesso e operator
    poa_comparison(data, plot_folder)

    boxplot_accessTechs(data, plot_folder)

    #violin_plot_poa(data, violin_plot_poa)

    #violin_plot_operators(data, violin_plot_poa)

if __name__ == "__main__":
    main()
