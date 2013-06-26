$(function(){
    var map = L.map('map', {attributionControl: false});

    // Bring global, for debugging..
    window.map = map;

    // add an OpenStreetMap tile layer
    var tile_url = 'http://{s}.tile.osm.org/{z}/{x}/{y}.png' // OSM
    // var tile_url = 'https://dnv9my2eseobd.cloudfront.net/v3/github.map-xgq2svrz/{z}/{x}/{y}.png' // OSM by GitHub

    options = {
        attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',
    }

    map.fitWorld().zoomIn();
    L.tileLayer(tile_url, options).addTo(map);

    // To create new icons
    // var icon = new L.Icon({
    //     iconUrl: 'https://dnv9my2eseobd.cloudfront.net/v3/marker/pin-s+438fd3.png',
    // });

    $.ajax({
        method: 'GET',
        url: '/api/layer/rshk/geojson-experiments/master/example.geojson',
        success: function(data) {
            L.geoJson(data, {
                onEachFeature: function (feature, layer) {
                    var table_html = "<table class=\"table-striped table-bordered\"><tbody>", key, val;
                    for (key in feature.properties) {
                        val = feature.properties[key];
                        table_html += "<tr><th>" + key + "</th><td>"
                            + val + "</td></tr>";
                    }
                    table_html += "</tbody></table>";
                    layer.bindPopup(table_html);

                    // To change the icon:
                    //layer.setIcon(icon);
                }
            }).addTo(map);
        }
    });

});
