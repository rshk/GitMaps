var Application = window.Application = (function(){
    var Application = {};

    // Modal dialog for the properties editing form
    var modal_dialog; /*= $(
        '<div class="modal hide fade" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">' +
        // '<div class="modal fade">' +
        '  <div class="modal-header">' +
        '    <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>' +
        '    <h3>Modal header</h3>' +
        '  </div>' +
        '  <div class="modal-body">' +
        '    <p>One fine body</p>' +
        '  </div>' +
        '  <div class="modal-footer">' +
        '    <button class="btn" data-dismiss="modal" aria-hidden="true">Close</button>' +
        '    <button class="btn btn-primary">Save changes</button>' +
        '  </div>' +
        '</div>');
    $(function(){$('body').append(modal_dialog)});
    modal_dialog.modal({show:true});
*/
    var initCommon = function() {
        modal_dialog = $(
            // '<div class="modal hide fade" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">' +
            '<div class="modal fade">' +
            '  <div class="modal-header">' +
            '    <button type="button" class="close" data-dismiss="modal">×</button>' +
            '    <h3>Modal header</h3>' +
            '  </div>' +
            '  <div class="modal-body">' +
            '    <p>One fine body</p>' +
            '  </div>' +
            '  <div class="modal-footer">' +
            '    <button class="btn" data-dismiss="modal" aria-hidden="true">Close</button>' +
            '    <button class="btn btn-primary" data-role="save">Save changes</button>' +
            '  </div>' +
            '</div>').appendTo('body');
        modal_dialog.modal({show:false});

        modal_dialog.on('click', 'button[data-role="save"]', function(){
            modal_dialog.trigger('save');
        });

        modal_dialog.bind('hidden', function(){
            modal_dialog.find('.modal-header h3').text('Dialog title');
            modal_dialog.find('.modal-body').html('');
        });
    };

    var showModal = function(options) {
        options = $.extend({
            title: "Dialog message",
            body: "Dialog body",
            save: null
        }, options);
        modal_dialog.find('.modal-header h3').text(options.title);
        modal_dialog.find('.modal-body').html(options.body);
        modal_dialog
            .unbind('save')
            .bind('save', function(){
                try {
                    if (options.save) {
                        options.save({dialog: modal_dialog});
                    }
                }
                catch (e) {
                    alert("Error! " + e);
                    return;
                }
                modal_dialog.modal('hide');
        });
        modal_dialog.modal('show');
    };

    var templates = {
        propertiesTable: function(context){
            var rendered, key, val, _ref;
            rendered = "<table class=\"table table-striped table-bordered table-hover table-condensed\"><tbody>";
            for (key in (_ref = context.feature.properties)) {
                val = _ref[key];
                rendered += "<tr><th>" + key + "</th><td>" + val + "</td></tr>";
            }
            rendered += "</tbody></table>";
            return rendered;
        }
    };

    var initializeBaseMap = function(geojson_url, tile_url) {
        initCommon();
        var map = L.map('map');
        var options = {
            attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',};
        L.tileLayer(tile_url, options).addTo(map);
        return map;
    };

    var initializeViewer = function(geojson_url, tile_url) {
        var map = initializeBaseMap(geojson_url, tile_url);

        $.ajax({
            method: 'GET',
            url: geojson_url,
            success: function(data) {
                var layer = L.geoJson(data, {
                    onEachFeature: function (feature, layer) {
                        var table_html = templates.propertiesTable({feature: feature});
                        layer.bindPopup(table_html);

                        // To change the icon:
                        //layer.setIcon(icon);
                    }
                }).addTo(map);
                try {
                    map.fitBounds(layer.getBounds());
                }
                catch (e) {
                    map.fitWorld();
                }
            },
            error: function() {
                alert("Error while getting data! Maybe you want to create a new map?");
            }
        });
        return map;
    };

    var initializeEditor = function(geojson_url, tile_url) {
        var map = initializeBaseMap(geojson_url, tile_url);

        var SaveButtonControl = L.Control.extend({
            options: {
                position: 'bottomleft'
            },
            onAdd: function (map) {
                // create the control container with a particular class name
                var container = L.DomUtil.create('div'),
                    $container = $(container);

                $container.html('<button type="button" class="btn btn-primary">Save changes</button>')
                $container.find('button').click(function(){
                    if (!map.editableLayer) return;
                    var data = JSON.stringify(map.editableLayer.toGeoJSON());

                    $.ajax({
                        method: 'PUT',
                        contentType: 'application/json',
                        url: geojson_url,
                        data: data,
                        success: function(){
                            alert("Data saved with success!");
                        },
                        error: function(){
                            alert("Error while saving stuff!");
                        }
                    });

                });

                // ... initialize other DOM elements, add listeners, etc.

                return container;
            }
        });

        map.addControl(new SaveButtonControl());

        var addEditingPopup = function(feature, layer) {
            //var table_html = templates.propertiesTable({feature: feature});

            // todo: the pop-up content should be generated dynamically when opening...
            // var popup_content = ("<div>" + table_html + "<div style='text-align:center;'><button type='button' class='btn btn-small'>Edit</button></div></div>");

            layer.bindPopup('Loading...');

            layer.on('popupopen', function(e) {
                var table_html = templates.propertiesTable({feature: feature});
                var popup_content = ("<div>" + table_html + "<div style='text-align:center;'><button type='button' class='btn btn-small'>Edit</button></div></div>");
                e.popup.setContent(popup_content);
                $(e.popup._container).find('button').click(function(){

                    //console.log('Will open the thing');
                    // todo: open feature editing dialog
                    // var dialog_body = modal_dialog.find('modal-body');
                    // dialog_body.html('Edit feature<br>');
                    var textarea = $('<textarea style="width:500px;height:300px;">');
                    textarea.val(JSON.stringify(feature.properties,true,2));
                    // dialog_body.append(textarea);

                    layer.closePopup();

                    showModal({
                        title: 'Edit feature',
                        body: textarea,
                        save: function(e) {
                            feature.properties =
                                $.parseJSON(e.dialog.find('textarea').val());
                        }
                    });
                });

            });

            layer.on('popupclose', function(e){
                e.popup.setContent('Loading...');
            });

            // $(popup_content).find('button').bind('click', function(){
            //     modal_dialog.find('.modal-body').html(templates.propertiesTable({feature: feature}));
            //     modal_dialog.modal('show');
            // });

            /*layer.on('click', function(e){
                console.log('I Got clicked!');
            });*/

            // var table_html = "<table class=\"table-striped table-bordered\"><tbody>", key, val;
            // for (key in feature.properties) {
            //     val = feature.properties[key];
            //     table_html += "<tr><th>" + key + "</th><td>"
            //         + "<input type='text' value='"+val+"'>"
            //         + "</td></tr>";
            // }
            // table_html += "</tbody></table>";
            // layer.bindPopup(table_html);

            // todo: on popup dismiss, we want to update the feature...
        };


        var initEditLayer = function(map, layer) {
            // Initialize the draw control and pass it the FeatureGroup of editable layers
            //layer.addTo(map);
            map.addLayer(layer);
            map.editableLayer = layer;

            try {
                map.fitBounds(layer.getBounds());
            }
            catch (e) {
                map.fitWorld();
            }

            var drawControl = new L.Control.Draw({
                position: 'topleft',
                edit: {featureGroup: map.editableLayer}
            });
            map.addControl(drawControl);

            // Keep edited things
            map.on('draw:created', function (e) {
                console.log("Draw created", e);
                var type = e.layerType,
                    layer = e.layer;

                // todo: we should make more checks here...
                if (type === 'marker') {
                    if (layer.feature === undefined) {
                        layer.feature = {};
                    }
                    layer.feature.properties = {};
                    addEditingPopup(layer.feature.properties, layer);
                }
                map.editableLayer.addLayer(layer);
           });
        };



        // Retrieve the GeoJSON file from the API and start editing..
        $.ajax({
            method: 'GET',
            url: geojson_url,
            success: function(data) {
                var layer = L.geoJson(data, {
                    onEachFeature: addEditingPopup
                });
                initEditLayer(map, layer);
            },
            error: function() {
                alert("Error while fetching file. Saving will attempt to create a new one!");
                var layer = L.featureGroup();
                initEditLayer(map, layer);
            }
        });
        return map;
        };

    return {
        initializeViewer: initializeViewer,
        initializeEditor: initializeEditor,
    };
})();
