#!/usr/bin/python3

#https://api.github.com/repos/tensorflow/tensorflow/pulls?state=merged
import json
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, date, timedelta
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys

plt.rcParams.update({'font.size': 22})

import pickle

NLARGEST=15

PROJECT_BASE = sys.argv[1]
PROJECT_NAME = sys.argv[2]

if not os.path.exists(PROJECT_NAME + '-stats'):
        os.makedirs(PROJECT_NAME + '-stats')

'''
PICKLE_DUMP = 'project-dump.pkl'

json_list = []
dframe_list = []

#url = 'https://api.github.com/users/chenlichao'
#print("URL", url)
#json_response = requests.get(url, auth=HTTPBasicAuth('srkreddy1238', '5438@Reset'))
#print(json.dumps(json.loads(json_response.text), indent=4, sort_keys=True))
#exit(0)


if os.path.exists(PICKLE_DUMP):
    with open(PICKLE_DUMP, 'rb') as infile:
        json_list = pickle.load(infile)
else:
    page_no = 1
    while True :
        url = 'https://api.github.com/repos/' + PROJECT_BASE + '/' + PROJECT_NAME + '/pulls?state=all&page=' + str(page_no)
        print("URL", url)
        json_response = requests.get(url, auth=HTTPBasicAuth('srkreddy1238', '5438@Reset'))
        print("Response:", json_response.status_code)
        if json_response.status_code != 200:
            break

        page_no = page_no + 1 
        json_records = json.loads(json_response.text)
        print("REC Len:", len(json_records))
        if len(json_records) == 0:
            break
        json_list.append(json_records)

    with open(PICKLE_DUMP, 'wb') as outfile:
        pickle.dump(json_list, outfile)

print("List Len:", len(json_list))
#print(json.dumps(json_list[0][0], indent=4, sort_keys=True))

'''

def make_pr_df_from_json():
    for json_rec in json_list:
        # Skip closed / abondned PR's
        if json_rec['state'] == 'closed' and not json_rec['merged_at']:
            continue
        frame = {}
        frame['pull_id'] = json_rec['number']
        frame['user'] = json_rec['user']['login']
        frame['title'] = json_rec['title']
        frame['created_at'] = datetime.strptime(json_rec['created_at'], '%Y-%m-%dT%H:%M:%SZ')
        frame['state'] = json_rec['state']

commit_df = pd.read_csv(PROJECT_BASE + '/' + PROJECT_NAME + '/' + PROJECT_NAME + '-log.csv', sep='\|')
commit_df['DATE'] = pd.to_datetime(commit_df['DATE'])
commit_df['MONTH'] = commit_df.DATE.dt.strftime('%Y%m').astype(str)
commit_df['YEAR'] = commit_df.DATE.dt.strftime('%Y').astype(str)
commit_df['WEEK'] = commit_df.DATE.dt.week
print(commit_df.head())

# Top 10 organization wise commits, KLOC and members investment
lcommits = commit_df.groupby(['DOMAIN']).size().nlargest(10)
lkloc = commit_df[['DOMAIN', 'LINES']].groupby(['DOMAIN']).agg('sum').nlargest(10, ['LINES'])
orgs_of_interest = set(list(lcommits.index) + list(set(lkloc.index) - set(lcommits.index)))


def draw_over_all_stats():
    def draw_fig(fig, rows, cols, fig_id, x_vals, y_vals, x_label, y_label, title, rotation=60, color='orange'):
        fig.add_subplot(rows, cols, fig_id)
        plt.bar(x_vals, y_vals, linewidth=2.0, color=color)
        plt.tight_layout()
        plt.title(title)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.xticks(rotation=rotation)
        return

    # Over all commits, KLOC and members
    fig = plt.figure(figsize=(45, 20))

    l = commit_df.groupby(['YEAR']).size()
    draw_fig(fig, 2, 3, 1, l.index, l.values, 'Year', 'Commits', "Year Wise Commits", color='orange')

    l = commit_df[commit_df.YEAR.isin(['2017', '2018', '2019'])].groupby(['MONTH']).size()
    draw_fig(fig, 2, 3, 2, l.index, l.values, 'Month', 'Commits', "2 Year Commits", color='blue')

    l = commit_df.groupby(['YEAR'])['EMAIL'].nunique()
    draw_fig(fig, 2, 3, 3, l.index, l.values, 'Year', 'Members', "Yearly Active Members", color='orange')

    l = commit_df[['YEAR', 'LINES']].groupby(['YEAR']).agg('sum')
    draw_fig(fig, 2, 3, 4, l.index, np.array(l.values/1000).flatten(), 'Year', 'KLOC', "Yearly KLOC", color='red')

    l = commit_df[commit_df.YEAR.isin(['2017', '2018', '2019'])][['MONTH', 'LINES']].groupby(['MONTH']).agg('sum')
    draw_fig(fig, 2, 3, 5, l.index, np.array(l.values/1000).flatten(), 'Month', 'KLOC', "2 Year KLOC Trend", color='green')

    l = commit_df[commit_df.YEAR.isin(['2017', '2018', '2019'])].groupby(['MONTH'])['EMAIL'].nunique()
    draw_fig(fig, 2, 3, 6, l.index, l.values, 'Month', 'Members', "Last 2 Year Active Members", color='blue')

    plt.savefig(PROJECT_NAME + '-stats/' + PROJECT_NAME + '-Overall-Stats.png')

    # All Organization commits, KLOC and members
    fig = plt.figure(figsize=(20, 15))

    l = commit_df.groupby(['DOMAIN']).size().nlargest(NLARGEST)
    draw_fig(fig, 1, 3, 1, l.index, l.values, 'Domain', 'Commits', "Domain Wise Commits", 90, color='orange')

    l = commit_df[['DOMAIN', 'LINES']].groupby(['DOMAIN']).agg('sum').nlargest(NLARGEST, ['LINES'])
    draw_fig(fig, 1, 3, 2, l.index, np.array(l.values/1000).flatten(), 'Domain', 'KLOC', "Domain wise KLOC", 90, color='blue')

    l = commit_df.groupby(['DOMAIN'])['EMAIL'].nunique().nlargest(NLARGEST)
    draw_fig(fig, 1, 3, 3, l.index, l.values, 'Domain', 'Members', "Domain Wise Members", 90, color='green')

    plt.savefig(PROJECT_NAME + '-stats/' + PROJECT_NAME + '-Domain-Overall-Stats.png')

    cols = 4
    rows = len(orgs_of_interest)
    fig = plt.figure(figsize=(cols * 10, 10 * rows))
    for idx, org in enumerate(orgs_of_interest):
        l = commit_df[commit_df.DOMAIN == org].groupby(['YEAR']).size()
        draw_fig(fig, rows, cols, (idx*cols) + 1 , l.index, l.values, 'Year', 'Commits', org + "  Yearly Commits", color='orange')

        l = commit_df[commit_df.DOMAIN == org][['YEAR', 'LINES']].groupby(['YEAR']).agg('sum')
        draw_fig(fig, rows, cols, (idx*cols) + 2 , l.index, np.array(l.values/1000).flatten(), 'Year', 'KLOC', org + "  Yearly KLOC", color='green')

        l = commit_df[commit_df.DOMAIN == org].groupby(['YEAR'])['EMAIL'].nunique()
        draw_fig(fig, rows, cols, (idx*cols) + 3 , l.index, l.values, 'Year', 'Members', org + "  Yearly Members", color='orange')

        l = commit_df[commit_df.DOMAIN == org].groupby(['MONTH'])['EMAIL'].nunique()
        draw_fig(fig, rows, cols, (idx*cols) + 4 , l.index, l.values, 'MONTH', 'Members', org + "  2 Years Monthly Members", color='green')

    plt.savefig(PROJECT_NAME + '-stats/' + PROJECT_NAME + '-Orgwise-Stats.png')
    
draw_over_all_stats()

def dump_module_stats():
    module_df = pd.read_csv(PROJECT_BASE + '/' + PROJECT_NAME + '/' + PROJECT_NAME + '-modules-uniq.csv', sep='\|')
    print(module_df.head())

    merged_df = pd.merge(module_df, commit_df, on = 'SHA', how = 'left')
    print(merged_df.head(20))

    l = module_df.groupby(['SUBMODULE']).size().nlargest(NLARGEST)
    l.to_csv(PROJECT_NAME + '-stats/' + PROJECT_NAME + '-Top-Modules.csv')

    l = module_df[merged_df.YEAR.isin(['2018', '2019'])].groupby(['SUBMODULE']).size().nlargest(NLARGEST)
    l.to_csv(PROJECT_NAME + '-stats/' + PROJECT_NAME + '-2Years-Top-Modules.csv')


    for year in ['2016', '2017', '2018', '2019'] :
        l = merged_df[merged_df.YEAR == year].groupby(['SUBMODULE'])['SHA'].size().nlargest(NLARGEST)
        l.to_csv(PROJECT_NAME + '-stats/' + PROJECT_NAME + '-' + year + '-Top-Modules.csv')

    for org in orgs_of_interest:
        l = merged_df[merged_df.DOMAIN == org][merged_df.YEAR.isin(['2018', '2019'])].groupby(['SUBMODULE'])['SHA'].size().nlargest(NLARGEST)
        l.to_csv(PROJECT_NAME + '-stats/' + PROJECT_NAME + '-2-Year-' + org + '-Top-Modules.csv')


dump_module_stats()


EMAIL_SUBSCRIBERS='sivar.b@huawei.com'
#EMAIL_SUBSCRIBERS='sivar.b@huawei.com,siju.samuel@huawei.com'

# Send Mail
body_head = []
body_tail = []

body_head.append("Hello All,<br>")
body_head.append("<br>")
body_head.append("<br>")
body_head.append("This is an alert from Open Source Project Monitor - " + PROJECT_NAME)
body_head.append("<br>")
body_head.append("<br>")

body_tail.append("Regards,<br>")
body_tail.append("Admin-Siva(283218)<br>")
body_tail.append("For any support please write to : sivar.b@huawei.com<br>")


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
import csv
from tabulate import tabulate

attachements = [ PROJECT_NAME + '-stats/' + PROJECT_NAME + '-Overall-Stats.png', PROJECT_NAME + '-stats/' + PROJECT_NAME + '-Domain-Overall-Stats.png', PROJECT_NAME + '-stats/' + PROJECT_NAME + '-Orgwise-Stats.png' ]
attachment_body = []
#for attach in attachements:
#	attachment_body.append('<br><img src="cid:' + attach + '"><br>')

msg = MIMEMultipart()
msg["To"] = EMAIL_SUBSCRIBERS
msg["From"] = 'qrelay@gmail.com'
msg["Subject"] = 'Open Source Project Stats Report - ' + PROJECT_NAME

for attach in attachements:
  fp = open(attach, 'rb')
  img = MIMEImage(fp.read())
  fp.close()
  #img.add_header('Content-ID', '<{}>'.format(attach))
  img.add_header('Content-Disposition', "attachment; filename= %s" % attach)
  msg.attach(img)

# Attach tables

html = """
<p><b><u>{heading}</u></b></p>
{table}
"""

with open(PROJECT_NAME + '-stats/' + PROJECT_NAME + '-Top-Modules.csv') as input_file:
    reader = csv.reader(input_file)
    data = list(reader)
    final_html = html.format(table=tabulate(data, tablefmt="html"), heading='Top Modules by Commits')
    attachment_body.append(final_html)

with open(PROJECT_NAME + '-stats/' + PROJECT_NAME + '-2Years-Top-Modules.csv') as input_file:
    reader = csv.reader(input_file)
    data = list(reader)
    final_html = html.format(table=tabulate(data, tablefmt="html"), heading='Top Modules by Commits - 2 Years')
    attachment_body.append(final_html)

for year in ['2016', '2017', '2018', '2019'] :
    with open(PROJECT_NAME + '-stats/' + PROJECT_NAME + '-' + year + '-Top-Modules.csv') as input_file:
        reader = csv.reader(input_file)
        data = list(reader)
        final_html = html.format(table=tabulate(data, tablefmt="html"), heading='Top Modules by Commits - ' + year)
        attachment_body.append(final_html)

for org in orgs_of_interest:
    with open(PROJECT_NAME + '-stats/' + PROJECT_NAME + '-2-Year-' + org + '-Top-Modules.csv') as input_file:
        reader = csv.reader(input_file)
        data = list(reader)
        final_html = html.format(table=tabulate(data, tablefmt="html"), heading='2 Year Top Modules - ' + org)
        attachment_body.append(final_html)

msgText = MIMEText('<b>%s</b>%s<br><b>%s</b>' % (''.join(body_head), ''.join(attachment_body), ''.join(body_tail)), 'html')  
msg.attach(msgText)   # Added, and edited the previous line

if os.path.exists("/tmp/project-stats.txt"):
    os.remove("/tmp/project-stats.txt")

f = open("/tmp/project-stats.txt", "a")
f.write(msg.as_string())
f.close()

cmd = "/usr/sbin/ssmtp -v " + EMAIL_SUBSCRIBERS + "  < /tmp/project-stats.txt"
cmd_ret = os.system(cmd)
print("CMD RET", cmd_ret)

