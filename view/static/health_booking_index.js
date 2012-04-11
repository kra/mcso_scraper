$(document).ready(function() {

    function getURLParameter(name) {
        return decodeURIComponent((new RegExp('[?|&]' + name + '=' + '([^&;]+?)(&|#|;|$)').exec(location.search)||[,""])[1].replace(/\+/g, '%20'))||'';
    }

    var health_booking_index_href = '../data/health/booking_index'
    health_booking_index_href += '?_=' + Number(new Date());
    var b_table = $('#health_booking_table').dataTable({
        "bProcessing": true,
        "bServerSide": true,
        "sAjaxSource": health_booking_index_href,
        "fnServerParams": function ( aoData ) {
            aoData.push(
                { "name": "period",
                  "value": getURLParameter('period') } );
            aoData.push(
                { "name": "booking_date_end",
                  "value": $('#booking_date_end').val() } ) ;},

        "aoColumns": [
            { "sTitle": "Period Start", "bSortable": false },
            { "sTitle": "Bookings Updated", "bSortable": false },
            { "sTitle": "Bookings Booked", "bSortable": false },],
    }).columnFilter({
        "sPlaceHolder": "foot",
        "aoColumns": [
            null, null
        ]});

});    
