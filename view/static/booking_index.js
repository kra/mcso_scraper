$(document).ready(function() {

    var booking_index_href = '../data/booking_index'
    $.getJSON(booking_index_href, function(index_objs) {
        var index_arrays = [];
        index_objs.map(function (obj) {
            index_arrays.push(
                [obj.name_link, obj.age, obj.swisid, obj.race,
                 obj.gender, obj.arrestdate, obj.arrestingagency]);
        });
            
        $('#booking_table').dataTable({
  	  "aaData": index_arrays,
            "aoColumns": [
                { "sTitle": "name" },
                { "sTitle": "age" },
                { "sTitle": "swisid" },
                { "sTitle": "race" },
                { "sTitle": "gender" },
                { "sTitle": "arrestdate" },
                { "sTitle": "arrestingagency" }],
        });
    });
    
});    
