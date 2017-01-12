# at terminal window, run:
# python track_uscis_receipt_no.py <receipt_num_start> <number_of_receipts> <target_form_type> 
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

receipt_url = 'http://www.mycasetracker.org/index.php?dest=receipt'
receipt_num_start = 'SRC1790011000'
processing_center = receipt_num_start[:3]

number_of_receipts = '300'
number_of_intervals = 6
received_key = 'Case Was Approved'
approved_key = 'Case Was Received'
target_form_type = 'I131'

if len(sys.argv) > 1: 
	if sys.argv[1] is not None:
		receipt_no_start = sys.argv[1]

if len(sys.argv) > 2:
	if sys.argv[2] is not None: 
		number_of_receipts = sys.argv[2]
if len(sys.argv) > 3:
	if sys.argv[3] is not None:
		target_form_type = sys.argv[3]

new_info = []
receipt_starts = []
for interval in range(0,number_of_intervals): 
	current_start = processing_center+ str(int(receipt_num_start[3:]) + interval * int(number_of_receipts))
	receipt_starts.append(current_start)
	br = mechanize.Browser()
	br.open(receipt_url)

	for form in br.forms():
		if 'class' in form.attrs.keys():
			br.form = form 

	br.form.find_control("in_Receipt").value = current_start
	br.form.find_control("in_Num").value = number_of_receipts

	response = br.submit()

	rd_soup = BeautifulSoup(response.read(),'html.parser')
	rd_soup_tables = (rd_soup.find("div", class_="ym-cbox ym-clearfix")).find_all("table")
	
	for i,table in enumerate(rd_soup_tables):
		table_head = table.find("thead")
		if table_head.find("b") is not None:
			form_type = table_head.find("b").text.split(" ")[1]
			
			if form_type == target_form_type:
				general_info = []
				detailed_info = {}

				for td_tag in table.find("tr").find_all("td"):
					content = td_tag.find("b").text 
					general_info.append(content)

				detail_table = rd_soup_tables[i+1]

				for table_row in detail_table.find_all("tr"):
					this_row_info = table_row.find_all("td")
					info_type = this_row_info[0].text
					
					if info_type != received_key and info_type != approved_key:
						continue
					else:	
						number = this_row_info[1].text
						percent = this_row_info[2].text
						start_date = this_row_info[3].text
						end_date = this_row_info[4].text
						detailed_info[info_type] = [number, percent, start_date, end_date]
	new_info.append(detailed_info)

for i,info in enumerate(new_info):
	print colored('######################################################################')
	print colored('# Receipt number: '+receipt_starts[i]+'--'+processing_center+str( int(receipt_starts[i][3:]) + int(number_of_receipts)), 'blue',attrs=['bold']) 
	
	for key in info.keys():
		if key == approved_key:
			print colored('# Approved: '+info[key][0]+' '+info[key][1]+' '+info[key][2]+' '+info[key][3], 'white', attrs=['bold','underline'])
		elif key == received_key: 
			print colored('# Received: '+info[key][0]+' '+info[key][1]+' '+info[key][2]+' '+info[key][3], 'yellow', attrs=['bold'])

