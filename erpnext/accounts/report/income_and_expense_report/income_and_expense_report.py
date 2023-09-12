# Copyright (c) 2013, ER and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from frappe.utils import getdate, validate_email_add, today, add_years, flt
from frappe.utils.nestedset import get_descendants_of

def execute(filters=None):
    columns, data = [], []
    columns = get_columns(filters)
    data = get_details(columns,filters)
    return columns, data

def get_columns(filters):
    columns = [
        _("Type") + ":Data:350",_("Total") + ":Currency:120"
    ]
    mode_of_payment= [x.get("name") for x in frappe.get_all('Mode of Payment',filters={'company': filters.get("company")},fields = ["name"],order_by="name")]

    return columns

def get_conditions(filters):
    conditions= "and si.company='{0}' and si.posting_date>='{1}' and si.posting_date<='{2}'".format(filters.get("company"),filters.get("from_date"),filters.get("to_date"))
    return conditions

def get_details(columns,filters):
    data=[]
    sales=frappe.db.sql("""select sum(si.rounded_total),sum(base_change_amount) from `tabSales Invoice` si WHERE 
        si.docstatus=1 and si.company='%s' and si.posting_date>='%s' and si.posting_date<='%s'"""%(filters.get("company"),filters.get("from_date"),filters.get("to_date")),as_list=1)
    
    receipts=frappe.db.sql("""select sip.mode_of_payment,sum(sip.base_amount) from `tabSales Invoice Payment` sip,`tabSales Invoice` si 
        where si.name=sip.parent and si.docstatus=1 and si.company='%s' and si.posting_date>='%s' and si.posting_date<='%s' group by sip.mode_of_payment"""%(filters.get("company"),filters.get("from_date"),filters.get("to_date")),as_list=1)
    
    si_mop_mapper={}
    sales=[]
    total_sales=0.0
    for mop in receipts:
        si_mop_mapper[mop[0]]=mop[1]
        total_sales+=flt(mop[1])
        sales.append(mop)
    for sale in sales:
        data.append(sale)
    data.append(["Total Sales Income",total_sales])

    total_other_exp=0
    childs=get_descendants_of('Account','Hair Treatment Product Expense - IBS')
    childs1=get_descendants_of('Account','Steam Bath Expense - IBS')
    childs2=get_descendants_of('Account','Indirect Expenses - IBS')
    childs3=['Hand Tools - IBS']
    frappe.errprint('","'.join(childs+childs1+childs2+childs3))
    other_expences=frappe.db.sql("""select jva.account,sum(jva.debit)-sum(jva.credit) from `tabJournal Entry` jv,`tabJournal Entry Account` jva 
        where jv.name=jva.parent and jv.docstatus=1 and jv.company="%s" and jv.posting_date>="%s" and jv.posting_date<="%s"
        and jva.account in ("%s") group by jva.account
        """%(filters.get("company"),filters.get("from_date"),filters.get("to_date"),'","'.join(childs+childs1+childs2+childs3)),as_list=1)
    for exp in other_expences:
        total_other_exp+=flt(exp[1])
    data.append(['',''])
    for exp in other_expences:
        data.append(exp)
    data.append(["Total Other Expenses",total_other_exp])
    data.append(['',''])
    payments=frappe.db.sql("""select sum(paid_amount) from `tabPayment Entry` where docstatus=1 and company='%s' 
         and posting_date>='%s' and posting_date<='%s' """%(filters.get("company"),filters.get("from_date"),filters.get("to_date")),as_list=1)[0][0] or 0

    data.append(["Total Pamyents",payments])
    data.append(['',''])
    pinv=frappe.db.sql("""select sum(grand_total) from `tabPurchase Invoice` where docstatus=1 and company='%s' and 
        posting_date>='%s' and posting_date<='%s' """%(filters.get("company"),filters.get("from_date"),filters.get("to_date")),as_list=1)[0][0] or 0
    data.append(["Total Purchase",pinv])
    net_total=flt(total_sales)-flt(total_other_exp)-flt(payments)
    data.append(["Total Net Balance",flt(net_total)])
    data.append(["Grant Total ",flt(net_total)-flt(pinv)])
    return data

