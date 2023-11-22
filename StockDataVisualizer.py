import requests
import csv
import json
import pygal
from datetime import datetime
from flask import Flask, render_template, request, abort

app = Flask(__name__)
app.config["DEBUG"] = True
app.config['SECRET_KEY'] = 'your_secret_key'


def get_symbol(request):

    symbol = request.form['symbol']
    return symbol

def get_chart(request):
    chart_type = request.form['chart_type']
    return 'Bar' if chart_type == '1' else 'Line'

def get_time_series(request):

    number = int(request.form['time_series'])
    if number == 1:
        return ['INTRADAY', '60min']
    elif number == 2:
        return ['DAILY', 'null']
    elif number == 3:
        return ['WEEKLY', 'null']
    elif number == 4:
        return ['MONTHLY', 'null']
    else:
        abort(400)

def get_dates(request):

    start_date = request.form['start_date']
    end_date = request.form['end_date']

    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

    if end_date_obj < start_date_obj:
        abort(400)

    return [start_date_obj, end_date_obj]

def generate_chart(symbol, chart_type, time_series, start_end, symbols):

    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_{}&symbol={}&interval={}&apikey=9I22O100RNSZ6IPR'.format(time_series[0], symbol, time_series[1])

    response = requests.get(url)
    data = json.loads(response.text)

    i = 0

    key = ""

    for item in data:

        if i == 1:
            key = item
        i += 1

    dates = []

    for item in data[key]:

        dates.append(item)

    usable_dates = []
    open_values = []
    high_values = []
    low_values = []
    close_values = []

    for x in dates:

        x_time_obj = datetime.strptime(x, '%Y-%m-%d')

        if x_time_obj >= start_end[0] and x_time_obj <= start_end[1]:

            usable_dates.append(x) 
            
            for item in data[key][x]:

                if 'open' in item:

                    open_values.append(float(data[key][x][item]))

                elif 'high' in item:

                    high_values.append(float(data[key][x][item]))

                elif 'low' in item:

                    low_values.append(float(data[key][x][item]))

                elif 'close' in item:

                    close_values.append(float(data[key][x][item]))
    
    usable_dates = usable_dates[::-1]

    if chart_type == 'Bar':
        chart = pygal.Bar(x_label_rotation=45)
    elif chart_type == 'Line':
        chart = pygal.Line(x_label_rotation=45)

    chart.title = 'Stock Data for {}: {} to {}'.format(symbols[0], str(start_end[0]), str(start_end[1]))
    chart.x_labels = [x for x in usable_dates]
    chart.add('open', open_values)
    chart.add('high', high_values)
    chart.add('low', low_values)
    chart.add('close', close_values)

    chart_path = 'static/{}_chart.svg'.format(symbol.lower())
    chart.render_to_file(chart_path)

    return chart_path

def get_symbols():
    symbols = []
    file_path = '/Users/coltonsharp/Documents/MIZZOU/SoftwareEngin/Project3/Project3_Files/stocks.csv'
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            symbols.append(row[0]) 
    return symbols

@app.route('/', methods=['GET', 'POST'])
def home():
    symbols = get_symbols()
    if request.method == 'POST':
        symbol = get_symbol(request)
        chart_type = get_chart(request)
        time_series = get_time_series(request)
        start_end = get_dates(request)

        chart_path = generate_chart(symbol, chart_type, time_series, start_end, symbols)

        return render_template('index.html', symbols=symbols, chart_path=chart_path)
    
    return render_template('index.html', symbols=symbols)

app.run(host="0.0.0.0", port=5001, debug=True)
