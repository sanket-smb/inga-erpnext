// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.require("assets/erpnext/js/financial_statements_custom.js", function() {
	frappe.query_reports["Profit and Loss Statement Cstm"] = $.extend({},
		erpnext.financial_statements_custom);

//console.log("filetrs"+JSON.stringify(frappe.query_reports["Profit and Loss Statement Cstm"]["filters"]));
	frappe.query_reports["Profit and Loss Statement Cstm"]["filters"].push(





		{
			"fieldname":"project",
			"label": __("Project"),
			"fieldtype": "MultiSelect",
			get_data: function() {
				var projects = frappe.query_report.get_filter_value("project") || "";

				const values = projects.split(/\s*,\s*/).filter(d => d);
				const txt = projects.match(/[^,\s*]*$/)[0] || '';
				let data = [];

				frappe.call({
					type: "GET",
					method:'frappe.desk.search.search_link',
					async: false,
					no_spinner: true,
					args: {
						doctype: "Project",
						txt: txt,
						filters: {
							"name": ["not in", values]
						}
					},
					callback: function(r) {
						data = r.results;
					}
				});
				return data;
			}
		},
		{
			"fieldname": "accumulated_values",
			"label": __("Accumulated Values"),
			"fieldtype": "Check"
		},
//month_list = ['January','February','March','April',  'May',  'June',  'July', 'August','September','October', 'November','December']
		{
			"fieldname": "month_mp",
			"label": __("Month"),
			"fieldtype": "Select",
			"options": [
				{ "value": "January", "label": __("January") },
				{ "value": "February", "label": __("February") },
				{ "value": "March", "label": __("March") },
				{ "value": "April", "label": __("April") },
				{ "value": "May", "label": __("May") },
				{ "value": "June", "label": __("June") },
				{ "value": "July", "label": __("July") },
				{ "value": "August", "label": __("August") },
				{ "value": "September", "label": __("September") },
				{ "value": "October", "label": __("October") },
				{ "value": "November", "label": __("November") },
				{ "value": "December", "label": __("December") }
			],
			"default": "January",
			"reqd": 1
		}
	);

});




