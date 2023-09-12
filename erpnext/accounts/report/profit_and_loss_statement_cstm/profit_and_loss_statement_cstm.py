# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from erpnext.accounts.report.financial_statements_custom import (get_period_list, get_columns, get_data)

def execute(filters=None):
	period_list = get_period_list(filters.from_fiscal_year, filters.to_fiscal_year,
		filters.periodicity, filters.accumulated_values, filters.company)

	income = get_data(filters.company, "Income", "Credit", period_list, filters = filters,
		accumulated_values=filters.accumulated_values,
		ignore_closing_entries=True, ignore_accumulated_values_for_fy= True)

	expense = get_data(filters.company, "Expense", "Debit", period_list, filters=filters,
		accumulated_values=filters.accumulated_values,
		ignore_closing_entries=True, ignore_accumulated_values_for_fy= True)

	net_profit_loss = get_net_profit_loss(income, expense, period_list, filters.company, filters.presentation_currency)

	data = []
	#data.extend(income or [])
	#suresh_custom_start.
	mode_of_payments_list = get_mode_of_payments_list()
        company = filters.company
	for mode_of_payment in mode_of_payments_list :
		month_wise_mop_amount = get_month_wise_mop_amount(mode_of_payment,filters.from_fiscal_year) 
		total_mop_amount = 0
		month_list = ['January','February','March','April',  'May',  'June',  'July', 'August',
		'September','October', 'November','December']
		for month in month_list:
			if month_wise_mop_amount[month]:
				total_mop_amount += month_wise_mop_amount[month]
		if filters.month_mp == "January":
			data.append(["",mode_of_payment,
			frappe.db.get_value("Company", company, "default_currency"),
			month_wise_mop_amount["January"] ])
		if filters.month_mp == "February":
			data.append(["",mode_of_payment,
			frappe.db.get_value("Company", company, "default_currency"),
			month_wise_mop_amount["February"]])
		if filters.month_mp == "March":
			data.append(["",mode_of_payment,
			frappe.db.get_value("Company", company, "default_currency"),
			month_wise_mop_amount["March"]])
		if filters.month_mp == "April":
			data.append(["",mode_of_payment,
			frappe.db.get_value("Company", company, "default_currency"),
			month_wise_mop_amount["April"]])
		if filters.month_mp == "May":
			data.append(["",mode_of_payment,
			frappe.db.get_value("Company", company, "default_currency"),
			month_wise_mop_amount["May"]])
		if filters.month_mp == "June":
			data.append(["",mode_of_payment,
			frappe.db.get_value("Company", company, "default_currency"),
			month_wise_mop_amount["June"]])
		if filters.month_mp == "July":
			data.append(["",mode_of_payment,
			frappe.db.get_value("Company", company, "default_currency"),
			month_wise_mop_amount["July"]])
		if filters.month_mp == "August":
			data.append(["",mode_of_payment,
			frappe.db.get_value("Company", company, "default_currency"),
			month_wise_mop_amount["August"]])
		if filters.month_mp == "September":
			data.append(["",mode_of_payment,
			frappe.db.get_value("Company", company, "default_currency"),
			month_wise_mop_amount["September"]])
		if filters.month_mp == "October":
			data.append(["",mode_of_payment,
			frappe.db.get_value("Company", company, "default_currency"),
			month_wise_mop_amount["October"]])
		if filters.month_mp == "November":
			data.append(["",mode_of_payment,
			frappe.db.get_value("Company", company, "default_currency"),
			month_wise_mop_amount["November"]]
			)
		if filters.month_mp == "December":
			data.append(["",mode_of_payment,
			frappe.db.get_value("Company", company, "default_currency"),
			month_wise_mop_amount["December"]]
			)
	
		#month_wise_mop_amount = month_wise_mop_amount()

	#suresh_custom_end.

	data.extend(expense or [])
	if net_profit_loss:
		data.append(net_profit_loss)

	columns = get_columns(filters.month_mp,filters.periodicity, period_list, filters.accumulated_values, filters.company)

	#suresh_custom_start.
	columns.insert(1,
	{
		"fieldname": "mode_f_payment",
		"label": _("Mode Of Payment"),
		"fieldtype": "Link",
		"options": "Mode of Payment"
	}
	)
	#suresh_custom_end


	chart = get_chart_data(filters, columns, income, expense, net_profit_loss)

	return columns, data, None, chart

def get_net_profit_loss(income, expense, period_list, company, currency=None, consolidated=False):
	total = 0
	net_profit_loss = {
		"account_name": "'" + _("Profit for the year") + "'",
		"account": "'" + _("Profit for the year") + "'",
		"warn_if_negative": True,
		"currency": frappe.db.get_value("Company", company, "default_currency")
	}

	has_value = False

	for period in period_list:
		key = period if consolidated else period.key
		total_income = flt(income[-2][key], 3) if income else 0
		total_expense = flt(expense[-2][key], 3) if expense else 0

		net_profit_loss[key] = total_income - total_expense

		if net_profit_loss[key]:
			has_value=True

		total += flt(net_profit_loss[key])
		net_profit_loss["total"] = total

	if has_value:
		return net_profit_loss

def get_chart_data(filters, columns, income, expense, net_profit_loss):
	labels = [d.get("label") for d in columns[2:]]

	income_data, expense_data, net_profit = [], [], []

	for p in columns[2:]:
		if income:
			income_data.append(income[-2].get(p.get("fieldname")))
		if expense:
			expense_data.append(expense[-2].get(p.get("fieldname")))
		if net_profit_loss:
			net_profit.append(net_profit_loss.get(p.get("fieldname")))

	datasets = []
	if income_data:
		datasets.append({'name': 'Income', 'values': income_data})
	if expense_data:
		datasets.append({'name': 'Expense', 'values': expense_data})
	if net_profit:
		datasets.append({'name': 'Net Profit/Loss', 'values': net_profit})

	chart = {
		"data": {
			'labels': labels,
			'datasets': datasets
		}
	}

	if not filters.accumulated_values:
		chart["type"] = "bar"
	else:
		chart["type"] = "line"

	return chart

#suresh_custom_start
def get_mode_of_payments_list():
	mode_of_payments_dic =  frappe.db.sql("""select name from `tabMode of Payment`""", as_dict=1)
	print("suresh mode_of_payments_list with dic",mode_of_payments_dic)
	mode_of_payments_list = []
	for mode_of_payment in mode_of_payments_dic:
		mode_of_payments_list.append( mode_of_payment["name"] )
	print("suresh mode_of_payments_list new",mode_of_payments_list)
	return mode_of_payments_list

def get_month_wise_mop_amount(mode_of_payment,year):
	month_list = ['January','February','March',  'April',  'May',  'June',  'July', 'August','September','October', 'November','December']
	month_wise_mop_amount_dic = {}
	for month in month_list:
		amount = frappe.db.sql("""select sum(sip.amount) as total_amount from `tabSales Invoice` si,`tabSales Invoice Payment` sip  where si.status="Paid" and si.name = sip.parent and sip.mode_of_payment=%s and MONTHNAME(si.posting_date)=%s and YEAR(si.posting_date)=%s;""",(mode_of_payment,month,year), as_dict=1)
		moonth_mop_amount =	{month: amount[0]["total_amount"]}
		month_wise_mop_amount_dic.update( moonth_mop_amount)
	print ("----month_wise_mop_amount_dic ",month_wise_mop_amount_dic)
	return month_wise_mop_amount_dic






#suresh_custom_end
