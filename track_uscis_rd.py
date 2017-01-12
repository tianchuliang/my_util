# at terminal window, run:
# python track_uscis_rd.py <rd_process_center argument> <rd_date_start argument> <rd_date_end argument> <rd_form argument>

import re 
import mechanize
from lxml import html 
from bs4 import BeautifulSoup
import os 
import sys
from termcolor import colored
import glob
from time import gmtime, strftime
import datetime
import copy 

rd_url = 'http://www.mycasetracker.org/index.php?dest=rd'
rd_process_center = "SRC"
rd_form = "I131"
rd_date_start = "2016-10-03"
rd_date_end = "2016-10-08"
received_key = 'Case Was Approved'
approved_key = 'Case Was Received'
log_file_dir = '/logs'
back_look = 1 

if not os.path.exists(os.getcwd()+log_file_dir):
	os.system("mkdir logs")

if len(sys.argv) > 2: 
	if sys.argv[2] is not None:
		rd_process_center = sys.argv[2]

if len(sys.argv) > 3:
	if sys.argv[3] is not None: 
		rd_date = sys.argv[3]

if len(sys.argv) > 4: 
	if sys.argv[4] is not None: 
		rd_form = sys.argv[4]

day_length = int(rd_date_end[-2:]) - int(rd_date_start[-2:])
rd_dates = []
new_info = []
for i in range (0,day_length):
	new_day = int(rd_date_start[-2:]) + i
	if new_day > 9:
		rd_date = rd_date_start[:-2] + "0" + str(new_day)
	else:
		rd_date = rd_date_start[:-2] + str(new_day)
	rd_dates.append(rd_date)
	br = mechanize.Browser()
	br.open(rd_url)
	for form in br.forms():
		if "class" in form.attrs.keys():
			br.form = form

	br.form.find_control("in_Form").value=[rd_form]
	br.form.find_control("in_RD").value=rd_date

	response = br.submit()
	# tree = html.fromstring(response.read())
	rd_soup = BeautifulSoup(response.read(),'html.parser')
	rd_soup_tables = (rd_soup.find("div", class_="ym-cbox ym-clearfix")).find_all("table")

	# fetch new info
	for i,table in enumerate(rd_soup_tables):
		table_head = table.find("thead")
		if table_head.find("b") is not None:
			process_center = table_head.find("b").text.split(" ")[1]
			
			if process_center == rd_process_center: 
				general_info = []
				detailed_info = {}
				for td_tag in table.find("tr").find_all("td"):
					content = td_tag.find("b").text 
					general_info.append(content)

				detail_table = rd_soup_tables[i+1]

				for table_row in detail_table.find_all("tr"):
					this_row_info = table_row.find_all("td")
					info_type = this_row_info[0].text
					number = this_row_info[1].text
					percent = this_row_info[2].text
					start_date = this_row_info[3].text
					end_date = this_row_info[4].text
					detailed_info[info_type] = [number, percent, start_date, end_date]

	new_info.append([detailed_info[received_key],detailed_info[approved_key]])

# read the most recent file info from log file
log_files = glob.glob(os.getcwd()+log_file_dir+"/*.log")
last_time_date = None 
if len(log_files) > 0:
	# most_recent_file = min(glob.iglob(os.getcwd()+log_file_dir+'/*.log'),key=os.path.getctime)
	
	# sort log_files: 
	log_files.sort(key=lambda x: os.stat(os.path.join(log_file_dir,x)).st_mtime)
	log_files = log_files[::-1]

	for log_file in log_files:
		this_file_date = datetime.datetime.fromtimestamp(\
			os.path.getctime(log_file))
		if this_file_date.year == datetime.datetime.now().year \
		and this_file_date.month == datetime.datetime.now().month \
		and this_file_date.day == datetime.datetime.now().day:
			continue 
		elif datetime.datetime.now().day - this_file_date.day >= back_look or \
		this_file_date.day - datetime.datetime.now().day >= back_look:
			last_time_date = this_file_date
			most_recent_file = log_file
			break 

	old_dates = None 
	old_info = None 

	with open(most_recent_file) as f: 
		lines = f.readlines()
		old_dates = []
		old_info = []
		for line in lines:
			line_content = line.split(",")
			old_dates.append(line_content[0])
			old_info.append(line_content[1:])
	f.close()

# save new info into log file 
# date, number of received(percentage,date range),number of approved (percentage,date range)
new_file_path = os.getcwd()+log_file_dir+'/'+"date_range"+rd_date_start+"_"+rd_date_end+\
strftime("_inqury_%Y_%m_%d-%H_%M_%S", gmtime())+".log"

with open(new_file_path,'w') as f: 
	for t,date in enumerate(rd_dates):
		f.write(date+", "+new_info[t][0][0]+"("+new_info[t][0][1]+";"+new_info[t][0][2]+";"+\
			new_info[t][0][3]+")" + ", " +new_info[t][1][0]+"("+new_info[t][1][1]+";"+\
			new_info[t][1][2]+";"+new_info[t][1][3]+")"+"\n")
f.close()

#display content
print colored('#################################### USCIS Tracker RD ####################################','red',attrs=['bold'])
print colored('# Status of current inquiry:'+strftime("_inqury_%Y_%m_%d-%H_%M_%S", gmtime()),\
	'blue',attrs=['bold'])
for rd_time, new_info_entry in enumerate(new_info):
	
	print colored('# RD: '+rd_dates[rd_time]+' Approved: '+new_info_entry[0][0]+'('+new_info_entry[0][1]+'%'+' in date range: '+ \
		new_info_entry[0][2]+'--'+new_info_entry[0][3]+')' \
		+' Received: '+new_info_entry[1][0]+'('+new_info_entry[1][1]+'%'+' in date range: '+ \
		new_info_entry[1][2]+'--'+new_info_entry[1][3]+')', 'white',attrs=['bold','underline']) 
	print ''
print '------------------------------------------------------------------------------------------'
print colored('# Status of previous inquiry on '+str(last_time_date.year)+"-"+str(last_time_date.month)+"-"+str(last_time_date.day),\
	'blue',attrs=['bold'])
for rd_time, old_info_entry in enumerate(old_info):
	print colored('# RD: '+old_dates[rd_time] +' Approved: '+ old_info_entry[0] + ' Received: '+ old_info_entry[1], 'white', attrs=['bold','underline'])





