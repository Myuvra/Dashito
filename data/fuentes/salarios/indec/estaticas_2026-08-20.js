$(document).ready(function () {
    if ($('#BotonesNav').children('button') != null) {
        if ($('#tabSelect').val() != 0 && $('#BotonesNav').children('button').eq($('#tabSelect').val()).length >0) {
            $('#BotonesNav').find('button').eq($('#tabSelect').val()).click();
        } else {
            firstSelect($('#BotonesNav').children('button').first());
        }
    }
})

function firstSelect(e) {
    var tab = $(e).attr('data-tab');
    $('body').find('.tabContent').each(function () {
        $(this).fadeOut(0, function () {
        });
    })
    $('#tab' + tab).fadeIn('normal');
    var countBtn = 0;
    $('#BotonesNav').find('button').each(function () {
        $(this).removeClass('btn-Activo');
    })

    $(e).addClass('btn-Activo');
    $('#BotonesNav').find('button').each(function () {
        countBtn++;
        if ($(this).hasClass('btn-Activo')) {
            return false;
        }
    })
    $('#tabSelect').val(countBtn);

}

    function SelectButton(e) {
        var tab = $(e).attr('data-tab');
        $('body').find('.tabContent').each(function () {
            $(this).fadeOut(0, function () {
            });
        })
        $('#tab' + tab).fadeIn('normal');
        var countBtn = 0;
        $('#BotonesNav').find('button').each(function () {   
            $(this).removeClass('btn-Activo');
        })

        $(e).addClass('btn-Activo');
        $('#BotonesNav').find('button').each(function () {
            countBtn++;
            if($(this).hasClass('btn-Activo')){
                return false;
            }
        })
        $('#tabSelect').val(countBtn);

        var View = window.location.href.split('/').pop();
        var url = View.split('-');

        View = url[0] + "-" + url[1] + "-" + url[2] + "-" + $('#tabSelect').val();

        window.history.pushState('', '', "/indec/web/" + View);
    }

    function SelectGrilla(e) {
        var tab = $(e).attr('data-tab');
        $('body').find('.tabContent').each(function () {
            $(this).fadeOut(0, function () {
            });
        })
        $('#tab' + tab).fadeIn('normal');

        $('#GrillaNav').find('button').each(function () {
            $(this).removeClass('btn-Activo');
        })
        $(e).addClass('btn-Activo');
    }

    function ShowHideCollapse(e) {
        $(e).parent().children('div').fadeToggle('normal');

        $('body').find('.downContent').each(function () {
            if ($(e).parent().children('div').attr('id') != $(this).attr('id')) {
                $(this).fadeOut(0, function () {
                });
            }       
        })
        
    }



    function iralbuscador() {
        var texto = document.getElementById("buscartxt").value;
        if (texto == '') {
            return false;
        }
        var direccion = "buscador.asp";
        direccion = direccion + "?t=" + texto;
        document.location.href = direccion;
    }