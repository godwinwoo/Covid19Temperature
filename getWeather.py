import urllib3
import csv
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from scipy import stats
import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
http = urllib3.PoolManager()


def get_city_weather(lat, long):
    # https://www.meteoguru.com/en/data_ret/gfs2xml_reports_daily_matrix.php?latlon=40.18238,116.4142
    url = 'www.meteoguru.com/en/data_ret/gfs2xml_reports_daily_matrix.php?latlon=' + lat + ',' + long
    response = http.request('GET', url)
    xmlstring = response.data.decode("utf-8").replace('\n', '')
    tokens = xmlstring.split(',')
    pieces = []
    start = False
    for word in tokens:
        if word.find('tmpmax') >= 0:
            pieces.append(word.split('[')[1])
            start = True
            continue
        if word.find('tmpmin') >= 0:
            break
        if start:
            pieces.append(word.strip("'[]"))
            continue

    sum = 0
    for piece in pieces:
        sum = sum + float(piece)
    return sum/len(pieces)


def get_rate_avg(counts):
    rate_sum = 0
    if len(counts) < 2:
        return 1
    for i in range(1, len(counts)):
        rate = (counts[i]/counts[i-1])-1
        rate_sum = rate_sum + rate
    avg_rate = rate_sum / i
    return avg_rate


def get_infection_rate_and_weather():
    locations = {}
    with open('Data/time_series_19-covid-Confirmed.csv') as csv_file:
        csv_reader = csv.reader(csv_file)
        row_count = 0
        for row in csv_reader:
            row_count = row_count + 1
            if row[2] == "Lat":  # skip first row
                continue
            location = row[0] + " " + row[1]
            location = location.strip()

            # get average rate that is not 0
            lookback = 5  # get moving average
            counts = []
            # for i in range(4, len(row)):
            for i in range(len(row) - lookback, len(row)):
                if row[i] != '':
                    count = int(row[i])
                    if count >= 15:  # the % increase must be meaningful
                        counts.append(count)
            if len(counts) <= 0:
                continue
            avg_rate = get_rate_avg(counts)
            avg_temp = get_city_weather(row[2], row[3])
            data = {'lat': row[2], 'long': row[3], 'rate': avg_rate, 'temp': avg_temp}

            print(location, data)
            locations[location] = data
    return locations


def label_point(x, y, val, ax):
    a = pd.concat({'x': x, 'y': y, 'val': val}, axis=1)
    for i, point in a.iterrows():
        ax.text(point['x'] + .02, point['y'], str(point['val']))


def r2(x, y):
    return stats.pearsonr(x, y)[0] ** 2


def plot(location_data):
    rates = []
    temps = []
    locations = []
    for location in location_data:
        locations.append(location)
        rates.append(location_data[location]['rate'])
        temps.append(location_data[location]['temp'])

    plot_data = {'location': locations, 'rate': rates, 'temperature': temps}
    df = pd.DataFrame(data=plot_data)
    sns.set()
    plot = sns.jointplot(x='temperature', y='rate', data=df, kind="reg", stat_func=r2)

    ax = plt.gca()
    # label_point(df.temperature, df.rate, df.location, ax)
    date = datetime.datetime.today()
    ax.set_title("Covid-19 Infection Rate vs Temperature " + date.strftime('%d-%m-%Y'))
    ax.set(ylabel="Average Daily Confirmed Infection Increase")
    ax.set(xlabel="Average 7 day High Temperature Forecast")
    plt.show()


location_data = get_infection_rate_and_weather()
plot(location_data)


