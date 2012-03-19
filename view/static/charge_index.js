$(document).ready(function() {

    $.datepicker.regional[""].dateFormat = 'yy-mm-dd';
    $.datepicker.setDefaults($.datepicker.regional['']);

    var charge_index_href = '../data/charge_index'
    charge_index_href += '?_=' + Number(new Date());
    $('#charge_table').dataTable({
        "bProcessing": true,
        "bServerSide": true,
        "sAjaxSource": charge_index_href,
        "aoColumns": [
            { "sTitle": "charge" },
            { "sTitle": "status" },
            { "sTitle": "parsed_bail"},
            { "sTitle": "parsed_arrestdate" },
            { "sTitle": "parsed_bookingdate", "bSearchable": true }]
    }).columnFilter({
        "sPlaceHolder": "foot",
        "aoColumns": [
            null, null, null, null,
            { "type": "date-range"}
        ]});
    
});    
