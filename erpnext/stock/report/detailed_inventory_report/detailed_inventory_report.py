# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns()
	items = get_items(filters)
	sl_entries = get_stock_ledger_entries(filters, items)
	item_details = get_item_details(items, sl_entries)
	opening_row = get_opening_balance(filters, columns)

	data = []
	if opening_row:
		data.append(opening_row)

	for sle in sl_entries:
		item_detail = item_details[sle.item_code]
		# frappe.errprint(sle.voucher_type)
		# frappe.errprint(type(sle.voucher_type))
		out_rate = 0.0
		if sle.voucher_type == "Sales Invoice":
			out_rate = get_out_rate(sle.item_code,sle.voucher_no)
			frappe.errprint(sle.item_code)
		data.append([sle.date, sle.item_code,item_detail.item_name, item_detail.item_group,
			item_detail.item_category,
			item_detail.brand, sle.warehouse,
			sle.actual_qty, sle.qty_after_transaction,
			(sle.incoming_rate if sle.actual_qty > 0 else 0.0),out_rate,
			sle.voucher_type, sle.voucher_no,sle.supplier])

	return columns, data
def get_out_rate(item_code,invoice_number):
	selling_rate = 0.0
	si = frappe.get_doc("Sales Invoice", invoice_number)
	items_table = si.get("items")
	frappe.errprint(items_table)
	for item in items_table:
		if item.item_code == item_code:
			if item.base_net_rate :
				selling_rate = item.base_net_rate
			else:
				selling_rate = item.rate

	return selling_rate

def get_columns():
	columns = [
		_("Date") + ":Datetime:95", _("Item") + ":Link/Item:130",
		_("Item Name") + "::100", _("Item Group") + ":Link/Item Group:100",
		_("Item Category") + ":Link/Item Category:100",
		_("Brand") + ":Link/Brand:100",
		_("Warehouse") + ":Link/Warehouse:100",
		_("Qty") + ":Float:50", _("Balance Qty") + ":Float:100",
		{"label": _("Incoming Rate"), "fieldtype": "Currency", "width": 110,
			"options": "Company:company:default_currency"},
		{"label": _("Outgoing Rate"), "fieldtype": "Currency", "width": 110,
			"options": "Company:company:default_currency"},
		_("Voucher Type") + "::110",
		_("Voucher #") + ":Dynamic Link/" + _("Voucher Type") + ":100",
		_("Supplier") + "::110"
	]

	return columns

def get_stock_ledger_entries(filters, items):
	item_conditions_sql = ''
	if items:
		item_conditions_sql = 'and sle.item_code in ({})'\
			.format(', '.join(['"' + frappe.db.escape(i) + '"' for i in items]))

	return frappe.db.sql("""select concat_ws(" ", posting_date, posting_time) as date,
			item_code,supplier, warehouse, actual_qty, qty_after_transaction, incoming_rate, valuation_rate,
			stock_value, voucher_type, voucher_no, batch_no, serial_no, company, project
		from `tabStock Ledger Entry` sle
		where company = %(company)s and
			posting_date between %(from_date)s and %(to_date)s
			{sle_conditions}
			{item_conditions_sql}
			order by posting_date asc, posting_time asc, name asc"""\
		.format(
			sle_conditions=get_sle_conditions(filters),
			item_conditions_sql = item_conditions_sql
		), filters, as_dict=1)

def get_items(filters):
	conditions = []
	if filters.get("item_code"):
		conditions.append("item.name=%(item_code)s")
	else:
		if filters.get("brand"):
			conditions.append("item.brand=%(brand)s")
		if filters.get("item_group"):
			conditions.append(get_item_group_condition(filters.get("item_group")))
		if filters.get("item_category"):
			conditions.append(get_item_category_condition(filters.get("item_category")))

	items = []
	if conditions:
		items = frappe.db.sql_list("""select name from `tabItem` item where {}"""
			.format(" and ".join(conditions)), filters)
	return items

def get_item_details(items, sl_entries):
	item_details = {}
	if not items:
		items = list(set([d.item_code for d in sl_entries]))

	if not items:
		return item_details

	for item in frappe.db.sql("""
		select name, item_name, description, item_group,item_category, brand, stock_uom
		from `tabItem`
		where name in ({0})
		""".format(', '.join(['"' + frappe.db.escape(i,percent=False) + '"' for i in items])), as_dict=1):
			item_details.setdefault(item.name, item)

	return item_details

def get_sle_conditions(filters):
	conditions = []
	if filters.get("warehouse"):
		warehouse_condition = get_warehouse_condition(filters.get("warehouse"))
		if warehouse_condition:
			conditions.append(warehouse_condition)
	if filters.get("voucher_no"):
		conditions.append("voucher_no=%(voucher_no)s")
	if filters.get("batch_no"):
		conditions.append("batch_no=%(batch_no)s")
	if filters.get("project"):
		conditions.append("project=%(project)s")
	if filters.get("supplier"):
		conditions.append("(supplier=%(supplier)s or voucher_type='Sales Invoice')")


	return "and {}".format(" and ".join(conditions)) if conditions else ""

def get_opening_balance(filters, columns):
	if not (filters.item_code and filters.warehouse and filters.from_date):
		return

	from erpnext.stock.stock_ledger import get_previous_sle
	last_entry = get_previous_sle({
		"item_code": filters.item_code,
		"warehouse_condition": get_warehouse_condition(filters.warehouse),
		"posting_date": filters.from_date,
		"posting_time": "00:00:00"
	})
	row = [""]*len(columns)
	row[1] = _("'Opening'")
	for i, v in ((9, 'qty_after_transaction'), (11, 'valuation_rate'), (12, 'stock_value')):
			row[i] = last_entry.get(v, 0)

	return row

def get_warehouse_condition(warehouse):
	warehouse_details = frappe.db.get_value("Warehouse", warehouse, ["lft", "rgt"], as_dict=1)
	if warehouse_details:
		return " exists (select name from `tabWarehouse` wh \
			where wh.lft >= %s and wh.rgt <= %s and warehouse = wh.name)"%(warehouse_details.lft,
			warehouse_details.rgt)

	return ''

def get_item_group_condition(item_group):
	item_group_details = frappe.db.get_value("Item Group", item_group, ["lft", "rgt"], as_dict=1)
	if item_group_details:
		return "item.item_group in (select ig.name from `tabItem Group` ig \
			where ig.lft >= %s and ig.rgt <= %s and item.item_group = ig.name)"%(item_group_details.lft,
			item_group_details.rgt)

	return ''

def get_item_category_condition(item_category):
	# item_group_details = frappe.db.get_value("Item Category", item_category,"", as_dict=1)
	return "item.item_category = '%s'"%(item_category)
	# if item_group_details:
	# 	return "item.item_category in (select ig.name from `tabItem Category` ig \
	# 		where ig.lft >= %s and ig.rgt <= %s and item.item_category = ig.name)"%(item_group_details.lft,
	# 		item_group_details.rgt)

	# return ''
