$(document).ready(function() {

    var charge_index_href = '../data/charge_index'
    $.getJSON(charge_index_href, function(index_objs) {
        var index_arrays = [];
        index_objs.map(function (obj) {
            index_arrays.push(
                [obj.charge_link, obj.status, obj.bail]);
        });
            
        $('#charge_table').dataTable({
  	  "aaData": index_arrays,
            "aoColumns": [
                { "sTitle": "charge" },
                { "sTitle": "status" },
                { "sTitle": "bail" }],
        });
    });
    
});    
